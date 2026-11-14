"""From a hiring post to an approved message, with the person's choice
about mentioning a weakness bound to that one message."""
from datetime import date

from copilot import company, drill, facts, outreach, store

ID = "outreach_drill"
TITLE = "Hiring post to approved outreach in one guided flow"
BACKLOG = "B-080"
BEFORE = ("The drill was hand-run across six tools, and a visa deadline "
          "could never be mentioned, even when the person chose to "
          "(GitHub #36).")
POST = ("Jordan Avery\n1d •\nWe're hiring a Data Engineer at Northwind. "
        "Python, Airflow, SQL. Email jordan@northwind.example")


def run(user, measure):
    company.fetch_page = {}.get
    facts.add(user, "Built Airflow pipelines in Python for 30 analysts",
              confirmed=True, apply=True)
    before = sum(len(v) for v in store.export_all(user).values())
    flow = drill.run(user, POST, today=date(2026, 11, 14))
    measure("draft ready from a confirmed fact, passing checks",
            bool(flow["draft"]) and flow["draft"]["check"]["ok"], True)
    measure("review, yes, send and log left for the person",
            [s["status"] for s in flow["steps"][-4:]], ["todo"] * 4)
    after = sum(len(v) for v in store.export_all(user).values())
    measure("records stored by the flow", after - before, 0)
    mail = {"channel": "email", "to": "jordan@northwind.example",
            "subject": "Your Data Engineer post",
            "body": "Hi Jordan, my visa deadline is in March, and I built "
                    "Airflow pipelines in Python for 30 analysts. Open to "
                    "a chat? Sam"}
    measure("weakness mentioned without a choice gets approval",
            "approval_id" in outreach.review(user, **mail), False)
    chosen = outreach.review(user, share_anyway=["visa deadline"], **mail)
    ticket = chosen.get("approval_id", "")
    measure("mentioned by the person's choice gets approval", bool(ticket),
            True)
    measure("approved without restating the choice",
            outreach.approve(user, ticket, consent=True, **mail)["approved"],
            False)
    measure("approved with the same choice and a yes",
            outreach.approve(user, ticket, consent=True,
                             share_anyway=["visa deadline"],
                             **mail)["approved"], True)
