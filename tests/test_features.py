"""Feature test over stdio: finance, resumes, roles, prep, nudges, economy.

Synthetic data only. The economy check needs internet; it is skipped
(not failed) when the World Bank API can't be reached.
"""
import asyncio
import json
import os
import shutil
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

TEST_DIR = "./test_data_features"
TODAY = "2026-11-02"
OLD_RESUME = ("Sam Example | Backend Engineer\n"
              "- Worked on the payments service\n"
              "- Built an API used by 2 million users, cutting latency 40%\n")
NEW_RESUME = ("Sam Example | Senior Backend Engineer\n"
              "- Built an API used by 2 million users, cutting latency 40%\n"
              "- Designed an event pipeline across 5 services, reducing cost "
              "by 30%\n")
LINKEDIN = ("Software Engineer at ExampleCo\n"
            "I build web things.\n"
            "- Worked on APIs\n")


async def call(session, name, args=None):
    result = await session.call_tool(name, args or {})
    assert not result.isError, f"{name}: {result.content[0].text}"
    text = result.content[0].text if result.content else "null"
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


async def finance_checks(s):
    for name, kind, bal in (("Checking", "cash", 6000),
                            ("Savings", "cash", 24000),
                            ("Brokerage", "brokerage", 50000),
                            ("401k", "retirement", 80000),
                            ("Card", "debt", 1000)):
        await call(s, "finance_account_set", {
            "name": name, "kind": kind, "balance": bal, "as_of": TODAY})
    await call(s, "finance_account_set", {
        "name": "Old", "kind": "cash", "balance": 0, "as_of": "2026-08-01"})
    bad = await call(s, "finance_account_set", {
        "name": "X", "kind": "crypto-ish", "balance": 1})
    assert "error" in bad
    await call(s, "finance_holding_set", {
        "symbol": "acme", "value": 30000, "employer": True})
    await call(s, "finance_holding_set", {
        "symbol": "VTI", "value": 20000, "kind": "fund"})
    await call(s, "finance_budget_set", {
        "category": "Rent", "current": 2000, "target": 2000})
    await call(s, "finance_budget_set", {
        "category": "Food", "current": 1000, "target": 500})

    dash = await call(s, "finance_dashboard", {"today": TODAY})
    assert dash["net_worth"] == 159000, dash
    assert dash["accessible"] == 80000 and dash["locked"] == 80000
    assert dash["monthly_burn"] == 3000
    assert dash["runway_months"] == {"cash_only": 10.0,
                                     "all_accessible": 26.7}
    assert any("Old" in s_ for s_ in dash["stale_balances"])
    assert any("ACME is 60%" in f for f in dash["portfolio_flags"])
    print("finance dashboard: OK")

    review = await call(s, "finance_budget_review")
    assert review["monthly_savings"] == 500
    assert review["runway_months_at_target"] == 32.0
    plan = await call(s, "layoff_fund_plan", {
        "monthly_core_spend": 3000, "current_fund": 9000,
        "monthly_saving": 1000, "status_tied_to_job": True})
    assert plan["target_months"] == 9 and plan["gap"] == 18000
    assert plan["months_to_goal"] == 18
    assert (await call(s, "finance_account_remove",
                       {"name": "old"}))["removed"]
    print("budget review, layoff fund plan: OK")


async def career_checks(s):
    await call(s, "resume_import", {"text": OLD_RESUME, "label": "2024"})
    await call(s, "resume_import", {"text": NEW_RESUME, "label": "2026"})
    assert len(await call(s, "resume_versions")) == 2
    merged = await call(s, "resume_merge")
    assert merged["unique_bullets"] == 3, merged
    shared = [b for b in merged["bullets"] if "2 million" in b["bullet"]]
    assert sorted(shared[0]["sources"]) == ["2024", "2026"]
    assert merged["bullets"][-1]["bullet"] == "Worked on the payments service"
    print("resume import + merge (dedupe across versions): OK")

    weak = await call(s, "contribution_check", {"bullet": "- Helped on APIs"})
    strong = await call(s, "contribution_check", {
        "bullet": "Launched a hiring platform in 6 countries, cutting launch "
                  "time by 60%"})
    assert weak["score"] < strong["score"] == 4
    assert weak["ask_the_user"], weak
    print("contribution check:", weak["score"], "vs", strong["score"])

    li = await call(s, "linkedin_review", {
        "profile_text": LINKEDIN, "target_role": "backend"})
    assert "distributed systems" in li["keywords_missing"]
    assert len(li["fixes"]) >= 3
    print("linkedin review fixes:", len(li["fixes"]))

    fit = await call(s, "role_match", {
        "skills": ["Python", "SQL", "AWS", "Kafka", "Docker", "REST",
                   "Java"], "years": 6})
    assert fit["best_fits"][0]["role"] == "backend", fit["best_fits"]
    assert fit["level_estimate"] == "senior"
    front = next(r for r in fit["all"] if r["role"] == "frontend")
    assert "javascript" not in front["matched"], "java matched javascript"
    gap = await call(s, "skills_gap", {
        "target_role": "Backend Engineer", "level": "senior",
        "skills": ["python", "sql"]})
    assert "distributed systems" in gap["missing_core"]
    sections = await call(s, "resume_sections", {"years": 6})
    assert sections["level"] == "senior"
    print("role match, skills gap, resume sections: OK")


async def prep_checks(s):
    window = await call(s, "coding_pattern", {
        "query": "longest substring without repeating characters"})
    assert window["candidates"][0]["id"] == "window", window
    exact = await call(s, "coding_pattern", {"query": "dp"})
    assert exact["match"] == "exact"
    cache = await call(s, "system_design", {"topic": "redis"})
    assert cache["component"]["name"].startswith("Cache")
    frame = await call(s, "system_design")
    assert len(frame["framework"]) == 7
    plan = await call(s, "study_plan", {
        "start": TODAY, "interview_date": "2026-11-12",
        "save_as_nudges": True})
    assert plan["days"] == 10 and plan["nudges_created"] == 10
    assert plan["plan"][-1]["items"][-1] == "Rest and sleep"
    print("coding pattern, system design, study plan: OK")


async def nudge_checks(s):
    daily = await call(s, "nudge_add", {
        "title": "Apply to 10 roles", "due": "2026-11-01",
        "repeat_days": 1})
    await call(s, "application_log", {
        "company": "Acme", "role": "SWE", "next_action": "Recruiter call",
        "due_date": "2026-11-03"})
    due = await call(s, "nudges_due", {"today": TODAY})
    assert any(n["title"] == "Apply to 10 roles" for n in due["overdue"])
    assert any(n["source"] == "application" for n in due["upcoming"])
    done = await call(s, "nudge_done", {
        "nudge_id": daily["id"], "today": TODAY})
    assert done["next_due"] == "2026-11-03"
    ics = await call(s, "calendar_export")
    assert ics.startswith("BEGIN:VCALENDAR") and "RRULE:FREQ=DAILY" in ics
    # 10 plan days, 1 daily, 1 app deadline, 1 autopilot follow-up
    assert ics.count("BEGIN:VEVENT") == 13
    res = await s.read_resource("copilot://calendar.ics")
    assert "BEGIN:VEVENT" in res.contents[0].text
    print("nudges, calendar export: OK")


async def guide_checks(s):
    assert "points" in await call(s, "invest_guide", {"topic": "what_works"})
    assert "error" in await call(s, "invest_guide", {"topic": "crypto moon"})
    assert "points" in await call(s, "economy_guide",
                                  {"topic": "business_cycle"})
    assert len((await call(s, "layoff_playbook"))["steps"]) == 4
    connect = await s.read_resource("copilot://connect")
    assert "chatgpt" in connect.contents[0].text
    econ = await call(s, "economy_indicators", {
        "country": "USA", "indicators": ["inflation", "gdp_growth"]})
    latest = econ["indicators"]["inflation"].get("latest")
    if latest:
        print("economy (live):", econ.get("country_name"), "inflation",
              latest)
    else:
        print("economy: SKIPPED (World Bank API unreachable)")
    print("guides, connect resource: OK")


async def generic_checks(s):
    start = await call(s, "next_steps")
    assert start["next"][0]["use"] == "profile_save", start
    await call(s, "profile_save", {
        "target_role": "Product Manager", "current_role": "Sales",
        "industry": "retail", "years_experience": 4, "country": "IN",
        "goals": "career_move, future"})
    steps = await call(s, "next_steps")
    tracks = {step["track"] for step in steps["next"] + steps["remaining"]}
    assert tracks == {"Move into a different role", "Plan for the future"}
    print("next_steps follows the profile's goals: OK")

    fit = await call(s, "role_match", {
        "skills": ["prospecting", "negotiation", "CRM", "closing",
                   "Salesforce"], "years": 3})
    assert fit["best_fits"][0]["role"] == "sales", fit["best_fits"]
    move = await call(s, "career_move", {
        "current_role": "sales", "target_role": "product manager",
        "skills": ["communication", "stakeholder"]})
    assert move["distance"] == "career change", move
    assert "communication" in move["transferable"]
    assert "Marketing Manager" in move["stepping_stones"]
    adjacent = await call(s, "career_move", {
        "current_role": "Data Analyst", "target_role": "Data Engineer"})
    assert adjacent["distance"] == "adjacent"
    lead = await call(s, "skills_gap", {"target_role": "marketing",
                                        "level": "Team Lead"})
    assert lead["level"] == "staff"
    nurse_bullet = await call(s, "contribution_check", {
        "bullet": "Created a triage checklist for 40 patients a day that "
                  "reduced wait times by 30%"})
    assert nurse_bullet["score"] == 4, nurse_bullet
    print("non-tech roles, career move, levels, bullets: OK")

    await call(s, "goal_set", {"name": "Emergency fund",
                               "target_amount": 12000,
                               "target_date": "2027-11-02", "saved": 6000})
    await call(s, "goal_set", {"name": "Course fees", "target_amount": 2400,
                               "target_date": "2027-05-02"})
    goals = await call(s, "goals_review", {"monthly_budget": 600,
                                           "today": TODAY})
    assert goals["goals"][0]["name"] == "Course fees"
    assert goals["total_monthly_needed"] == 900.0 and not goals["on_track"]
    proj = await call(s, "future_projection", {
        "current_savings": 10000, "monthly_saving": 500, "years": 10,
        "target_amount": 50000})
    bal = proj["scenarios"]["balanced"]
    assert 90000 < bal["future_value"] < 95000, bal
    assert bal["in_todays_money"] < bal["future_value"]
    assert proj["total_contributed"] == 70000
    assert proj["scenarios"]["growth"]["years_to_target"] < \
        proj["scenarios"]["cautious"]["years_to_target"]
    print("goals, future projection:", bal["future_value"], "OK")


async def main():
    shutil.rmtree(TEST_DIR, ignore_errors=True)
    env = {**os.environ, "COPILOT_DATA_DIR": TEST_DIR,
           "CAREER_COPILOT_LOG_DIR": os.path.join(TEST_DIR, "logs")}
    params = StdioServerParameters(
        command=sys.executable, args=["app.py", "--stdio"], env=env)
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as s:
            await s.initialize()
            tools = await s.list_tools()
            print("tools:", len(tools.tools))
            await generic_checks(s)
            await finance_checks(s)
            await career_checks(s)
            await prep_checks(s)
            await nudge_checks(s)
            await guide_checks(s)
    log = os.path.join(TEST_DIR, "logs", "mcp_server.log")
    with open(log, encoding="utf-8") as handle:
        text = handle.read()
    assert "'balance': '***'" in text and "80000" not in text, \
        "money amounts leaked into logs"
    print("money amounts masked in logs: OK")
    shutil.rmtree(TEST_DIR, ignore_errors=True)
    print("ALL PASSED")


asyncio.run(main())
