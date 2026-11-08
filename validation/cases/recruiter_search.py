"""A recruiter finds the right personas for a job, and learns nothing
that identifies anyone. Six made-up candidates, one made-up posting."""
import json

from copilot import facts, journey, persona, recruiter

ID = "recruiter_search"
TITLE = "Job posting to top 5 personas, ranked by verified evidence"
BACKLOG = "B-053"
BEFORE = ("No way for someone hiring to find a person's verified work "
          "without a resume carrying their name, contacts and employers.")

POSTING = ("Senior Data Engineer. You will own our Spark and Airflow ETL, "
           "model data in dbt and keep data quality high. Python and SQL "
           "required. Remote in the EU. Salary EUR 90k-110k.")
# (handle, employer, ownership, facts, still published)
PEOPLE = [
    ("ana", "Quillon Labs", "owned", [
        "Built Spark and Airflow ETL for 40 sources in Python",
        "Owned dbt data modeling and SQL tests for data quality"], True),
    ("ben", "Brightwell", "contributed", [
        "Helped migrate Airflow ETL jobs written in Python and SQL"], True),
    ("cleo", "Hexatone", "owned", [
        "Built React and TypeScript dashboards"], True),
    ("dev", "Moraine", "led", [
        "Led a Spark ETL rebuild in Python and SQL for 12 teams",
        "Led dbt rollout and data quality checks"], True),
    ("eli", "Tarnwood", "owned", [
        "Owned Airflow and Spark ETL in Python, SQL and dbt"], False),
    ("fay", "Orrin", "contributed", [
        "Wrote SQL reports in Python for finance"], True),
]


def _person(base, handle, employer, part, lines, publish):
    user = f"{base}-{handle}"
    journey.save_profile(user, {"target_role": "Data Engineer",
                                "locations": ["Remote"]})
    for line in lines:
        facts.add(user, line + f" at {employer}", employer=employer,
                  ownership=part, confirmed=True, apply=True)
    preview = persona.publish(user)
    persona.publish(user, accept=True, preview_id=preview["preview_id"])
    if not publish:
        persona.unpublish(user)          # published once, then taken down
    return user


def run(user, measure):
    for row in PEOPLE:
        _person(user, *row)
    result = recruiter.search(f"{user}-recruiter", POSTING,
                              title="Senior Data Engineer",
                              must_have=["spark"])
    order = [m["persona_id"] for m in result["matches"]]
    ids = {h: persona.current(f"{user}-{h}")["persona_id"]
           for h, *_ in PEOPLE}
    measure("ranked by verified evidence: owner and lead first",
            order[:2] == [ids["ana"], ids["dev"]] or
            order[:2] == [ids["dev"], ids["ana"]], True)
    measure("must-have 'spark' filters out personas that don't prove it",
            sorted(h for h, pid in ids.items() if pid in order),
            ["ana", "dev"])
    loose = recruiter.search(f"{user}-recruiter", POSTING)
    measure("never more than 5 matches", len(loose["matches"]) <= 5, True)
    measure("unpublished persona never found",
            ids["eli"] in [m["persona_id"] for m in loose["matches"]], False)
    text = json.dumps({k: v for k, v in loose.items() if k != "say"}).lower()
    measure("employer names in results",
            [e for _, e, *_ in PEOPLE if e.lower() in text], [])
    measure("salary in results", any(w in text for w in
                                      ("90k", "110k", "salary", "eur")),
            False)
    pid = ids["ana"]
    measure("identity question refused",
            recruiter.chat(f"{user}-recruiter", pid,
                           "What is her name and LinkedIn?").get("refused"),
            "identity")
    measure("salary question refused",
            recruiter.chat(f"{user}-recruiter", pid,
                           "What pay would she want?").get("refused"),
            "salary")
    answer = recruiter.chat(f"{user}-recruiter", pid,
                            "Has she worked with dbt?")
    measure("skill question answered from verified evidence only",
            [a["part"] for a in answer["answer_from"]], ["owned"])
