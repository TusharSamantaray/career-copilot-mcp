"""Coach, relocation, inbox autopilot, calendar and interview tools, over
stdio with synthetic data only."""
import asyncio
import json
import os
import re
import shutil
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from pg_reset import fresh_database

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
    compass = await call(s, "life_compass")
    assert compass["of"] >= 5 and compass["next_question"]["number"] == 1


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
                                             "apply": True, "today": TODAY})
    assert len(applied["applied"]) == 3
    again = await call(s, "inbox_triage", {"emails": EMAILS})
    assert again["proposals"] == [], "re-running must not duplicate"
    print("inbox triage: classify, propose, apply, idempotent: OK")

    cal = await call(s, "calendar_interviews", {
        "apply": True, "today": TODAY, "events": [
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
    assert draft["check"]["ok"], draft["check"]
    assert draft["voice"] == "plain" and draft["body"].startswith("Hi ")
    formal = await call(s, "message_draft", {
        "kind": "thank_you", "company": "Acme", "role": "Analyst",
        "name": "Jordan", "detail": "the data platform", "me": "Sam",
        "voice": "formal"})
    assert formal["body"].startswith("Dear Jordan") and \
        "Kind regards," in formal["body"], formal["body"]
    assert "the data platform" in formal["body"], "voice changed the facts"
    await call(s, "profile_save", {"voice": "warm"})
    warm = await call(s, "message_draft", {"kind": "thank_you",
                                           "name": "Jordan", "me": "Sam"})
    assert warm["voice"] == "warm" and "Warm wishes," in warm["body"]
    await call(s, "profile_save", {"replace": True})   # newcomer again
    risky = await call(s, "message_draft", {
        "kind": "thank_you", "company": "Acme", "role": "Analyst",
        "detail": "I'm a guaranteed hire and cut costs by 85%"})
    flagged = {i["type"] for i in risky["check"]["issues"]}
    assert {"overpromise", "unsupported_number"} <= flagged, flagged
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
    acts = data["actions"]["items"]
    named = {a["company"]: a for a in acts}
    assert "Globex" not in named, "a closed loop asked for action"
    assert named["Hooli"]["why"] == "no next step", acts
    assert 'id="view"' in html and "Loops needing action" in html
    later = await call(s, "dashboard", {"today": "2026-11-12",
                                        "save_local": False})
    raw = later["html"].split('id="cc-data" type="application/json">')[1]
    first = json.loads(raw.split("</script>")[0])["actions"]["items"][0]
    assert first["tone"] == "alert" and first["why"].endswith("overdue"), \
        first
    print("dashboard action strip: live loops only, overdue first: OK")
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
    rules = await call(s, "ground_rules")
    assert len(rules["summary"]) == 3 and rules["data_handling"]["stored"]
    assert "reply_style" not in rules and "show_user" not in rules
    # A disclosure states what the product does; it gives the assistant no
    # orders ("call", "ask", "never block", "you must").
    told = " ".join(rules["summary"] + rules["how_career_copilot_talks"])
    assert not re.search(r"(call|ask (?:if|them)|you must|then ask)",
                         told, re.I), told
    print("short chat replies enforced, plans may be longer: OK")


async def journey_checks(s):
    # First visit: two ways in, nothing required.
    state = await call(s, "journey_state")
    assert state["ground_rules_accepted"] and not state["known"]
    assert "ask me questions" in state["next"]["question"]["options"]

    # Starter questions, one at a time, saved at once, never re-asked.
    await call(s, "profile_save", {"situation": "working, want a change"})
    state = await call(s, "journey_state")
    assert state["next"]["saves_to"] == "target_role", state
    await call(s, "profile_save", {"skip": ["target_role"]})
    state = await call(s, "journey_state")
    assert state["next"]["saves_to"] == "current_role", state
    assert "target_role" in state["skipped"]
    await call(s, "profile_save", {"current_role": "Analyst",
                                   "location": "remote",
                                   "unsure": ["location"]})
    # After three answers it gives something back instead of asking more.
    state = await call(s, "journey_state")
    assert state["next"]["use"] == "direction_options", state
    assert state["unsure"] == ["location"]
    assert state["stage"] in ("orient", "prepare")

    # Merges: lists add items, earlier answers stay.
    await call(s, "profile_save", {"wants": ["remote", "growth"]})
    await call(s, "profile_save", {"wants": ["growth", "mentoring"]})
    profile = await call(s, "profile_get")
    assert profile["wants"] == ["remote", "growth", "mentoring"], profile
    assert profile["current_role"] == "Analyst"
    assert profile["confidence"]["location"] == "unsure"

    # life_compass saves answers and moves on.
    await call(s, "life_compass", {"question": 1, "answer": "Building "
                                   "things with a small team",
                                   "save_as": "want"})
    compass = await call(s, "life_compass")
    assert compass["answered"] == 1 and compass["next_question"]["number"] \
        == 2
    profile = await call(s, "profile_get")
    assert "Building things with a small team" in profile["wants"]
    print("journey_state, two ways in, merged profile, saved compass: OK")

    # Talks it out: facts read back first, saved only after they agree.
    facts = [{"field": "dealbreakers", "value": "fully on-site",
              "confirmed": True},
             {"field": "comp_floor", "value": "90k", "confirmed": False},
             {"field": "experience", "employer": "Globex",
              "title": "Analyst", "value": "Built the weekly sales report",
              "confirmed": True},
             {"field": "shoe_size", "value": "9", "confirmed": True}]
    before = len(await call(s, "experience_list"))
    preview = await call(s, "profile_from_text", {"facts": facts})
    assert len(preview["read_back"]) == 3 and preview["problems"], preview
    assert "comp floor: 90k (unsure)" in preview["read_back"]
    assert "comp_floor" not in await call(s, "profile_get"), "saved early"
    await call(s, "profile_from_text", {"facts": facts, "apply": True})
    profile = await call(s, "profile_get")
    assert "fully on-site" in profile["dealbreakers"]
    assert profile["confidence"]["comp_floor"] == "unsure"
    assert len(await call(s, "experience_list")) == before + 1
    print("profile_from_text reads back before saving: OK")

    options = await call(s, "direction_options", {
        "skills": ["sql", "python", "statistics", "dashboards"]})
    assert 2 <= len(options["options"]) <= 3, options
    first = options["options"][0]
    assert {"fit", "distance", "gaps", "risk", "first_test"} <= set(first)
    assert "test" in options["level_note"]
    print("direction_options gives 2-3 directions to test: OK")


async def fact_checks(s):
    # Acceptance C: resume versions disagree on a date and a number.
    job = {"employer": "Initech", "title": "Data Engineer"}
    a = await call(s, "fact_add", {
        **job, "start": "2021", "end": "2024", "source": "imported",
        "source_ref": "2024 resume", "ownership": "led",
        "statement": "Cut nightly pipeline runtime by 35%",
        "metrics": [{"value": 35, "unit": "%"}], "apply": True})
    assert not a["conflicts"]
    preview = await call(s, "fact_add", {
        **job, "start": "2022", "end": "2024", "source": "imported",
        "source_ref": "2025 resume", "ownership": "led",
        "statement": "Cut the nightly pipeline runtime by 55%",
        "metrics": [{"value": 55, "unit": "%"}]})
    fields = {c["field"] for c in preview["conflicts"]}
    assert fields == {"date", "metric"}, preview["conflicts"]
    assert "fact_id" not in preview, "preview must not save"
    b = await call(s, "fact_add", {
        **job, "start": "2022", "end": "2024", "source": "imported",
        "source_ref": "2025 resume", "ownership": "led",
        "statement": "Cut the nightly pipeline runtime by 55%",
        "metrics": [{"value": 55, "unit": "%"}], "apply": True})
    assert len((await call(s, "fact_conflicts"))["conflicts"]) == 2

    # Not a confirmed fact yet, so a draft using 40% is flagged.
    draft = "Led a fix that cut nightly pipeline runtime by 35%."
    check = await call(s, "response_check", {"text": draft,
                                             "kind": "resume"})
    assert any(i["type"] == "unsupported_number" for i in check["issues"])

    # The person says the 35% version is right.
    done = await call(s, "fact_resolve", {"keep_id": a["fact_id"],
                                          "drop_id": b["fact_id"]})
    assert done["kept_confidence"] == "confirmed"
    assert not (await call(s, "fact_conflicts"))["conflicts"]
    check = await call(s, "response_check", {"text": draft,
                                             "kind": "resume"})
    assert check["ok"], check
    check = await call(s, "response_check", {
        "text": "Cut nightly pipeline runtime by 55%.", "kind": "resume"})
    assert not check["ok"], "a retired number must not pass"

    helped = await call(s, "fact_add", {
        "statement": "Built the alerting dashboard for the ops team",
        "employer": "Initech", "ownership": "contributed",
        "confirmed": True, "apply": True})
    inflated = await call(s, "ownership_check", {
        "bullet": "Led the alerting dashboard for the ops team"})
    assert not inflated["ok"] and inflated["fact_ownership"] == \
        "contributed", inflated
    fine = await call(s, "ownership_check", {
        "bullet": "Built the alerting dashboard for the ops team",
        "fact_id": helped["fact_id"]})
    assert fine["ok"]
    unknown = await call(s, "ownership_check", {
        "bullet": "Architected a billing platform"})
    assert not unknown["ok"] and "lead it" in unknown["ask"]
    print("ownership_check: verbs can't claim more than the fact: OK")

    guess = await call(s, "fact_add", {
        "statement": "Probably mentored juniors", "source": "inferred",
        "confirmed": True})
    assert "error" in guess, "inferred facts can't be confirmed"
    print("facts: conflicts raised, person resolves, only kept number "
          "passes: OK")

    # Imported resumes feed the fact record; versions that disagree are
    # caught without anyone describing them.
    first = await call(s, "resume_import", {
        "label": "v1", "text": "- Cut onboarding time by 30% for new "
                               "hires\n- Ran weekly demos for 12 clients"})
    assert first["facts_saved_unsure"] == 2 and "conflicts" not in first
    second = await call(s, "resume_import", {
        "label": "v2", "text": "- Cut onboarding time by 45% for new "
                               "hires\n- Ran weekly demos for 12 clients"})
    assert second.get("conflicts") == 1, second
    record = (await call(s, "data_export"))["fact"]
    demos = [f for f in record if "weekly demos" in f["statement"]]
    assert len(demos) == 1 and demos[0]["also_in"] == ["v2"], demos
    assert all(f["confidence"] == "unsure" for f in record
               if f["source_ref"] in ("v1", "v2"))
    print("resume imports become unsure facts, version conflicts caught: OK")


# Public job-board answers, in each board's own shape (synthetic).
BOARD_FIXTURE = {
    "https://boards-api.greenhouse.io/v1/boards/acme/jobs": {"jobs": [
        {"id": 1, "title": "Senior Data Analyst",
         "location": {"name": "Remote - US"},
         "first_published": "2026-10-30T10:00:00Z",
         "updated_at": "2026-11-01T10:00:00Z",
         "absolute_url": "https://boards.greenhouse.io/acme/jobs/1"},
        {"id": 2, "title": "Data Analyst", "location": {"name": "Remote"},
         "updated_at": "2026-11-01T10:00:00Z",
         "absolute_url": "https://boards.greenhouse.io/acme/jobs/2"},
        {"id": 3, "title": "Data Analyst II", "location": {"name": "Remote"},
         "first_published": "2026-09-01T10:00:00Z",
         "absolute_url": "https://boards.greenhouse.io/acme/jobs/3"},
        {"id": 4, "title": "Data Analyst", "location": {"name": "Austin"},
         "first_published": "2026-11-01T10:00:00Z",
         "absolute_url": "https://boards.greenhouse.io/acme/jobs/4"}]},
    "https://api.lever.co/v0/postings/globex?mode=json": [
        {"id": "g-1", "text": "Analyst, Growth", "workplaceType": "remote",
         "categories": {"location": "Remote"}, "createdAt": 1793491200000,   # 2026-11-01

         "hostedUrl": "https://jobs.lever.co/globex/g-1"}],
    "https://api.ashbyhq.com/posting-api/job-board/hooli": {"jobs": [
        {"id": "h-1", "title": "Data Analyst", "location": "Remote",
         "isRemote": True, "publishedAt": "2026-11-01T09:00:00Z",
         "jobUrl": "https://jobs.ashbyhq.com/hooli/h-1"}]},
    "https://api.ashbyhq.com/posting-api/job-board/initech": {"jobs": [
        {"id": "i-1", "title": "Product Analyst", "location": "Remote",
         "isRemote": True, "publishedAt": "2026-10-31T09:00:00Z",
         "jobUrl": "https://jobs.ashbyhq.com/initech/i-1"}]},
}


async def job_checks(s):
    # Acceptance E: no dealbreaker broken, every result dated, second run
    # silent. The profile already says "fully on-site" is a hard no.
    first = await call(s, "job_search", {
        "companies": ["greenhouse:acme", "lever:globex", "ashby:initech"],
        "keywords": ["analyst"], "today": TODAY})
    titles = {j["title"] for j in first["new"]}
    assert titles == {"Senior Data Analyst", "Analyst, Growth",
                      "Product Analyst"}, titles
    assert all(j["posted"] and j["url"] and j["remote"]
               for j in first["new"])
    assert first["dropped"]["no_date"] == 1, "updated_at isn't a post date"
    assert first["dropped"]["too_old"] == 1
    assert first["dropped"]["dealbreaker"] == 1, "on-site role slipped in"
    again = await call(s, "job_search", {
        "companies": ["greenhouse:acme", "lever:globex", "ashby:initech"],
        "keywords": ["analyst"], "today": TODAY})
    assert again["new_count"] == 0 and again["say"].startswith("Nothing new")
    await call(s, "profile_save", {"excluded_companies": ["globex"]})
    shown = await call(s, "job_search", {
        "companies": ["lever:globex"], "keywords": ["analyst"],
        "include_seen": True, "today": TODAY})
    assert not shown["new"], "excluded company shown"
    print("job_search: dated, filtered, deduped, silent when nothing new: OK")

    found = await call(s, "recruiter_find", {"company": "Acme Corp",
                                             "role": "Data Analyst"})
    urls = [l["url"] for l in found["links"]]
    assert urls[0].startswith("https://www.linkedin.com/search/results/")
    assert all("Acme" in u for u in urls) and "Links only" in found["note"]
    print("recruiter_find: links only: OK")

    posting = ("Senior Data Analyst at Acme. 5+ years with SQL and Python, "
               "dashboards in Tableau. Remote. Pay range $120k - $150k. We "
               "are unable to sponsor visas for this role.")
    await call(s, "profile_save", {"domain_keywords": ["sql", "python"]})
    read = await call(s, "jd_analyze", {"text": posting,
                                        "title": "Senior Data Analyst",
                                        "company": "Acme"})
    assert read["level_read"] == "senior" and read["years_asked"] == [5]
    assert read["pay_read"]["vs_floor"] == "meets your floor", read
    assert read["sponsorship_read"] == "says no sponsorship"
    assert {"sql", "python"} <= set(read["fit_points"])
    assert "tableau" in read["gap_points"]
    assert read["verdict"].startswith("apply"), read["verdict"]
    await call(s, "profile_save", {"dealbreakers": ["no visa sponsorship"]})
    read = await call(s, "jd_analyze", {"text": posting})
    assert read["verdict"].startswith("skip"), read
    print("jd_analyze: level, pay vs floor, sponsorship, fit, verdict: OK")

    messy = ("Sam Lee | Analyst | Remote\n"
             "Work            Jan 2024 - now\n"
             "★ Built reports 03/2022\nEducation\nSkills: SQL")
    check = await call(s, "ats_profile_check", {
        "posting_url": "https://acme.wd5.myworkdayjobs.com/en-US/jobs/1",
        "posting_text": "Must be located in Austin. 5+ years. Bachelor's "
                        "degree required. Must be authorized to work in "
                        "the US.",
        "resume_text": messy})
    assert check["platform"] == "workday"
    joined = " ".join(check["parse_risks"])
    for risk in ("Table", "Two columns", "Icons", "Mixed date",
                 "experience", "email"):
        assert risk in joined, (risk, check["parse_risks"])
    assert set(check["likely_knockouts"]) >= {"location", "years", "degree",
                                              "work_authorization"}
    assert "degree" in check["need_an_answer"]
    assert check["verdict"] == "knockout_risk"
    clean = await call(s, "ats_profile_check", {
        "posting_url": "https://boards.greenhouse.io/acme/jobs/1",
        "posting_text": "Remote-friendly analyst role.",
        "resume_text": "sam@example.com\nExperience\nAnalyst, Acme, "
                       "Jan 2022 - Jan 2025\nEducation\nBS\nSkills\nSQL"})
    assert clean["platform"] == "greenhouse" and clean["verdict"] == "ready",\
        clean
    print("ats_profile_check: platform, parse risks, knock-outs, verdict: OK")

    await call(s, "profile_save", {"honest_gaps": ["kubernetes"]})
    keys = await call(s, "ats_keyword_check", {
        "posting_text": "We need SQL, Python, Kubernetes and Tableau.",
        "resume_text": "Experience\nBuilt SQL reports for finance."})
    assert keys["covered"] == ["sql"], keys
    assert keys["missing_but_true"] == ["python"], keys    # profile keyword
    assert set(keys["missing_and_gap"]) == {"kubernetes", "tableau"}, keys
    print("ats_keyword_check: covered, missing but true, real gaps: OK")

    letter = await call(s, "cover_letter_draft", {
        "company": "Acme", "role": "Data Analyst", "me": "Sam",
        "posting_text": "You will own reporting and cut report time."})
    assert "Cut report time from 6 hours to 40 minutes" in letter["body"]
    assert letter["check"]["ok"], letter["check"]
    assert all(f in letter["body"] for f in letter["facts_used"])
    print("cover_letter_draft: confirmed facts only, checked: OK")


async def loop_checks(s):
    tense = await call(s, "story_add", {
        "title": "Led a tense migration", "situation": "Two teams disagreed "
        "on the cut-over plan", "task": "Agree a plan", "action": "I led "
        "the team through the conflict and wrote the plan",
        "result": "Moved 4 services with no outage before the deadline"})
    assert {"conflict", "leadership", "speed"} <= set(tense["themes"]), tense
    preview = await call(s, "loop_round_log", {
        "company": "Acme Corp", "round_n": 1, "round_format": "behavioral",
        "role": "Analyst"})
    assert "requisition" in preview["note"] and "saved" not in preview
    logged = await call(s, "loop_round_log", {
        "company": "Acme Corp", "req_id": "R-104", "round_n": 1,
        "round_format": "behavioral",
        "panel": [{"role": "Hiring manager", "focus_area": "teamwork"}],
        "questions": [{"text": "Tell me about a time you disagreed with a "
                               "teammate", "story_id": tense["id"],
                       "self_rating": 2}],
        "feedback": [{"text": "Strong on ownership, go deeper on numbers",
                      "source": "recruiter_said"}],
        "apply": True})
    loop_id = logged["loop_id"]
    assert loop_id == "acme-corp#r-104", loop_id
    plan = await call(s, "loop_next_round_prep", {
        "loop_id": loop_id, "next_format": "panel",
        "known_panel": [{"role": "Hiring manager"}]})
    assert "conflict" in plan["covered_competencies"]
    assert "conflict" not in plan["uncovered_competencies"]
    by_theme = {p["competency"]: p for p in plan["story_plan"]}
    # A story this panel hasn't heard wins when there is one...
    assert by_theme["leadership"]["story_id"] != tense["id"]
    assert by_theme["leadership"]["reuse_risk"] == "none"
    # ...and a repeat is flagged when it's the only option.
    assert by_theme["speed"]["story_id"] == tense["id"]
    assert by_theme["speed"]["reuse_risk"] == "same_panelist"
    assert len(plan["weak_spots"]) == 2, plan["weak_spots"]
    assert plan["one_thing_today"].startswith("Rework")
    assert plan["calendar"]["status"] == "not_checked"
    await call(s, "lessons", {"add": "Lead with the number, then the story",
                              "loop_id": loop_id})
    noted = await call(s, "lessons")
    assert noted["lessons"][0]["text"].startswith("Lead with the number")
    again = await call(s, "loop_next_round_prep", {"loop_id": loop_id})
    assert again["your_lessons"][0]["loop"] == loop_id
    booked = await call(s, "loop_next_round_prep", {
        "loop_id": loop_id, "calendar_events": [
            {"subject": "Acme Corp panel interview",
             "start": "2026-11-10T15:00:00Z"}]})
    assert booked["calendar"] == {"status": "on_calendar",
                                  "date": "2026-11-10"}, booked["calendar"]
    missing = await call(s, "loop_next_round_prep", {
        "loop_id": loop_id, "calendar_events": [
            {"subject": "Dentist", "start": "2026-11-10T15:00:00Z"}]})
    assert missing["calendar"]["status"] == "not_on_calendar"
    print("interview rounds: logged by req id, next round builds on it, "
          "repeat stories flagged: OK")

    # A rejection closes only the application it names.
    analyst = await call(s, "application_log", {
        "company": "Umbrella", "role": "Data Analyst", "status":
        "interviewing", "req_id": "r-104"})
    engineer = await call(s, "application_log", {
        "company": "Umbrella", "role": "Data Engineer", "status": "applied",
        "req_id": "R-200"})
    named = {"from": "Umbrella Talent <talent@umbrella.example>",
             "subject": "Your application to Umbrella", "date": "2026-11-02",
             "snippet": "Unfortunately we will not be moving forward with "
                        "your application (Req ID: R-200)."}
    vague = {**named, "date": "2026-11-03",
             "snippet": "Unfortunately we will not be moving forward."}
    plan = await call(s, "inbox_triage", {"emails": [named]})
    update = [p for p in plan["proposals"] if p["company"] == "Umbrella"]
    assert len(update) == 1 and update[0]["application_id"] == \
        engineer["id"], plan["proposals"]
    plan = await call(s, "inbox_triage", {"emails": [vague], "apply": True})
    ask = [p for p in plan["proposals"] if p["company"] == "Umbrella"]
    assert ask and ask[0]["action"] == "confirm" and \
        len(ask[0]["candidates"]) == 2, ask
    rows = {r["id"]: r for r in (await call(s, "data_export"))["application"]}
    assert rows[analyst["id"]]["status"] == "interviewing", "closed blindly"
    assert rows[engineer["id"]]["status"] == "applied"
    print("rejections close only the role or req id they name: OK")

    await call(s, "application_log", {"company": "Wayne", "role": "Analyst",
                                      "sponsorship": "no"})
    digest = await call(s, "pipeline_digest", {"today": TODAY})
    assert "Wayne" in digest["sponsorship"]["says_no"], digest
    assert "Umbrella" in digest["sponsorship"]["unknown"]
    assert "overdue" in digest
    print("pipeline_digest: sponsorship column when it's a need: OK")

    values = await call(s, "study_plan", {
        "start": "2026-11-02", "interview_date": "2026-11-14",
        "loop_format": "values_heavy"})
    story_days = [d for d in values["plan"]
                  if d["items"][0].startswith("Stories:")]
    assert len(story_days) >= 4, values["plan"]
    sample = await call(s, "study_plan", {
        "start": "2026-11-02", "interview_date": "2026-11-14",
        "loop_format": "non_technical"})
    text = str(sample["plan"])
    assert "Pattern:" not in text and "work sample" in text
    assert "error" in await call(s, "study_plan", {
        "start": "2026-11-02", "interview_date": "2026-11-14",
        "loop_format": "chess"})
    from copilot.knowledge.interview import LOOP_FORMATS
    from copilot.prep import ROTATION
    assert set(ROTATION) == set(LOOP_FORMATS), "a loop format has no plan"
    print("study_plan follows the loop format: OK")

    grid = await call(s, "story_coverage")
    assert grid["stories"] >= 2
    conflict = grid["grid"]["conflict"][0]
    assert conflict["title"] == "Led a tense migration"
    assert conflict["score"] == 4, conflict
    failure = grid["grid"]["failure"][0]          # "Rescued a failing launch"
    assert "has_number" in failure["missing"]
    assert "ambiguity" in grid["gaps"] and "failure" in grid["gaps"]
    assert grid["next_story"]["do"]
    assert conflict["numbers_not_in_confirmed_facts"] == [], conflict
    print("story_coverage: grid, strength, gaps, next story: OK")


async def evidence_checks(s):
    early = await call(s, "skill_gap_evidence", {})
    assert early["skills"] == [] and "at least 5" in early["say"], early
    for n in range(4):
        await call(s, "jd_analyze", {
            "title": f"Data Analyst {n}", "company": f"Co{n}",
            "text": "Required: SQL and Airflow every day. Tableau is a "
                    "plus. Python preferred."})
    gaps = await call(s, "skill_gap_evidence", {})
    by_skill = {r["skill"]: r for r in gaps["skills"]}
    assert by_skill["airflow"]["evidence"] == "none"
    assert by_skill["sql"]["evidence"] == "claimed"     # profile keyword
    assert by_skill["tableau"]["required_share"] < by_skill["tableau"][
        "demand"], "a plus is preferred, not required"
    assert gaps["skills"][0]["gap_cost"] >= gaps["skills"][-1]["gap_cost"]
    assert "not industry-wide" in gaps["caveats"][0]
    assert gaps["outcome_signal"]["status"] == "not_enough_data"
    for n in range(5):
        await call(s, "application_log", {
            "company": f"Outcome{n}", "role": "Analyst",
            "status": "interviewing" if n < 2 else "applied",
            "resume_label": "v2"})
    gaps = await call(s, "skill_gap_evidence", {})
    v2 = gaps["outcome_signal"]["by_resume_version"]["v2"]
    assert v2 == {"sent": 5, "replies": 2, "reply_rate": 0.4}, v2
    record = (await call(s, "data_export"))["posting"]
    assert all("text" not in p for p in record), "full posting text kept"
    print("skill_gap_evidence: demand, evidence, gap cost, outcome log: OK")


async def watch_checks(s):
    bad = await call(s, "watch_create", {"kind": "new_postings",
                                         "cadence": "hourly"})
    assert "error" in bad
    w = await call(s, "watch_create", {
        "kind": "new_postings", "companies": ["ashby:hooli"],
        "keywords": ["analyst"]})
    await call(s, "watch_create", {"kind": "assessment_expiry"})
    await call(s, "application_log", {
        "company": "Hooli", "role": "Data Analyst", "status": "assessment",
        "next_action": "Finish the coding assessment",
        "due_date": "2026-11-03"})
    first = await call(s, "digest_get", {"today": TODAY})
    texts = " ".join(i["text"] for i in first["items"])
    assert "Data Analyst at hooli" in texts and "assessment" in texts, texts
    again = await call(s, "digest_get", {"today": TODAY})
    assert again["count"] == 0 and again["say"] == "Nothing new."
    listed = await call(s, "watches", {"remove_id": w["id"]})
    assert listed["removed"] and len(listed["watches"]) == 1
    print("watches: findings wait in the outbox, read once, removable: OK")


async def mirror_checks(s):
    mirror = await call(s, "data_mirror", {})
    text = mirror["markdown"]
    assert text.startswith("# My Career Copilot data")
    assert "## Fact (" in text and "**confidence**: unsure" in text
    assert "Cut onboarding time by 30%" in text
    assert "test_data_soul" in mirror["saved_to"], "wrote outside the test"
    with open(mirror["saved_to"], encoding="utf-8") as handle:
        assert handle.read() == text
    print("data_mirror: readable Markdown, saved on the device: OK")


async def tailor_checks(s):
    hooli = {"employer": "Hooli", "title": "Platform Engineer",
             "confirmed": True, "apply": True}
    owned = (await call(s, "fact_add", {
        **hooli, "ownership": "contributed",
        "statement": "Built Python ETL jobs that cut report lag by 25%"}))
    other = (await call(s, "fact_add", {
        "employer": "Pied Piper", "title": "Analyst", "confirmed": True,
        "apply": True, "statement": "Built SQL dashboards for 12 teams"}))
    unsure = (await call(s, "fact_add", {
        "employer": "Hooli", "statement": "Ran the on-call rotation"}))
    await call(s, "profile_save", {"honest_gaps": ["kafka"]})
    posting = ("Senior Data Engineer. Python, ETL, SQL, Kafka and "
               "Databricks. Build reliable pipelines.")
    oid = owned["fact_id"]
    result = await call(s, "resume_tailor", {
        "posting_text": posting, "company": "Globex",
        "save_as": "Globex data eng", "edits": [
            {"line": "Built Python ETL jobs that cut report lag by 25%",
             "fact_ids": [oid]},
            {"line": "Built Python ETL jobs that cut report lag by 40%",
             "fact_ids": [oid]},
            {"line": "Led Python ETL jobs that cut report lag by 25%",
             "fact_ids": [oid]},
            {"line": "Built Python ETL and SQL dashboards for 12 teams",
             "fact_ids": [oid, other["fact_id"]]},
            {"line": "Built Python ETL jobs feeding Kafka",
             "fact_ids": [oid]},
            {"line": "Built Python ETL jobs in Databricks",
             "fact_ids": [oid]},
            {"line": "Ran the on-call rotation", "fact_ids": [
                unsure.get("fact_id", "missing")]},
            {"line": "Shipped Python ETL jobs"}]})
    assert [a["line"] for a in result["accepted"]] == [
        "Built Python ETL jobs that cut report lag by 25%"], result
    rules = [{p["rule"] for p in b["problems"]} for b in result["blocked"]]
    assert rules == [{"unsupported_number"}, {"ownership"}, {"merged_claim"},
                     {"honest_gap"}, {"invented_keyword"},
                     {"unconfirmed_fact"}, {"no_fact"}], rules
    assert result["honest_gaps"] == ["kafka"], result["honest_gaps"]
    assert result["invented_claims_blocked"] == ["databricks"], result
    assert result["saved"]["label"] == "Globex data eng"
    assert result["check"]["ok"], result["check"]
    versions = await call(s, "resume_versions")
    assert any(v["label"] == "Globex data eng" for v in versions)
    print("resume_tailor: only fact-backed lines pass, each block has a "
          "reason, accepted lines saved as a version: OK")


async def outreach_checks(s):
    mail = {"channel": "email", "to": "Jordan@Acme.example",
            "subject": "Following up on the analyst role",
            "body": "Hi Jordan, thanks for the call on Monday. I'm keen to "
                    "keep talking about the analyst role. Best, Sam"}
    weak = await call(s, "outreach_review", {
        **mail, "body": mail["body"] + " I'm on a PIP so this is urgent."})
    assert "approval_id" not in weak, weak
    found = {i["type"] for i in weak["check"]["issues"]}
    assert "volunteers_weakness" in found, found
    review = await call(s, "outreach_review", mail)
    assert review["check"]["ok"] and review["approval_id"], review
    assert review["show_user"]["body"] == mail["body"]
    assert "Nothing" in review["stored"]
    ticket = review["approval_id"]
    no = await call(s, "outreach_approve", {**mail, "approval_id": ticket,
                                            "consent": False})
    assert no["approved"] is False and no["status"] == "not_sent", no
    edited = await call(s, "outreach_approve", {
        **mail, "body": mail["body"] + " P.S. call me", "approval_id": ticket,
        "consent": True})
    assert edited["status"] == "refused", edited
    other = await call(s, "outreach_approve", {
        **mail, "to": "someone@else.example", "approval_id": ticket,
        "consent": True})
    assert other["status"] == "refused", other
    forged = await call(s, "outreach_approve", {
        **mail, "approval_id": "9999999999.forged", "consent": True})
    assert forged["status"] == "refused", forged
    yes = await call(s, "outreach_approve", {**mail, "approval_id": ticket,
                                             "consent": True})
    assert yes["approved"] and "sent mail" in yes["verify"], yes
    event = {"channel": "calendar_event", "subject": "Acme round 2",
             "when": "2026-11-12T15:00"}
    seen = await call(s, "outreach_review", event)
    assert seen["show_user"]["reminders_minutes_before"] == [30, 1]
    ok = await call(s, "outreach_approve", {
        **event, "approval_id": seen["approval_id"], "consent": True})
    assert ok["reminders_minutes_before"] == [30, 1], ok
    post = await call(s, "outreach_review", {
        "channel": "linkedin_post", "body": "Open to analyst roles in "
        "Seattle. Ask me about SQL dashboards."})
    assert post["approval_id"], post
    gone = await call(s, "outreach_review", {"channel": "fax"})
    assert "error" in gone
    print("outreach: checked, sealed to the exact text, refused when "
          "edited or without a yes, sent only by the person's own app: OK")


async def timeline_checks(s):
    head = ("Data Engineer | Python, SQL\n"
            "Summary\n"
            "Data engineer who cut report lag by 25% with reliable ETL "
            "pipelines for analytics teams.\n"
            "Experience\n"
            "Hooli Data Platform, Data Engineer, 2022 - 2026\n")
    tail = "Education\nB.S. Statistics, State University, 2018 - 2022\n"
    old = (head.replace("Data engineer who cut report lag by 25% with",
                        "I am a passionate L5 engineer who builds")
           .replace("Hooli Data Platform", "Hooli Blue Hub") +
           "- Built Python ETL jobs that cut report lag by 25%\n"
           "- Grew revenue by 300% with a new data platform\n"
           "- Wrote runbooks for ETL jobs\n")
    fixed = (head + "- Built Python ETL jobs that cut report lag by 25%\n"
             "- Wrote runbooks for the nightly ETL jobs\n")
    branch = fixed.replace("Data Engineer |", "L5 Data Engineer |") + \
        "- Grew revenue by 300% with a new data platform\n"
    none = await call(s, "resume_timeline")
    assert none["count"] == 0
    first = await call(s, "resume_snapshot", {
        "text": old + tail, "label": "Sep pre-rebuild",
        "avoid_terms": ["Blue Hub"],
        "rendered_file": "C:/Users/Wombat/cv-sep.pdf"})
    assert first["checks"]["level_tags"] == ["L5"], first
    assert first["checks"]["internal_names"] == ["Blue Hub"], first
    assert first["checks"]["unsupported_numbers"] == [
        "Grew revenue by 300% with a new data platform"], first
    assert set(first["checks"]["summary_issues"]) == {
        "no numbers up front", "passionate"}, first
    assert len(first["roles"]) == 1, first["roles"]   # education isn't a role
    second = await call(s, "resume_snapshot", {
        "text": fixed, "label": "Oct accuracy rebuild",
        "note": "Removed the invented bullet and level tags"})
    assert not any(second["checks"].values()), second
    third = await call(s, "resume_snapshot", {
        "text": branch, "label": "Oct branch", "parent": second["id"]})
    assert {r["check"] for r in third["regressions"]} == {
        "level_tags", "unsupported_numbers"}, third
    final = await call(s, "resume_snapshot", {
        "text": fixed + "- Mentored two analysts on SQL reviews\n",
        "label": "Oct final", "parent": second["id"]})
    assert "regressions" not in final, final
    again = await call(s, "resume_snapshot", {"text": fixed,
                                              "label": "Copy"})
    assert again["same_as"] == "Oct accuracy rebuild", again
    bad = await call(s, "resume_snapshot", {"text": fixed, "parent": "nope"})
    assert "error" in bad

    line = await call(s, "resume_timeline")
    labels = [v["label"] for v in line["versions"]]
    assert labels == ["Sep pre-rebuild", "Oct accuracy rebuild",
                      "Oct branch", "Oct final", "Copy"], labels
    rows = {v["label"]: v for v in line["versions"]}
    assert rows["Oct branch"]["regressions"], "regression hidden"
    assert "branch" in rows["Oct final"], "branch not shown"
    assert rows["Sep pre-rebuild"]["rendered_file"].endswith("cv-sep.pdf")

    change = await call(s, "resume_diff", {"a": "Sep pre-rebuild",
                                           "b": "Oct final"})
    assert change["removed"] == [
        "Grew revenue by 300% with a new data platform"], change
    assert change["changed"] == [{
        "before": "Wrote runbooks for ETL jobs",
        "after": "Wrote runbooks for the nightly ETL jobs"}], change
    assert "Mentored two analysts on SQL reviews" in change["added"]
    assert change["word_delta"] == (change["words"]["after"]
                                    - change["words"]["before"])
    assert change["checks"]["level_tags"] == {"before": 1, "after": 0,
                                              "now": []}
    missing = await call(s, "resume_diff", {"a": "Nope"})
    assert "error" in missing

    proof = await call(s, "resume_proof", {"a": "Sep pre-rebuild",
                                           "b": "Oct final"})
    md = proof["markdown"]
    assert "## Timeline" in md and "## Before and after" in md
    assert "(came back)" in md and "Oct branch" in md
    assert md.rstrip().endswith("Mentored two analysts on SQL reviews"), md
    assert "| Internal level tags | 1 | 0 |" in md, md
    assert proof["check"]["ok"], proof["check"]
    print("resume timeline: append-only snapshots, computed checks, "
          "branches and regressions visible, diff and proof: OK")


async def sponsorship_checks(s):
    blank = await call(s, "sponsorship_verify", {"company": "Vandelay"})
    assert blank["answer"] == "unstated" and blank["confidence"] == "low"
    assert len(blank["public_filings"]) == 2 and "recruiter" in blank["say"]
    vague = await call(s, "sponsorship_verify", {
        "company": "Vandelay",
        "posting_text": "Great team. Tell us about your work authorization."})
    assert vague["answer"] == "unstated", vague
    assert vague["evidence"][0]["signal"] == "unclear"
    for no in ("We are unable to sponsor visas for this role.",
               "You must be authorized to work in the US without "
               "sponsorship."):
        result = await call(s, "sponsorship_verify", {
            "company": "Vandelay", "posting_text": "Remote. " + no})
        assert result["answer"] == "no" and result["confidence"] == "high", \
            result
        assert result["evidence"][0]["quote"] == no
    app = await call(s, "application_log", {
        "company": "Vandelay", "role": "Importer", "status": "applied"})
    yes = await call(s, "sponsorship_verify", {
        "company": "Vandelay", "application_id": app["id"], "save": True,
        "posting_text": "Visa sponsorship is available for this role."})
    assert yes["answer"] == "yes" and yes["saved"]["sponsorship"] == "yes"
    await call(s, "application_log", {
        "company": "Vandelay", "role": "Exporter", "status": "applied",
        "sponsorship": "no"})
    mixed = await call(s, "sponsorship_verify", {
        "company": "Vandelay",
        "posting_text": "Visa sponsorship is available."})
    assert mixed["conflict"] and mixed["answer"] == "no", mixed
    print("sponsorship_verify: quoted evidence, unstated never becomes yes, "
          "conflicts raised, explicit answers saved: OK")


async def error_checks(s):
    stale = await s.call_tool("no_such_tool", {})
    assert stale.isError and \
        stale.content[0].text.startswith("[UNKNOWN_TOOL]"), stale.content
    bad = await s.call_tool("finance_dashboard",
                            {"monthly_burn": "Zanzibar-secret-77"})
    text = bad.content[0].text
    assert bad.isError and text.startswith("[BAD_ARGUMENTS]"), text
    assert "monthly_burn" in text and "Zanzibar" not in text, text
    print("stale tool and bad values get stable codes, not a crash: OK")
    crash = await s.call_tool("calendar_interviews",
                              {"events": [], "today": "31/12/Quokka"})
    text = crash.content[0].text
    assert crash.isError and text.startswith("[INTERNAL_ERROR]"), text
    assert "(ref " in text and "Quokka" not in text, text
    print("a fault inside a tool comes back as INTERNAL_ERROR with a ref, "
          "raw error hidden: OK")

    known = await call(s, "report_issue", {
        "error_code": "[INTERNAL_ERROR] Something went wrong (ref a1b2c3).",
        "tool_name": "job_search", "ref": "a1b2c3",
        "client_hint": "Claude desktop on Jordan's laptop"})
    assert known["known"] and known["code"] == "INTERNAL_ERROR"
    assert known["retry"] is True and known["ref"] == "a1b2c3"
    reconnect = await call(s, "report_issue", {"error_code": "UNKNOWN_TOOL"})
    assert reconnect["retry"] is False and "reconnect" in \
        reconnect["what_to_do"].lower()
    odd = await call(s, "report_issue", {"error_code": "WAT",
                                         "ref": "not a ref; DROP"})
    assert odd["known"] is False and "AUTH_REQUIRED" in odd["codes"]
    print("report_issue: known codes get a fix, unknown ones a fallback: OK")


async def main():
    shutil.rmtree(TEST_DIR, ignore_errors=True)
    fresh_database()
    os.makedirs(TEST_DIR)
    fixture = os.path.join(TEST_DIR, "boards.json")
    with open(fixture, "w", encoding="utf-8") as handle:
        json.dump(BOARD_FIXTURE, handle)
    env = {**os.environ, "COPILOT_DATA_DIR": TEST_DIR,
           "CAREER_COPILOT_JOBS_FIXTURE": fixture,
           "CAREER_COPILOT_HOME": os.path.join(TEST_DIR, "home"),
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
            await journey_checks(s)
            await fact_checks(s)
            await job_checks(s)
            await loop_checks(s)
            await evidence_checks(s)
            await watch_checks(s)
            await mirror_checks(s)
            await tailor_checks(s)
            await timeline_checks(s)
            await outreach_checks(s)
            await sponsorship_checks(s)
            await error_checks(s)
    with open(os.path.join(TEST_DIR, "logs", "mcp_server.log"),
              encoding="utf-8") as handle:
        log = handle.read()
    assert "jordan@acme.com" not in log and "can't go on" not in log
    assert "acc-secret-1" not in log and "4200" not in log, \
        "imported account data leaked into logs"
    print("emails, moods and imported accounts kept out of logs: OK")
    assert "practising Hindu" not in log, "checked text leaked into logs"
    assert "Lead with the number" not in log, "lesson text leaked into logs"
    assert "billing platform" not in log, "resume line leaked into logs"
    print("text sent to response_check kept out of logs: OK")
    assert "Zanzibar" not in log, "a bad argument's value leaked into logs"
    assert "Jordan's laptop" not in log, "client hint leaked into logs"
    assert "Wombat" not in log, "a file path leaked into logs"
    assert "Jordan@Acme" not in log and "keen to keep" not in log,         "outreach recipient or draft leaked into logs"
    assert "bad arguments: finance_dashboard: monthly_burn" in log, \
        "field name not logged"
    assert "issue reported: INTERNAL_ERROR job_search (ref a1b2c3)" in log
    print("errors log field names and refs only, never values: OK")
    shutil.rmtree(TEST_DIR, ignore_errors=True)
    print("ALL PASSED")


asyncio.run(main())
