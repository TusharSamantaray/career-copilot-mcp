"""Coach, relocation, inbox autopilot, calendar and interview tools, over
stdio with synthetic data only."""
import asyncio
import json
import os
import shutil
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

TEST_DIR = "./test_data_soul"
TODAY = "2026-11-02"   # a Monday
EMAILS = [
    {"from": "Acme Careers <no-reply@greenhouse.io>",
     "subject": "Thank you for applying to Acme",
     "date": "2026-10-20", "snippet": "We received your application for "
     "the Senior Data Analyst role."},
    {"from": "Jordan <jordan@acme.com>", "subject": "Acme - next round",
     "date": "2026-10-27", "snippet": "We'd like to schedule an interview."
     " Please share your availability."},
    {"from": "Globex Talent <talent@globex.com>",
     "subject": "Your application to Globex",
     "date": "2026-10-28", "snippet": "Unfortunately we will not be moving "
     "forward with your application."},
    {"from": "HackerRank <support@hackerrank.com>",
     "subject": "Initech coding assessment invitation",
     "date": "2026-10-31", "snippet": "Complete the coding assessment for "
     "Initech. The link expires in 5 days."},
    {"from": "newsletter@shop.example", "subject": "50% off shoes",
     "date": "2026-10-31", "snippet": "Big sale this weekend."},
]


async def call(s, name, args=None):
    result = await s.call_tool(name, args or {})
    assert not result.isError, f"{name}: {result.content[0].text}"
    text = result.content[0].text if result.content else "null"
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


async def coach_checks(s):
    crisis = await call(s, "daily_step", {"energy": "low",
                                          "mood": "I can't go on like this",
                                          "today": TODAY})
    assert crisis.get("crisis") and "988" in str(crisis["resources"])
    print("crisis mood gets support, not a task: OK")

    step = await call(s, "daily_step", {"energy": "low", "today": TODAY})
    assert step["one_step"]["step"] and step["streak_days"] == 0
    for day in ("2026-10-30", "2026-10-31"):        # Fri, Sat; Sun rested
        await call(s, "step_done", {"note": "applied", "today": day})
    done = await call(s, "step_done", {"today": TODAY})
    assert done["streak_days"] == 3, done           # one rest day is fine
    again = await call(s, "daily_step", {"today": TODAY})
    assert again["already_done"]
    gap = await call(s, "daily_step", {"today": "2026-11-05"})
    assert gap["streak_days"] == 0, gap             # two rest days reset it
    print("daily step, step_done, never-skip-twice streak: OK")
    assert len((await call(s, "life_compass"))["questions"]) >= 5


async def places_checks(s):
    home = await call(s, "where_to_move", {
        "target_role": "data analyst", "country": "India",
        "priorities": ["low_cost"]})
    cities = [o["city"] for o in home["options"]]
    assert cities and all(o["country"] == "IN" for o in home["options"])
    assert cities[0] == "Hyderabad", cities
    abroad = await call(s, "where_to_move", {
        "target_role": "sales", "country": "US", "open_to_abroad": True,
        "priorities": ["big_market"]})
    assert abroad["options"][0]["country"] == "US"   # home first: no visa
    assert any(o["country"] != "US" for o in abroad["options"])
    print("where_to_move:", cities[:3], "OK")


async def autopilot_checks(s):
    preview = await call(s, "inbox_triage", {"emails": EMAILS})
    assert preview["by_category"]["other"] == 1
    actions = {(p["company"], p["status"]) for p in preview["proposals"]}
    assert actions == {("Acme", "interviewing"), ("Globex", "rejected"),
                       ("Initech", "assessment")}, actions
    initech = next(p for p in preview["proposals"]
                   if p["company"] == "Initech")
    assert initech["due_date"] == "2026-11-05"
    applied = await call(s, "inbox_triage", {"emails": EMAILS,
                                             "apply": True})
    assert len(applied["applied"]) == 3
    again = await call(s, "inbox_triage", {"emails": EMAILS})
    assert again["proposals"] == [], "re-running must not duplicate"
    print("inbox triage: classify, propose, apply, idempotent: OK")

    cal = await call(s, "calendar_interviews", {"apply": True, "events": [
        {"subject": "Acme hiring manager interview",
         "start": {"dateTime": "2026-11-06T10:00:00"}},
        {"subject": "Dentist", "start": "2026-11-04T09:00:00"}]})
    assert len(cal["interviews"]) == 1
    due = await call(s, "nudges_due", {"today": "2026-11-05",
                                       "within_days": 1})
    titles = [n["title"] for n in due["due_today"] + due["upcoming"]]
    assert any("Prep for Acme" in t for t in titles), titles
    assert any("thank-you" in t for t in titles), titles
    assert any("Initech assessment" in t for t in
               [n["title"] for n in due["overdue"] + due["due_today"]])
    app = await call(s, "application_log", {
        "company": "Hooli", "role": "PM", "status": "applied"})
    assert app["reminders_created"] == 1
    print("calendar interviews + autopilot reminders: OK")


async def interview_checks(s):
    qs = await call(s, "interview_questions", {"round": "recruiter",
                                               "likely_only": True})
    assert qs["questions"] and all(q["likely"] for q in qs["questions"])
    await call(s, "story_add", {
        "title": "Rescued a failing launch", "situation": "A launch was "
        "failing across two teams", "task": "Find the cause",
        "action": "I traced it and drove the fix", "result": "Recovered "
        "every lost signup within a week"})
    match = await call(s, "story_match", {
        "question": "Tell me about a time you failed"})
    assert match["story_count"] == 1 and "failure" in match[
        "question_themes"]
    draft = await call(s, "message_draft", {
        "kind": "thank_you", "company": "Acme", "role": "Analyst",
        "name": "Jordan", "detail": "the data platform", "me": "Sam"})
    assert "Jordan" in draft["body"] and "never sends" in draft["note"]
    assert "story_bank" in await call(s, "prep_checklist")
    print("interview questions, story bank, drafts: OK")


async def connector_checks(s):
    # Shapes as a Plaid-style finance connector returns them.
    accounts = [
        {"institution": "Demo Bank", "name": "Everyday Checking",
         "type": "depository", "subtype": "checking", "mask": "1234",
         "account_id": "acc-secret-1", "balance": {"current": 4200}},
        {"institution": "Demo Bank", "name": "Card", "type": "credit",
         "subtype": "credit card", "balance": {"current": 800}},
        {"institution": "Demo Invest", "name": "Roth IRA",
         "type": "investment", "subtype": "roth", "balance": 15000},
        {"institution": "Demo Invest", "name": "Brokerage",
         "type": "investment", "subtype": "brokerage", "balance": 9000},
        {"institution": "Demo Health", "name": "HSA", "type": "depository",
         "subtype": "hsa", "balance": 1000},
    ]
    holdings = [{"symbol": "VTI", "market_value": 6000, "type": "etf"},
                {"symbol": "XYZ", "market_value": 3000, "type": "equity"}]
    out = await call(s, "finance_import", {"accounts": accounts,
                                           "holdings": holdings})
    kinds = {a["name"]: a["kind"] for a in out["accounts_imported"]}
    assert kinds == {"Demo Bank Everyday Checking": "cash",
                     "Demo Bank Card": "debt",
                     "Demo Invest Roth IRA": "retirement",
                     "Demo Invest Brokerage": "brokerage",
                     "Demo Health HSA": "hsa"}, kinds
    assert out["holdings_imported"] == 2
    dash = await call(s, "finance_dashboard", {"today": TODAY})
    assert dash["accessible"] == 13200 and dash["locked"] == 16000
    assert dash["debt"] == 800
    assert "1234" not in str(dash) and "acc-secret" not in str(dash)
    assert any("XYZ is 33%" in f for f in dash["portfolio_flags"])
    guide = await call(s, "companions", {"need": "finance"})
    assert "finance_import" in guide["companions"]["finance"]["hand_to"]
    assert any("password" in r for r in guide["rules"])
    print("finance_import from a connector (no ids kept), companions: OK")


async def dashboard_checks(s):
    out = await call(s, "dashboard", {"today": TODAY})
    html = out["html"]
    assert html.startswith("<!doctype html>") and "__DATA__" not in html
    raw = html.split('id="cc-data" type="application/json">')[1]
    raw = raw.split("</script>")[0]           # the data ends at its own tag
    data = json.loads(raw)
    assert data["momentum"]["done_today"] is True    # step_done ran earlier
    companies = {i["company"] for c in data["pipeline"] for i in c["items"]}
    assert {"Acme", "Globex", "Initech", "Hooli"} <= companies, companies
    assert data["money"]["net_worth"] == 28400       # 13200 + 16000 - 800
    assert data["stories"]["count"] == 1
    path = out["saved_to"]
    assert os.path.exists(path) and path.endswith("dashboard.html")
    demo = os.environ.get("CC_DEMO_OUT")
    if demo:
        shutil.copy(path, demo)
    print("dashboard built and saved on the device:", os.path.basename(path))


async def conduct_checks(s):
    rules = await call(s, "ground_rules")
    assert rules["accepted"] is False and rules["privacy"] and rules["terms"]
    assert any("not financial" in t for t in rules["terms"])
    rules = await call(s, "ground_rules", {"accept": True})
    assert rules["accepted"] is True and rules["accepted_on"]
    assert (await call(s, "ground_rules"))["accepted"] is True

    rude = await call(s, "response_check", {
        "text": "Honestly that recruiter is an idiot. This is guaranteed "
                "to work, damn it."})
    kinds = {i["type"] for i in rude["issues"]}
    assert rude["ok"] is False
    assert {"insult", "profanity", "overpromise"} <= kinds, kinds

    biased = await call(s, "response_check", {
        "text": "Seeking a young, energetic salesman who is a culture fit.",
        "kind": "message"})
    assert any(i["type"] == "biased_wording" for i in biased["issues"])

    trait = await call(s, "response_check", {
        "text": "I am married and a practising Hindu.", "kind": "message"})
    assert any(i["type"] == "personal_trait" for i in trait["issues"])
    chat = await call(s, "response_check", {
        "text": "I am married and a practising Hindu.", "kind": "chat"})
    assert chat["ok"] and not chat["issues"], "traits only flagged in sends"

    money = await call(s, "response_check", {
        "text": "Put the rest into an index fund for retirement."})
    assert any(i["type"] == "missing_disclaimer" for i in money["issues"])
    money = await call(s, "response_check", {
        "text": "Index funds are common for retirement. This is general "
                "education, not financial advice."})
    assert money["ok"], money

    # Numbers in a resume must come from a confirmed fact.
    await call(s, "experience_add", {
        "employer": "Acme", "title": "Analyst", "start": "2022",
        "end": "2025", "fact": "Cut report time from 6 hours to 40 minutes",
        "confirmed": True})
    made_up = await call(s, "response_check", {
        "text": "Cut report time by 85% and saved $2M across 40 teams.",
        "kind": "resume"})
    nums = next(i for i in made_up["issues"]
                if i["type"] == "unsupported_number")["found"]
    assert "85%" in nums and "$2M" in nums and "40" not in nums, nums
    clean = await call(s, "response_check", {
        "text": "Cut report time from 6 hours to 40 minutes at Acme "
                "(2022-2025), using lazy loading to fix a race condition.",
        "kind": "resume"})
    assert clean["ok"] and not clean["issues"], clean
    print("ground rules, terms consent and response_check: OK")

    # Chat replies stay short: one step, one question, no lecture.
    lecture = ("## How to make it land\n" + "Lead with what you built. " * 20
               + "\n- one\n- two\n- three\n- four\nWant that? Or this?")
    kinds = {i["type"] for i in (await call(s, "response_check", {
        "text": lecture}))["issues"]}
    assert {"too_long", "many_questions", "too_many_items",
            "heading"} <= kinds, kinds
    short = await call(s, "response_check", {
        "text": "Add it as a Projects section under your latest job, with "
                "the GitHub link. Want me to draft the first line?"})
    assert short["ok"] and not short["issues"], short
    plan = await call(s, "response_check", {"text": lecture.replace(
        "Or this?", ""), "kind": "plan"})
    assert not any(i["type"] == "too_long" for i in plan["issues"])
    assert (await call(s, "ground_rules"))["reply_style"]
    print("short chat replies enforced, plans may be longer: OK")


async def main():
    shutil.rmtree(TEST_DIR, ignore_errors=True)
    env = {**os.environ, "COPILOT_DATA_DIR": TEST_DIR,
           "CAREER_COPILOT_LOG_DIR": os.path.join(TEST_DIR, "logs"),
           "CAREER_COPILOT_DASHBOARD_DIR": os.path.join(TEST_DIR, "dash")}
    params = StdioServerParameters(
        command=sys.executable, args=["app.py", "--stdio"], env=env)
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as s:
            await s.initialize()
            print("tools:", len((await s.list_tools()).tools))
            await coach_checks(s)
            await places_checks(s)
            await autopilot_checks(s)
            await interview_checks(s)
            await connector_checks(s)
            await dashboard_checks(s)
            await conduct_checks(s)
    with open(os.path.join(TEST_DIR, "logs", "mcp_server.log"),
              encoding="utf-8") as handle:
        log = handle.read()
    assert "jordan@acme.com" not in log and "can't go on" not in log
    assert "acc-secret-1" not in log and "4200" not in log, \
        "imported account data leaked into logs"
    print("emails, moods and imported accounts kept out of logs: OK")
    assert "practising Hindu" not in log, "checked text leaked into logs"
    print("text sent to response_check kept out of logs: OK")
    shutil.rmtree(TEST_DIR, ignore_errors=True)
    print("ALL PASSED")


asyncio.run(main())
