"""GitHub sign-in mode, end to end, against a fake GitHub.

Checks: plain /mcp URL, nothing works without signing in, apps can find
and register for sign-in, a full sign-in works, and (the free-host case)
the same sign-in still works after a restart that wipes the disk.
"""
import asyncio
import base64
import hashlib
import json
import os
import secrets
import shutil
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

import httpx
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport

PORT = 8766
GH_PORT = 8767
BASE = f"http://127.0.0.1:{PORT}"
TEST_DIR = "./test_data_oauth"
APP_REDIRECT = "http://127.0.0.1:9/callback"
INIT = {"jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                   "clientInfo": {"name": "test", "version": "0"}}}
MCP_HEADERS = {"Accept": "application/json, text/event-stream"}
USERS = {"good-code": {"id": 4242, "login": "octo-tester"},
         "stranger-code": {"id": 777, "login": "not-invited"}}


class FakeGitHub(BaseHTTPRequestHandler):
    """Just enough of GitHub: code -> token -> user."""

    def _send(self, status, body):
        data = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        form = parse_qs(self.rfile.read(length).decode())
        code = form.get("code", [""])[0]
        assert form.get("client_secret") == ["fake-client-secret"]
        if code == "garbled-code":              # e.g. an outage or a proxy page
            data = b"<html>upstream error</html>"
            self.send_response(200)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        elif code in USERS:
            self._send(200, {"access_token": f"gho_{code}"})
        else:
            self._send(200, {"error": "bad_verification_code"})

    def do_GET(self):
        token = self.headers.get("Authorization", "").split()[-1]
        code = token.replace("gho_", "")
        self._send(200, USERS[code]) if code in USERS else \
            self._send(401, {"message": "Bad credentials"})

    def log_message(self, *args):
        pass


def start_server(console):
    env = {**os.environ, "PORT": str(PORT), "HOST": "127.0.0.1",
           "CAREER_COPILOT_GITHUB_CLIENT_ID": "fake-client-id",
           "CAREER_COPILOT_GITHUB_CLIENT_SECRET": "fake-client-secret",
           "CAREER_COPILOT_PUBLIC_URL": BASE,
           "CAREER_COPILOT_JWT_KEY": "test-jwt-key",
           "CAREER_COPILOT_ALLOWED_GITHUB_USERS": "Octo-Tester",
           "CAREER_COPILOT_GITHUB_BASE": f"http://127.0.0.1:{GH_PORT}",
           "CAREER_COPILOT_GITHUB_API": f"http://127.0.0.1:{GH_PORT}",
           "CAREER_COPILOT_API_KEY": "key-old-style",
           # The fake GitHub is local: never send it through a proxy.
           "NO_PROXY": "127.0.0.1,localhost", "no_proxy": "127.0.0.1,localhost",
           "COPILOT_DATA_DIR": TEST_DIR,
           "CAREER_COPILOT_LOG_DIR": os.path.join(TEST_DIR, "logs")}
    server = subprocess.Popen([sys.executable, "app.py"], env=env,
                              stdout=console, stderr=subprocess.STDOUT)
    for _ in range(80):
        try:
            if httpx.get(f"{BASE}/health").status_code == 200:
                return server
        except httpx.TransportError:
            time.sleep(0.25)
    server.terminate()
    raise RuntimeError("server did not start")


def stop(server):
    server.terminate()
    server.wait(timeout=10)


def sign_in(github_code):
    """Do what claude.ai does: register, authorize, GitHub, token."""
    meta = httpx.get(f"{BASE}/.well-known/oauth-authorization-server").json()
    reg = httpx.post(meta["registration_endpoint"], json={
        "client_name": "test app", "redirect_uris": [APP_REDIRECT],
        "grant_types": ["authorization_code", "refresh_token"],
        "response_types": ["code"],
        "token_endpoint_auth_method": "client_secret_post"})
    assert reg.status_code == 201, reg.text
    app_client = reg.json()
    verifier = secrets.token_urlsafe(48)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(
        verifier.encode()).digest()).decode().rstrip("=")
    go = httpx.get(meta["authorization_endpoint"], params={
        "response_type": "code", "client_id": app_client["client_id"],
        "redirect_uri": APP_REDIRECT, "state": "app-state",
        "code_challenge": challenge, "code_challenge_method": "S256"})
    assert go.status_code == 302, go.text
    to_github = urlparse(go.headers["location"])
    assert to_github.netloc == f"127.0.0.1:{GH_PORT}"
    state = parse_qs(to_github.query)["state"][0]
    back = httpx.get(f"{BASE}/auth/callback",
                     params={"code": github_code, "state": state})
    if back.status_code != 302:
        return app_client, None, back
    to_app = urlparse(back.headers["location"])
    query = parse_qs(to_app.query)
    assert f"{to_app.scheme}://{to_app.netloc}{to_app.path}" == APP_REDIRECT
    assert query["state"] == ["app-state"]
    token = httpx.post(meta["token_endpoint"], data={
        "grant_type": "authorization_code", "code": query["code"][0],
        "redirect_uri": APP_REDIRECT, "client_id": app_client["client_id"],
        "client_secret": app_client["client_secret"],
        "code_verifier": verifier})
    assert token.status_code == 200, token.text
    return app_client, token.json(), back


async def use(access_token, save=None):
    transport = StreamableHttpTransport(
        f"{BASE}/mcp", headers={"Authorization": f"Bearer {access_token}"})
    async with Client(transport) as c:
        if save:
            await c.call_tool("profile_save", {"target_role": save})
        return (await c.call_tool("profile_get", {})).data


def first_run():
    health = httpx.get(f"{BASE}/health").json()
    assert health["status"] == "ok" and health["auth_mode"] == "github-oauth"
    assert health["invite_only"] is True and health["tool_count"] > 0
    assert "octo" not in json.dumps(health).lower(), "invitees leaked"
    print("/health says GitHub sign-in, invite-only, no names: OK")
    anon = httpx.post(f"{BASE}/mcp", json=INIT, headers=MCP_HEADERS)
    assert anon.status_code == 401
    assert "resource_metadata" in anon.headers.get("www-authenticate", "")
    for bad in ({"Authorization": "Bearer key-old-style"},
                {"Authorization": "Bearer not-a-token"}):
        assert httpx.post(f"{BASE}/mcp", json=INIT, headers={
            **MCP_HEADERS, **bad}).status_code == 401
    assert httpx.post(f"{BASE}/mcp?key=key-old-style", json=INIT,
                      headers=MCP_HEADERS).status_code == 401
    print("no sign-in, old keys, URL keys and junk tokens refused: OK")

    _, _, denied = sign_in("stranger-code")
    assert denied.status_code == 403 and "invite-only" in denied.text
    print("GitHub user not on the invite list is turned away: OK")

    _, _, garbled = sign_in("garbled-code")
    assert garbled.status_code == 502, garbled.status_code
    assert "Couldn't reach GitHub" in garbled.text
    print("GitHub answering with garbage gives a clear page, not a crash: OK")

    app_client, tokens, _ = sign_in("good-code")
    profile = asyncio.run(use(tokens["access_token"], save="Staff SRE"))
    assert profile["target_role"] == "Staff SRE"
    print("full sign-in: register, GitHub, code, token, tools: OK")
    return app_client, tokens


def after_restart(app_client, tokens):
    # The free host wipes its disk on restart: the same token must work.
    profile = asyncio.run(use(tokens["access_token"]))
    assert "note" in profile, "data dir was wiped, so no profile expected"
    meta = httpx.get(f"{BASE}/.well-known/oauth-authorization-server").json()
    fresh = httpx.post(meta["token_endpoint"], data={
        "grant_type": "refresh_token",
        "refresh_token": tokens["refresh_token"],
        "client_id": app_client["client_id"],
        "client_secret": app_client["client_secret"]})
    assert fresh.status_code == 200, fresh.text
    asyncio.run(use(fresh.json()["access_token"]))
    tampered = tokens["access_token"][:-4] + "AAAA"
    assert httpx.post(f"{BASE}/mcp", json=INIT, headers={
        **MCP_HEADERS, "Authorization": f"Bearer {tampered}"}
    ).status_code == 401
    print("after a restart that wiped the disk: same sign-in and refresh "
          "still work, tampered token refused: OK")


def run():
    shutil.rmtree(TEST_DIR, ignore_errors=True)
    os.makedirs(TEST_DIR, exist_ok=True)
    github = HTTPServer(("127.0.0.1", GH_PORT), FakeGitHub)
    threading.Thread(target=github.serve_forever, daemon=True).start()
    console_path = os.path.join(TEST_DIR, "..", "test_oauth_console.txt")
    console = open(console_path, "w", encoding="utf-8")
    try:
        server = start_server(console)
        try:
            app_client, tokens = first_run()
        finally:
            stop(server)
        shutil.rmtree(TEST_DIR, ignore_errors=True)      # the wipe
        os.makedirs(TEST_DIR, exist_ok=True)
        server = start_server(console)
        try:
            after_restart(app_client, tokens)
        finally:
            stop(server)
    finally:
        console.close()
        github.shutdown()
    with open(console_path, encoding="utf-8", errors="replace") as handle:
        printed = handle.read()
    os.remove(console_path)
    assert "GitHub sign-in (1 invited)" in printed, printed[-1500:]
    for secret in ("fake-client-secret", "gho_good-code", "test-jwt-key"):
        assert secret not in printed, f"{secret} printed"
    print("startup says GitHub sign-in, no secrets printed: OK")
    shutil.rmtree(TEST_DIR, ignore_errors=True)
    print("ALL PASSED")


if __name__ == "__main__":
    run()
