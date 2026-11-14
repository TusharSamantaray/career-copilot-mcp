"""The hiring-post drill over stdio: company research, the one-pager,
ranking pasted hiring posts, and the guided outreach flow.

Made-up people and companies only. The web and job boards are canned
(CAREER_COPILOT_WEB_FIXTURE, CAREER_COPILOT_JOBS_FIXTURE), so nothing
leaves the machine.
"""
import asyncio
import json
import os
import shutil
import sys
from datetime import date

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

TEST_DIR = "./test_data_outreach_kit"
TODAY = date.today()
HOME = ("<html><head><title>Northwind Talent</title><meta "
        "property=\"og:description\" content=\"Northwind Talent places data "
        "and AI engineers with fast-growing companies.\"></head></html>")
WEB = {"https://northwind.example/": HOME}
BOARDS = {"https://boards-api.greenhouse.io/v1/boards/northwind/jobs": {
    "jobs": [{"id": 1, "title": "Data Engineer",
              "location": {"name": "London"},
              "first_published": f"{TODAY.isoformat()}T09:00:00Z",
              "absolute_url": "https://boards.greenhouse.io/northwind/1"},
             {"id": 2, "title": "Talent Partner",
              "location": {"name": "London"},
              "first_published": "2026-10-01T09:00:00Z",
              "absolute_url": "https://boards.greenhouse.io/northwind/2"}]}}


async def call(s, name, args=None):
    result = await s.call_tool(name, args or {})
    assert not result.isError, f"{name}: {result.content[0].text}"
    return json.loads(result.content[0].text)


async def setup(s):
    await call(s, "ground_rules", {"accept": True})
    await call(s, "profile_save", {"target_role": "Data Engineer",
                                   "comp_floor": "90k",
                                   "locations": ["London", "Remote"]})
    for line in ("Built Airflow pipelines in Python that cut report time "
                 "40%",
                 "Led a team of 4 data engineers on a Spark migration"):
        await call(s, "fact_add", {"statement": line, "confirmed": True,
                                   "apply": True})


async def research_and_one_pager(s):
    record = await call(s, "company_research", {
        "company": "Northwind", "domain": "https://northwind.example/x",
        "found": [{"kind": "service_line", "statement": "Places data "
                   "engineers on contract and permanent roles",
                   "source": "https://northwind.example/services"},
                  {"kind": "news", "statement": "Opened a Berlin office"}]})
    kinds = [f["kind"] for f in record["facts"]]
    assert "what_they_do" in kinds and "service_line" in kinds, kinds
    hiring = [f for f in record["facts"] if f["kind"] == "hiring_context"]
    assert hiring and "2 open roles" in hiring[0]["statement"], hiring
    assert hiring[0]["source"] == "https://boards.greenhouse.io/northwind"
    assert record["unverified"][0]["statement"] == "Opened a Berlin office"
    assert "news" in record["gaps"] and record["search_next"]
    print("company research: their words, their board, links required: OK")

    local = await call(s, "company_research", {
        "company": "Inside", "domain": "localhost"})
    assert not local["facts"] and local["domain"] is None, local
    print("company research won't fetch private addresses: OK")

    draft = await call(s, "one_pager_build", {"research": record,
                                              "role": "Data Engineer"})
    assert draft["mode"] == "draft" and draft["material"]["fit"]
    mine = next(k for k, v in draft["sources"].items()
                if "40%" in v["statement"])
    line = next(f["id"] for f in record["facts"]
                if f["kind"] == "service_line")
    lines = [{"section": "fit", "text": "I build Airflow pipelines in "
              "Python; mine cut report time 40%.", "sources": [mine]},
             {"section": "plugs_in", "text": "You place data engineers. I "
              "lead them, so I know what your clients need.",
              "sources": [line] + [k for k, v in draft["sources"].items()
                                  if "Led a team" in v["statement"]]}]
    bad = await call(s, "one_pager_build", {
        "research": record, "lines": lines + [{
            "section": "why_now", "text": "You grew 300% this year.",
            "sources": [line]}], "offer": "A 20-minute call"})
    assert not bad["ok"] and any("300" in p for p in bad["problems"]), bad
    rude = await call(s, "one_pager_build", {
        "research": record, "lines": [{
            "section": "fit", "text": "Your current recruiters are idiots.",
            "sources": [mine]}], "offer": "A call"})
    assert not rude["ok"], rude
    page = await call(s, "one_pager_build", {
        "research": record, "role": "Data Engineer", "lines": lines,
        "offer": "A 20-minute call next week", "me": "Sam Example"})
    assert page["ok"] and "<h1>Sam Example for Northwind</h1>" in \
        page["html"], page
    assert "https://northwind.example/services" in page["html"]
    assert "A 20-minute call next week" in page["html"]
    print("one-pager: invented numbers and insults refused, clean page "
          "built with sources: OK")


async def main():
    shutil.rmtree(TEST_DIR, ignore_errors=True)
    os.makedirs(TEST_DIR)
    web = os.path.join(TEST_DIR, "web.json")
    boards = os.path.join(TEST_DIR, "boards.json")
    with open(web, "w", encoding="utf-8") as handle:
        json.dump(WEB, handle)
    with open(boards, "w", encoding="utf-8") as handle:
        json.dump(BOARDS, handle)
    env = {**os.environ, "COPILOT_DATA_DIR": TEST_DIR,
           "CAREER_COPILOT_WEB_FIXTURE": web,
           "CAREER_COPILOT_JOBS_FIXTURE": boards,
           "CAREER_COPILOT_HOME": os.path.join(TEST_DIR, "home"),
           "CAREER_COPILOT_LOG_DIR": os.path.join(TEST_DIR, "logs")}
    for name in ("DATABASE_URL", "CAREER_COPILOT_MASTER_KEY"):
        env.pop(name, None)
    params = StdioServerParameters(
        command=sys.executable, args=["app.py", "--stdio"], env=env)
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as s:
            await s.initialize()
            await setup(s)
            await research_and_one_pager(s)
    with open(os.path.join(TEST_DIR, "logs", "mcp_server.log"),
              encoding="utf-8") as handle:
        log = handle.read()
    assert "report time" not in log and "20-minute call" not in log \
        and "Sam Example" not in log, \
        "one-pager lines leaked into the log"
    print("one-pager lines and offers kept out of the log: OK")
    shutil.rmtree(TEST_DIR, ignore_errors=True)
    print("ALL PASSED")


if __name__ == "__main__":
    asyncio.run(main())
