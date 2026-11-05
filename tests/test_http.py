"""HTTP test: health check, API key enforcement, per-key data isolation."""
import asyncio
import os
import shutil
import subprocess
import sys
import time

import httpx
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport

PORT = 8765
BASE = f"http://127.0.0.1:{PORT}"
TEST_DIR = "./test_data_http"
KEYS = ["key-alice-test", "key-bob-test"]
ADMIN = "admin-key-test"


def client(key=None):
    headers = {"Authorization": f"Bearer {key}"} if key else {}
    return Client(StreamableHttpTransport(f"{BASE}/mcp", headers=headers))


async def main():
    async with client() as anon:
        try:
            await anon.call_tool("profile_get", {})
            raise AssertionError("call without a key was allowed")
        except AssertionError:
            raise
        except Exception as exc:
            assert "Unauthorized" in str(exc), exc
            assert "[AUTH_REQUIRED]" in str(exc), exc
    print("no key rejected, with a stable error code: OK")

    async with client("wrong-key") as bad:
        try:
            await bad.call_tool("profile_get", {})
            raise AssertionError("call with a wrong key was allowed")
        except AssertionError:
            raise
        except Exception as exc:
            assert "Unauthorized" in str(exc), exc
    print("wrong key rejected: OK")

    async with client(KEYS[0]) as alice:
        await alice.call_tool("profile_save", {"target_role": "Staff SRE"})
        profile = (await alice.call_tool("profile_get", {})).data
        assert profile["target_role"] == "Staff SRE"
        pipe = await alice.read_resource("copilot://pipeline")
        assert "applications" in pipe[0].text
    print("valid key works, resource readable: OK")

    async with client(KEYS[1]) as bob:
        profile = (await bob.call_tool("profile_get", {})).data
        assert "note" in profile, "bob can see alice's data"
    print("keys are isolated: OK")

    # claude.ai and ChatGPT put the key in the URL instead of a header.
    url = Client(StreamableHttpTransport(f"{BASE}/mcp?key={KEYS[1]}"))
    async with url as bob:
        profile = (await bob.call_tool("profile_get", {})).data
        assert "note" in profile
    bad_url = Client(StreamableHttpTransport(f"{BASE}/mcp?key=wrong"))
    async with bad_url as bad:
        try:
            await bad.call_tool("profile_get", {})
            raise AssertionError("wrong key in the URL was allowed")
        except AssertionError:
            raise
        except Exception as exc:
            assert "Unauthorized" in str(exc), exc
    print("key in the URL works, wrong one rejected: OK")

    # Self-improvement signals: k-anonymous, scrubbed, admin-only.
    async with client(KEYS[0]) as alice:
        await alice.call_tool("skills_gap", {"target_role": "Pastry Chef"})
        await alice.call_tool("feedback", {
            "tool": "skills_gap", "helpful": False, "reason": "missing_role",
            "missing_role": "jane@example.com"})
    assert httpx.get(f"{BASE}/insights").status_code == 401
    assert httpx.get(f"{BASE}/insights", headers={
        "Authorization": "Bearer wrong"}).status_code == 401
    admin = {"Authorization": f"Bearer {ADMIN}"}
    one_user = httpx.get(f"{BASE}/insights", headers=admin).json()
    assert "unmet_role" not in one_user["labels"], "k-anonymity broken"
    async with client(KEYS[1]) as bob:
        await bob.call_tool("skills_gap", {"target_role": "pastry chef"})
    report = httpx.get(f"{BASE}/insights", headers=admin).json()
    roles = [r["label"] for r in report["labels"]["unmet_role"]]
    assert roles == ["pastry chef"], report
    text = str(report)
    assert "jane" not in text and "example.com" not in text, "PII leaked"
    assert "key-alice" not in text
    print("insights: admin-only, k-anonymous, scrubbed: OK")


def run():
    shutil.rmtree(TEST_DIR, ignore_errors=True)
    env = {**os.environ, "PORT": str(PORT), "HOST": "127.0.0.1",
           "CAREER_COPILOT_API_KEY": ",".join(KEYS),
           "CAREER_COPILOT_ADMIN_KEY": ADMIN, "CAREER_COPILOT_K_ANON": "2",
           "CAREER_COPILOT_INSIGHTS_SALT": "test-salt",
           "COPILOT_DATA_DIR": TEST_DIR,
           "CAREER_COPILOT_LOG_DIR": os.path.join(TEST_DIR, "logs")}
    os.makedirs(TEST_DIR, exist_ok=True)
    console_path = os.path.join(TEST_DIR, "console.txt")
    console = open(console_path, "w", encoding="utf-8")
    server = subprocess.Popen([sys.executable, "app.py"], env=env,
                              stdout=console, stderr=subprocess.STDOUT)
    try:
        for _ in range(60):
            try:
                if httpx.get(f"{BASE}/health").status_code == 200:
                    break
            except httpx.TransportError:
                time.sleep(0.25)
        else:
            raise RuntimeError("server did not start")
        health = httpx.get(f"{BASE}/health").json()
        assert health["storage"] in ("sqlite", "postgres"), health
        print("health: OK")
        asyncio.run(main())
        log = os.path.join(TEST_DIR, "logs", "mcp_server.log")
        with open(log, encoding="utf-8") as handle:
            text = handle.read()
        assert "tool done: profile_save in" in text
        assert "key-alice-test" not in text, "API key leaked into logs"
        server.terminate()
        server.wait(timeout=10)
        console.close()
        with open(console_path, encoding="utf-8", errors="replace") as handle:
            printed = handle.read()
        assert "Career Copilot" in printed, "console output not captured"
        assert "key-bob-test" not in printed, "URL key leaked to the console"
        print("log file written, no keys in it or on the console: OK")
    finally:
        server.terminate()
        server.wait(timeout=10)
        console.close()
        shutil.rmtree(TEST_DIR, ignore_errors=True)
    print("ALL PASSED")


if __name__ == "__main__":
    run()
