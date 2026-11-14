"""Proficiency tiers over stdio: evidence in, tiers computed out.

Synthetic data only, one made-up person. Checks the issue #18 rules:
a tier per dimension with the evidence behind it, tiers computed from
verified evidence only, no self-typed ratings, no game words anywhere.
"""
import asyncio
import json
import os
import re
import shutil
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

TEST_DIR = "./test_data_proficiency"
NEW_TOOLS = {"proficiency_evidence_add", "proficiency_evidence_list",
             "proficiency_evidence_remove", "proficiency_get"}
BANNED = re.compile(r"\b(level|levels|xp|points|badge|badges|achievement"
                    r"|achievements|rank|ranking|unlock|grind|quest)\b", re.I)
TIER_KEYS = {"dimension", "label", "tier", "tier_index", "verified",
             "pending", "evidence", "pending_evidence", "next_tier",
             "verified_needed"}


async def call(session, name, args=None):
    result = await session.call_tool(name, args or {})
    assert not result.isError, f"{name}: {result.content[0].text}"
    text = result.content[0].text if result.content else "null"
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def tiers(view):
    return {row["dimension"]: row for row in view["tiers"]}


async def main():
    shutil.rmtree(TEST_DIR, ignore_errors=True)
    env = {**os.environ, "COPILOT_DATA_DIR": TEST_DIR,
           "CAREER_COPILOT_LOG_DIR": os.path.join(TEST_DIR, "logs")}
    params = StdioServerParameters(
        command=sys.executable, args=["app.py", "--stdio"], env=env)
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as s:
            await s.initialize()
            names = {t.name for t in (await s.list_tools()).tools}
            print("tools:", len(names))
            assert NEW_TOOLS <= names, NEW_TOOLS - names
            assert len(names) == 109, len(names)

            # A new person starts at Foundational everywhere.
            fresh = await call(s, "proficiency_get")
            assert all(row["tier"] == "Foundational"
                       for row in fresh["tiers"]), fresh
            assert all(TIER_KEYS <= set(row) for row in fresh["tiers"])
            assert fresh["verified_total"] == 0
            print("fresh person: all Foundational: OK")

            # Bad input is refused, with the allowed values named.
            assert "error" in await call(s, "proficiency_evidence_add", {
                "title": "x", "kind": "trophy", "dimensions": ["domain"]})
            assert "error" in await call(s, "proficiency_evidence_add", {
                "title": "x", "kind": "design_doc",
                "dimensions": ["charisma"]})
            assert "error" in await call(s, "proficiency_evidence_add", {
                "title": "x", "kind": "design_doc", "dimensions": [],
                })
            assert "error" in await call(s, "proficiency_evidence_add", {
                "title": "", "kind": "design_doc",
                "dimensions": ["domain"]})
            assert "error" in await call(s, "proficiency_evidence_add", {
                "title": "x", "kind": "design_doc",
                "dimensions": ["domain"], "verification": "pinkie-swear"})
            assert "error" in await call(s, "proficiency_evidence_list",
                                        {"dimension": "charisma"})
            print("bad input refused: OK")

            # One verified item moves its dimensions to Developing.
            first = await call(s, "proficiency_evidence_add", {
                "title": "Notification system, 6 countries",
                "kind": "shipped_system", "dimensions": ["domain", "scope"],
                "topics": ["Distributed Systems"],
                "source": "github.com/example/notify",
                "verification": "verified"})
            assert first["tiers"] == {"domain": "Developing",
                                      "scope": "Developing"}, first
            assert "tier" not in first["recorded"], first
            view = await call(s, "proficiency_get")
            row = tiers(view)["domain"]
            assert row["tier"] == "Developing" and row["verified"] == 1
            assert row["evidence"][0]["id"] == first["id"]
            assert row["next_tier"] == "Proficient"
            assert row["verified_needed"] == 2
            assert tiers(view)["stack_depth"]["tier"] == "Foundational"
            print("1 verified item: Developing, evidence behind it: OK")

            # Submitted and corroborated items never move a tier.
            await call(s, "proficiency_evidence_add", {
                "title": "Design doc: exactly-once events",
                "kind": "design_doc", "dimensions": ["domain"]})
            await call(s, "proficiency_evidence_add", {
                "title": "Peer review: on-call handover",
                "kind": "peer_review", "dimensions": ["domain"],
                "verification": "corroborated"})
            view = await call(s, "proficiency_get")
            row = tiers(view)["domain"]
            assert row["tier"] == "Developing" and row["verified"] == 1
            assert row["pending"] == 2
            assert view["pending_total"] == 2
            assert view["verified_from"] == {"shipped_system": 1}
            print("unverified items listed as pending, tiers unmoved: OK")

            # Thresholds: 3 verified Proficient, 6 Advanced, 9 Expert.
            ids = [first["id"]]
            for n in range(2, 10):
                added = await call(s, "proficiency_evidence_add", {
                    "title": f"Design doc {n}: event pipeline",
                    "kind": "design_doc", "dimensions": ["domain"],
                    "verification": "verified"})
                ids.append(added["id"])
                row = tiers(await call(s, "proficiency_get"))["domain"]
                want = ("Developing" if n < 3 else "Proficient" if n < 6
                        else "Advanced" if n < 9 else "Expert")
                assert row["tier"] == want, (n, row["tier"])
                assert row["verified"] == n
            view = await call(s, "proficiency_get")
            row = tiers(view)["domain"]
            assert row["tier"] == "Expert" and row["next_tier"] == ""
            assert [e["id"] for e in row["evidence"]] == ids
            assert view["verified_from"] == {"shipped_system": 1,
                                             "design_doc": 8}
            print("thresholds 1/3/6/9: Developing to Expert: OK")

            # Listing and filters.
            listed = await call(s, "proficiency_evidence_list")
            assert listed["count"] == 11, listed["count"]
            only_docs = await call(s, "proficiency_evidence_list",
                                   {"kind": "design_doc"})
            assert only_docs["count"] == 9
            pending = await call(s, "proficiency_evidence_list",
                                 {"verification": "submitted"})
            assert pending["count"] == 1
            print("list + filters: OK")

            # Removing evidence drops the tier back: it is computed,
            # never stored.
            removed = await call(s, "proficiency_evidence_remove",
                                 {"evidence_id": ids[-1]})
            assert removed["removed"]
            row = tiers(await call(s, "proficiency_get"))["domain"]
            assert row["tier"] == "Advanced" and row["verified"] == 8
            gone = await call(s, "proficiency_evidence_remove",
                              {"evidence_id": "no-such-id"})
            assert not gone["removed"] and "error" in gone
            print("remove recomputes tiers: OK")

            # No game words anywhere in what the tools return.
            blob = json.dumps(await call(s, "proficiency_get"))
            assert not BANNED.search(blob), BANNED.search(blob).group(0)
            blob = json.dumps(await call(s, "proficiency_evidence_list"))
            assert not BANNED.search(blob), BANNED.search(blob).group(0)
            print("no game words in output: OK")
    shutil.rmtree(TEST_DIR, ignore_errors=True)
    print("ALL PASSED")


asyncio.run(main())
