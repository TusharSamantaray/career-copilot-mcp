"""Introductions: someone hiring asks to meet a persona; identity is
revealed only when both sides confirm.

The request goes to the persona's owner with the company, role and a
checked message. Nothing about who either side is changes hands until
both have said yes and each chose what contact to share. Each side's
contact stays in its own data file; the persona record notes every
reveal and that it came after the merit screen.
"""
import secrets
from datetime import date

from copilot import conduct
from copilot import persona
from copilot import store


def _find(intro_id, side):
    for user in store.users():
        try:
            row = store.get(user, intro_id)
        except Exception:
            continue
        if row and row.get("side") == side:
            return user, row
    return None, None


def request(user, persona_id, company, role, message):
    owner, record = persona.find(persona_id)
    if not record:
        return {"error": "No published persona with that id."}
    if owner == user:
        return {"error": "That's your own persona."}
    if not company.strip() or not role.strip():
        return {"error": "Say which company and role this is for, so they "
                         "can decide."}
    check = conduct.check(user, message, "plan")
    issues = [i for i in check["issues"]
              if i["type"] != "missing_disclaimer"]
    if any(i["severity"] == "fix" for i in issues):
        return {"sent": False, "check": {"issues": issues},
                "say": "Fix the flagged wording, then send again."}
    screen = store.get(user, f"screen-{persona_id}") or {}
    intro_id = "i_" + secrets.token_hex(4)
    today = str(date.today())
    store.put(owner, "intro", {
        "side": "candidate", "intro_id": intro_id, "persona_id": persona_id,
        "company": company.strip()[:80], "role": role.strip()[:80],
        "message": message.strip()[:1000], "requested_on": today,
        "screened_questions": screen.get("questions", 0),
        "status": "requested"}, record_id=intro_id)
    store.put(user, "intro_sent", {
        "side": "recruiter", "intro_id": intro_id, "persona_id": persona_id,
        "company": company.strip()[:80], "role": role.strip()[:80],
        "sent_on": today}, record_id=intro_id)
    return {"sent": True, "intro_id": intro_id,
            "say": "Say the request went to the persona, with no names on "
                   "either side yet. Identity is shared only if they agree "
                   "and you both confirm with identity_reveal."}


def _status(intro):
    return {"intro_id": intro["intro_id"], "company": intro["company"],
            "role": intro["role"], "status": intro["status"],
            "requested_on": intro["requested_on"],
            "you_confirmed": None, "they_confirmed": None}


def inbox(user):
    """Requests to the person's persona, and requests they sent."""
    received = []
    for row in store.list_kind(user, "intro"):
        item = _status(row)
        item.update(message=row["message"],
                    screened_questions=row["screened_questions"],
                    you_confirmed=bool(row.get("candidate_on")),
                    they_confirmed=bool(row.get("recruiter_on")))
        received.append(item)
    sent = []
    for row in store.list_kind(user, "intro_sent"):
        _, intro = _find(row["intro_id"], "candidate")
        if intro:
            item = _status(intro)
            item.update(you_confirmed=bool(intro.get("recruiter_on")),
                        they_confirmed=bool(intro.get("candidate_on")))
        else:
            item = {"intro_id": row["intro_id"], "status": "withdrawn"}
        sent.append(item)
    return {"received": received, "sent": sent,
            "say": "For each request, give the company, role and message in "
                   "one line and ask: talk to them (identity_reveal with "
                   "confirm=true and what contact to share) or decline?"
                   if received else "Nothing new."}


def reveal(user, intro_id, confirm, share=""):
    mine = store.get(user, intro_id)
    if not mine or mine.get("side") not in ("candidate", "recruiter"):
        return {"error": "No introduction with that id for you."}
    side = mine["side"]
    owner, intro = (user, mine) if side == "candidate" else \
        _find(intro_id, "candidate")
    if not intro:
        return {"revealed": False, "status": "withdrawn",
                "say": "The other side deleted this request."}
    if intro["status"] in ("declined", "revealed"):
        return {"revealed": intro["status"] == "revealed",
                "status": intro["status"], **(_shared(user, side, intro)
                                              if intro["status"] ==
                                              "revealed" else {})}
    today = str(date.today())
    if not confirm:
        intro["status"] = "declined"
        intro["declined_on"] = today
        intro["declined_by"] = side
        store.put(owner, "intro", intro, record_id=intro_id)
        return {"revealed": False, "status": "declined",
                "say": "Say it's declined, and nothing about either of you "
                       "was shared."}
    if not share.strip():
        return {"revealed": False, "error": "Say what contact to share when "
                "both agree (for example a name and an email). Nothing is "
                "shared before both confirm."}
    mine["share"] = share.strip()[:200]
    store.put(user, "intro" if side == "candidate" else "intro_sent", mine,
              record_id=intro_id)
    if side == "candidate":
        intro = mine
    intro[f"{side}_on"] = today
    if intro.get("candidate_on") and intro.get("recruiter_on"):
        intro["status"] = "revealed"
        intro["revealed_on"] = today
        _note_on_persona(owner, intro)
    else:
        intro["status"] = "waiting"
    store.put(owner, "intro", intro, record_id=intro_id)
    if intro["status"] != "revealed":
        other = "the person hiring" if side == "candidate" else "the persona"
        return {"revealed": False, "status": "waiting",
                "waiting_for": other,
                "say": f"Say you've confirmed; nothing is shared until "
                       f"{other} confirms too."}
    return {"revealed": True, "status": "revealed",
            **_shared(user, side, intro)}


def _shared(user, side, intro):
    """What the other side chose to share, read from their own file."""
    if side == "candidate":
        _, theirs = _find(intro["intro_id"], "recruiter")
    else:
        theirs = intro
    return {"they_shared": (theirs or {}).get("share", ""),
            "merit_screen": {
                "questions_before_intro": intro["screened_questions"],
                "requested_on": intro["requested_on"],
                "revealed_on": intro.get("revealed_on")},
            "say": "Give the shared contact as it is. From here the two of "
                   "them talk directly; Career Copilot sends nothing."}


def _note_on_persona(owner, intro):
    record = store.get(owner, "persona")
    if not record:
        return
    record.setdefault("reveals", []).append({
        "intro_id": intro["intro_id"], "company": intro["company"],
        "role": intro["role"], "requested_on": intro["requested_on"],
        "revealed_on": intro["revealed_on"],
        "after_screen": intro["screened_questions"] > 0})
    store.put(owner, "persona", record, record_id="persona")
