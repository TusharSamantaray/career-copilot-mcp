"""Where the person is on their journey, and the one best next question.

Two ways in: the person says what's on their mind in their own words, or
answers a few starter questions. Either way the profile builds as a side
effect, one answer at a time, and every field is confirmed or unsure.
"""
from copilot import conduct
from copilot import store
from copilot.knowledge.coach import COMPASS, PRINCIPLES

TEXT_FIELDS = ("situation", "target_role", "current_role", "level",
               "industry", "location", "country", "goals",
               "hours_preference", "comp_floor", "work_authorization",
               "schedule")
LIST_FIELDS = ("wants", "dealbreakers", "locations", "target_companies",
               "excluded_companies", "domain_keywords", "honest_gaps")

SITUATIONS = ["starting out", "between jobs", "working, want a change",
              "interviewing"]

# The starter questions, in order. Known or skipped ones are never asked.
QUESTIONS = [
    {"field": "situation", "ask": "Where are you right now?",
     "options": SITUATIONS},
    {"field": "target_role", "ask": "Do you know the role you want?",
     "options": ["yes: tell me the role", "a few ideas", "not sure yet"]},
    {"field": "current_role", "ask": "What do you do now, or did last?",
     "options": []},
    {"field": "location", "ask": "Where do you want to work?",
     "options": ["where I live", "remote", "open to moving"]},
    {"field": "dealbreakers", "ask": "Anything that's a hard no?",
     "options": ["pay below a floor", "fully on-site",
                 "no visa sponsorship", "nothing yet"]},
]
MAX_QUESTIONS = 5

# Which path fits each situation, and the tool or starter prompt for it.
PATHS = {
    "starting out": ("Find a direction", "life_compass"),
    "between jobs": ("Steady the ground: dates first, then a 72-hour plan",
                     "prompt: i_just_got_laid_off"),
    "working, want a change": ("Compare 2 or 3 directions",
                               "career_move"),
    "interviewing": ("Prepare for the loop", "prompt: interview_coming_up"),
}

DOORS = {
    "ask": "Want to tell me what's on your mind, or should I ask a few "
           "quick questions?",
    "options": ["I'll tell you", "ask me questions", "here's my resume"],
}


def profile(user):
    rows = store.list_kind(user, "profile")
    return rows[-1] if rows else {}


def save_profile(user, fields, unsure=(), skip=(), replace=False):
    """Merge answers into the profile. Text fields overwrite, list fields
    add new items, empty values leave what's there. Fields named in
    unsure are labelled unsure; every other saved field is confirmed."""
    body = {} if replace else {k: v for k, v in profile(user).items()
                               if k not in ("id", "updated")}
    confidence = {} if replace else dict(body.get("confidence", {}))
    skipped = set() if replace else set(body.get("skipped", []))
    saved = []
    for name, value in fields.items():
        if name in LIST_FIELDS:
            items = [str(v).strip() for v in (value or []) if str(v).strip()]
            if not items:
                continue
            current = body.get(name, [])
            body[name] = current + [i for i in items if i not in current]
        elif value not in ("", None, 0):
            body[name] = value
        else:
            continue
        saved.append(name)
        confidence[name] = "unsure" if name in unsure else "confirmed"
        skipped.discard(name)
    for name in unsure:
        if name in body:
            confidence[name] = "unsure"
    skipped |= {name for name in skip if name not in body}
    body["confidence"] = confidence
    body["skipped"] = sorted(skipped)
    store.put(user, "profile", body, record_id="profile")
    return {"saved": saved, "skipped": sorted(skipped)}


def _known(body):
    confidence = body.get("confidence", {})
    known = []
    for name in TEXT_FIELDS + LIST_FIELDS + ("years_experience",):
        value = body.get(name)
        if value not in (None, "", [], 0):
            known.append({"field": name, "value": value,
                          "confidence": confidence.get(name, "confirmed")})
    return known


def _stage(user, body):
    apps = store.list_kind(user, "application")
    statuses = {a["status"] for a in apps}
    if "offer" in statuses:
        return "decide"
    if statuses & {"assessment", "interviewing"} or \
            body.get("situation") == "interviewing":
        return "prepare"
    if not body.get("target_role") and not body.get("wants") \
            and not body.get("dealbreakers"):
        return "orient"
    facts = [f for f in store.list_kind(user, "experience")
             if f.get("confirmed")]
    if len(facts) < 3 and not store.list_kind(user, "resume"):
        return "foundation"
    return "search"


def journey_state(user):
    body = profile(user)
    consent = conduct.ground_rules(user)["accepted"]
    known = _known(body)
    known_fields = {k["field"] for k in known}
    skipped = set(body.get("skipped", []))
    open_questions = [q for q in QUESTIONS
                      if q["field"] not in known_fields | skipped]
    answered = len(QUESTIONS) - len(open_questions)
    stage = _stage(user, body)
    result = {"stage": stage, "ground_rules_accepted": consent,
              "known": known,
              "unsure": [k["field"] for k in known
                         if k["confidence"] == "unsure"],
              "missing": [q["field"] for q in open_questions],
              "skipped": sorted(skipped)}
    if not consent:
        result["next"] = {"do": "Call ground_rules and ask if that's OK."}
    elif not known and not skipped:
        result["next"] = {"question": DOORS,
                          "do": "First visit: offer the two ways in. If "
                                "they talk, pull out facts, read them back "
                                "and save only what they confirm "
                                "(profile_save). If they want questions, "
                                "ask the starter questions one at a time."}
    elif open_questions and answered < 3:
        q = open_questions[0]
        result["next"] = {"question": {"ask": q["ask"],
                                       "options": q["options"]},
                          "saves_to": q["field"],
                          "do": "Ask just this. Save the answer at once "
                                "with profile_save; 'not sure' or 'skip' "
                                "goes in skip."}
    else:
        path, use = PATHS.get(body.get("situation"),
                              ("Pick the next small step", "next_steps"))
        if stage == "orient" and use == "next_steps":
            path, use = PATHS["starting out"]
        result["next"] = {"path": path, "use": use,
                          "do": "Give something back now: read the profile "
                                "back in one or two lines with confirmed or "
                                "unsure labels, then offer this one step as "
                                "a question."}
        if open_questions:
            result["later_questions"] = [q["field"] for q in open_questions]
    result["say"] = ("Reply in 2 to 4 short sentences and one question. "
                     "Never re-ask a known or skipped field. At most "
                     f"{MAX_QUESTIONS} questions before giving something "
                     "useful back.")
    return result


def life_compass(user, question=0, answer="", save_as=""):
    """Reflection questions, asked one at a time. With an answer, saves it
    (and, if save_as is want or dealbreaker, adds it to the profile)."""
    if answer:
        if not 1 <= question <= len(COMPASS):
            return {"error": f"question must be 1 to {len(COMPASS)}"}
        store.put(user, "compass", {"question": COMPASS[question - 1],
                                    "answer": answer[:500]},
                  record_id=f"compass:{question}")
        if save_as in ("want", "dealbreaker"):
            save_profile(user, {save_as + "s": [answer[:200]]})
    done = {int(r["id"].split(":")[1]) for r in
            store.list_kind(user, "compass")}
    left = [i for i in range(1, len(COMPASS) + 1) if i not in done]
    result = {"answered": len(done), "of": len(COMPASS),
              "principles": PRINCIPLES}
    if left:
        result["next_question"] = {"number": left[0],
                                   "ask": COMPASS[left[0] - 1]}
        result["say"] = ("Reflect their last answer back in one line, then "
                         "ask only next_question. If an answer is a clear "
                         "want or hard no, pass save_as.")
    else:
        result["say"] = ("All done. Sum up what they want in two lines, then "
                         "offer 2 or 3 directions to test (career_move or "
                         "role_match).")
    return result
