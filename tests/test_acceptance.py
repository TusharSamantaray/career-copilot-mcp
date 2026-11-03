"""Acceptance tests from Spec v2, as scripted conversations with a fresh
synthetic person each. Here: A (Lost)."""
import asyncio
import json
import os
import shutil
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

TEST_DIR = "./test_data_acceptance"


async def call(s, name, args=None):
    result = await s.call_tool(name, args or {})
    assert not result.isError, f"{name}: {result.content[0].text}"
    return json.loads(result.content[0].text)


async def lost(s):
    """A: "I don't know what I want", no resume. Within five questions:
    2 to 3 directions with reasons, one picked, and a saved profile with
    every line labelled confirmed or unsure."""
    questions = 0
    rules = await call(s, "ground_rules")
    assert not rules["accepted"]
    await call(s, "ground_rules", {"accept": True})

    state = await call(s, "journey_state")
    assert state["stage"] == "orient" and "question" in state["next"]
    questions += 1                                   # tell me, or ask me?

    state = await call(s, "journey_state")
    assert state["next"]["question"]["ask"]          # still the two doors
    await call(s, "profile_save", {"situation": "starting out"})
    questions += 1                                   # where are you now?
    state = await call(s, "journey_state")
    assert state["next"]["saves_to"] == "target_role"
    await call(s, "profile_save", {"skip": ["target_role"]})   # "not sure"
    questions += 1
    state = await call(s, "journey_state")
    assert state["next"]["saves_to"] == "current_role"
    await call(s, "profile_save", {"current_role": "Retail team lead",
                                   "domain_keywords": ["excel", "sql"],
                                   "unsure": ["domain_keywords"]})
    questions += 1

    # Something useful comes back now instead of a sixth question.
    state = await call(s, "journey_state")
    assert "use" in state["next"] and "question" not in state["next"], state
    assert state["next"]["use"] == "life_compass"
    compass = await call(s, "life_compass")
    await call(s, "life_compass", {
        "question": compass["next_question"]["number"],
        "answer": "Working with numbers and people",
        "save_as": "want"})
    questions += 1
    assert questions <= 5, questions

    options = await call(s, "direction_options", {})
    assert 2 <= len(options["options"]) <= 3, options
    for option in options["options"]:
        assert option["fit"] and option["first_test"] and option["risk"]
    picked = options["options"][0]["direction"]
    await call(s, "profile_save", {"target_role": picked})

    profile = await call(s, "profile_get")
    state = await call(s, "journey_state")
    labels = {k["field"]: k["confidence"] for k in state["known"]}
    assert labels["target_role"] == "confirmed"
    assert labels["domain_keywords"] == "unsure"
    assert all(v in ("confirmed", "unsure") for v in labels.values())
    assert "Working with numbers and people" in profile["wants"]
    assert state["stage"] != "orient", "a direction was chosen"
    print(f"A Lost: {questions} questions, {len(options['options'])} "
          f"directions, picked {picked!r}, every line labelled: OK")


async def main():
    shutil.rmtree(TEST_DIR, ignore_errors=True)
    env = {**os.environ, "COPILOT_DATA_DIR": TEST_DIR,
           "CAREER_COPILOT_HOME": os.path.join(TEST_DIR, "home"),
           "CAREER_COPILOT_LOG_DIR": os.path.join(TEST_DIR, "logs")}
    params = StdioServerParameters(command=sys.executable,
                                   args=["app.py", "--stdio"], env=env)
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as s:
            await s.initialize()
            await lost(s)
    shutil.rmtree(TEST_DIR, ignore_errors=True)
    print("ALL PASSED")


asyncio.run(main())
