"""Interview loops round by round: what was asked, which stories were
told to whom, what feedback came back, and how to prepare the next round
so it adds to the last one instead of repeating it."""
import re

from copilot import prep
from copilot import store
from copilot.knowledge.interview import STORY_THEMES

FORMATS = ("recruiter", "hiring_manager", "coding", "system_design",
           "behavioral", "bar_raiser", "take_home", "panel", "team_match")
FEEDBACK_SOURCES = ("recruiter_said", "interviewer_said", "self_read")


def loop_key(company, req_id="", role=""):
    """company + requisition id; the role title only when there's no id."""
    company = re.sub(r"[^a-z0-9]+", "-", company.lower()).strip("-")
    tail = req_id or role
    tail = re.sub(r"[^a-z0-9]+", "-", tail.lower()).strip("-")
    return f"{company}#{tail}" if tail else company


def _rounds(user, key):
    return sorted((r for r in store.list_kind(user, "round")
                   if r["loop"] == key), key=lambda r: r["n"])


def round_log(user, company, round_n, round_format, req_id="", role="",
              round_date="", panel=None, questions=None, feedback=None,
              apply=False):
    if round_format not in FORMATS:
        return {"error": f"format must be one of {FORMATS}"}
    key = loop_key(company, req_id, role)
    clean_q = []
    for q in questions or []:
        text = str(q.get("text", ""))[:300]
        theme = q.get("competency") or (prep._themes(text) or ["general"])[0]
        clean_q.append({"text": text, "competency": theme,
                        "story_id": q.get("story_id", ""),
                        "self_rating": q.get("self_rating"),
                        "follow_ups": [str(f)[:200]
                                       for f in q.get("follow_ups", [])]})
    clean_f = []
    for f in feedback or []:
        source = f.get("source", "self_read")
        if source not in FEEDBACK_SOURCES:
            return {"error": f"feedback source must be one of "
                             f"{FEEDBACK_SOURCES}"}
        clean_f.append({"text": str(f.get("text", ""))[:300],
                        "source": source})
    body = {"loop": key, "company": company, "req_id": req_id, "role": role,
            "n": int(round_n), "format": round_format, "date": round_date,
            # People by role and focus only, never names.
            "panel": [{"role": str(p.get("role", ""))[:60],
                       "focus": str(p.get("focus_area", p.get("focus", "")))
                       [:60]} for p in panel or []],
            "questions": clean_q, "feedback": clean_f}
    result = {"loop_id": key, "round": body}
    if not req_id:
        result["note"] = ("No requisition id: ask for it, so a rejection "
                          "for a different role at this company can't close "
                          "this loop.")
    if apply:
        store.put(user, "round", body, record_id=f"round:{key}:{body['n']}")
        result["saved"] = True
    return result


def _calendar_check(company, events):
    """Is the next round actually on the calendar? Spec: verify interview
    status against the calendar before planning around it."""
    if events is None:
        return {"status": "not_checked",
                "do": "Pass upcoming events from the person's calendar "
                      "connector to confirm the date."}
    name = company.lower()
    hits = sorted(str(e.get("start", ""))[:10] for e in events
                  if name in str(e.get("subject", "")).lower()
                  or name in str(e.get("organizer", "")).lower())
    if hits:
        return {"status": "on_calendar", "date": hits[0]}
    return {"status": "not_on_calendar",
            "do": "No matching event. Confirm the date with the recruiter "
                  "before planning prep around it."}


def next_round_prep(user, loop_id, next_format="", known_panel=None,
                    calendar_events=None):
    rounds = _rounds(user, loop_id)
    if not rounds:
        return {"error": "No rounds logged for this loop yet.",
                "loops": sorted({r["loop"] for r in
                                 store.list_kind(user, "round")})}
    calendar = _calendar_check(rounds[0]["company"], calendar_events)
    stories = {s["id"]: s for s in store.list_kind(user, "story")}
    covered, used = set(), {}
    weak = []
    for r in rounds:
        for q in r["questions"]:
            covered.add(q["competency"])
            if q["story_id"]:
                used.setdefault(q["story_id"], []).append(
                    {"round": r["n"],
                     "panel_roles": [p["role"] for p in r["panel"]]})
            if q.get("self_rating") is not None and q["self_rating"] <= 2:
                weak.append({"round": r["n"], "question": q["text"],
                             "why": "you rated it low"})
        for f in r["feedback"]:
            if f["source"] != "self_read":
                weak.append({"round": r["n"], "feedback": f["text"],
                             "why": f["source"].replace("_", " ")})
    uncovered = [t for t in STORY_THEMES if t not in covered]
    panel_roles = {str(p.get("role", "")).lower() for p in known_panel or []}
    plan = []
    for theme in uncovered:
        options = [s for s in stories.values() if theme in s["themes"]]
        options.sort(key=lambda s: s["id"] in used)
        if not options:
            plan.append({"competency": theme, "story_id": None,
                         "why_this_one": "No story yet: write one "
                                         "(story_add)."})
            continue
        story = options[0]
        risk = "none"
        if story["id"] in used:
            heard_by = {role.lower() for u in used[story["id"]]
                        for role in u["panel_roles"]}
            risk = "same_panelist" if heard_by & panel_roles else \
                "same_company"
        plan.append({"competency": theme, "story_id": story["id"],
                     "story": story["title"],
                     "why_this_one": "Covers a competency the earlier "
                                     "rounds didn't.",
                     "reuse_risk": risk})
    if weak:
        today = f"Rework your answer to: {weak[0].get('question') or weak[0]['feedback']}"
    elif plan and plan[0]["story_id"] is None:
        today = f"Write one {plan[0]['competency']} story."
    elif plan:
        today = f"Tell the '{plan[0]['story']}' story out loud in 90 seconds."
    else:
        today = "Every competency is covered: do one mock round."
    return {"loop_id": loop_id, "rounds_logged": len(rounds),
            "next_format": next_format or "unknown", "calendar": calendar,
            "covered_competencies": sorted(covered),
            "uncovered_competencies": uncovered, "story_plan": plan,
            "weak_spots": weak, "one_thing_today": today,
            "say": "Give one_thing_today first, then the top story to bring. "
                   "Recruiter or interviewer feedback beats your own read."}
