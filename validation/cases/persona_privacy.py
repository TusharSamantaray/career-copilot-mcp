"""A persona shows verified work only, and only after a yes to the exact
view. Made-up person; the PII planted here must never come out."""
import json

from copilot import facts, journey, persona

ID = "persona_privacy"
TITLE = "Anonymous persona: verified skills only, published on a yes"
BACKLOG = "B-052"
BEFORE = ("No persona: showing your work to recruiters meant sending a "
          "resume with your name, contacts and employers on it.")

PLANTED = ["Lumen Robotics", "dana.k@lumen.example", "415 555 0199",
           "linkedin.com/in/danak", "Catholic"]


def run(user, measure):
    journey.save_profile(user, {"target_role": "Data Engineer",
                                "level": "senior", "years_experience": 7,
                                "locations": ["Remote"]})
    add = lambda text, ok=True: facts.add(  # noqa: E731
        user, text, employer="Lumen Robotics", ownership="owned",
        confirmed=ok, apply=True)
    add("Built Airflow and Spark ETL at Lumen Robotics that cut load time "
        "from 6 hours to 40 minutes")
    add("Owned dbt data modeling for 30 analysts; contact "
        "dana.k@lumen.example, 415 555 0199, linkedin.com/in/danak")
    add("Led the Catholic charity data drive")
    add("Knows Snowflake", ok=False)
    first = persona.publish(user)
    shown = json.dumps(first["preview"])
    measure("planted name, contact, link or trait in the preview",
            [p for p in PLANTED if p.lower() in shown.lower()], [])
    skills = [s["skill"] for s in first["preview"]["skills"]]
    measure("skill with no confirmed fact behind it shown",
            "snowflake" in skills, False)
    measure("verified skills shown",
            all(s in skills for s in ("airflow", "spark", "etl", "dbt")),
            True)
    measure("experience shown as a range, not exact years",
            first["preview"]["experience"], "6-9 years")
    measure("published without a yes", first["published"], False)
    measure("published with a stale preview",
            persona.publish(user, accept=True,
                            preview_id="0" * 16)["published"], False)
    done = persona.publish(user, accept=True,
                           preview_id=first["preview_id"])
    found = [pid for _, rec in persona.published()
             for pid in [rec["persona_id"]]]
    measure("searchable after the yes", done["persona_id"] in found, True)
    persona.unpublish(user)
    found = [rec["persona_id"] for _, rec in persona.published()]
    measure("gone from search after unpublish",
            done["persona_id"] in found, False)
