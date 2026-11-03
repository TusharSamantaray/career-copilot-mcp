"""Validates the knowledge base. Runs on every change, including the
weekly automated improvements, so a bad edit can't ship.

Checks: every entry is well-formed, cross-references resolve, guides keep
their disclaimers, and no knowledge file contains personal data.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from copilot.knowledge import ats, careers, connect, money, patterns, system_design  # noqa: E402

FAILURES = []


def check(cond, msg):
    if not cond:
        FAILURES.append(msg)


def roles():
    for key, role in careers.ROLES.items():
        check(re.fullmatch(r"[a-z_]+", key), f"role id {key!r} not snake_case")
        for field in ("title", "family", "core", "edge", "loop"):
            check(field in role, f"role {key} missing {field}")
        check(len(role.get("core", [])) >= 5, f"role {key}: <5 core skills")
        check(len(role.get("loop", [])) >= 2, f"role {key}: <2 loop stages")
        for skill in role.get("core", []) + role.get("edge", []):
            check(skill == skill.lower(), f"role {key}: skill {skill!r} "
                  "must be lowercase")
    for key, nexts in careers.ADJACENT.items():
        check(key in careers.ROLES, f"ADJACENT has unknown role {key}")
        for n in nexts:
            check(n in careers.ROLES, f"ADJACENT[{key}] -> unknown {n}")
            check(n != key, f"ADJACENT[{key}] points to itself")
    missing = set(careers.ROLES) - set(careers.ADJACENT)
    check(not missing, f"roles with no ADJACENT entry: {sorted(missing)}")
    for level in careers.LEVELS:
        check(level in careers.RESUME_SECTIONS, f"no sections for {level}")
        check(level in careers.SECTION_FOCUS, f"no focus for {level}")
    q = careers.CONTRIBUTION_FRAMEWORK["questions"]
    check(set(q) == {"ownership", "artifact", "scale", "result"},
          "contribution questions must cover the 4 checked parts")


def ats_content():
    for frag, name in ats.PLATFORMS.items():
        check(name in ats.QUIRKS, f"platform {name} ({frag}) has no quirks")
    check("unknown" in ats.QUIRKS, "no fallback quirks for unknown systems")
    for name in ats.STRICT_PARSERS:
        check(name in ats.QUIRKS, f"strict parser {name} has no quirks")
    for kind, patterns_ in ats.KNOCKOUTS.items():
        for p in patterns_:
            try:
                re.compile(p)
            except re.error:
                check(False, f"knock-out pattern for {kind} is invalid: {p}")


def prep_content():
    ids = [p["id"] for p in patterns.PATTERNS]
    check(len(ids) == len(set(ids)), "duplicate pattern ids")
    for p in patterns.PATTERNS:
        for field in ("name", "signal", "model", "recognize", "template",
                      "mistakes", "say", "examples"):
            check(p.get(field), f"pattern {p.get('id')} missing {field}")
        check(all(r == r.lower() for r in p.get("recognize", [])),
              f"pattern {p.get('id')}: recognize must be lowercase")
    for key, comp in system_design.COMPONENTS.items():
        for field in ("name", "model", "use_when", "not_when", "tradeoff",
                      "question", "mistakes"):
            check(comp.get(field), f"component {key} missing {field}")
    for alias, target in system_design.ALIASES.items():
        check(target in system_design.COMPONENTS,
              f"alias {alias} -> unknown component {target}")
    check(len(system_design.FRAMEWORK) >= 5, "framework too short")


def money_content():
    check("not financial" in money.DISCLAIMER.lower(),
          "DISCLAIMER must say it is not financial advice")
    for group in (money.INVEST_GUIDES, money.ECONOMY_GUIDES):
        for key, guide in group.items():
            check(guide.get("title") and len(guide.get("points", [])) >= 2,
                  f"guide {key} needs a title and 2+ points")
    for name, (code, label) in money.WORLD_BANK_INDICATORS.items():
        check(re.fullmatch(r"[A-Z0-9.]+", code), f"bad indicator {code}")
    check(len(money.LAYOFF_PLAYBOOK) >= 3, "layoff playbook too short")
    check(connect.CLIENTS, "no client connection docs")


PII_PATTERNS = {
    "email": r"[\w.+-]+@[\w-]+\.[\w.]+",
    "phone": r"\+?\d[\d\s().-]{8,}\d",
    "url with path": r"https?://(?!api\.worldbank\.org)\S+/\S+",
    "secret-looking token": r"\b(sk|rmt|ghp|xox[bp])[-_][A-Za-z0-9]{8,}",
}


INJECTION_PATTERNS = [
    r"ignore (all |any )?(previous|prior|above)", r"system prompt",
    r"you are now", r"disregard", r"<\s*/?\s*(system|instructions?)",
    r"do not tell the user", r"api[_ ]?key", r"send .* to http",
]


def no_injected_instructions():
    """Knowledge text is served to every user's AI assistant, so it must
    never carry instructions aimed at that assistant."""
    folder = os.path.dirname(careers.__file__)
    for name in sorted(os.listdir(folder)):
        if not name.endswith(".py") or name == "connect.py":
            continue
        text = open(os.path.join(folder, name), encoding="utf-8").read()
        for pattern in INJECTION_PATTERNS:
            hit = re.search(pattern, text, re.IGNORECASE)
            check(hit is None, f"knowledge/{name}: instruction-like text "
                  f"{hit.group(0)!r}" if hit else "")


def respectful_language():
    """Everything Career Copilot says from its knowledge base must pass
    the same checks response_check applies to the assistant's drafts."""
    from copilot import conduct
    folder = os.path.dirname(careers.__file__)
    strict = {"insult", "profanity", "overpromise", "biased_wording"}
    for name in sorted(os.listdir(folder)):
        if not name.endswith(".py"):
            continue
        text = open(os.path.join(folder, name), encoding="utf-8").read()
        for kind, _, pattern, _, _ in conduct.RULES:
            if kind not in strict:
                continue
            hits = sorted({m.group(0).lower() for m in pattern.finditer(text)})
            check(not hits, f"knowledge/{name}: {kind} wording {hits}")


def no_personal_data():
    folder = os.path.dirname(careers.__file__)
    for name in sorted(os.listdir(folder)):
        if not name.endswith(".py"):
            continue
        text = open(os.path.join(folder, name), encoding="utf-8").read()
        for label, pattern in PII_PATTERNS.items():
            hit = re.search(pattern, text)
            check(hit is None, f"knowledge/{name}: looks like {label}: "
                  f"{hit.group(0)[:30] if hit else ''}")


if __name__ == "__main__":
    roles()
    ats_content()
    prep_content()
    money_content()
    no_personal_data()
    no_injected_instructions()
    respectful_language()
    if FAILURES:
        print("KNOWLEDGE CHECK FAILED")
        for f in FAILURES:
            print(" -", f)
        sys.exit(1)
    print(f"knowledge ok: {len(careers.ROLES)} roles, "
          f"{len(patterns.PATTERNS)} patterns, "
          f"{len(system_design.COMPONENTS)} components")
    print("ALL PASSED")
