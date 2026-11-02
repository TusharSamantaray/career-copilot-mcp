"""Resume versions, contribution bullets, LinkedIn review, role fit."""
import re

from copilot import store
from copilot.knowledge.careers import (ADJACENT, COMP_LEVERS, CONTRIBUTION_FRAMEWORK,
                               LEVELS, RESUME_SECTIONS, ROLES, SECTION_FOCUS)
from copilot.scoring import NUMBER_PATTERN, OWNERSHIP_VERBS, _bullets

STRONG_VERBS = OWNERSHIP_VERBS + (
    "cut", "reduced", "scaled", "migrated", "automated", "drove",
    "delivered", "rebuilt", "redesigned", "closed", "grew", "won",
    "negotiated", "increased", "improved", "managed", "established",
    "founded", "trained", "organised", "organized")
SCALE_WORDS = (
    "users", "customers", "clients", "accounts", "countries", "regions",
    "teams", "services", "apis", "requests", "managers", "engineers",
    "employees", "staff", "people", "patients", "students", "beds",
    "stores", "sites", "warehouses", "locations", "projects", "partners",
    "vendors", "budget", "revenue", "$", "million", "billion", "tb", "qps",
    "transactions", "orders")
RESULT_WORDS = ("cut", "reduced", "increased", "saved", "improved",
                "faster", "grew", "lowered", "zero", "eliminated", "%",
                "against", "from", "to ")


def _norm(text):
    return re.sub(r"[^a-z0-9 ]", "", text.lower()).strip()


def resolve_role(name):
    key = _norm(name).replace(" ", "_")
    if key in ROLES:
        return key
    for role_key, role in ROLES.items():
        title = _norm(role["title"])
        if _norm(name) in title or title in _norm(name):
            return role_key
    for role_key in ROLES:
        if role_key.split("_")[0] in key:
            return role_key
    return None


def resolve_level(level, years=0):
    level = (level or "").lower()
    for name, info in LEVELS.items():
        if name in level or any(alias in level for alias in info["aka"]):
            return name
    if years >= 8:
        return "staff"
    if years >= 5:
        return "senior"
    if years >= 2:
        return "mid"
    return "junior"


# ------------------------------------------------------------ contributions

def contribution_check(bullet):
    text = bullet.strip().lstrip("-*• ").strip()
    low = text.lower()
    found = {
        "ownership": low.startswith(STRONG_VERBS),
        "artifact": len(text.split()) >= 5,
        "scale": any(w in low for w in SCALE_WORDS),
        "result": bool(NUMBER_PATTERN.search(text))
        and any(w in low for w in RESULT_WORDS),
    }
    missing = [part for part, ok in found.items() if not ok]
    questions = [CONTRIBUTION_FRAMEWORK["questions"][part]
                 for part in missing]
    if len(text.split()) > 35:
        questions.append("It's over 35 words. Cut it to one line.")
    return {"bullet": text, "score": sum(found.values()), "out_of": 4,
            "has": [p for p, ok in found.items() if ok],
            "missing": missing, "ask_the_user": questions,
            "formula": CONTRIBUTION_FRAMEWORK["formula"]}


# ----------------------------------------------------------------- resumes

def resume_import(user, text, label):
    bullets = _bullets(text)
    body = {"label": label, "text": text, "bullets": len(bullets)}
    record_id = store.put(user, "resume", body)
    return {"id": record_id, "label": label, "bullets_found": len(bullets)}


def resume_versions(user):
    return [{"id": r["id"], "label": r["label"], "bullets": r["bullets"],
             "chars": len(r["text"]), "updated": r["updated"]}
            for r in store.list_kind(user, "resume")]


def resume_merge(user):
    """Unique bullets across every stored version, strongest first."""
    best = {}
    for version in store.list_kind(user, "resume"):
        for bullet in _bullets(version["text"]):
            key = _norm(bullet)
            if not key:
                continue
            check = contribution_check(bullet)
            current = best.get(key)
            if current is None or check["score"] > current["score"]:
                best[key] = {**check, "sources": [version["label"]]}
            elif version["label"] not in current["sources"]:
                current["sources"].append(version["label"])
    merged = sorted(best.values(), key=lambda b: -b["score"])
    return {"unique_bullets": len(merged), "bullets": merged,
            "next": "Confirm each fact with the user, then save it with "
                    "experience_add(confirmed=True)."}


def resume_sections(level="", target_role="", years=0):
    lvl = resolve_level(level, years)
    role = resolve_role(target_role) if target_role else None
    result = {"level": lvl, "section_order": RESUME_SECTIONS[lvl],
              "focus": SECTION_FOCUS[lvl],
              "rules": ["One page under ~8 years of experience, two at most "
                        "after.",
                        "Tagline names the exact target role.",
                        "Every bullet: ownership verb, scale, result.",
                        "Skills section mirrors the job's keywords, "
                        "truthfully.",
                        "No em dashes or unusual glyphs: they break ATS "
                        "parsers."]}
    if role:
        result["keywords_to_cover"] = ROLES[role]["core"]
    return result


# ---------------------------------------------------------------- linkedin

def linkedin_review(profile_text, target_role):
    role_key = resolve_role(target_role)
    if not role_key:
        return {"error": f"Unknown role. Try one of {sorted(ROLES)}"}
    role = ROLES[role_key]
    low = profile_text.lower()
    lines = [ln.strip() for ln in profile_text.splitlines() if ln.strip()]
    headline = lines[0] if lines else ""
    title_words = [w for w in _norm(role["title"]).split() if len(w) > 3]
    keywords = role["core"] + role["edge"]
    present = [k for k in keywords if k in low]
    missing = [k for k in keywords if k not in low]
    bullets = _bullets(profile_text)
    with_numbers = [b for b in bullets if NUMBER_PATTERN.search(b)]
    fixes = []
    if not any(w in headline.lower() for w in title_words):
        fixes.append(f"Headline should name the target role "
                     f"('{role['title']}') plus your strongest area.")
    about_words = len(profile_text.split())
    if about_words < 120:
        fixes.append("Profile text is thin. Write an About section of "
                     "150-250 words: role, what you build, scale, results.")
    core_missing = [k for k in role["core"] if k not in low]
    if core_missing:
        fixes.append("Add the core keywords you genuinely have: "
                     + ", ".join(core_missing[:6]))
    if bullets and len(with_numbers) / len(bullets) < 0.5:
        fixes.append(f"Only {len(with_numbers)}/{len(bullets)} experience "
                     "bullets carry a number. Recruiters search and skim "
                     "for impact.")
    return {"target_role": role["title"], "headline": headline,
            "keywords_present": present, "keywords_missing": missing,
            "fixes": fixes or ["Strong profile for this role."],
            "how_to_get_text": "Paste the profile, or use LinkedIn's "
                               "'More > Save to PDF' and paste its text. "
                               "This tool never logs in to LinkedIn."}


# ---------------------------------------------------------------- role fit

def _word_in(needle, hay):
    return re.search(rf"(^|\W){re.escape(needle)}($|\W)", hay) is not None


def _has(skill, skills):
    """Whole-word match either way, so 'java' never matches 'javascript'."""
    skill = _norm(skill)
    return any(_word_in(skill, s) or _word_in(s, skill) for s in skills)


def role_match(skills, years=0):
    mine = [_norm(s) for s in skills if s.strip()]
    ranked = []
    for key, role in ROLES.items():
        core = [s for s in role["core"] if _has(s, mine)]
        edge = [s for s in role["edge"] if _has(s, mine)]
        score = 0.7 * len(core) / len(role["core"]) \
            + 0.3 * len(edge) / len(role["edge"])
        ranked.append({"role": key, "title": role["title"],
                       "fit_pct": round(score * 100),
                       "matched": core + edge,
                       "missing_core": [s for s in role["core"]
                                        if s not in core]})
    ranked.sort(key=lambda r: -r["fit_pct"])
    return {"level_estimate": resolve_level("", years),
            "best_fits": ranked[:3], "all": ranked}


def career_move(current_role, target_role, skills=None, years=0):
    """Plan a move from one role to another: what carries over, what to
    learn, which stepping-stone roles help, and a rough timeline."""
    cur, tgt = resolve_role(current_role), resolve_role(target_role)
    if not tgt:
        return {"error": f"Unknown target role. Try one of {sorted(ROLES)}"}
    mine = [_norm(s) for s in (skills or [])]
    if cur:
        mine += [_norm(s) for s in ROLES[cur]["core"]]
    target = ROLES[tgt]
    carry = [s for s in target["core"] if _has(s, mine)]
    gaps = [s for s in target["core"] if s not in carry]
    stepping = []
    if cur and tgt not in ADJACENT.get(cur, []):
        stepping = [ROLES[r]["title"] for r in ADJACENT.get(cur, [])
                    if tgt in ADJACENT.get(r, [])]
    distance = ("adjacent" if cur and tgt in ADJACENT.get(cur, [])
                else "same family" if cur and ROLES[cur]["family"]
                == target["family"] else "career change")
    months = min(3 + 2 * len(gaps), 24) if distance == "career change" \
        else min(1 + len(gaps), 12)
    steps = [
        f"Learn the top gaps first: {', '.join(gaps[:3]) or 'none'}. Prove "
        "each with a real project or certification, not just a course.",
        "Try an internal move or a stretch project in your current job: "
        "the cheapest way to get the new title on your resume.",
        "Rewrite your resume and LinkedIn for the target role, leading with "
        "the skills that carry over (use resume_sections and "
        "linkedin_review).",
        f"Talk to 5 people already working as a {target['title']} about "
        "how they got in.",
        "Apply to roles that value your background, where your old field "
        "is an advantage (e.g. fintech for a finance person).",
    ]
    if stepping:
        steps.insert(1, "Consider a stepping-stone role first: "
                        + ", ".join(stepping))
    return {"from": ROLES[cur]["title"] if cur else current_role,
            "to": target["title"], "distance": distance,
            "transferable": carry, "skills_to_build": gaps,
            "nice_to_have": target["edge"], "stepping_stones": stepping,
            "rough_timeline_months": months, "steps": steps,
            "interview_loop": target["loop"]}


def skills_gap(target_role, level="", skills=None, years=0):
    role_key = resolve_role(target_role)
    if not role_key:
        return {"error": f"Unknown role. Try one of {sorted(ROLES)}"}
    role = ROLES[role_key]
    lvl = resolve_level(level, years)
    mine = [_norm(s) for s in (skills or [])]
    return {"role": role["title"], "level": lvl,
            "level_expectations": LEVELS[lvl],
            "missing_core": [s for s in role["core"] if not _has(s, mine)],
            "missing_edge": [s for s in role["edge"] if not _has(s, mine)],
            "interview_loop": role["loop"],
            "pay_levers": COMP_LEVERS}
