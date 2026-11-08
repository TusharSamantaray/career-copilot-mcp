"""The persona: an anonymous, verified view of a person's profile.

Built from what the person already confirmed: confirmed work facts and
the skills those facts prove. Never a name, contact details, photo, age,
gender, salary, work authorization or employer names. Private until the
person previews it and says yes to that exact view; they can unpublish
or delete it at any time. It lives in their own data file, so deleting
their data deletes it too.
"""
import hashlib
import json
import re
import secrets
from datetime import date

from copilot import conduct
from copilot import facts
from copilot import journey
from copilot import store
from copilot.knowledge.careers import ROLES

SKILLS = sorted({s for r in ROLES.values() for s in r["core"] + r["edge"]},
                key=len, reverse=True)
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
URL = re.compile(r"https?://\S+|www\.\S+|\b[\w-]+\.(?:com|io|dev|me|org|"
                 r"net)/\S*", re.I)
HANDLE = re.compile(r"(?<![\w.])@\w{2,}")
PHONE_ISH = re.compile(r"\+?\(?\d[\d\s().-]{7,}\d")
STRENGTH = {"owned": 3, "led": 3, "contributed": 2, "observed": 1}
HIDDEN = "[hidden]"


def has_skill(skill, text):
    return re.search(rf"(^|[^a-z0-9]){re.escape(skill)}($|[^a-z0-9])",
                     text.lower()) is not None


def _phone(match):
    digits = re.sub(r"\D", "", match.group(0))
    return HIDDEN if 9 <= len(digits) <= 15 else match.group(0)


def _names(user, profile):
    """Words that could point at the person: employers they named,
    companies on their lists and internal names from resume snapshots."""
    names = {f.get("employer", "") for f in store.list_kind(user, "fact")}
    names |= {e.get("employer", "") for e in
              store.list_kind(user, "experience")}
    names |= set(profile.get("target_companies", []))
    names |= set(profile.get("excluded_companies", []))
    for snap in store.list_kind(user, "snapshot"):
        names |= set(snap.get("avoid_terms", []))
    return sorted({n.strip() for n in names if n and len(n.strip()) > 1},
                  key=len, reverse=True)


def scrub(text, names):
    text = EMAIL.sub(HIDDEN, text)
    text = URL.sub(HIDDEN, text)
    text = HANDLE.sub(HIDDEN, text)
    text = PHONE_ISH.sub(_phone, text)
    for name in names:
        text = re.sub(rf"(?<!\w){re.escape(name)}(?!\w)", "[employer]", text,
                      flags=re.I)
    return text


def _band(years):
    years = int(years or 0)
    if not years:
        return ""
    return ("0-2 years" if years <= 2 else "3-5 years" if years <= 5 else
            "6-9 years" if years <= 9 else "10+ years")


def _line_id(statement):
    return hashlib.sha256(statement.lower().encode()).hexdigest()[:6]


def build(user, hide=()):
    """The exact view others would see, and what was left out and why."""
    profile = journey.profile(user)
    sure = profile.get("confidence", {})
    names = _names(user, profile)

    def confirmed(field):
        value = profile.get(field)
        if value in (None, "", [], 0) or sure.get(field) == "unsure":
            return None
        return value

    evidence, left_out = [], []
    for fact in facts.confirmed_facts(user):
        line_id = _line_id(fact["statement"])
        text = scrub(fact["statement"], names)
        if line_id in hide:
            left_out.append({"id": line_id, "why": "you hid it"})
            continue
        traits = [i for i in conduct.check(user, text, "resume")["issues"]
                  if i["type"] == "personal_trait"]
        if traits:
            left_out.append({"id": line_id,
                             "why": "mentions a personal trait"})
            continue
        evidence.append({"id": line_id, "text": text,
                         "part": fact.get("ownership", "contributed"),
                         "skills": [s for s in SKILLS if has_skill(s, text)]})
    skills = {}
    for line in evidence:
        for skill in line["skills"]:
            row = skills.setdefault(skill, {"skill": skill, "evidence": 0,
                                            "strongest": "observed"})
            row["evidence"] += 1
            if STRENGTH[line["part"]] > STRENGTH[row["strongest"]]:
                row["strongest"] = line["part"]
    headline = confirmed("target_role") or confirmed("current_role") or ""
    locations = list(confirmed("locations") or [])
    if confirmed("location") and confirmed("location") not in locations:
        locations.insert(0, confirmed("location"))
    view = {"headline": scrub(str(headline), names),
            "level": confirmed("level") or "",
            "experience": _band(confirmed("years_experience")),
            "locations": locations,
            "skills": sorted(skills.values(),
                             key=lambda r: (-r["evidence"], r["skill"])),
            "evidence": evidence}
    return view, left_out


def _digest(view):
    return hashlib.sha256(json.dumps(view, sort_keys=True).encode()
                          ).hexdigest()[:16]


def current(user):
    return store.get(user, "persona")


def publish(user, accept=False, preview_id="", hide=None):
    """accept=False: a preview of exactly what would be visible, with a
    preview_id. accept=True with that preview_id publishes that view."""
    saved = current(user) or {}
    hide = sorted(set(hide if hide is not None else saved.get("hide", [])))
    view, left_out = build(user, set(hide))
    digest = _digest(view)
    if not view["skills"]:
        return {"published": False, "preview": view, "left_out": left_out,
                "error": "Nothing verified to show yet. A skill appears "
                         "only when a confirmed work fact proves it.",
                "say": "Offer to add one confirmed fact about their work "
                       "first (experience_add)."}
    if not accept:
        return {"published": False, "preview": view, "preview_id": digest,
                "hide": hide, "left_out": left_out,
                "never_shown": ["name", "contact details", "photo", "age",
                                "gender", "salary", "work authorization",
                                "employer names"],
                "say": "Show every line of the preview exactly as it is and "
                       "ask 'Publish this?'. To leave a line out, call again "
                       "with its id in hide. Publish only after their yes, "
                       "with this preview_id."}
    if preview_id != digest:
        return {"published": False, "error": "The persona changed since the "
                "preview, or the preview_id is wrong. Show the new preview "
                "and ask again.", "preview": view, "preview_id": digest}
    record = {"persona_id": saved.get("persona_id") or
              "p_" + secrets.token_hex(4),
              "published": True, "published_on": str(date.today()),
              "view": view, "hide": hide}
    store.put(user, "persona", record, record_id="persona")
    return {"published": True, "persona_id": record["persona_id"],
            "say": "Say it's published and anonymous, that people searching "
                   "see only this view, and that persona_unpublish takes it "
                   "down any time. It doesn't update by itself: publish "
                   "again after adding facts."}


def unpublish(user, delete=False):
    saved = current(user)
    if not saved:
        return {"published": False, "note": "No persona to take down."}
    if delete:
        store.delete(user, "persona")
        return {"published": False, "deleted": True}
    saved["published"] = False
    saved["unpublished_on"] = str(date.today())
    store.put(user, "persona", saved, record_id="persona")
    return {"published": False, "persona_id": saved["persona_id"],
            "note": "Hidden from search. Publish again any time."}


def published():
    """(user, record) for every published persona."""
    for user in store.users():
        try:
            record = store.get(user, "persona")
        except Exception:          # an unreadable file never breaks search
            continue
        if record and record.get("published"):
            yield user, record


def find(persona_id):
    for user, record in published():
        if record["persona_id"] == persona_id:
            return user, record
    return None, None
