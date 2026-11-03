"""The fact record: every claim with its source, ownership and numbers.

A fact is one statement about the person's work. It says where it came
from (said, imported, inferred), how sure we are (confirmed or unsure),
what the person's part was (owned, led, contributed, observed) and the
numbers in it. When two sources disagree on a date or a number, that's a
conflict for the person to settle, never for the tool to pick.
"""
import re
from datetime import date

from copilot import store

SOURCES = ("said", "imported", "inferred")
OWNERSHIP = ("owned", "led", "contributed", "observed")
STOP = {"the", "a", "an", "and", "of", "to", "in", "for", "on", "by",
        "with", "from", "at", "my", "our", "i", "we", "was", "were"}


def _words(text):
    return {w for w in re.findall(r"[a-z]+", text.lower())
            if w not in STOP and len(w) > 2}


def _similar(a, b):
    wa, wb = _words(a), _words(b)
    return bool(wa and wb) and len(wa & wb) / len(wa | wb) >= 0.4


def _role(fact):
    return (fact.get("employer", "").lower().strip(),
            fact.get("title", "").lower().strip())


def _conflicts_between(new, old):
    found = []
    if _role(new) == _role(old) and new.get("employer"):
        for edge in ("start", "end"):
            if new.get(edge) and old.get(edge) and new[edge] != old[edge]:
                found.append({"field": "date",
                              "detail": f"{edge}: {new[edge]} vs {old[edge]}"})
    if _role(new)[0] == _role(old)[0] and \
            _similar(new["statement"], old["statement"]):
        units = {m["unit"]: m["value"] for m in old.get("metrics", [])}
        for metric in new.get("metrics", []):
            other = units.get(metric["unit"])
            if other is not None and other != metric["value"]:
                found.append({"field": "metric",
                              "detail": f"{metric['value']} vs {other} "
                                        f"{metric['unit']}"})
    return found


METRIC = re.compile(r"(\$)?(\d[\d,]*(?:\.\d+)?)\s*(%|[kmb]\b|x\b|"
                    r"[a-z]+)?", re.I)
SCALE = {"k": 1e3, "m": 1e6, "b": 1e9}


def parse_metrics(text):
    """Numbers in a statement with their units: '40%', '$2M', '6 hours'.
    Years (19xx, 20xx) are dates, not metrics."""
    found = []
    for dollar, number, unit in METRIC.findall(text):
        value = float(number.replace(",", ""))
        unit = (unit or "").lower()
        if not dollar and not unit and re.fullmatch(r"(19|20)\d\d", number):
            continue
        if unit in SCALE:
            value, unit = value * SCALE[unit], "$" if dollar else ""
        elif dollar:
            unit = "$"
        found.append({"value": value, "unit": unit or "count"})
    return found


def _live(user):
    return [f for f in store.list_kind(user, "fact")
            if not f.get("superseded_by")]


def add(user, statement, source="said", employer="", title="", start="",
        end="", ownership="contributed", metrics=None, confirmed=False,
        source_ref="", apply=False):
    if source not in SOURCES:
        return {"error": f"source must be one of {SOURCES}"}
    if ownership not in OWNERSHIP:
        return {"error": f"ownership must be one of {OWNERSHIP}"}
    if source == "inferred" and confirmed:
        return {"error": "An inferred fact can't be saved as confirmed. Ask "
                         "the person, then save it with source 'said'."}
    clean = []
    for m in metrics or []:
        try:
            clean.append({"value": float(m["value"]), "unit": str(m["unit"]),
                          "approx": bool(m.get("approx"))})
        except (KeyError, TypeError, ValueError):
            return {"error": "each metric needs a numeric value and a unit"}
    fact = {"statement": statement.strip()[:300], "source": source,
            "source_ref": source_ref[:60], "employer": employer,
            "title": title, "start": start, "end": end,
            "ownership": ownership, "metrics": clean,
            "confidence": "confirmed" if confirmed else "unsure",
            "confirmed_on": str(date.today()) if confirmed else None}
    conflicts = [{"with_fact_id": old["id"], "with": old["statement"], **c}
                 for old in _live(user)
                 for c in _conflicts_between(fact, old)]
    result = {"fact": fact, "conflicts": conflicts}
    if conflicts:
        result["ask"] = ("These disagree with something already saved. Ask "
                         "the person which is right, then fact_resolve.")
    if apply:
        same = next((old for old in _live(user)
                     if old["statement"].lower() == fact["statement"].lower()
                     and _role(old) == _role(fact)), None)
        if same:
            # The same claim from another source: one fact, more sources.
            seen = same.setdefault("also_in", [])
            if source_ref and source_ref not in seen:
                seen.append(source_ref[:60])
            if confirmed and same["confidence"] != "confirmed":
                same["confidence"] = "confirmed"
                same["confirmed_on"] = fact["confirmed_on"]
            store.put(user, "fact", same, record_id=same["id"])
            result.update(fact_id=same["id"], merged=True)
        else:
            result["fact_id"] = store.put(user, "fact", fact)
    return result


def import_bullets(user, bullets, label):
    """Each resume bullet becomes an imported, unsure fact."""
    ids, conflicts = [], []
    for bullet in bullets:
        added = add(user, bullet, source="imported", source_ref=label,
                    metrics=parse_metrics(bullet), apply=True)
        ids.append(added["fact_id"])
        conflicts += added["conflicts"]
    return {"facts": len(set(ids)), "conflicts": len(conflicts)}


def confirmed_facts(user):
    """Confirmed, current facts, for drafts."""
    return [f for f in _live(user) if f["confidence"] == "confirmed"]


def conflicts(user):
    live = _live(user)
    found = []
    for i, new in enumerate(live):
        for old in live[:i]:
            for c in _conflicts_between(new, old):
                found.append({"fact_ids": [old["id"], new["id"]],
                              "statements": [old["statement"],
                                             new["statement"]], **c})
    return {"conflicts": found,
            "say": "Ask about one conflict at a time: which is right?"
            if found else "No conflicts."}


def resolve(user, keep_id, drop_id, confirm_kept=True):
    keep, drop = store.get(user, keep_id), store.get(user, drop_id)
    if keep is None or drop is None:
        return {"error": "no such fact"}
    drop["superseded_by"] = keep_id
    store.put(user, "fact", drop, record_id=drop_id)
    if confirm_kept and keep.get("source") != "inferred":
        keep["confidence"] = "confirmed"
        keep["confirmed_on"] = str(date.today())
        store.put(user, "fact", keep, record_id=keep_id)
    return {"kept": keep_id, "dropped": drop_id,
            "kept_confidence": keep["confidence"]}


def confirmed_statements(user):
    """Confirmed, current statements: what drafts may rely on."""
    return [f["statement"] for f in confirmed_facts(user)]
