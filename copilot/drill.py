"""The hiring-post drill as one guided flow (GitHub #36).

From one hiring post the person pasted to a reviewed, approved message
and a logged application:

    read the post → fit → company research → one-pager (optional)
    → message draft → outreach_review → the person's yes →
    outreach_approve → they send it → application_log

This module does the reading and drafting in one call and returns the
checklist with the one next step. It never sends, stores or skips the
person's yes: the review, the approval and the log stay separate tools,
so each happens only when the person is there for it.
"""
from datetime import date, timedelta

from copilot import company
from copilot import conduct
from copilot import facts
from copilot import hiring_posts
from copilot import jobs
from copilot import prep

CHANNELS = ("linkedin_message", "email")
FOLLOW_UP_DAYS = 5


def _words(text):
    return set(company._words(text))


def _best_fact(user, text):
    """The confirmed fact that best matches the post, quoted as said."""
    mine = facts.confirmed_statements(user)
    if not mine:
        return None
    want = _words(text)
    return max(mine, key=lambda f: len(_words(f) & want))


def _detail(fact):
    """'Led a team of 4' reads as 'One thing I've done that fits: led a
    team of 4.' The fact's own words, unchanged otherwise."""
    fact = fact.strip().rstrip(".")
    if len(fact) > 1 and fact[0].isupper() and fact[1].islower():
        fact = fact[0].lower() + fact[1:]
    return f"One thing I've done that fits: {fact}."


def run(user, post, domain="", channel="linkedin_message", me="",
        voice="plain", today=None):
    if channel not in CHANNELS:
        return {"error": f"channel must be one of {list(CHANNELS)}"}
    text = str(post or "")[:6000]
    if not hiring_posts.HIRING.search(text):
        return {"error": "This doesn't read like a hiring post.",
                "ask": "Paste the post where someone says they're hiring."}
    today = today or date.today()
    fields = hiring_posts.parse(text, today)
    role, firm = fields["role"] or "", fields["company"] or ""
    if not firm:
        return {"post": fields, "error": "Which company is this for?",
                "ask": "The post doesn't name the company. Which is it, "
                       "and its website if you know it?"}
    fit = jobs.jd_analyze(user, text, role, firm, remember=False)
    stale = fields["age_days"] is not None and \
        fields["age_days"] > hiring_posts.FRESH_DAYS
    research = company.research(firm, domain, today=today)
    pitch = company.one_pager(user, research, role)
    best = _best_fact(user, text)
    to = fields["contact"] if fields["contact"] and "@" in \
        fields["contact"] else (fields["poster"] or "")
    draft = None
    if best:
        draft = prep.message_draft(
            "hiring_post_reply", firm, role or "open",
            (fields["poster"] or "").split(" ")[0], _detail(best),
            me, voice)
        draft["check"] = conduct.check(
            user, f"{draft['subject']}\n{draft['body']}", "message")
        draft["fact_used"] = best
    if channel == "email" and "@" not in (to or ""):
        channel_note = ("The post gives no email; send it as a LinkedIn "
                        "message instead.")
        channel = "linkedin_message"
    else:
        channel_note = None
    follow = (today + timedelta(days=FOLLOW_UP_DAYS)).isoformat()
    steps = [
        {"step": "read the post", "status": "done"},
        {"step": "fit", "status": "done", "verdict": fit["verdict"]},
        {"step": "company research",
         "status": "done" if not research.get("gaps") else "gaps",
         "do": "Search the web for: " + "; ".join(research["search_next"])
               + ". Then company_research(found=[...]) with links."
         if research.get("gaps") else None},
        {"step": "one-pager (optional)", "status": "todo",
         "do": "one_pager_build with the research record, if they want "
               "an attachment."},
        {"step": "message", "status": "draft" if draft else "blocked",
         "do": "Read the draft with them and edit together."
         if draft else "No confirmed facts yet: ask for one thing they did "
                       "that fits this role, read it back, save it."},
        {"step": "review", "status": "todo",
         "do": f"outreach_review(channel='{channel}', to, subject, body). "
               "If they want to mention their visa deadline or another "
               "weakness in this message, add share_anyway with its name "
               "only after they say so."},
        {"step": "their yes", "status": "todo",
         "do": "Show the exact text. Only a yes to it counts. Then "
               "outreach_approve(consent=True) with the same fields."},
        {"step": "send", "status": "todo",
         "do": "They send it themselves (LinkedIn) or with their own "
               "email connector."},
        {"step": "log", "status": "todo",
         "do": f"After they confirm it's sent: application_log(company="
               f"'{firm}', role='{role}', status='applied', next_action="
               f"'Follow up on the outreach', due_date='{follow}')."},
    ]
    warnings = []
    if fit["dealbreakers_hit"]:
        warnings.append("Breaks a dealbreaker: "
                        + ", ".join(fit["dealbreakers_hit"])
                        + ". Ask if they still want to go ahead.")
    if stale:
        warnings.append(f"Posted {fields['age_days']} days ago; the role "
                        "may be filled.")
    if channel_note:
        warnings.append(channel_note)
    nxt = next(s for s in steps if s["status"] in ("gaps", "blocked",
                                                    "draft"))
    return {
        "post": fields, "channel": channel, "to": to or None,
        "fit": {k: fit[k] for k in ("verdict", "fit_points", "gap_points",
                                    "pay_read", "sponsorship_read")},
        "research": research,
        "one_pager_material": pitch.get("material"),
        "draft": draft, "warnings": warnings, "steps": steps,
        "next": nxt,
        "stored": "Nothing. Review, approval and the log are separate "
                  "steps, each with the person.",
        "say": "Give the fit verdict and one reason, any warning, then the "
               "one next step. Don't run ahead: each step waits for them.",
    }
