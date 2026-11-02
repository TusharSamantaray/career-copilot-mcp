"""Interview prep: coding patterns, system design and study plans."""
from datetime import date, timedelta

from copilot import store
from copilot.knowledge.interview import (LOOP_FORMATS, PREP_CHECKLIST, QUESTIONS,
                                 ROUNDS, STORY_THEMES, TEMPLATES)
from copilot.knowledge.patterns import BY_ID, PATTERNS
from copilot.knowledge.system_design import ALIASES, COMPONENTS, FRAMEWORK

# Most interview-relevant patterns first.
STUDY_ORDER = ["hashmap", "twoptr", "window", "bsearch", "stack", "treedfs",
               "treebfs", "graph", "heap", "intervals", "linked", "dp",
               "backtrack", "prefix", "monostack", "toposort", "greedy",
               "unionfind", "fastslow", "trie", "design", "matrix", "bits"]
DESIGN_ORDER = ["load_balancer", "cache", "relational_db", "nosql", "queue",
                "event_stream", "cdn", "api_gateway", "rate_limiting",
                "sharding", "idempotency", "object_storage", "search_index",
                "dns"]


def coding_pattern(query):
    """Exact pattern by id/name, or the best matches for a problem text."""
    q = query.strip().lower()
    for p in PATTERNS:
        if q in (p["id"], p["name"].lower()):
            return {"match": "exact", "pattern": p}
    scored = []
    for p in PATTERNS:
        hits = [sig for sig in p["recognize"] if sig in q]
        hits += [ex for ex in p["examples"] if ex.lower() in q]
        if hits:
            scored.append((len(hits), p, hits))
    scored.sort(key=lambda item: -item[0])
    if not scored:
        return {"match": "none",
                "patterns": [{"id": p["id"], "name": p["name"],
                              "signal": p["signal"]} for p in PATTERNS],
                "tip": "Describe the problem's constraints (sorted? "
                       "contiguous? all combinations?) to get a match."}
    return {"match": "signals",
            "candidates": [{"id": p["id"], "name": p["name"],
                            "why": hits, "ask_yourself": p["ask"],
                            "model": p["model"], "template": p["template"],
                            "say": p["say"]}
                           for _, p, hits in scored[:3]]}


def system_design(topic="framework"):
    key = topic.strip().lower().replace(" ", "_").replace("-", "_")
    if key in ("framework", "steps", "how", ""):
        return {"framework": FRAMEWORK,
                "components": sorted(COMPONENTS)}
    key = ALIASES.get(key, key)
    if key in COMPONENTS:
        return {"component": COMPONENTS[key]}
    return {"error": "Unknown topic.", "components": sorted(COMPONENTS)}


def interview_questions(round_="", likely_only=False):
    rows = [{"round": r, "question": q, "likely": likely, "why": why,
             "how_to_answer": how}
            for r, q, likely, why, how in QUESTIONS
            if (not round_ or r == round_) and (likely or not likely_only)]
    return {"rounds": ROUNDS, "questions": rows,
            "loop_formats": LOOP_FORMATS if not round_ else None}


def message_draft(kind, company="", role="", name="", detail="", me=""):
    if kind not in TEMPLATES:
        return {"error": f"kind must be one of {sorted(TEMPLATES)}"}
    subject, body = TEMPLATES[kind]
    values = {"company": company or "[company]", "role": role or "[role]",
              "name": name or "there", "detail": detail or "[detail]",
              "me": me or "[your name]"}
    return {"subject": subject.format(**values),
            "body": body.format(**values),
            "note": "A draft for the user to edit and send themselves. "
                    "Career Copilot never sends messages on its own."}


def _themes(text):
    low = text.lower()
    return sorted(t for t, words in STORY_THEMES.items()
                  if any(w in low for w in words))


def story_add(user, title, situation, task, action, result, themes=None):
    themes = sorted(set(themes or []) | set(_themes(
        f"{title} {situation} {action} {result}")))
    body = {"title": title, "situation": situation, "task": task,
            "action": action, "result": result, "themes": themes}
    return {"id": store.put(user, "story", body), "themes": themes}


def story_match(user, question):
    wanted = set(_themes(question))
    stories = store.list_kind(user, "story")
    ranked = sorted(stories, key=lambda s: -len(wanted & set(s["themes"])))
    covered = {t for s in stories for t in s["themes"]}
    return {"question_themes": sorted(wanted),
            "best": [{"id": s["id"], "title": s["title"],
                      "matches": sorted(wanted & set(s["themes"]))}
                     for s in ranked[:3] if wanted & set(s["themes"])],
            "story_count": len(stories),
            "missing_themes": sorted(set(STORY_THEMES) - covered),
            "tip": "Open with the situation in one sentence, spend most of "
                   "the time on your actions, end with the number."}


def prep_checklist():
    return PREP_CHECKLIST


def study_plan(start, interview_date, hours_per_day=2.0):
    """Day-by-day plan from start to the day before the interview."""
    try:
        first = date.fromisoformat(start)
        last = date.fromisoformat(interview_date) - timedelta(days=1)
    except ValueError:
        return {"error": "dates must be YYYY-MM-DD"}
    days = (last - first).days + 1
    if days < 1:
        return {"error": "interview_date must be after start"}
    plan, p_i, d_i = [], 0, 0
    for n in range(days):
        day = first + timedelta(days=n)
        left = days - n
        if left == 1:
            items = ["Light review of your cheat sheet", "Rest and sleep"]
        elif left <= 3:
            items = ["Full mock interview (coding + design)",
                     "Rehearse 3 behavioural stories out loud"]
        elif n % 3 == 2:
            topic = DESIGN_ORDER[d_i % len(DESIGN_ORDER)]
            d_i += 1
            items = [f"System design: {COMPONENTS[topic]['name']}",
                     "One end-to-end design question using the framework"]
        else:
            pid = STUDY_ORDER[p_i % len(STUDY_ORDER)]
            p_i += 1
            pat = BY_ID[pid]
            items = [f"Pattern: {pat['name']}",
                     "Solve: " + ", ".join(pat["examples"][:2]),
                     "Say the approach out loud before coding"]
        if hours_per_day >= 3 and left > 3:
            items.append("Behavioural: write or polish one story")
        plan.append({"date": str(day), "hours": hours_per_day,
                     "items": items})
    return {"days": days, "plan": plan}
