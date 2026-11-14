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
                                   "locations": ["London", "Remote"],
                                   "dealbreakers": ["needs visa "
                                                    "sponsorship"]})
    for line in ("Built Airflow pipelines in Python that cut report time "
                 "40%",
                 "Led a team of 4 data engineers on a Spark migration"):
        await call(s, "fact_add", {"statement": line, "confirmed": True,
                                   "apply": True})


POSTS = [
    "Jordan Avery • 2nd\nTalent Partner at Northwind Talent\n2d •\nWe're "
    "hiring a Senior Data Engineer to join our team in London (hybrid). "
    "Python, Airflow, Spark, SQL. £85k-£100k. DM me or email "
    "jordan@northwind.example\n"
    "https://www.linkedin.com/posts/jordan-avery_hiring-activity-1",
    "Priya Nair\nFounder, Lumen Labs\n3w •\nLumen Labs is hiring a Founding "
    "ML Engineer. Remote. $180k-$220k. Send me a DM.",
    "Chris Okafor\n1d •\nGreat conference this week, thanks everyone!",
    "Alex Morgan • 3rd+\n5h •\n#hiring Staff Platform Engineer at Contoso "
    "Cloud, remote. We cannot sponsor visas. Kubernetes, Go, Terraform.",
    "Sam Lee\nWe're looking for a Data Analyst at Fabrikam in Paris. SQL, "
    "Excel, Tableau.",
]


async def hiring_posts(s):
    result = await call(s, "hiring_posts_rank", {
        "posts": POSTS, "today": TODAY.isoformat()})
    top = result["top"]
    assert top[0]["company"] == "Northwind Talent", top
    first = top[0]
    assert first["role"] == "Senior Data Engineer" and first["pay"] == \
        "£85k–£100k" and first["contact"] == "jordan@northwind.example"
    assert first["url"].startswith("https://www.linkedin.com/posts/")
    assert "airflow" in first["fit_reason"].lower(), first
    why = {d["n"]: d["why"] for d in result["filtered_out"]}
    assert "older than 7" in why[2] and "dealbreaker" in why[4], why
    assert result["not_hiring_posts"] == [3], result
    paris = next(p for p in top if p["company"] == "Fabrikam")
    assert "outside your places" in paris["flags"] and \
        "date unknown: check it's recent" in paris["flags"], paris
    print("hiring posts: read, stale and dealbreaker posts dropped, the "
          "rest ranked with flags: OK")


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


async def drill(s):
    flow = await call(s, "outreach_from_post", {
        "post": POSTS[0], "domain": "northwind.example", "me": "Sam"})
    assert flow["post"]["company"] == "Northwind Talent"
    assert flow["fit"]["verdict"].startswith("apply"), flow["fit"]
    draft = flow["draft"]
    assert draft and draft["check"]["ok"], draft
    assert "Senior Data Engineer" in draft["body"] and "Hi Jordan" in \
        draft["body"] and draft["fact_used"].lower().rstrip(".") in         draft["body"].lower(), draft["body"]
    assert flow["to"] == "jordan@northwind.example"
    assert [st["step"] for st in flow["steps"]][-4:] == [
        "review", "their yes", "send", "log"]
    assert flow["next"]["step"] in ("company research", "message")
    print("outreach from a post: read, fit, research, draft, checklist: OK")

    base = {"channel": "linkedin_message", "to": "Jordan Avery",
            "subject": draft["subject"],
            "body": draft["body"].replace(
                "Would you be open", "My visa deadline is in mid-March, so I "
                "can start soon. Would you be open")}
    blocked = await call(s, "outreach_review", base)
    assert "approval_id" not in blocked, blocked
    assert "share_anyway" in json.dumps(blocked["check"]["issues"])
    bad = await call(s, "outreach_review", {**base,
                                            "share_anyway": ["salary"]})
    assert "error" in bad, bad
    chosen = await call(s, "outreach_review", {
        **base, "share_anyway": ["visa deadline"]})
    ticket = chosen["approval_id"]
    assert chosen["shared_by_choice"] == ["visa deadline"]
    assert "visa deadline" in chosen["ask"]
    without = await call(s, "outreach_approve", {
        **base, "approval_id": ticket, "consent": True})
    assert not without["approved"], "the choice is sealed in"
    ok = await call(s, "outreach_approve", {
        **base, "approval_id": ticket, "consent": True,
        "share_anyway": ["visa deadline"]})
    assert ok["approved"] and ok["shared_by_choice"]["mentions"] == [
        "visa deadline"] and "LinkedIn" in ok["send_with"], ok
    rude = await call(s, "outreach_review", {
        **base, "body": base["body"] + " Your other candidates are idiots.",
        "share_anyway": ["visa deadline"]})
    assert "approval_id" not in rude, "a choice never unlocks rudeness"
    logged = await call(s, "application_log", {
        "company": "Northwind Talent", "role": "Senior Data Engineer",
        "status": "applied", "next_action": "Follow up on the outreach"})
    assert logged.get("id"), logged
    print("visa deadline only by explicit choice, sealed to the exact "
          "text; rudeness still blocked; application logged: OK")


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
            await hiring_posts(s)
            await drill(s)
    with open(os.path.join(TEST_DIR, "logs", "mcp_server.log"),
              encoding="utf-8") as handle:
        log = handle.read()
    assert "report time" not in log and "20-minute call" not in log \
        and "Sam Example" not in log and "Jordan Avery" not in log \
        and "jordan@" not in log, \
        "one-pager lines leaked into the log"
    assert "visa deadline is" not in log, "outreach text leaked into log"
    print("drafts, offers, posts and names kept out of the log: OK")
    shutil.rmtree(TEST_DIR, ignore_errors=True)
    print("ALL PASSED")


if __name__ == "__main__":
    asyncio.run(main())
