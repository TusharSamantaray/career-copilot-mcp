"""The recruiter side: find personas for a job, and ask them questions.

A recruiter is any signed-in person on this server who searches; there
is no separate website or account type. They bring a posting and what
they need, and get the top 5 published personas ranked by verified
evidence. Persona chat answers only from the published view, and refuses
identity and salary questions. No job posts are hosted, no salary is
shown, stored or negotiated, and nobody is contacted automatically.
"""
import re
from datetime import date

from copilot import demand
from copilot import facts
from copilot import persona
from copilot import store
from copilot.jobs import LEVELS, YEARS

TOP = 5
IDENTITY = re.compile(
    r"\b(name|who (?:is|are) (?:they|you|this)|e-?mail|phone|call (?:them|"
    r"you)|contact|reach (?:them|you)|linkedin|github|twitter|instagram|"
    r"social media|address|where (?:do|does) (?:they|you|he|she) (?:live|"
    r"work)|which (?:company|employer)|current (?:company|employer)|"
    r"employers?|which compan(?:y|ies)|age|how old|born|gender|"
    r"married|photo|picture|nationality|citizen\w*|religio\w*|identity|"
    r"real person|resume with)\b", re.I)
PAY = re.compile(r"\b(salary|salaries|pay|compensation|comp|wages?|"
                 r"(?:day|hourly) rate|ctc|earns?|earning|bonus|"
                 r"offer amount)\b", re.I)
WEIGHT = {"owned": 3, "led": 3, "contributed": 2, "observed": 1}


def _terms(items):
    return [t.strip().lower() for t in items or [] if t and t.strip()]


def _proves(view, term):
    """Evidence lines in a persona that prove a term (a skill or a word)."""
    return [line for line in view["evidence"]
            if term in line["skills"] or persona.has_skill(term, line["text"])]


def _card(view, persona_id, wanted):
    matched, missing, score = [], [], 0
    for term in wanted:
        lines = _proves(view, term)
        if lines:
            best = max(lines, key=lambda line: WEIGHT[line["part"]])
            matched.append({"skill": term, "evidence": len(lines),
                            "strongest": best["part"]})
            score += min(len(lines), 3) * WEIGHT[best["part"]]
        else:
            missing.append(term)
    proof = []
    for row in matched:
        for line in _proves(view, row["skill"]):
            if line["text"] not in proof and len(proof) < 2:
                proof.append(line["text"])
    led = sum(1 for row in matched if row["strongest"] in ("owned", "led"))
    return {"persona_id": persona_id, "headline": view["headline"],
            "level": view["level"], "experience": view["experience"],
            "locations": view["locations"], "matched": matched,
            "missing": missing, "proof": proof,
            "why": f"Proves {len(matched)} of {len(wanted)} skills asked"
                   + (f", {led} owned or led" if led else ""),
            "_rank": (len(matched) / max(len(wanted), 1), score)}


def search(user, posting_text, title="", must_have=None, nice_to_have=None,
           location=""):
    low = f"{title} {posting_text or ''}".lower()
    asked = [s for s in persona.SKILLS if persona.has_skill(s, low)]
    must = _terms(must_have)
    wanted = list(dict.fromkeys(must + asked + _terms(nice_to_have)))
    if not wanted:
        return {"error": "No skills found in the posting. Paste the full "
                         "posting, or say what the role must have."}
    demand.note_search(user, title or posting_text[:200], wanted)
    place = (location or "").strip().lower()
    cards, out = [], {"missing_a_must_have": 0, "location": 0}
    for owner, record in persona.published():
        if owner == user:
            continue                      # never show people themselves
        view = record["view"]
        if any(not _proves(view, term) for term in must):
            out["missing_a_must_have"] += 1
            continue
        where = " ".join(view["locations"]).lower()
        if place and where and place not in where and "remote" not in where:
            out["location"] += 1
            continue
        card = _card(view, record["persona_id"], wanted)
        if card["matched"]:
            cards.append(card)
    cards.sort(key=lambda c: c["_rank"], reverse=True)
    top = [{k: v for k, v in c.items() if k != "_rank"} for c in cards[:TOP]]
    head = low[:400]
    return {"role": title or "untitled",
            "level_read": next((name for word, name in LEVELS
                                if word in head), "not stated"),
            "years_asked": sorted({int(y) for y in YEARS.findall(low)
                                   if int(y) < 30}),
            "skills_asked": wanted, "must_have": must,
            "matches": top, "searched": len(cards) + sum(out.values()),
            "filtered_out": out,
            "say": "List each match in one line: its why and one proof "
                   "line. These are anonymous personas: verified work only, "
                   "no names, contacts or salary. To learn more, use "
                   "persona_chat; to ask to meet one, persona_intro." if top
                   else
                   "No published persona matches yet. Say so plainly; "
                   "loosening a must-have may help."}


def _screened(user, persona_id):
    """Count the recruiter's questions to a persona (never the text)."""
    record_id = f"screen-{persona_id}"
    row = store.get(user, record_id) or {"persona_id": persona_id,
                                         "questions": 0,
                                         "first_on": str(date.today())}
    row["questions"] += 1
    row["last_on"] = str(date.today())
    store.put(user, "screen", row, record_id=record_id)


def chat(user, persona_id, question):
    owner, record = persona.find(persona_id)
    if not record:
        return {"error": "No published persona with that id. It may have "
                         "been taken down."}
    if IDENTITY.search(question or ""):
        return {"refused": "identity",
                "say": "Say the persona can't share who they are, where they "
                       "work or how to reach them. Identity is shared only "
                       "when both sides agree to talk: use persona_intro."}
    if PAY.search(question or ""):
        return {"refused": "salary",
                "say": "Say Career Copilot doesn't show, store or negotiate "
                       "salary. That's for the two of them to discuss directly."}
    if owner != user:
        _screened(user, persona_id)
    view = record["view"]
    asked = [s for s in persona.SKILLS if persona.has_skill(s, question)]
    if asked:
        lines = [line for line in view["evidence"]
                 if set(asked) & set(line["skills"])]
    else:
        words = facts._words(question)
        lines = [line for line in view["evidence"]
                 if words & facts._words(line["text"])]
    shown = {row["skill"] for row in view["skills"]}
    return {"persona_id": persona_id, "headline": view["headline"],
            "answer_from": [{"text": line["text"], "part": line["part"]}
                            for line in lines[:4]],
            "skills_asked": asked,
            "not_verified": [s for s in asked if s not in shown],
            "say": "Answer only from answer_from: what the persona did, and "
                   "whether they owned, led or contributed. If it's empty or "
                   "a skill is in not_verified, say the persona has no "
                   "verified work for that. Never guess or add detail."}
