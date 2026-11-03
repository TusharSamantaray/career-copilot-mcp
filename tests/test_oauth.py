"""GitHub sign-in mode: plain /mcp URL, nothing works without signing in,
and claude.ai / ChatGPT can discover where to sign in. Uses fake GitHub
app credentials, so no real sign-in happens."""
import os
import shutil
import subprocess
import sys
import time

import httpx

PORT = 8766
BASE = f"http://127.0.0.1:{PORT}"
TEST_DIR = "./test_data_oauth"
INIT = {"jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                   "clientInfo": {"name": "test", "version": "0"}}}
MCP_HEADERS = {"Accept": "application/json, text/event-stream"}


def checks():
    assert httpx.get(f"{BASE}/health").json()["status"] == "ok"
    print("health open without sign-in: OK")

    anon = httpx.post(f"{BASE}/mcp", json=INIT, headers=MCP_HEADERS)
    assert anon.status_code == 401, anon.status_code
    assert "resource_metadata" in anon.headers.get("www-authenticate", "")
    keyed = httpx.post(f"{BASE}/mcp", json=INIT, headers={
        **MCP_HEADERS, "Authorization": "Bearer key-old-style"})
    assert keyed.status_code == 401, "API keys must not work in sign-in mode"
    url_key = httpx.post(f"{BASE}/mcp?key=key-old-style", json=INIT,
                         headers=MCP_HEADERS)
    assert url_key.status_code == 401, "keys in the URL must not work"
    print("no sign-in, old keys and URL keys all refused: OK")

    meta = httpx.get(f"{BASE}/.well-known/oauth-authorization-server")
    assert meta.status_code == 200, meta.status_code
    body = meta.json()
    assert body.get("registration_endpoint"), "apps can't self-register"
    assert body["authorization_endpoint"].startswith(BASE)
    print("sign-in discoverable, apps can register themselves: OK")


def run():
    shutil.rmtree(TEST_DIR, ignore_errors=True)
    os.makedirs(TEST_DIR, exist_ok=True)
    env = {**os.environ, "PORT": str(PORT), "HOST": "127.0.0.1",
           "CAREER_COPILOT_GITHUB_CLIENT_ID": "fake-client-id",
           "CAREER_COPILOT_GITHUB_CLIENT_SECRET": "fake-client-secret",
           "CAREER_COPILOT_PUBLIC_URL": BASE,
           "CAREER_COPILOT_JWT_KEY": "test-jwt-key",
           "CAREER_COPILOT_API_KEY": "key-old-style",
           "COPILOT_DATA_DIR": TEST_DIR,
           "CAREER_COPILOT_LOG_DIR": os.path.join(TEST_DIR, "logs")}
    console_path = os.path.join(TEST_DIR, "console.txt")
    console = open(console_path, "w", encoding="utf-8")
    server = subprocess.Popen([sys.executable, "app.py"], env=env,
                              stdout=console, stderr=subprocess.STDOUT)
    try:
        for _ in range(80):
            try:
                if httpx.get(f"{BASE}/health").status_code == 200:
                    break
            except httpx.TransportError:
                time.sleep(0.25)
        else:
            raise RuntimeError("server did not start")
        checks()
    finally:
        server.terminate()
        server.wait(timeout=10)
        console.close()
    with open(console_path, encoding="utf-8", errors="replace") as handle:
        printed = handle.read()
    assert "GitHub sign-in (anyone)" in printed, printed[-1500:]
    assert "fake-client-secret" not in printed, "secret printed"
    print("startup says GitHub sign-in, secret never printed: OK")
    shutil.rmtree(TEST_DIR, ignore_errors=True)
    print("ALL PASSED")


if __name__ == "__main__":
    run()
