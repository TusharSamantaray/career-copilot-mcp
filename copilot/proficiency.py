"""Proficiency tiers, computed from submitted evidence, never typed in.

A person describes their work (a shipped system, a design doc, code
history, peer review, coursework with real artifacts) and says which of
three dimensions it demonstrates: Domain knowledge, Stack depth, Scope
of work. The tier in each dimension is then computed from how much
verified evidence sits behind it. Nobody types a tier, and nobody types
a claim about their own skill: the rating is always derived, and every
tier lists the evidence it comes from.

Tiers, in hiring words, not game words: Foundational, Developing,
Proficient, Advanced, Expert. With no verified evidence in a dimension
the tier is Foundational, honestly: that is where a new grad starts,
and the record builds as verified work is added.

Verification depth is a field on the evidence record: submitted
(recorded, not yet checked), corroborated (matches another source),
verified (checked against an independent source). Only verified
evidence moves a tier; the rest is listed as pending, so a tier can
never hide behind unchecked items. For now the depth is recorded as
given. The verification engine (GitHub issue #19) will own checking
evidence against independent sources and setting this field itself.
"""
from datetime import date

from copilot import store

KIND = "proficiency_evidence"

TIERS = ("Foundational", "Developing", "Proficient", "Advanced", "Expert")

DIMENSIONS = {"domain": "Domain knowledge",
              "stack_depth": "Stack depth",
              "scope": "Scope of work"}

EVIDENCE_TYPES = {"shipped_system": "Shipped system",
                  "code_history": "Code history",
                  "design_doc": "Design document",
                  "peer_review": "Peer review",
                  "employment": "Employment record",
                  "coursework": "Coursework with artifacts"}

VERIFICATION = ("submitted", "corroborated", "verified")

# Verified evidence items in a dimension needed to reach each tier.
# A first-slice rule, stated plainly so anyone can check it: the counts
# are the whole computation. The verification engine (issue #19) may
# refine how different kinds of evidence weigh.
THRESHOLDS = {"Foundational": 0, "Developing": 1, "Proficient": 3,
              "Advanced": 6, "Expert": 9}

MAX_TITLE = 200
MAX_SOURCE = 300
MAX_TOPICS = 8
MAX_TOPIC = 60


def tier_for(verified_count):
    """The tier a count of verified evidence items in one dimension
    earns. Zero verified items is Foundational."""
    tier = TIERS[0]
    for name in TIERS:
        if verified_count >= THRESHOLDS[name]:
            tier = name
    return tier


def _clean_topics(topics):
    if isinstance(topics, str):
        topics = [topics]
    cleaned = []
    for topic in topics or []:
        topic = str(topic).strip()[:MAX_TOPIC]
        if topic and topic not in cleaned:
            cleaned.append(topic)
    return cleaned[:MAX_TOPICS]


def _shown(item):
    """One evidence record as the person (or a view) sees it."""
    return {"id": item["id"], "title": item["title"],
            "kind": item["kind"],
            "kind_label": EVIDENCE_TYPES.get(item["kind"], item["kind"]),
            "dimensions": list(item.get("dimensions", [])),
            "topics": list(item.get("topics", [])),
            "source": item.get("source", ""),
            "verification": item.get("verification", "submitted"),
            "day": item.get("day", "")}


def add_evidence(user, title, kind, dimensions, topics=None, source="",
                 verification="submitted"):
    """Record one piece of work as proficiency evidence. dimensions says
    which of the three dimensions this work demonstrates; topics name
    the skills or subjects it covers. No tier is ever taken in: tiers
    are computed from what is recorded."""
    title = (title or "").strip()
    if not title:
        return {"error": "title is required: what the work is, in one "
                         "line, e.g. 'Notification system, 6 countries'."}
    if kind not in EVIDENCE_TYPES:
        return {"error": f"kind must be one of {sorted(EVIDENCE_TYPES)}"}
    if isinstance(dimensions, str):
        dimensions = [dimensions]
    dimensions = [d for d in dict.fromkeys(dimensions or [])]
    bad = [d for d in dimensions if d not in DIMENSIONS]
    if not dimensions:
        return {"error": "dimensions is required: at least one of "
                         f"{sorted(DIMENSIONS)}."}
    if bad:
        return {"error": f"unknown dimension: {', '.join(bad)}; use "
                         f"{sorted(DIMENSIONS)}."}
    if verification not in VERIFICATION:
        return {"error": f"verification must be one of "
                         f"{list(VERIFICATION)}"}
    record = {"title": title[:MAX_TITLE], "kind": kind,
              "dimensions": dimensions,
              "topics": _clean_topics(topics),
              "source": (source or "").strip()[:MAX_SOURCE],
              "verification": verification, "day": str(date.today())}
    record_id = store.put(user, KIND, record)
    record["id"] = record_id
    view = compute(user)
    tiers = {row["dimension"]: row["tier"] for row in view["tiers"]
             if row["dimension"] in dimensions}
    counted = verification == "verified"
    return {"id": record_id, "recorded": _shown(record), "tiers": tiers,
            "say": ("Recorded. " + ("It is verified, so it counts toward "
                                    "the tiers shown."
                                    if counted else
                                    "It is not verified yet, so no tier "
                                    "moved. Verified evidence is what "
                                    "moves a tier."))}


def list_evidence(user, dimension="", kind="", verification=""):
    """Evidence recorded so far, newest last, with optional filters."""
    if dimension and dimension not in DIMENSIONS:
        return {"error": f"dimension must be one of {sorted(DIMENSIONS)}"}
    if kind and kind not in EVIDENCE_TYPES:
        return {"error": f"kind must be one of {sorted(EVIDENCE_TYPES)}"}
    if verification and verification not in VERIFICATION:
        return {"error": f"verification must be one of "
                         f"{list(VERIFICATION)}"}
    items = store.list_kind(user, KIND)
    if dimension:
        items = [i for i in items if dimension in i.get("dimensions", [])]
    if kind:
        items = [i for i in items if i.get("kind") == kind]
    if verification:
        items = [i for i in items
                 if i.get("verification", "submitted") == verification]
    return {"evidence": [_shown(i) for i in items], "count": len(items)}


def remove_evidence(user, evidence_id):
    """Take one evidence record out (a mistake, or work that should not
    count). Tiers recompute from what is left."""
    if store.delete(user, evidence_id):
        return {"removed": True, "id": evidence_id,
                "say": "Removed. Tiers recompute from the evidence left."}
    return {"removed": False,
            "error": "No proficiency evidence with that id."}


def compute(user):
    """The person's proficiency: one tier per dimension, each with the
    verified evidence behind it, plus what is still pending. Computed
    fresh from the evidence records every time, so it can never drift
    from what was actually recorded."""
    items = store.list_kind(user, KIND)
    verified_from = {}
    verified_total = 0
    pending_total = 0
    tiers = []
    for key, label in DIMENSIONS.items():
        mine = [i for i in items if key in i.get("dimensions", [])]
        verified = [i for i in mine
                    if i.get("verification") == "verified"]
        pending = [i for i in mine
                   if i.get("verification") != "verified"]
        count = len(verified)
        tier = tier_for(count)
        index = TIERS.index(tier)
        if index < len(TIERS) - 1:
            next_tier = TIERS[index + 1]
            needed = THRESHOLDS[next_tier] - count
        else:
            next_tier, needed = "", 0
        tiers.append({"dimension": key, "label": label, "tier": tier,
                      "tier_index": index, "verified": count,
                      "pending": len(pending),
                      "evidence": [_shown(i) for i in verified],
                      "pending_evidence": [_shown(i) for i in pending],
                      "next_tier": next_tier, "verified_needed": needed})
    for item in items:
        if item.get("verification") == "verified":
            verified_total += 1
            kind = item.get("kind", "")
            verified_from[kind] = verified_from.get(kind, 0) + 1
        else:
            pending_total += 1
    if not items:
        say = ("No verified work recorded yet, so every dimension is "
               "Foundational. Offer to record a first piece of work: a "
               "shipped system, a design doc, code history, peer review, "
               "or coursework with real artifacts.")
    elif not verified_total:
        say = (f"{pending_total} item(s) recorded but none verified yet, "
               "so no tier has moved. Verified evidence is what moves a "
               "tier.")
    else:
        say = ("Tiers come only from verified evidence; each tier lists "
               "the work behind it. New verified work updates them "
               "automatically.")
    return {"tiers": tiers, "verified_from": verified_from,
            "verified_total": verified_total,
            "pending_total": pending_total, "say": say}
