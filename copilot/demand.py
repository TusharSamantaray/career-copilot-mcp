"""Demand from people hiring, and pathways built on it.

Recruiters answer a short, versioned survey; their persona searches add
which skills they asked for. The demand digest counts who said what:
"3 recruiters named Spark for Data Engineer (survey v1)", never "the
market wants". A pathway turns the direction a person picked, plus that
demand, into a few small steps, each citing its reason. Candidate data
never enters the digest: it reads only survey answers and searches.
"""
import re
from datetime import date, timedelta

from copilot import facts
from copilot import persona
from copilot import store
from copilot.careers import resolve_role
from copilot.knowledge.careers import ROLES

# Versioned question sets. Add a new version to change questions; old
# answers keep the version they were given under.
SURVEYS = {
    "1": [
        {"id": "seeing_roles",
         "ask": "What kinds of jobs are you seeing a lot right now?"},
        {"id": "skills_by_role",
         "ask": "What skill sets are wanted for a role? Name the role and "
                "the skills."},
        {"id": "expectations",
         "ask": "What do you expect from a candidate, technical and "
                "non-technical?"},
    ],
}
CURRENT = "1"
RECENT_DAYS = 90
MAX_STEPS = 5
ALIASES = {"sre": "sre_infra", "infra": "sre_infra", "devops": "sre_infra",
           "ml": "ml_engineer", "machine learning engineer": "ml_engineer",
           "pm": "product_manager", "designer": "ux_designer",
           "recruiter": "hr_recruiting", "analyst": "data_analyst"}
FIRST_WORD = ("backend", "frontend", "fullstack", "mobile", "security",
              "marketing", "sales", "operations")


def _norm(text):
    return re.sub(r"[^a-z0-9 ]", " ", (text or "").lower())


def roles_in(text):
    low = f" {_norm(text)} "
    found = []
    for key, role in ROLES.items():
        names = {_norm(role["title"]).strip(), key.replace("_", " ")}
        if key.split("_")[0] in FIRST_WORD:
            names.add(key.split("_")[0])
        if any(f" {n} " in low for n in names if n):
            found.append(key)
    for alias, key in ALIASES.items():
        if f" {alias} " in low and key not in found:
            found.append(key)
    return found


def skills_in(text):
    return [s for s in persona.SKILLS if persona.has_skill(s, text or "")]


def survey(user, answers=None, company="", role=""):
    questions = SURVEYS[CURRENT]
    if not answers:
        return {"version": CURRENT, "questions": questions,
                "say": "Ask one question at a time and save the answers "
                       "together. company is optional: if given, it's shown "
                       "with these answers in the demand digest."}
    known = {q["id"] for q in questions}
    unknown = sorted(set(answers) - known)
    if unknown:
        return {"error": f"Unknown question ids: {unknown}",
                "questions": questions}
    picked = resolve_role(role) if role else None
    seeing = roles_in(answers.get("seeing_roles", ""))
    by_role = answers.get("skills_by_role", "")
    target = picked or next(iter(roles_in(by_role)), None)
    record = {"version": CURRENT, "company": company.strip()[:80],
              "on": str(date.today()), "roles_seen": seeing,
              "role": target,
              "skills": skills_in(by_role + " " +
                                  answers.get("expectations", "")),
              "answers": {k: str(v)[:500] for k, v in answers.items()}}
    record_id = store.put(user, "survey", record)
    return {"saved": record_id, "version": CURRENT, "role": target,
            "roles_seen": seeing, "skills": record["skills"],
            "say": "Thank them; say their answers count in the demand "
                   "digest with their company name"
                   + ("" if company else " left out") + "."}


def note_search(user, title, skills):
    """A persona search is a demand signal too: role and skills only."""
    target = next(iter(roles_in(title)), None) or resolve_role(title or "")
    if skills:
        store.put(user, "search", {"role": target, "skills": skills[:15],
                                   "on": str(date.today())})


def digest(direction="", today=None):
    today = today or date.today()
    since = str(today - timedelta(days=RECENT_DAYS))
    want = resolve_role(direction) if direction else None
    if direction and not want:
        return {"error": f"Unknown direction. Try one of {sorted(ROLES)}"}
    tally = {}

    def count(role, skill, who, label, source):
        # One row per role and skill: a person counts once however many
        # ways they said it; every source is listed.
        row = tally.setdefault((role, skill), {"who": {}, "sources": set()})
        if label != "a recruiter" or who not in row["who"]:
            row["who"][who] = label
        row["sources"].add(source)

    seen = {}
    for user in store.users():
        try:
            answers = store.list_kind(user, "survey")
            searches = store.list_kind(user, "search")
        except Exception:
            continue
        for row in answers:
            if row["on"] < since:
                continue
            label = row.get("company") or "a recruiter"
            source = f"survey v{row['version']}"
            for role in row.get("roles_seen", []):
                seen.setdefault(role, {})[user] = label
            if row.get("role"):
                for skill in row["skills"]:
                    count(row["role"], skill, user, label, source)
        for row in searches:
            if row["on"] >= since and row.get("role"):
                for skill in row["skills"]:
                    count(row["role"], skill, user, "a recruiter",
                          "persona searches")
    signals = []
    for (role, skill), row in tally.items():
        if want and role != want:
            continue
        names = sorted({n for n in row["who"].values() if n !=
                        "a recruiter"})
        others = sum(1 for n in row["who"].values() if n == "a recruiter")
        signals.append({"direction": ROLES[role]["title"], "role": role,
                        "skill": skill, "said_by": len(row["who"]),
                        "who": names + ([f"{others} unnamed"] if others
                                        else []),
                        "sources": sorted(row["sources"])})
    signals.sort(key=lambda s: (-s["said_by"], s["direction"], s["skill"]))
    roles_seen = sorted(({"direction": ROLES[r]["title"],
                          "said_by": len(who)} for r, who in seen.items()
                         if not want or r == want),
                        key=lambda r: -r["said_by"])
    return {"since": since, "survey_version": CURRENT,
            "signals": signals, "roles_seen": roles_seen,
            "say": "Report each signal as who said it and how many, with "
                   "its sources, e.g. '3 recruiters named Spark (survey v1)'. "
                   "Never say 'the market wants'." if signals else
                   "No demand signals yet. Say so; don't guess."}


def _verified_skills(user):
    text = " ".join(facts.confirmed_statements(user))
    return set(skills_in(text))


def _signal_reason(direction, signal):
    return (f"{direction}: {signal['said_by']} "
            f"{'recruiter' if signal['said_by'] == 1 else 'recruiters'} "
            f"named {signal['skill']} ({', '.join(signal['sources'])})")


def build(user, direction="", mode="guided"):
    """guided: steps toward the chosen direction, each with its reason.
    immediate: roles that want what the person already proves, no new
    learning."""
    mine = _verified_skills(user)
    if mode == "immediate":
        signals = digest()["signals"]
        roles = {}
        for s in signals:
            if s["skill"] in mine:
                roles.setdefault(s["role"], []).append(s)
        ranked = sorted(roles.items(), key=lambda kv: -sum(
            s["said_by"] for s in kv[1]))
        options = [{"direction": ROLES[r]["title"],
                    "you_prove": sorted({s["skill"] for s in sig}),
                    "reason": "; ".join(_signal_reason(ROLES[r]["title"], s)
                                        for s in sig[:3])}
                   for r, sig in ranked[:3]]
        return {"mode": "immediate", "options": options,
                "say": "Offer these in one line each: roles asking for what "
                       "they already prove, no new learning. Let them pick; "
                       "then pathway_build with that direction." if options
                       else "No demand yet matches what they prove. Say so, "
                       "and offer guided mode."}
    role = resolve_role(direction or "")
    if not role:
        return {"error": "Pick a direction first (the person chooses it). "
                         f"Try one of {sorted(ROLES)}"}
    title = ROLES[role]["title"]
    signals = digest(role)["signals"]
    steps, used = [], set()
    have = [s for s in signals if s["skill"] in mine]
    if have:
        names = sorted({s["skill"] for s in have})[:3]
        steps.append({"step": "Publish or refresh your persona so it shows "
                              f"your proof of {', '.join(names)}.",
                      "reason": _signal_reason(title, have[0]),
                      "done": False})
        used |= set(names)
    for s in signals:
        if len(steps) >= MAX_STEPS:
            break
        if s["skill"] in mine or s["skill"] in used:
            continue
        used.add(s["skill"])
        steps.append({"step": f"Build one piece of proof for {s['skill']}: "
                              "a small project or a work example, then "
                              "save it as a confirmed fact.",
                      "reason": _signal_reason(title, s), "done": False})
    record = {"direction": title, "mode": "guided", "steps": steps,
              "built_on": str(date.today())}
    store.put(user, "pathway", record, record_id="pathway")
    return {**record, "say": "Give only the first step and its reason in "
                             "one line; pathway_next gives the next."
            if steps else "No demand signals yet for this direction, so "
                          "there's no step with a reason. Say so plainly."}


def next_step(user, done=False):
    path = store.get(user, "pathway")
    if not path:
        return {"error": "No pathway yet. Build one for a direction the "
                         "person picked."}
    open_steps = [s for s in path["steps"] if not s["done"]]
    if done and open_steps:
        open_steps[0]["done"] = True
        store.put(user, "pathway", path, record_id="pathway")
        open_steps = open_steps[1:]
    if not open_steps:
        return {"direction": path["direction"], "next": None,
                "say": "Every step is done. Celebrate it, then offer to "
                       "rebuild with fresh demand."}
    return {"direction": path["direction"], "next": open_steps[0],
            "left": len(open_steps),
            "say": "Give this one step and its reason. Nothing else."}
