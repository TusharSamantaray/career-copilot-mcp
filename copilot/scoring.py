"""Ten-check resume rubric. Heuristic POC: 10 points per check."""
import re

BANNED_WORDS = [
    "utilize", "spearheaded", "leveraged", "synergies", "cutting-edge",
]
NUMBER_PATTERN = re.compile(r"\d[\d,.]*\s?(%|k|K|m|M|x|ms|s)?")
OWNERSHIP_VERBS = (
    "designed", "architected", "built", "owned", "led", "shipped",
    "launched", "created", "implemented",
)
SENIOR_WORDS = ("senior", "staff", "lead", "principal", "architect")


def _bullets(text):
    lines = [line.strip() for line in text.splitlines()]
    return [ln.lstrip("-*• ").strip() for ln in lines
            if ln.startswith(("-", "*", "•"))]


def score_resume(text):
    bullets = _bullets(text)
    words = text.split()
    first_lines = "\n".join(text.splitlines()[:6]).lower()
    with_numbers = [b for b in bullets if NUMBER_PATTERN.search(b)]
    with_owner = [b for b in bullets
                  if b.lower().startswith(OWNERSHIP_VERBS)]
    banned_hits = [w for w in BANNED_WORDS if w in text.lower()]
    long_bullets = [b for b in bullets if len(b.split()) > 35]
    ratio_numbers = len(with_numbers) / max(len(bullets), 1)
    ratio_owner = len(with_owner) / max(len(bullets), 1)

    checks = {
        "six_second_scan": (
            10 if bullets and len(text.splitlines()) > 5 else 4,
            "Name, title and top bullets visible in the first screen.",
        ),
        "role_clarity": (
            10 if "|" in first_lines or "engineer" in first_lines else 3,
            "A tagline that names the target role.",
        ),
        "quantified_impact": (
            round(10 * min(ratio_numbers / 0.6, 1)),
            f"{len(with_numbers)}/{len(bullets)} bullets carry a number.",
        ),
        "ownership": (
            round(10 * min(ratio_owner / 0.5, 1)),
            f"{len(with_owner)}/{len(bullets)} bullets open with an "
            "ownership verb.",
        ),
        "seniority": (
            10 if any(w in text.lower() for w in SENIOR_WORDS) else 4,
            "Seniority signal in title or scope.",
        ),
        "thesis": (
            10 if 40 <= len(text.split("\n\n")[0].split()) <= 90 else 5,
            "A 3-sentence summary of about 70 words.",
        ),
        "bullet_order": (
            7 if len(bullets) >= 3 else 3,
            "Strongest result first within each role (manual review).",
        ),
        "credibility": (
            10 - 3 * len(banned_hits),
            "Banned words found: " + (", ".join(banned_hits) or "none"),
        ),
        "ats_parse": (
            0 if "—" in text else 10,
            "No em dashes or odd glyphs that break parsers.",
        ),
        "density": (
            0 if long_bullets else (10 if len(words) < 900 else 6),
            f"{len(long_bullets)} bullets over 35 words.",
        ),
    }
    checks = {k: (max(0, min(10, p)), why)
              for k, (p, why) in checks.items()}
    total = sum(points for points, _ in checks.values())
    worst = min(checks, key=lambda name: checks[name][0])
    return {
        "score": total,
        "checks": {k: {"points": p, "note": why}
                   for k, (p, why) in checks.items()},
        "top_fix": f"{worst}: {checks[worst][1]}",
    }
