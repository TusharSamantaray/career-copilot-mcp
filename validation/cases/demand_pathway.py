"""Recruiters say what they need; a candidate's pathway cites it. Three
made-up recruiters and one made-up candidate."""
import json

from copilot import demand, facts, journey

ID = "demand_pathway"
TITLE = "Survey to demand digest to a pathway where every step has a reason"
BACKLOG = "B-061"
BEFORE = ("Pathways came from a static skills list, with no say from "
          "people hiring and no reason on each step.")

SURVEYS = [
    ("Northwind", "Data engineer: Spark, Airflow, dbt and SQL"),
    ("Contoso", "Data engineer roles want Spark, dbt and data quality"),
    ("", "Data engineer: Spark and Kafka"),
]


def run(user, measure):
    for i, (company, skills) in enumerate(SURVEYS):
        demand.survey(f"{user}-r{i}", {
            "seeing_roles": "mostly data engineer and analyst roles",
            "skills_by_role": skills,
            "expectations": "Explains trade-offs plainly"}, company=company)
    me = f"{user}-cand"
    journey.save_profile(me, {"target_role": "Data Engineer"})
    facts.add(me, "Built Airflow DAGs in Python and SQL for 20 reports",
              employer="Fabrikam", ownership="owned", confirmed=True,
              apply=True)
    digest = demand.digest("data engineer")
    spark = next(s for s in digest["signals"] if s["skill"] == "spark")
    measure("Spark counted once per recruiter", spark["said_by"], 3)
    measure("who said it: named companies, the rest counted",
            spark["who"], ["Contoso", "Northwind", "1 unnamed"])
    measure("every signal names its source and version",
            all(s["source"] == "survey v1" for s in digest["signals"]), True)
    measure("candidate's data in the digest",
            "fabrikam" in json.dumps(digest).lower(), False)
    path = demand.build(me, "data engineer")
    measure("every step cites direction and demand",
            all("Data Engineer" in s["reason"] and "named" in s["reason"]
                for s in path["steps"]), True)
    measure("no long lists: at most 5 steps", len(path["steps"]) <= 5, True)
    measure("first step uses what they already prove",
            "airflow" in path["steps"][0]["step"], True)
    measure("skills nobody asked for appear in steps",
            any("pytorch" in s["step"] for s in path["steps"]), False)
    now = demand.build(me, mode="immediate")
    proven = {"airflow", "python", "sql"}
    measure("immediate mode needs no new learning",
            all(set(o["you_prove"]) <= proven for o in now["options"]), True)
    first = demand.next_step(me)
    measure("one step at a time", set(first) >= {"next", "left"} and
            isinstance(first["next"], dict), True)
