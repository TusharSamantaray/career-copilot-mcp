"""End-to-end test over stdio MCP with synthetic data."""
import asyncio
import json
import os
import shutil
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

TEST_DIR = "./test_data"
GOOD = (
    "Alex Example | Senior Software Engineer\n"
    "alex@example.com\n\n"
    "Senior backend engineer building event-driven systems. Designed "
    "and owned a messaging platform used by many teams. Cut cloud cost "
    "and shipped reliable services with strong testing habits and "
    "clear ownership across several quarters of delivery work.\n\n"
    "- Designed an event pipeline that updates records in under 3 "
    "seconds\n"
    "- Built a scheduler in 3 weeks against a 6 month estimate\n"
    "- Led 4 launches across 4 countries\n"
)
BAD = "I utilize synergies — cutting-edge things.\n- did stuff\n"


async def call(session, name, args=None):
    result = await session.call_tool(name, args or {})
    text = result.content[0].text if result.content else "null"
    return json.loads(text)


async def main():
    shutil.rmtree(TEST_DIR, ignore_errors=True)
    env = {**os.environ, "COPILOT_DATA_DIR": TEST_DIR}
    params = StdioServerParameters(
        command=sys.executable, args=["app.py", "--stdio"], env=env)
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print("tools:", len(tools.tools))
            prompts = await session.list_prompts()
            print("prompts:", [p.name for p in prompts.prompts])
            rubric = await session.read_resource("copilot://rubric")
            print("rubric ok:", "density" in rubric.contents[0].text)
            assert "density" in rubric.contents[0].text

            await call(session, "profile_save", {
                "target_role": "Senior Backend", "level": "senior"})
            print("profile:", (await call(session, "profile_get"))
                  ["target_role"])

            await call(session, "experience_add", {
                "employer": "ExampleCo", "title": "Engineer II",
                "start": "2022", "end": "2026",
                "fact": "Built a scheduler in 3 weeks",
                "confirmed": True})
            await call(session, "experience_add", {
                "employer": "ExampleCo", "title": "Engineer II",
                "start": "2022", "end": "2026",
                "fact": "Saved 90% cost (unsure)", "confirmed": False})
            draft = await session.call_tool("resume_build_draft", {})
            draft_text = draft.content[0].text
            assert "unsure" not in draft_text, "unconfirmed leaked"
            assert "[Check: ok.]" in draft_text, draft_text
            print("draft excludes unconfirmed: OK")

            good = await call(session, "resume_score",
                              {"resume_text": GOOD})
            bad = await call(session, "resume_score",
                             {"resume_text": BAD})
            print("score good/bad:", good["score"], bad["score"])
            assert good["score"] > bad["score"]
            print("top fix (bad):", bad["top_fix"])

            app = await call(session, "application_log", {
                "company": "Acme", "role": "SMTS", "status": "assessment",
                "next_action": "HackerRank", "due_date": "2026-11-03"})
            await call(session, "application_log", {
                "company": "Globex", "role": "Senior", "status": "applied",
                "next_action": "Follow up", "due_date": "2026-10-30"})
            digest = await call(session, "pipeline_digest",
                                {"today": "2026-11-02"})
            print("digest:", digest["overdue"], digest["due_within_3_days"])
            assert len(digest["overdue"]) == 1
            await call(session, "application_update", {
                "application_id": app["id"], "status": "interviewing"})

            runway = await call(session, "runway_calc", {
                "last_working_day": "2026-09-22",
                "payroll_end": "2026-11-14", "grace_days": 60,
                "today": "2026-11-02"})
            print("runway:", runway["days_of_pay_left"],
                  runway["grace_period_end"],
                  runway["days_to_hard_deadline"])
            assert runway["grace_period_end"] == "2027-01-13"

            refused = await call(session, "data_delete")
            assert refused["deleted"] is False
            export = await call(session, "data_export")
            print("export counts:", {k: len(v) for k, v in
                                     export.items()})
            done = await call(session, "data_delete", {"confirm": True})
            print("deleted:", done["deleted"])
    shutil.rmtree(TEST_DIR, ignore_errors=True)
    print("ALL PASSED")


asyncio.run(main())
