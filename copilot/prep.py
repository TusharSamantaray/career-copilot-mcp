"""Interview prep: coding patterns, system design and study plans."""
import re
from datetime import date, timedelta

from copilot import facts
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


VOICES = ("plain", "warm", "formal")
CLOSINGS = re.compile(r"\n\n(Best|Thanks|Thank you|Regards|Kind regards),\n")


def _voice(body, voice):
    """Plain is the template as written; warm and formal adjust the
    greeting, opening and sign-off only, never the facts."""
    if voice == "formal":
        body = re.sub(r"^Hi ", "Dear ", body)
        body = CLOSINGS.sub("\n\nKind regards,\n", body)
    elif voice == "warm":
        body = re.sub(r"^(Hi [^\n]+\n\n)", r"\1I hope your week is going "
                      "well. ", body)
        body = CLOSINGS.sub("\n\nWarm wishes,\n", body)
    return body


def message_draft(kind, company="", role="", name="", detail="", me="",
                  voice="plain"):
    if kind not in TEMPLATES:
        return {"error": f"kind must be one of {sorted(TEMPLATES)}"}
    voice = voice if voice in VOICES else "plain"
    subject, body = TEMPLATES[kind]
    values = {"company": company or "[company]", "role": role or "[role]",
              "name": name or "there", "detail": detail or "[detail]",
              "me": me or "[your name]"}
    return {"subject": subject.format(**values),
            "body": _voice(body.format(**values), voice), "voice": voice,
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


def _words(text):
    return {w for w in re.findall(r"[a-z]{3,}", text.lower())}


def cover_letter_draft(user, company, role, posting_text="", me="",
                       voice="plain"):
    """A short letter built only from confirmed facts, the two that best
    match the posting, quoted as the person stated them."""
    confirmed = facts.confirmed_statements(user) + [
        e["fact"] for e in store.list_kind(user, "experience")
        if e.get("confirmed")]
    confirmed = list(dict.fromkeys(confirmed))
    if not confirmed:
        return {"error": "No confirmed facts yet.",
                "ask": "What's one thing you did in your last role that "
                       "you're proud of, with a number if you have one?"}
    want = _words(posting_text)
    best = sorted(confirmed, key=lambda f: -len(_words(f) & want))[:2]
    greet = {"formal": f"Dear Hiring Team at {company},",
             "warm": f"Hello {company} team,"}.get(voice, f"Hi {company} team,")
    close = {"formal": "Kind regards,", "warm": "Warm wishes,"}.get(voice,
                                                                     "Best,")
    points = "\n".join(f"- {f.rstrip('.')}." for f in best)
    body = (f"{greet}\n\nI'm applying for the {role} role at {company}. "
            f"Here's what I'd bring, from work I've done:\n\n{points}\n\n"
            f"I'd welcome a short conversation about how I could help "
            f"{company}.\n\n{close}\n{me or '[your name]'}")
    return {"subject": f"Application: {role}", "body": body,
            "facts_used": best,
            "note": "Built only from confirmed facts. Edit it, then send it "
                    "yourself."}


def story_strength(user, story):
    """Four checks a story must pass to hold up under follow-ups."""
    result, action = story.get("result", ""), story.get("action", "")
    numbers = facts.parse_metrics(result)
    backed = facts.confirmed_statements(user)
    checks = {
        "has_number": bool(numbers),
        "clear_ownership": bool(re.search(r"\bI\b", action)),
        "has_result": len(result.split()) >= 3,
        "enough_detail": len(action.split()) >= 8,
    }
    unbacked = [m for m in re.findall(r"\$?\d[\d,.]*%?", result)
                if not any(m.strip("$%") in s for s in backed)
                and not re.fullmatch(r"\d", m)]
    return {"score": sum(checks.values()), "out_of": 4,
            "missing": [k for k, ok in checks.items() if not ok],
            "numbers_not_in_confirmed_facts": unbacked}


def story_coverage(user):
    stories = store.list_kind(user, "story")
    grid, gaps = {}, []
    for theme in STORY_THEMES:
        rows = []
        for s in stories:
            if theme in s["themes"]:
                rows.append({"id": s["id"], "title": s["title"],
                             **story_strength(user, s)})
        rows.sort(key=lambda r: -r["score"])
        grid[theme] = rows
        if not rows or rows[0]["score"] < 3:
            gaps.append(theme)
    weakest = None
    for theme in gaps:
        weakest = {"competency": theme,
                   "do": f"Write a {theme} story (story_add)." if not
                   grid[theme] else
                   f"Strengthen '{grid[theme][0]['title']}': add "
                   f"{', '.join(grid[theme][0]['missing'])}."}
        break
    return {"stories": len(stories), "grid": grid, "gaps": gaps,
            "next_story": weakest or {"do": "Every competency has a strong "
                                            "story. Practise them out loud."},
            "say": "Give next_story.do in one line. Numbers not in "
                   "confirmed facts need checking before an interview."}


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


# Which kind of day comes next, by loop format (keys of LOOP_FORMATS).
ROTATION = {
    "big_tech_algorithmic": ["coding", "coding", "design"],
    "values_heavy": ["coding", "stories", "design", "stories"],
    "practical": ["practical", "design", "coding"],
    "enterprise": ["coding", "design", "stories"],
    "startup": ["practical", "stories", "design"],
    "non_technical": ["work_sample", "stories", "case"],
}
DAY_ITEMS = {
    "practical": ["Applied coding: build or debug a small service end to end",
                  "Handle retries, idempotency and data consistency"],
    "work_sample": ["Prepare the work sample like a real deliverable",
                    "Present it out loud in 10 minutes"],
    "case": ["Practise one case study out loud (30 minutes)",
             "Structure: goal, options, numbers, recommendation"],
}


def study_plan(start, interview_date, hours_per_day=2.0, loop_format=""):
    """Day-by-day plan from start to the day before the interview, shaped
    by the loop format when one is given."""
    if loop_format and loop_format not in ROTATION:
        return {"error": f"loop_format must be one of {sorted(ROTATION)}"}
    rotation = ROTATION.get(loop_format, ROTATION["big_tech_algorithmic"])
    themes = list(STORY_THEMES)
    try:
        first = date.fromisoformat(start)
        last = date.fromisoformat(interview_date) - timedelta(days=1)
    except ValueError:
        return {"error": "dates must be YYYY-MM-DD"}
    days = (last - first).days + 1
    if days < 1:
        return {"error": "interview_date must be after start"}
    plan, p_i, d_i, s_i = [], 0, 0, 0
    for n in range(days):
        day = first + timedelta(days=n)
        left = days - n
        kind = rotation[n % len(rotation)]
        if left == 1:
            items = ["Light review of your cheat sheet", "Rest and sleep"]
        elif left <= 3:
            items = (["Full mock: case or work sample, then a panel",
                      "Rehearse 3 stories out loud"]
                     if loop_format == "non_technical" else
                     ["Full mock interview (coding + design)",
                      "Rehearse 3 behavioural stories out loud"])
        elif kind == "design":
            topic = DESIGN_ORDER[d_i % len(DESIGN_ORDER)]
            d_i += 1
            items = [f"System design: {COMPONENTS[topic]['name']}",
                     "One end-to-end design question using the framework"]
        elif kind == "stories":
            theme = themes[s_i % len(themes)]
            s_i += 1
            items = [f"Stories: write or polish a {theme} story",
                     "Tell it out loud in 90 seconds, ending on the number"]
        elif kind in DAY_ITEMS:
            items = list(DAY_ITEMS[kind])
        else:
            pid = STUDY_ORDER[p_i % len(STUDY_ORDER)]
            p_i += 1
            pat = BY_ID[pid]
            items = [f"Pattern: {pat['name']}",
                     "Solve: " + ", ".join(pat["examples"][:2]),
                     "Say the approach out loud before coding"]
        if hours_per_day >= 3 and left > 3 and kind != "stories":
            items.append("Behavioural: write or polish one story")
        plan.append({"date": str(day), "hours": hours_per_day,
                     "items": items})
    return {"days": days, "loop_format": loop_format or "big_tech_algorithmic",
            "plan": plan}
