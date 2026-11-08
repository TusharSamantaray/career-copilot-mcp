"""Nothing is sent without a yes to the exact text, and nothing is kept."""
from copilot import outreach, store

ID = "outreach_gate"
TITLE = "Send only after a yes to the exact text"
BACKLOG = "B-056"
BEFORE = ("Drafts only: every outreach dead-ended at a draft the person "
          "copied by hand, and nothing checked the exact text sent.")

MAIL = {"channel": "email", "to": "recruiter@example.com",
        "subject": "Thanks for today",
        "body": "Hi Alex, thanks for the call today. I'd like to keep "
                "talking about the platform role. Best, Sam"}


def run(user, measure):
    kept_before = sum(len(v) for v in store.export_all(user).values())
    weak = outreach.review(user, **{**MAIL, "body": MAIL["body"] +
                                    " My visa expires soon, so this is "
                                    "urgent."})
    measure("draft mentioning visa deadline or urgency gets approval",
            "approval_id" in weak, False)
    ok = outreach.review(user, **MAIL)
    ticket = ok.get("approval_id", "")
    measure("clean draft gets approval to ask", bool(ticket), True)
    measure("approved without a yes",
            outreach.approve(user, ticket, consent=False, **MAIL)["approved"],
            False)
    edited = {**MAIL, "body": MAIL["body"] + " Call me."}
    measure("approved after an edit",
            outreach.approve(user, ticket, consent=True, **edited)
            ["approved"], False)
    measure("approved for the exact text with a yes",
            outreach.approve(user, ticket, consent=True, **MAIL)["approved"],
            True)
    late = outreach.approve(user, ticket, consent=True, now=10 ** 11, **MAIL)
    measure("approved after it expired", late["approved"], False)
    kept_after = sum(len(v) for v in store.export_all(user).values())
    measure("records stored by the send flow", kept_after - kept_before, 0)
