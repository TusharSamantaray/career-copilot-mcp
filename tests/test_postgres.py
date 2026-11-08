"""Postgres storage: what the free hosted database must guarantee.

Runs only when DATABASE_URL points at a throwaway test database (it
drops Career Copilot's tables first). Without it, it says SKIPPED.
"""
import asyncio
import json
import os
import shutil
import subprocess
import sys

URL = os.environ.get("DATABASE_URL", "")
TEST_DIR = "./test_data_pg"


def reset():
    import psycopg
    with psycopg.connect(URL, autocommit=True) as conn:
        conn.execute("DROP TABLE IF EXISTS cc_records")
        conn.execute("DROP TABLE IF EXISTS cc_keys")
        conn.execute("DROP TABLE IF EXISTS cc_signals")


def store_checks():
    os.environ["CAREER_COPILOT_MASTER_KEY"] = "pg-test-master"
    sys.path.insert(0, os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    from copilot import store
    assert store.BACKEND.name == "postgres"
    rid = store.put("u_ana", "fact", {"statement": "Cut costs by 30%"})
    store.put("u_ben", "fact", {"statement": "Ben's fact"})
    assert store.get("u_ana", rid)["statement"] == "Cut costs by 30%"
    assert store.get("u_ben", rid) is None, "people's rows mixed"
    store.put("u_ana", "fact", {"statement": "Cut costs by 35%"},
              record_id=rid)
    assert [f["statement"] for f in store.list_kind("u_ana", "fact")] == \
        ["Cut costs by 35%"], "update didn't replace"
    import psycopg
    with psycopg.connect(URL) as conn:
        raw = [r[0] for r in conn.execute("SELECT body FROM cc_records")]
    assert all(r.startswith("enc:") for r in raw) and \
        "Cut costs" not in " ".join(raw), "plain text in the database"
    assert set(store.users()) == {"u_ana", "u_ben"}
    assert store.export_all("u_ana")["fact"][0]["id"] == rid
    assert store.delete("u_ana", rid) and store.get("u_ana", rid) is None
    store.put("u_ana", "goal", {"name": "Fund"})
    assert store.delete_all("u_ana") and not store.list_kind("u_ana", "goal")
    assert store.list_kind("u_ben", "fact"), "deleting ana hurt ben"
    print("postgres store: per person, encrypted, update, delete: OK")


def insights_checks():
    """Anonymous counts kept in the database when the owner opts in, so
    the weekly improver doesn't see an empty week after every restart."""
    os.environ["CAREER_COPILOT_INSIGHTS_STORE"] = "database"
    from copilot import insights
    assert insights.location() == "database"
    for n in range(5):
        insights.record("tool", "job_search", f"u_{n}", ok=n != 0, ms=12)
        insights.record("issue:INTERNAL_ERROR", "job_search", f"u_{n}",
                        ok=False)
    summary = insights.summary(7)
    json.dumps(summary)                       # must be JSON-safe
    assert summary["tools"][0]["tool"] == "job_search", summary
    assert summary["tools"][0]["success_rate"] == 0.8
    assert summary["labels"]["issue:INTERNAL_ERROR"][0]["users"] == 5
    insights.forget("u_0")
    assert "issue:INTERNAL_ERROR" not in insights.summary(7)["labels"],         "forget left a person's counts behind"
    import psycopg
    with psycopg.connect(URL) as conn:
        whos = [r[0] for r in conn.execute("SELECT who FROM cc_signals")]
    assert whos and not any(w.startswith("u_") for w in whos),         "raw ids stored"
    print("anonymous counts in the database: k-anonymous, hashed, "
          "forgettable: OK")


async def tool_call(env, name, args):
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    params = StdioServerParameters(command=sys.executable,
                                   args=["app.py", "--stdio"], env=env)
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as s:
            await s.initialize()
            result = await s.call_tool(name, args)
            return json.loads(result.content[0].text)


def survives_restart():
    """The free host wipes its disk on every restart. With Postgres the
    data lives elsewhere, so a fresh process with an empty disk sees it."""
    env = {**os.environ, "DATABASE_URL": URL,
           "CAREER_COPILOT_MASTER_KEY": "pg-test-master",
           "COPILOT_DATA_DIR": TEST_DIR,
           "CAREER_COPILOT_HOME": os.path.join(TEST_DIR, "home"),
           "CAREER_COPILOT_LOG_DIR": os.path.join(TEST_DIR, "logs")}
    asyncio.run(tool_call(env, "profile_save", {"target_role": "Analyst"}))
    shutil.rmtree(TEST_DIR, ignore_errors=True)            # the wipe
    profile = asyncio.run(tool_call(env, "profile_get", {}))
    assert profile.get("target_role") == "Analyst", profile
    assert not os.path.exists(os.path.join(TEST_DIR, "data")), \
        "records went to local files instead of Postgres"
    print("data survives a restart that wipes the disk: OK")


def logs_hide_the_url():
    env = {**os.environ, "DATABASE_URL": URL, "PORT": "8768",
           "HOST": "127.0.0.1", "CAREER_COPILOT_API_KEY": "pg-key",
           "COPILOT_DATA_DIR": TEST_DIR,
           "CAREER_COPILOT_LOG_DIR": os.path.join(TEST_DIR, "logs")}
    out = subprocess.run([sys.executable, "-c",
                          "import app; app.setup_logging(); app.log_startup()"],
                         env=env, capture_output=True, text=True, timeout=60)
    text = out.stdout + out.stderr
    assert "storage postgres (DATABASE_URL)" in text, text[-800:]
    assert URL not in text, "database URL printed"
    print("startup names the storage, never prints the URL: OK")


if __name__ == "__main__":
    if not URL:
        print("SKIPPED: set DATABASE_URL to a throwaway Postgres database")
        sys.exit(0)
    reset()
    store_checks()
    insights_checks()
    reset()
    survives_restart()
    logs_hide_the_url()
    reset()
    shutil.rmtree(TEST_DIR, ignore_errors=True)
    print("ALL PASSED")
