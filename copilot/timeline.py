"""Resume evolution: append-only snapshots, timeline, diffs and a proof.

Every snapshot is a new record (kind "snapshot"); nothing here updates
or deletes one, so a version that brought old problems back stays
visible as a regression instead of being rewritten. Every check is
computed from the stored text, never claimed:

- level_tags: internal level labels (L5, E4, IC3, SDE II) that mean
  nothing outside one company;
- unsupported_numbers: numbers no confirmed fact holds (likely invented);
- summary_issues: the summary doesn't lead with a number, or uses
  filler words;
- internal_names: shorthand the person listed as internal-only (team or
  org nicknames), which recruiters won't recognise.
"""
import difflib
import hashlib
import re

from copilot import facts, store
from copilot.scoring import BANNED_WORDS, _bullets

MAX_TEXT = 40_000
LEVEL_TAG = re.compile(r"\b(?:[LEM]\d{1,2}|IC\d{1,2}|SDE[ -]?(?:I{1,3}|\d))\b")
YEAR = re.compile(r"\b(?:19|20)\d\d\b")
FILLER = ("passionate", "results-driven", "results driven", "dynamic",
          "go-getter", "self-starter", "rockstar", "ninja", "synergy",
          "hard-working", "detail-oriented") + tuple(BANNED_WORDS)
NOT_ROLES = re.compile(r"educat|certif|award|honou?r|publication|course",
                       re.I)
CHANGED = 0.6          # bullets this similar count as edited, not new


def _words(text):
    return len(text.split())


def _heading(line):
    return (0 < _words(line) <= 4 and not YEAR.search(line)
            and not line.startswith(("-", "*", "•")) and "|" not in line
            and "@" not in line)


def _roles(text):
    """Role lines: not bullets, short, carrying a year, and not under an
    Education, Certifications or Awards heading."""
    roles, skip = [], False
    for ln in text.splitlines():
        line = ln.strip()
        if _heading(line):
            skip = bool(NOT_ROLES.search(line))
            continue
        if (line and not skip and not line.startswith(("-", "*", "•"))
                and YEAR.search(line) and _words(line) <= 16):
            roles.append(line)
    return roles


def _summary(text):
    """The paragraph under a Summary heading, else the first long lines
    before any bullet or dated line. Contact lines are skipped."""
    lines = [ln.strip() for ln in text.splitlines()]
    for i, line in enumerate(lines):
        if _heading(line) and re.search(r"summary|profile|about", line,
                                        re.I):
            body = []
            for nxt in lines[i + 1:]:
                if body and (_heading(nxt) or YEAR.search(nxt)
                             or nxt.startswith(("-", "*", "•"))):
                    break
                if nxt:
                    body.append(nxt)
            return " ".join(body)
    body = []
    for line in lines:
        if line.startswith(("-", "*", "•")) or YEAR.search(line):
            break
        if _words(line) >= 8 and "@" not in line and line.count("|") < 2:
            body.append(line)
    return " ".join(body)


def checks(user, text, avoid_terms=()):
    """Problems in one version, computed from its text."""
    held = {(m["value"], m["unit"]) for f in facts.confirmed_facts(user)
            for m in f.get("metrics") or facts.parse_metrics(
                f.get("statement", ""))}
    invented = [b for b in _bullets(text)
                if any((m["value"], m["unit"]) not in held
                       for m in facts.parse_metrics(b))]
    summary = _summary(text)
    style = []
    if summary:
        if not facts.parse_metrics(LEVEL_TAG.sub("", summary)):
            style.append("no numbers up front")
        style += [w for w in FILLER if w in summary.lower()]
    low = text.lower()
    return {"level_tags": sorted(set(LEVEL_TAG.findall(text))),
            "unsupported_numbers": invented,
            "summary_issues": style,
            "internal_names": [t for t in avoid_terms if t.lower() in low]}


def _problems(found):
    return {k for k, v in found.items() if v}


def snapshot(user, text="", label="", note="", from_version="",
             rendered_file="", parent="", avoid_terms=None):
    """Save one version. Append-only: never replaces an earlier one."""
    if from_version:
        version = store.get(user, from_version)
        if not version or "text" not in version:
            return {"error": "No stored resume version with that id. "
                             "Call resume_versions."}
        text = text or version["text"]
        label = label or version.get("label", "")
    text = (text or "").strip()
    if not text:
        return {"error": "Paste the resume text, or name a stored version "
                         "with from_version."}
    if len(text) > MAX_TEXT:
        return {"error": f"That's over {MAX_TEXT:,} characters. Paste the "
                         "resume itself, not a whole folder."}
    earlier = _ordered(user)
    if parent and not any(s["id"] == parent for s in earlier):
        return {"error": "parent must be the id of an earlier snapshot."}
    parent = parent or (earlier[-1]["id"] if earlier else "")
    if avoid_terms is None:          # keep the list from the last snapshot
        avoid_terms = earlier[-1].get("avoid_terms", []) if earlier else []
    avoid_terms = [t.strip() for t in avoid_terms if t and t.strip()][:30]
    found = checks(user, text, avoid_terms)
    body = {"label": label or f"Version {len(earlier) + 1}",
            "text": text, "note": note.strip(),
            "sha256": hashlib.sha256(text.encode()).hexdigest(),
            "words": _words(text), "roles": _roles(text),
            "bullets": len(_bullets(text)), "parent": parent,
            "rendered_file": rendered_file.strip(), "checks": found,
            "avoid_terms": avoid_terms,
            "seq": len(earlier) + 1}
    duplicate = next((s for s in earlier if s["sha256"] == body["sha256"]),
                     None)
    record_id = store.put(user, "snapshot", body)
    result = {"id": record_id, "label": body["label"], "words": body["words"],
              "bullets": body["bullets"], "roles": body["roles"],
              "checks": found, "parent": parent}
    if duplicate:
        result["same_as"] = duplicate["label"]
    back = _regressions(user, {**body, "id": record_id})
    if back:
        result["regressions"] = back
    return result


def _ordered(user):
    return sorted(store.list_kind(user, "snapshot"),
                  key=lambda s: (s.get("seq", 0), s["updated"]))


def _ancestors(by_id, snap):
    seen, chain, cur = set(), [], by_id.get(snap.get("parent"))
    while cur and cur["id"] not in seen:
        seen.add(cur["id"])
        chain.append(cur)
        cur = by_id.get(cur.get("parent"))
    return chain


def _regressions(user, snap, ordered=None):
    """Problems this version has that an earlier ancestor had fixed."""
    ordered = ordered or _ordered(user)
    by_id = {s["id"]: s for s in ordered}
    by_id[snap["id"]] = snap
    now = _problems(snap["checks"])
    chain = _ancestors(by_id, snap)
    back = []
    for problem in sorted(now):
        had = [a for a in chain if problem in _problems(a["checks"])]
        clean = [a for a in chain if problem not in _problems(a["checks"])]
        if had and clean and chain.index(clean[0]) < chain.index(had[0]):
            back.append({"check": problem, "clean_in": clean[0]["label"],
                         "found": snap["checks"][problem]})
    return back


def _summary_line(diff):
    parts = []
    for key, sign in (("added", "+"), ("removed", "-"), ("changed", "~")):
        if diff[key]:
            parts.append(f"{sign}{len(diff[key])} {key}")
    delta = diff["word_delta"]
    parts.append(f"{'+' if delta >= 0 else ''}{delta} words")
    return ", ".join(parts)


def timeline(user):
    """Every snapshot in order, with what changed against its parent."""
    ordered = _ordered(user)
    by_id = {s["id"]: s for s in ordered}
    rows = []
    for i, snap in enumerate(ordered):
        parent = by_id.get(snap.get("parent"))
        row = {"id": snap["id"], "label": snap["label"],
               "saved": snap["updated"], "words": snap["words"],
               "bullets": snap["bullets"], "note": snap.get("note", ""),
               "problems": sorted(_problems(snap["checks"]))}
        if parent:
            row["from"] = parent["label"]
            row["changed"] = _summary_line(_diff(parent, snap))
            if i and parent["id"] != ordered[i - 1]["id"]:
                row["branch"] = (f"Built from {parent['label']}, not the "
                                 f"latest ({ordered[i - 1]['label']}).")
        back = _regressions(user, snap, ordered)
        if back:
            row["regressions"] = back
        if snap.get("rendered_file"):
            row["rendered_file"] = snap["rendered_file"]
        rows.append(row)
    return {"versions": rows, "count": len(rows),
            "note": "Snapshots are never edited or removed one at a time, "
                    "so a step back stays visible." if rows else
                    "No snapshots yet. Save one with resume_snapshot."}


def _diff(old, new):
    before, after = _bullets(old["text"]), _bullets(new["text"])
    gone = [b for b in before if b not in after]
    fresh = [b for b in after if b not in before]
    changed = []
    for b in list(fresh):
        best = max(gone, key=lambda g: difflib.SequenceMatcher(
            None, g, b).ratio(), default=None)
        if best and difflib.SequenceMatcher(None, best, b).ratio() >= CHANGED:
            changed.append({"before": best, "after": b})
            gone.remove(best)
            fresh.remove(b)
    return {"added": fresh, "removed": gone, "changed": changed,
            "word_delta": new["words"] - old["words"]}


def _find(user, ref, ordered):
    for snap in ordered:
        if ref in (snap["id"], snap["label"]):
            return snap
    return None


def diff(user, a="", b=""):
    """Compare two snapshots (default: the first and the latest)."""
    ordered = _ordered(user)
    if len(ordered) < 2 and not (a and b):
        return {"error": "Save at least two snapshots first."}
    old = _find(user, a, ordered) if a else ordered[0]
    new = _find(user, b, ordered) if b else ordered[-1]
    if not old or not new:
        return {"error": "No snapshot with that id or label. Call "
                         "resume_timeline."}
    result = {"from": old["label"], "to": new["label"], **_diff(old, new),
              "words": {"before": old["words"], "after": new["words"]},
              "roles": {"before": len(old.get("roles", [])),
                        "after": len(new.get("roles", []))}}
    if old["words"]:
        result["word_change_pct"] = round(
            100 * (new["words"] - old["words"]) / old["words"])
    before, after = old["checks"], new["checks"]
    result["checks"] = {k: {"before": len(before.get(k, [])),
                            "after": len(after.get(k, [])),
                            "now": after.get(k, [])}
                        for k in set(before) | set(after)}
    result["summary"] = _summary_line(result)
    return result


def _cell(text):
    return str(text).replace("|", "/").replace("\n", " ")


def proof(user, a="", b=""):
    """A Markdown proof: timeline, before and after, final resume."""
    ordered = _ordered(user)
    if len(ordered) < 2:
        return {"error": "Save at least two snapshots first."}
    change = diff(user, a, b)
    if "error" in change:
        return change
    final = _find(user, b, ordered) if b else ordered[-1]
    rows = timeline(user)["versions"]
    out = ["# Resume evolution", "",
           f"{len(rows)} versions, from {change['from']} to {change['to']}. "
           "Every count below is computed from the saved text.", "",
           "## Timeline", "",
           "| Saved | Version | Words | Changed | Problems | File |",
           "|---|---|---|---|---|---|"]
    for r in rows:
        flags = ", ".join(r["problems"]) or "none"
        if r.get("regressions"):
            flags += " (came back)"
        changed = r.get("changed", "first version")
        if r.get("branch"):
            changed += ". " + r["branch"]
        out.append(f"| {r['saved'][:10]} | {_cell(r['label'])} | "
                   f"{r['words']} | {_cell(changed)} | {flags} | "
                   f"{_cell(r.get('rendered_file', ''))} |")
    out += ["", "## Before and after", "",
            f"| Check | {_cell(change['from'])} | {_cell(change['to'])} |",
            "|---|---|---|",
            f"| Words | {change['words']['before']} | "
            f"{change['words']['after']}"
            + (f" ({change['word_change_pct']:+d}%)"
               if "word_change_pct" in change else "") + " |",
            f"| Roles | {change['roles']['before']} | "
            f"{change['roles']['after']} |"]
    for key, label in (("level_tags", "Internal level tags"),
                       ("internal_names", "Internal names"),
                       ("unsupported_numbers", "Numbers no fact backs"),
                       ("summary_issues", "Summary issues")):
        c = change["checks"].get(key, {"before": 0, "after": 0})
        out.append(f"| {label} | {c['before']} | {c['after']} |")
    out += ["", f"Bullets: {len(change['added'])} added, "
            f"{len(change['removed'])} removed, {len(change['changed'])} "
            "reworded.", "", f"## Final resume ({_cell(final['label'])})",
            "", final["text"]]
    return {"markdown": "\n".join(out), "from": change["from"],
            "to": change["to"], "versions": len(rows),
            "screenshots": "Not made by the server. Add each version's "
                           "rendered_file (a PDF or image path) when you "
                           "snapshot it, and it's listed in the timeline."}
