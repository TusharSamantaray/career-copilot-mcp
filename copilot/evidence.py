"""Skill gaps from evidence: what the postings this person looked at
actually ask for, weighed against what their confirmed facts prove, plus
what their own outcome log says about which resume version gets replies.

Built only on the person's own data (postings they analyzed, their
applications), and it says so. No industry hiring data is claimed.
"""
import hashlib
import re
from datetime import date, timedelta

from copilot import facts
from copilot import journey
from copilot import store

PREFERRED = re.compile(r"preferred|nice to have|bonus|a plus|plus if|ideally",
                       re.I)
REPLIED = {"assessment", "interviewing", "offer"}
WEIGHT = {"proven": 1.0, "claimed": 0.5, "none": 0.0}
MIN_OUTCOMES = 5


def _has(skill, text):
    return re.search(rf"(^|[^a-z0-9]){re.escape(skill)}($|[^a-z0-9])",
                     text) is not None


def remember_posting(user, title, company, text, skills, today=None):
    """Keep a short record of an analyzed posting: title, company and the
    skills it asks for, split into required and preferred. Never the
    full text."""
    required, preferred = set(), set()
    for line in re.split(r"[\n.;]", text.lower()):
        for skill in skills:
            if _has(skill, line):
                (preferred if PREFERRED.search(line) else required).add(skill)
    preferred -= required
    key = hashlib.sha256(f"{title}|{company}|{text[:300]}".encode()) \
        .hexdigest()[:12]
    store.put(user, "posting", {
        "title": title[:120], "company": company[:80],
        "required": sorted(required), "preferred": sorted(preferred),
        "day": str(today or date.today())}, record_id=f"posting:{key}")


def _evidence(user, profile):
    proven = " ".join(facts.confirmed_statements(user)).lower()
    unsure = " ".join(f["statement"] for f in store.list_kind(user, "fact")
                      if f.get("confidence") != "confirmed").lower()
    claimed = unsure + " " + " ".join(
        profile.get("domain_keywords", [])).lower()
    return proven, claimed


def skill_gap_evidence(user, role_keyword="", window_days=90,
                       min_postings=5, today=None):
    now = today or date.today()
    since = now - timedelta(days=window_days)
    postings = [p for p in store.list_kind(user, "posting")
                if date.fromisoformat(p["day"]) >= since and
                (not role_keyword or role_keyword.lower() in
                 p["title"].lower())]
    result = {"sample": {"postings": len(postings),
                         "window_days": window_days,
                         "source": "postings you analyzed with jd_analyze"},
              "caveats": ["Based only on postings you looked at and your "
                          "own applications, not industry-wide data."]}
    if len(postings) < min_postings:
        result.update(skills=[], say=f"Only {len(postings)} postings so "
                      f"far; analyze at least {min_postings} before "
                      "drawing conclusions.")
        result["outcome_signal"] = outcome_signal(user)
        return result
    profile = journey.profile(user)
    proven, claimed = _evidence(user, profile)
    honest = {g.lower() for g in profile.get("honest_gaps", [])}
    counts = {}
    for p in postings:
        for skill in p["required"]:
            counts.setdefault(skill, [0, 0])[0] += 1
        for skill in p["preferred"]:
            counts.setdefault(skill, [0, 0])[1] += 1
    rows = []
    for skill, (req, pref) in counts.items():
        level = "proven" if _has(skill, proven) else \
            "claimed" if _has(skill, claimed) else "none"
        demand = (req + pref) / len(postings)
        rows.append({"skill": skill, "demand": round(demand, 2),
                     "required_share": round(req / len(postings), 2),
                     "evidence": level,
                     "honest_gap": skill in honest,
                     "gap_cost": round(demand * (1 - WEIGHT[level]), 2)})
    rows.sort(key=lambda r: (-r["gap_cost"], -r["demand"]))
    top = next((r for r in rows if r["gap_cost"] > 0), None)
    result.update(skills=rows, outcome_signal=outcome_signal(user))
    result["say"] = (f"Biggest gap: {top['skill']} (in {int(top['demand'] * 100)}% "
                     f"of postings, evidence: {top['evidence']}). Offer one "
                     "way to prove it this week." if top else
                     "Your confirmed facts cover what these postings ask.")
    return result


def outcome_signal(user):
    """Reply rate per resume version, once each has enough applications."""
    by_version = {}
    for app in store.list_kind(user, "application"):
        label = app.get("resume_label")
        if not label or app["status"] == "saved":
            continue
        stats = by_version.setdefault(label, {"sent": 0, "replies": 0})
        stats["sent"] += 1
        stats["replies"] += app["status"] in REPLIED
    ready = {label: {**s, "reply_rate": round(s["replies"] / s["sent"], 2)}
             for label, s in by_version.items() if s["sent"] >= MIN_OUTCOMES}
    if not ready:
        return {"status": "not_enough_data",
                "note": f"Needs {MIN_OUTCOMES}+ applications per resume "
                        "version (log them with resume_label)."}
    return {"status": "ok", "by_resume_version": ready}
