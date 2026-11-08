"""Simulation: 5 made-up job seekers and 2 made-up recruiters, end to end.

    uv run simulation/run.py           # run it, write simulation/REPORT.md
    uv run simulation/run.py --check   # run it only (CI); exit 1 on a failure
    uv run simulation/run.py --serve   # run it, then keep the server up so
                                       # you can chat as any of them

It starts a real Career Copilot server on this computer, with one API key
per person, so every call goes through the same MCP connection and tools
Claude would use, and everyone's data stays separate. Everything is
invented and stays in a throwaway folder (simulation/.data with --serve).
Then it checks the rules held: no recruiter ever saw a name, employer,
contact or salary before both sides agreed, the private person never
appeared, rankings follow verified work, and every pathway step has a
reason.
"""
import asyncio
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import date

import httpx
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PORT = int(os.environ.get("SIM_PORT", "8790"))
BASE = f"http://127.0.0.1:{PORT}"
SERVE = "--serve" in sys.argv
CHECK = "--check" in sys.argv

# ---------------------------------------------------------------- people
# Five job seekers, each coming in a different way. Names are only for
# this report; Career Copilot never stores a name. Planted details (an
# employer, an email, a phone number) must never reach a recruiter.
SEEKERS = [
    {"key": "sim-maya", "name": "Maya", "says": "Here's my work: I run "
     "the data platform at a logistics firm.",
     "profile": {"situation": "working, want a change",
                 "target_role": "Data Engineer", "level": "senior",
                 "years_experience": 7, "locations": ["Remote", "Lisbon"]},
     "facts": [
         ("Quarry Freight", "owned", "Built Spark and Airflow ETL for 60 "
          "sources in Python, cutting load time from 5 hours to 35 "
          "minutes"),
         ("Quarry Freight", "owned", "Owned dbt data modeling and SQL "
          "tests that caught 90% of bad loads; reach me at "
          "maya.k@quarry.example"),
         ("Quarry Freight", "led", "Led data quality reviews for 4 "
          "analytics teams")],
     "publish": True},
    {"key": "sim-jon", "name": "Jon", "says": "I just want a backend role "
     "with good on-call.",
     "profile": {"situation": "between jobs", "target_role":
                 "Backend Engineer", "level": "senior",
                 "years_experience": 9, "locations": ["Remote"]},
     "facts": [
         ("Tidepool Pay", "led", "Led the move of payments to Kafka and "
          "Go, handling 3 million events a day"),
         ("Tidepool Pay", "owned", "Owned Postgres tuning that cut p95 "
          "latency from 800 to 120 ms; call 415 555 0142"),
         ("Tidepool Pay", "contributed", "Contributed to incident "
          "response runbooks")],
     "publish": True},
    {"key": "sim-priya", "name": "Priya", "says": "Frontend person, "
     "React mostly.",
     "profile": {"situation": "working, want a change", "target_role":
                 "Frontend Engineer", "level": "mid",
                 "years_experience": 4, "locations": ["Berlin"]},
     "facts": [
         ("Lark Studio", "owned", "Owned the React and TypeScript design "
          "system used by 6 product teams"),
         ("Lark Studio", "contributed", "Improved accessibility to WCAG "
          "AA on checkout")],
     "publish": True, "hide": "accessibility"},
    {"key": "sim-alex", "name": "Alex", "says": "I'm an analyst and I "
     "want to move into data engineering.",
     "profile": {"situation": "working, want a change", "target_role":
                 "Data Engineer", "current_role": "Data Analyst",
                 "level": "mid", "years_experience": 3,
                 "locations": ["Remote"]},
     "facts": [
         ("Brightline Health", "owned", "Built SQL and Python reports "
          "for 12 clinics"),
         ("Brightline Health", "contributed", "Helped move 30 reports "
          "into dbt models")],
     "publish": True},
    {"key": "sim-sam", "name": "Sam", "says": "ML engineer. I'm not ready "
     "to be found yet.",
     "profile": {"situation": "interviewing", "target_role":
                 "ML Engineer", "level": "senior", "years_experience": 6},
     "facts": [
         ("Ostrava AI", "owned", "Owned PyTorch model deployment for "
          "fraud scoring, with Spark features")],
     "publish": False},
]

RECRUITERS = [
    {"key": "sim-northwind", "name": "Northwind Logistics recruiter",
     "company": "Northwind Logistics", "role": "Senior Data Engineer",
     "posting": "Senior Data Engineer, Northwind Logistics. Own our Spark "
                "and Airflow ETL, model data in dbt, and keep data "
                "quality high. Python and SQL required. 5+ years. Remote "
                "in the EU. Salary EUR 85k-105k.",
     "must_have": ["spark"], "location": "Lisbon",
     "survey": {"seeing_roles": "Lots of data engineer and analytics "
                                "engineering roles",
                "skills_by_role": "Data engineer: Spark, Airflow, dbt, "
                                  "data quality and SQL",
                "expectations": "Explains trade-offs plainly and owns "
                                "pipelines end to end"},
     "ask": ["What have they built with Airflow?",
             "What's their name and LinkedIn?",
             "What salary are they expecting?"],
     "message": "Your Spark and Airflow ETL work is close to what we run. "
                "Open to a short chat about our Senior Data Engineer role?"},
    {"key": "sim-contoso", "name": "Contoso Pay recruiter",
     "company": "Contoso Pay", "role": "Backend Engineer",
     "posting": "Backend Engineer, payments. Kafka, Go and Postgres, "
                "on-call with incident response. Remote.",
     "must_have": ["kafka"], "location": "",
     "survey": {"seeing_roles": "Backend roles, mostly payments",
                "skills_by_role": "Backend engineer: Kafka, Go, Postgres "
                                  "and observability",
                "expectations": "Calm under incidents"},
     "ask": ["How much Kafka have they run?",
             "Which company do they work for now?"],
     "message": "We're building payments on Kafka and Go. Would you like "
                "to talk about our backend role?"},
]


# ------------------------------------------------------------- the run

class Run:
    def __init__(self):
        self.lines = []
        self.seen_by_recruiters = []      # every answer a recruiter got
        self.checks = []

    def say(self, who, text):
        self.lines.append(f"- **{who}:** {text}")
        print(f"{who}: {text}")

    def heading(self, text):
        self.lines += ["", f"## {text}", ""]
        print(f"\n== {text}")

    def check(self, what, ok, detail=""):
        self.checks.append((what, bool(ok), detail))


def client(key):
    return Client(StreamableHttpTransport(
        f"{BASE}/mcp", headers={"Authorization": f"Bearer {key}"}))


async def call(c, tool, args=None):
    result = await c.call_tool(tool, args or {})
    return result.data if result.data is not None else json.loads(
        result.content[0].text)


async def seekers(run):
    run.heading("1. Five people build a profile and decide about a persona")
    ids = {}
    for p in SEEKERS:
        async with client(p["key"]) as c:
            await call(c, "ground_rules", {"accept": True})
            run.say(p["name"], f'"{p["says"]}"')
            await call(c, "profile_save", p["profile"])
            for employer, part, fact in p["facts"]:
                await call(c, "experience_add", {
                    "employer": employer, "title": p["profile"]["target_role"],
                    "start": "2021", "end": "2025", "fact": fact,
                    "confirmed": True, "owned_or_contributed": part})
            state = await call(c, "journey_state")
            preview = await call(c, "persona_publish")
            view = preview["preview"]
            skills = ", ".join(s["skill"] for s in view["skills"])
            run.say("Career Copilot", f"saved {len(p['facts'])} confirmed "
                    f"facts (stage: {state.get('stage')}). Persona preview: "
                    f"\"{view['headline']}\", {view['experience']}, "
                    f"skills proven: {skills}.")
            for line in view["evidence"]:
                run.say("  preview line", line["text"])
            hide = []
            if p.get("hide"):
                hide = [e["id"] for e in view["evidence"]
                        if p["hide"] in e["text"].lower()]
                preview = await call(c, "persona_publish", {"hide": hide})
                run.say(p["name"], f'"Leave out the {p["hide"]} line."')
            if p["publish"]:
                done = await call(c, "persona_publish", {
                    "accept": True, "preview_id": preview["preview_id"],
                    "hide": hide})
                ids[p["name"]] = done["persona_id"]
                run.say(p["name"], '"Yes, publish it."')
                run.say("Career Copilot", f"published as "
                        f"{done['persona_id']} (anonymous).")
            else:
                run.say(p["name"], '"Not yet. Keep it private."')
                run.say("Career Copilot", "nothing published; nobody "
                        "searching can see Sam.")
    return ids


async def recruiters(run, ids):
    run.heading("2. Two recruiters bring a job and look for people")
    intros = {}
    for r in RECRUITERS:
        async with client(r["key"]) as c:
            await call(c, "ground_rules", {"accept": True})
            await call(c, "recruiter_survey", {"answers": r["survey"],
                                               "company": r["company"]})
            run.say(r["name"], f'answers the hiring survey, then: "I\'m '
                    f'hiring a {r["role"]}." (pastes the posting; must '
                    f'have: {", ".join(r["must_have"])})')
            found = await call(c, "persona_search", {
                "posting_text": r["posting"], "title": r["role"],
                "must_have": r["must_have"], "location": r["location"]})
            run.seen_by_recruiters.append(found)
            if not found["matches"]:
                run.say("Career Copilot", "no matches.")
                continue
            for m in found["matches"]:
                who = next((n for n, pid in ids.items()
                            if pid == m["persona_id"]), "?")
                run.say("Career Copilot", f"{m['persona_id']} "
                        f"\"{m['headline']}\": {m['why']}. Proof: "
                        f"\"{m['proof'][0]}\"  _(behind it: {who})_")
            out = found["filtered_out"]
            run.say("Career Copilot", f"searched {found['searched']} "
                    f"published personas; left out "
                    f"{out['missing_a_must_have']} without the must-have "
                    f"and {out['location']} outside the location.")
            r["matches"] = [m["persona_id"] for m in found["matches"]]
            top = found["matches"][0]["persona_id"]
            for q in r["ask"]:
                answer = await call(c, "persona_chat", {"persona_id": top,
                                                        "question": q})
                run.seen_by_recruiters.append(answer)
                run.say(r["name"], f'"{q}"')
                if answer.get("refused"):
                    run.say("Career Copilot", f"refused ({answer['refused']}"
                            "): the persona can't share that.")
                else:
                    lines = "; ".join(a["text"] for a in
                                      answer["answer_from"]) or "none"
                    run.say("Career Copilot", f"from verified work only: "
                            f"{lines}")
            sent = await call(c, "persona_intro", {
                "persona_id": top, "company": r["company"],
                "role": r["role"], "message": r["message"]})
            intros[r["name"]] = (sent["intro_id"], top)
            run.say(r["name"], f'"Ask to meet {top}." Sent; no names on '
                    "either side yet.")
            early = await call(c, "identity_reveal", {
                "intro_id": sent["intro_id"], "confirm": True,
                "share": f"Recruiter at {r['company']}, "
                         f"hiring@{r['company'].split()[0].lower()}.example"})
            run.seen_by_recruiters.append(early)
            run.say("Career Copilot", f"{r['name']} confirmed; revealed: "
                    f"{early['revealed']} (waiting for the persona).")
    return intros


async def answers(run, ids, intros):
    run.heading("3. The people decide: one says yes, one says no")
    owner_of = {pid: p for p in SEEKERS for n, pid in ids.items()
                if n == p["name"]}
    decisions = {"Northwind Logistics recruiter": True,
                 "Contoso Pay recruiter": False}
    for rname, (intro_id, pid) in intros.items():
        person = owner_of[pid]
        async with client(person["key"]) as c:
            box = await call(c, "persona_intros")
            req = next(x for x in box["received"]
                       if x["intro_id"] == intro_id)
            run.say(person["name"], f'"Any introduction requests?" '
                    f'Career Copilot: {req["company"]}, {req["role"]}, '
                    f'after {req["screened_questions"]} screening '
                    f'question(s): "{req["message"]}"')
            yes = decisions[rname]
            share = f"{person['name']} (made up), " \
                    f"{person['name'].lower()}@example.org"
            done = await call(c, "identity_reveal", {
                "intro_id": intro_id, "confirm": yes,
                "share": share if yes else ""})
            if yes:
                run.say(person["name"], f'"Yes, share my name and email."')
                run.say("Career Copilot", f"both confirmed; "
                        f"{person['name']} sees: \"{done['they_shared']}\"")
            else:
                run.say(person["name"], '"No thanks."')
                run.say("Career Copilot", "declined; nothing about either "
                        "side was shared.")
        recruiter = next(r for r in RECRUITERS if r["name"] == rname)
        async with client(recruiter["key"]) as c:
            final = await call(c, "identity_reveal", {
                "intro_id": intro_id, "confirm": True,
                "share": "Recruiter"})
            run.seen_by_recruiters.append({"after_both": yes, **final})
            run.say(rname, f"checks the intro: status {final['status']}"
                    + (f", sees \"{final['they_shared']}\"" if yes else
                       ", nothing shared."))
            recruiter["revealed"] = final.get("they_shared", "")


async def pathway(run):
    run.heading("4. Alex, switching careers, gets a pathway from that "
                "demand")
    async with client("sim-alex") as c:
        digest = await call(c, "demand_digest", {"direction":
                                                 "data engineer"})
        top = ", ".join(f"{s['skill']} ({s['said_by']}, {s['source']})"
                        for s in digest["signals"][:5])
        run.say("Alex", '"What are recruiters asking for in data '
                'engineering?"')
        run.say("Career Copilot", f"from people hiring here: {top}.")
        path = await call(c, "pathway_build", {"direction":
                                               "data engineer"})
        run.say("Alex", '"Build my pathway to data engineer."')
        for i, step in enumerate(path["steps"], 1):
            run.say(f"  step {i}", f"{step['step']} _Why: "
                    f"{step['reason']}_")
        first = await call(c, "pathway_next")
        run.say("Career Copilot", f"today, just this: "
                f"{first['next']['step']}")
        run.check("every pathway step cites direction and demand",
                  path["steps"] and all("named" in s["reason"]
                                        for s in path["steps"]))
        return digest


def verify(run, ids):
    seen = json.dumps(run.seen_by_recruiters[:-2]).lower()  # before reveals
    planted = ["quarry", "tidepool", "lark studio", "brightline",
               "ostrava", "maya.k@", "555 0142", "maya", "jon", "priya",
               "alex", "@example.org"]
    run.check("no name, employer or contact reached a recruiter before "
              "both agreed", not [p for p in planted if p in seen],
              [p for p in planted if p in seen])
    money = [w for w in ("85k", "105k", "eur", "salary expect")
             if w in json.dumps([{k: v for k, v in x.items() if k != "say"}
                                 for x in run.seen_by_recruiters]).lower()]
    run.check("no salary shown to anyone", not money, money)
    sam = [r for r in RECRUITERS if any(
        pid not in ids.values() for pid in r.get("matches", []))]
    run.check("the private person (Sam) never appeared", not sam)
    north, contoso = RECRUITERS
    run.check("Northwind's top match is the person who owns that work "
              "(Maya)", north["matches"][:1] == [ids["Maya"]])
    run.check("Contoso's must-have (Kafka) left only Jon",
              contoso["matches"] == [ids["Jon"]])
    run.check("identity and salary questions were refused",
              sum(1 for x in run.seen_by_recruiters
                  if x.get("refused")) == 3)
    run.check("Northwind saw Maya's chosen contact only after both said "
              "yes", north["revealed"].startswith("Maya"))
    run.check("Contoso saw nothing after Jon said no",
              contoso["revealed"] == "")


def report(run):
    passed = sum(ok for _, ok, _ in run.checks)
    out = ["# Simulation report", "",
           f"Run {date.today()}: 5 made-up job seekers and 2 made-up "
           "recruiters on a real local Career Copilot server, one sign-in "
           "each. Regenerated by `uv run simulation/run.py`; see "
           "[README.md](README.md). The names in italics are only for "
           "this report: Career Copilot never stores them, and recruiters "
           "never saw them.", "", f"**Checks: {passed}/{len(run.checks)} "
           "passed**", "", "| Check | |", "|---|---|"]
    out += [f"| {what} | {'pass' if ok else 'FAIL ' + str(detail)} |"
            for what, ok, detail in run.checks]
    return "\n".join(out + run.lines) + "\n"


async def main_async(run):
    ids = await seekers(run)
    intros = await recruiters(run, ids)
    await answers(run, ids, intros)
    await pathway(run)
    verify(run, ids)


def start_server(data_dir):
    keys = [p["key"] for p in SEEKERS] + [r["key"] for r in RECRUITERS]
    env = {**os.environ, "PORT": str(PORT), "HOST": "127.0.0.1",
           "CAREER_COPILOT_API_KEY": ",".join(keys),
           "COPILOT_DATA_DIR": data_dir,
           "CAREER_COPILOT_LOG_DIR": os.path.join(data_dir, "logs"),
           "CAREER_COPILOT_INSIGHTS": "0"}
    for name in ("DATABASE_URL", "CAREER_COPILOT_GITHUB_CLIENT_ID",
                 "CAREER_COPILOT_MASTER_KEY"):
        env.pop(name, None)
    console = open(os.path.join(data_dir, "console.txt"), "w",
                   encoding="utf-8")
    server = subprocess.Popen([sys.executable, os.path.join(ROOT, "app.py")],
                              env=env, cwd=ROOT, stdout=console,
                              stderr=subprocess.STDOUT)
    for _ in range(80):
        try:
            if httpx.get(f"{BASE}/health").status_code == 200:
                return server
        except httpx.TransportError:
            time.sleep(0.25)
    server.terminate()
    raise RuntimeError(f"server did not start; see {data_dir}/console.txt")


def main():
    if SERVE:
        data_dir = os.path.join(HERE, ".data")
        shutil.rmtree(data_dir, ignore_errors=True)
        os.makedirs(data_dir)
    else:
        data_dir = tempfile.mkdtemp(prefix="cc-simulation-")
    server = start_server(data_dir)
    run = Run()
    try:
        asyncio.run(main_async(run))
    finally:
        if not SERVE:
            server.terminate()
            server.wait(timeout=10)
            shutil.rmtree(data_dir, ignore_errors=True)
    failed = [c for c in run.checks if not c[1]]
    print("\nChecks:")
    for what, ok, detail in run.checks:
        print(f"  {'pass' if ok else 'FAIL'}  {what}"
              + (f"  ({detail})" if not ok and detail else ""))
    if not CHECK:
        with open(os.path.join(HERE, "REPORT.md"), "w",
                  encoding="utf-8") as f:
            f.write(report(run))
        print("report: simulation/REPORT.md")
    print("ALL PASSED" if not failed else f"{len(failed)} FAILED")
    if SERVE:
        print(f"\nServer still running at {BASE}/mcp with everyone's data. "
              "Chat as anyone from Claude Code, for example:")
        for key, who in [("sim-northwind", "the Northwind recruiter"),
                         ("sim-alex", "Alex")]:
            print(f"  claude mcp add --transport http cc-{key[4:]} "
                  f"{BASE}/mcp --header \"Authorization: Bearer {key}\""
                  f"    # {who}")
        print("Keys: " + ", ".join(p["key"] for p in SEEKERS + RECRUITERS))
        print("Press Ctrl+C to stop.")
        try:
            server.wait()
        except KeyboardInterrupt:
            server.terminate()
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
