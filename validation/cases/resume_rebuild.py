"""A resume rebuild, replayed with a made-up engineer.

Modelled on a real rebuild the owner proved by hand (four versions over
a month: invented bullets and level tags removed, internal team names
replaced, the summary led by numbers, then a branch that brought old
problems back, then a clean final). Every name and number here is
invented; no real resume text is used.
"""
from copilot import facts, timeline

ID = "resume_rebuild"
TITLE = "Resume timeline proves a rebuild from saved text"
BACKLOG = "B-051"
BEFORE = ("No history: proving an improvement meant diffing files by hand, "
          "and a version that brought old problems back went unnoticed.")

CONFIRMED = [
    "Built an alerting service that paged 4,000 on-call staff in under "
    "2 minutes",
    "Cut nightly batch time from 90 minutes to 12",
    "Recovered 8,000 lost orders after a failed migration",
]
ROLES = """Experience
Software Engineer II, Northwind (Platform Alerts {tag2}), 2024 - Present
{b1}
- Cut nightly batch time from 90 minutes to 12
- Recovered 8,000 lost orders after a failed migration{invented2}
Software Engineer, Northwind ({team}), 2022 - 2024
- Built the deploy checklist the team still uses
Research Assistant, Lakeside University, 2021 - 2022
- Built a data pipeline for county energy filings
Teaching Assistant, Lakeside University, 2021 - 2021
- Ran weekly database labs
Engineer, Contoso Services, 2017 - 2020
- Built REST APIs for the parts ordering site{invented1}
Education
M.S. Data Science, Lakeside University, 2020 - 2022
B.Tech. Computer Science, Riverbend College, 2013 - 2017
"""
NARRATIVE = ("Summary\nBackend engineer who enjoys building distributed "
             "systems and working with great teams on hard problems.\n")
NUMBERS = ("Summary\nBackend engineer: paged 4,000 on-call staff in under "
           "2 minutes, cut batch time from 90 minutes to 12, and recovered "
           "8,000 lost orders.\n")
B1 = ("- Built an alerting service that paged 4,000 on-call staff in under "
      "2 minutes")


def _resume(summary, tag="", team="Official Platform Team",
            invented=False, wordy=False):
    body = ROLES.format(
        tag2=tag, team=team, b1=B1,
        invented1="\n- Launched in 12 countries with 50+ changes"
                  if invented else "",
        invented2="\n- Grew platform adoption by 300%" if invented else "")
    if wordy:
        body = body.replace("- Built the deploy checklist the team still "
                            "uses", "- Built the deploy checklist the "
                            "team still uses today for every single "
                            "release, written up carefully and shared "
                            "widely across the whole wider organisation")
    return "Sam Rivera\nBackend Engineer\n" + summary + body


def run(user, measure):
    for statement in CONFIRMED:
        facts.add(user, statement, employer="Northwind", confirmed=True,
                  apply=True)
    snap = timeline.snapshot
    snap(user, _resume(NARRATIVE, tag="L5", team="Blue Hub L4",
                       invented=True, wordy=True), "Before",
         avoid_terms=["Blue Hub"])
    second = snap(user, _resume(NUMBERS), "Accuracy rebuild")
    branch = snap(user, _resume(NUMBERS, tag="L5", invented=True),
                  "Branch", parent=second["id"])
    snap(user, _resume(NUMBERS), "Final", parent=second["id"])
    change = timeline.diff(user, "Before", "Final")
    checks = change["checks"]
    measure("invented bullets, before", checks["unsupported_numbers"]
            ["before"], 2)
    measure("invented bullets, after", checks["unsupported_numbers"]
            ["after"], 0)
    measure("level tags, before -> after",
            (checks["level_tags"]["before"], checks["level_tags"]["after"]),
            (2, 0))
    measure("internal names, before -> after",
            (checks["internal_names"]["before"],
             checks["internal_names"]["after"]), (1, 0))
    measure("summary leads with numbers, after",
            "no numbers up front" not in checks["summary_issues"]["now"],
            True)
    measure("roles counted (education excluded), before -> after",
            (change["roles"]["before"], change["roles"]["after"]), (5, 5))
    measure("tighter after (word change below 0%)",
            change["word_change_pct"] < 0, True)
    measure("branch that brought problems back is flagged",
            sorted(r["check"] for r in branch.get("regressions", [])),
            ["level_tags", "unsupported_numbers"])
    rows = timeline.timeline(user)["versions"]
    measure("nothing overwritten (4 versions kept)", len(rows), 4)
    proof = timeline.proof(user, "Before", "Final")
    measure("proof ends with the final resume",
            proof["markdown"].rstrip().endswith(
                "B.Tech. Computer Science, Riverbend College, 2013 - 2017"),
            True)
