"""Review, then the person's yes, then their own app sends.

Career Copilot never sends, posts or schedules anything itself and never
holds a login. For any email, calendar change or LinkedIn post:

1. outreach_review checks the exact text (response_check plus "never
   volunteer weakness") and, if it passes, returns an approval_id: a
   signed seal over that exact text, recipient and channel, valid for
   30 minutes. Nothing is stored. Outreach never volunteers a weakness
   (a performance plan, urgency, a visa deadline) unless the person
   chooses to say it in this message: share_anyway names it, the check
   becomes a note, and that choice is sealed into the approval with the
   exact text, so it can't carry over to another message.
2. The assistant shows the exact text and asks "Send this?".
3. Only after a yes for that message, outreach_approve(consent=True)
   checks the seal. Any edit since review means review again.
4. The person's own connector in their chat (Gmail, Outlook, Google
   Calendar...) sends it, and the assistant checks sent mail or the
   calendar before saying it's done.

The seal is stateless, so no draft text is kept on the server.
"""
import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import time

from copilot import conduct

TTL = 30 * 60
REMINDERS = [30, 1]                 # minutes before, the standing rule
_LOCAL_KEY = secrets.token_bytes(32)
LINKEDIN_SHARE = "https://www.linkedin.com/feed/?shareActive=true"
LINKEDIN_PROFILE = "https://www.linkedin.com/in/me/edit/intro/"
CHANNELS = {
    "email": {"kind": "message", "needs": ("to", "body"),
              "send_with": "the person's own email connector (for example "
                           "Gmail or Outlook): reply in thread_id if given, "
                           "else a new message",
              "verify": "Search their sent mail for the subject and "
                        "recipient. Say it's sent only once it's there."},
    "calendar_event": {"kind": "plan", "needs": ("subject", "when"),
                       "send_with": "the person's own calendar connector, "
                                    "with reminders 30 and 1 minute before",
                       "verify": "List events at that time and check it's "
                                 "there with both reminders."},
    "calendar_cancel": {"kind": "plan", "needs": ("event_id",),
                        "send_with": "the person's own calendar connector: "
                                     "cancel only this event",
                        "verify": "List events at that time and check it's "
                                  "gone."},
    "linkedin_message": {"kind": "message", "needs": ("to", "body"),
                         "send_with": "the person sends it themselves in "
                                      "LinkedIn (Career Copilot can't and "
                                      "won't): give them the exact text to "
                                      "paste into a message to the poster",
                         "verify": "Ask them to confirm it's sent, then "
                                   "log the application."},
    "linkedin_post": {"kind": "linkedin", "needs": ("body",),
                      "send_with": "the person's own LinkedIn connector if "
                                   "they have one; otherwise give them the "
                                   "exact text to paste at "
                                   f"{LINKEDIN_SHARE}",
                      "verify": "Ask them to open the post and check it "
                                "matches the approved text."},
    "linkedin_profile": {"kind": "linkedin", "needs": ("body",),
                         "send_with": "the person's own LinkedIn connector "
                                      "if they have one; otherwise give the "
                                      "exact text to paste at "
                                      f"{LINKEDIN_PROFILE}",
                         "verify": "Ask them to reload their profile and "
                                   "check it matches."},
}
# Outreach never volunteers weakness (spec: "never volunteer weakness").
WEAKNESS = [
    ("performance plan", re.compile(
        r"\b(?:PIP|performance improvement plan|performance plan)\b", re.I)),
    ("urgency", re.compile(
        r"\b(?:urgent(?:ly)?|asap|desperate(?:ly)?|any job|need (?:a|this) "
        r"job (?:now|fast|quickly))\b", re.I)),
    ("visa deadline", re.compile(
        r"\b(?:visa (?:expires|runs out|deadline)|grace period|"
        r"(?:60|sixty)[- ]day(?:s)? (?:to find|grace)|status (?:ends|"
        r"expires))\b", re.I)),
]


def _key():
    base = (os.environ.get("CAREER_COPILOT_JWT_KEY")
            or os.environ.get("CAREER_COPILOT_MASTER_KEY"))
    if base:
        return hashlib.sha256(b"outreach:" + base.encode()).digest()
    return _LOCAL_KEY        # local mode: approvals last one run


def _fields(channel, to, subject, body, thread_id, when, event_id,
            share=()):
    return {"channel": channel, "to": to.strip().lower(),
            "subject": subject.strip(), "body": body.strip(),
            "thread_id": thread_id.strip(), "when": when.strip(),
            "event_id": event_id.strip(), "share": ",".join(share)}


def _share(share_anyway):
    """The weaknesses the person chose to mention, or an error."""
    chosen = sorted({s.strip().lower() for s in share_anyway or []
                     if s.strip()})
    names = [n for n, _ in WEAKNESS]
    unknown = [s for s in chosen if s not in names]
    if unknown:
        return chosen, {"error": f"share_anyway can only name {names}; "
                                 f"got {unknown}."}
    return chosen, None


def _sign(user, fields, expires):
    payload = json.dumps([user, expires, fields], sort_keys=True).encode()
    return hmac.new(_key(), payload, hashlib.sha256).digest()


def _b64(raw):
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def weakness(text, chosen=()):
    out = []
    for name, p in WEAKNESS:
        if not p.search(text or ""):
            continue
        found = sorted({m.group(0).lower() for m in p.finditer(text)})
        if name in chosen:
            out.append({"type": "shared_by_choice", "severity": "note",
                        "found": found,
                        "why": f"The person chose to mention {name} in "
                               "this message."})
            continue
        out.append({"type": "volunteers_weakness", "severity": "fix",
                    "found": found,
                    "why": f"Outreach shouldn't mention {name}: it gives "
                           "away leverage and isn't needed to start a "
                           "conversation.",
                    "suggest": "Remove it. Share it later only if asked "
                               "directly, and only the true, factual "
                               "wording. If the person says they want it in "
                               "this message, review again with "
                               f"share_anyway=['{name}']."})
    return out


def review(user, channel, to="", subject="", body="", thread_id="",
           when="", event_id="", now=None, share_anyway=None):
    if channel not in CHANNELS:
        return {"error": "Unknown channel.", "channels": sorted(CHANNELS)}
    chosen, problem = _share(share_anyway)
    if problem:
        return problem
    spec = CHANNELS[channel]
    fields = _fields(channel, to, subject, body, thread_id, when, event_id,
                     chosen)
    missing = [n for n in spec["needs"] if not fields[n]]
    if missing:
        return {"error": f"Missing: {', '.join(missing)}."}
    text = "\n".join(v for v in (fields["subject"], fields["body"]) if v)
    check = conduct.check(user, text, spec["kind"]) if text else \
        {"ok": True, "fix": 0, "issues": []}
    issues = check["issues"] + (weakness(text, chosen)
                                if channel != "calendar_cancel" else [])
    blocking = [i for i in issues if i["severity"] == "fix"]
    result = {"channel": channel, "check": {"ok": not blocking,
                                            "issues": issues}}
    if blocking:
        result["next"] = ("Fix what's flagged, then review again. No "
                          "approval until it passes.")
        return result
    expires = int((now or time.time()) + TTL)
    seal = _sign(user, fields, expires)
    result.update({
        "approval_id": f"{expires}.{_b64(seal)}",
        "expires_in_minutes": TTL // 60,
        "show_user": {k: v for k, v in fields.items()
                      if v and k not in ("channel", "share")},
        "ask": "Show exactly this and ask: send it? (yes / edit / no). "
               "Only a yes for this message counts.",
        "stored": "Nothing. The draft isn't kept on the server."})
    if channel == "calendar_event":
        result["show_user"]["reminders_minutes_before"] = REMINDERS
    if chosen:
        result["shared_by_choice"] = chosen
        result["ask"] = ("Show exactly this, and say it mentions "
                         + " and ".join(chosen) + ", as they chose. Then "
                         "ask: send it? (yes / edit / no). Only a yes for "
                         "this message counts.")
    return result


def approve(user, approval_id, channel, to="", subject="", body="",
            thread_id="", when="", event_id="", consent=False, now=None,
            share_anyway=None):
    if consent is not True:
        return {"approved": False, "status": "not_sent",
                "next": "Nothing was sent. Ask if they want to edit it or "
                        "leave it."}
    if channel not in CHANNELS:
        return {"error": "Unknown channel.", "channels": sorted(CHANNELS)}
    chosen, problem = _share(share_anyway)
    if problem:
        return problem
    fields = _fields(channel, to, subject, body, thread_id, when, event_id,
                     chosen)
    try:
        expires_text, given = approval_id.split(".", 1)
        expires = int(expires_text)
    except ValueError:
        return {"approved": False, "status": "refused",
                "why": "That approval_id isn't valid. Run outreach_review."}
    if (now or time.time()) > expires:
        return {"approved": False, "status": "refused",
                "why": "The approval expired. Review it again and ask "
                       "once more."}
    if not hmac.compare_digest(given, _b64(_sign(user, fields, expires))):
        return {"approved": False, "status": "refused",
                "why": "This isn't the exact text, recipient or channel "
                       "that was reviewed. Review the new version and ask "
                       "again."}
    spec = CHANNELS[channel]
    out = {"approved": True, "status": "approved",
           "send_with": spec["send_with"], "verify": spec["verify"],
           "rules": ["Send exactly the approved text, once.",
                     "Career Copilot doesn't send it and keeps no copy.",
                     "Say it's done only after the check in verify."]}
    if channel == "calendar_event":
        out["reminders_minutes_before"] = REMINDERS
    if chosen:
        out["shared_by_choice"] = {
            "mentions": chosen,
            "recorded": "Their choice is sealed into this approval with "
                        "the exact text. It doesn't carry over to any "
                        "other message, and nothing is stored."}
    return out
