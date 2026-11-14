"""Pasted hiring posts are read, filtered and ranked, never automated."""
from datetime import date

from copilot import hiring_posts, journey, store

ID = "hiring_posts"
TITLE = "Rank pasted hiring posts by fit, with the freshness rule"
BACKLOG = "B-079"
BEFORE = ("Finding hiring posts meant scrolling LinkedIn by hand and "
          "judging each one alone (GitHub #33).")
TODAY = date(2026, 11, 14)
POSTS = [
    "Jordan Avery\n1d •\nWe're hiring a Data Engineer at Northwind in "
    "London. Python, Airflow, SQL. DM me.",
    "Priya Nair\n2w •\nLumen Labs is hiring a Data Engineer. Remote.",
    "Alex Morgan\n3h •\n#hiring Platform Engineer at Contoso, remote. We "
    "cannot sponsor visas.",
    "Chris Okafor\n2d •\nLovely team offsite this week.",
]


def run(user, measure):
    journey.save_profile(user, {"target_role": "Data Engineer",
                                "dealbreakers": ["needs sponsorship"]})
    before = sum(len(v) for v in store.export_all(user).values())
    result = hiring_posts.rank(user, POSTS, today=TODAY)
    measure("posts ranked", [p["n"] for p in result["top"]], [1])
    measure("fields read from the top post",
            {k: result["top"][0][k] for k in ("poster", "role", "company",
                                               "contact", "posted")},
            {"poster": "Jordan Avery", "role": "Data Engineer",
             "company": "Northwind", "contact": "DM the poster",
             "posted": "2026-11-13"})
    reasons = sorted(d["why"].split(":")[0].split(" (")[0]
                     for d in result["filtered_out"])
    measure("filtered out, with the reason", reasons,
            ["breaks your dealbreaker", "posted 14 days ago"])
    measure("not a hiring post, set aside", result["not_hiring_posts"], [4])
    after = sum(len(v) for v in store.export_all(user).values())
    measure("records stored from the posts", after - before, 0)
