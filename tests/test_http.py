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

    # Persona: Alice publishes; Bob, hiring, finds her work, not her.
    async with client(KEYS[0]) as alice:
        await alice.call_tool("profile_save", {"target_role":
                                               "Backend Engineer",
                                               "locations": ["Remote"]})
        await alice.call_tool("experience_add", {
            "employer": "Vandelay", "title": "Engineer", "start": "2020",
            "end": "2025", "confirmed": True, "owned_or_contributed":
            "owned", "fact": "Built Kafka consumers in Python for 2 million "
            "orders a day; email alice.v@vandelay.example"})
        preview = (await alice.call_tool("persona_publish", {})).data
        await alice.call_tool("persona_publish", {
            "accept": True, "preview_id": preview["preview_id"]})
        own = (await alice.call_tool("persona_search", {
            "posting_text": "Backend engineer: Kafka, Python"})).data
        assert not own["matches"], "people see themselves in search"
    async with client(KEYS[1]) as bob:
        found = (await bob.call_tool("persona_search", {
            "posting_text": "Senior backend engineer. Kafka, Python and "
                            "Postgres. Salary $150k - $180k.",
            "location": "Berlin"})).data
        assert len(found["matches"]) == 1, found
        card = found["matches"][0]
        text = str(found).lower()
        assert "vandelay" not in text and "alice" not in text, text
        assert "150" not in text and "salary" not in str(card).lower()
        assert {m["skill"] for m in card["matched"]} >= {"kafka", "python"}
        none = (await bob.call_tool("persona_search", {
            "posting_text": "Kafka, Python", "must_have": ["go"]})).data
        assert not none["matches"] and             none["filtered_out"]["missing_a_must_have"] == 1, none
        pid = card["persona_id"]
        ask = lambda q: bob.call_tool("persona_chat", {  # noqa: E731
            "persona_id": pid, "question": q})
        skill = (await ask("What have they built with Kafka?")).data
        assert "Kafka consumers" in skill["answer_from"][0]["text"], skill
        assert skill["answer_from"][0]["part"] == "owned"
        for q in ("What's their email?", "Which company do they work for?"):
            assert (await ask(q)).data["refused"] == "identity", q
        assert (await ask("What salary do they expect?")).data[
            "refused"] == "salary"
        go = (await ask("Any Go experience?")).data
        assert go["not_verified"] == ["go"] and not go["answer_from"], go
    async with client(KEYS[0]) as alice:
        await alice.call_tool("persona_unpublish", {})
    async with client(KEYS[1]) as bob:
        gone = (await bob.call_tool("persona_search", {
            "posting_text": "Kafka, Python"})).data
        assert not gone["matches"], "unpublished persona still found"
    print("persona search and chat across people: work shown, identity and "
          "salary refused, unpublish works: OK")

    # Demand: Bob's survey and searches feed Alice's pathway.
    async with client(KEYS[1]) as bob:
        questions = (await bob.call_tool("recruiter_survey", {})).data
        assert questions["version"] == "1" and len(
            questions["questions"]) == 3
        saved = (await bob.call_tool("recruiter_survey", {
            "company": "Globex", "answers": {
                "seeing_roles": "Lots of backend and data engineer roles",
                "skills_by_role": "Backend engineer: Kafka, Go and Postgres",
                "expectations": "Clear writing and on-call experience"}}
        )).data
        assert saved["role"] == "backend" and "go" in saved["skills"], saved
    async with client(KEYS[0]) as alice:
        digest = (await alice.call_tool("demand_digest",
                                        {"direction": "backend"})).data
        kafka = [d for d in digest["signals"] if d["skill"] == "kafka"]
        sources = {d["source"] for d in kafka}
        assert sources == {"survey v1", "persona searches"}, digest
        assert any("Globex" in d["who"] for d in kafka), kafka
        assert "alice" not in str(digest).lower()
        path = (await alice.call_tool("pathway_build",
                                      {"direction": "backend"})).data
        assert path["steps"] and all(
            "recruiter" in st["reason"] and "Backend" in st["reason"]
            for st in path["steps"]), path
        assert "kafka" in path["steps"][0]["step"]       # proves it already
        assert any("go" in st["step"] for st in path["steps"][1:]), path
        first = (await alice.call_tool("pathway_next", {})).data
        after = (await alice.call_tool("pathway_next", {"done": True})).data
        assert after["next"] != first["next"] and after["left"] ==             first["left"] - 1
        now = (await alice.call_tool("pathway_build",
                                     {"mode": "immediate"})).data
        assert now["options"][0]["direction"].startswith("Backend"), now
    print("survey, demand digest and pathways: counted, attributed, every "
          "step cites its reason: OK")

    # Introductions: identity only after both sides confirm.
    async with client(KEYS[0]) as alice:
        preview = (await alice.call_tool("persona_publish", {})).data
        pid = (await alice.call_tool("persona_publish", {
            "accept": True, "preview_id": preview["preview_id"]})).data[
            "persona_id"]
    async with client(KEYS[1]) as bob:
        await bob.call_tool("persona_chat", {"persona_id": pid,
                                             "question": "Kafka scale?"})
        rude = (await bob.call_tool("persona_intro", {
            "persona_id": pid, "company": "Globex", "role": "Backend",
            "message": "You'd be an idiot to say no."})).data
        assert rude["sent"] is False, rude
        sent = (await bob.call_tool("persona_intro", {
            "persona_id": pid, "company": "Globex",
            "role": "Senior Backend Engineer",
            "message": "Your Kafka work fits our order pipeline. Open to a "
                       "chat?"})).data
        first = (await bob.call_tool("identity_reveal", {
            "intro_id": sent["intro_id"], "confirm": True,
            "share": "Bob B, bob.b@globex.example"})).data
        assert first["revealed"] is False and "they_shared" not in first
        decline = (await bob.call_tool("persona_intro", {
            "persona_id": pid, "company": "Globex", "role": "Data Engineer",
            "message": "Also hiring for data. Interested?"})).data
    async with client(KEYS[0]) as alice:
        box = (await alice.call_tool("persona_intros", {})).data
        got = {r["intro_id"]: r for r in box["received"]}
        assert got[sent["intro_id"]]["company"] == "Globex"
        assert got[sent["intro_id"]]["screened_questions"] >= 1
        assert "bob.b@" not in str(box), "contact shown before both agree"
        no = (await alice.call_tool("identity_reveal", {
            "intro_id": decline["intro_id"], "confirm": False})).data
        assert no["status"] == "declined"
        yes = (await alice.call_tool("identity_reveal", {
            "intro_id": sent["intro_id"], "confirm": True,
            "share": "Alice V, alice.v@vandelay.example"})).data
        assert yes["revealed"] and yes["they_shared"].startswith("Bob B")
        assert yes["merit_screen"]["questions_before_intro"] >= 1
    async with client(KEYS[1]) as bob:
        seen = (await bob.call_tool("identity_reveal", {
            "intro_id": sent["intro_id"], "confirm": True,
            "share": "Bob B"})).data
        assert seen["they_shared"].startswith("Alice V"), seen
        late = (await bob.call_tool("identity_reveal", {
            "intro_id": decline["intro_id"], "confirm": True,
            "share": "Bob B"})).data
        assert late["revealed"] is False and "they_shared" not in late
    print("introductions: nothing shared until both confirm, declines "
          "stay closed, reveal noted after the screen: OK")

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
        handling = httpx.get(f"{BASE}/data-handling").json()
        assert handling["stored"] and handling["never_stored"], handling
        assert all({"what", "where", "kept_for", "who_can_read"}
                   <= set(row) for row in handling["stored"])
        print("data-handling statement readable before sign-in: OK")
        asyncio.run(main())
        log = os.path.join(TEST_DIR, "logs", "mcp_server.log")
        with open(log, encoding="utf-8") as handle:
            text = handle.read()
        assert "tool done: profile_save in" in text
        assert "key-alice-test" not in text, "API key leaked into logs"
        assert "alice.v@" not in text and "What salary" not in text \
            and "bob.b@" not in text and "order pipeline" not in text, \
            "persona fact or recruiter question leaked into logs"
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
