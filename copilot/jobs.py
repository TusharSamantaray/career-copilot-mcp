"""Job discovery on public job boards, and reading a posting.

Only official, public, read-only board endpoints (Greenhouse, Lever,
Ashby). Every result needs a provable posting date; postings without one
are dropped and counted. Dealbreakers filter, preferences only rank.
Every role shown is recorded, so a second run reports only new ones.
LinkedIn and others: links only, never automated.
"""
import json
import os
import re
import time
from datetime import date, datetime, timezone

import httpx

from copilot import evidence
from copilot import facts
from copilot import journey
from copilot import store
from copilot.knowledge.careers import ROLES

BOARDS = {
    "greenhouse": "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs",
    "lever": "https://api.lever.co/v0/postings/{slug}?mode=json",
    "ashby": "https://api.ashbyhq.com/posting-api/job-board/{slug}",
}
USER_AGENT = ("CareerCopilot/0.3 (+https://github.com/TusharSamantaray/"
              "career-copilot-mcp)")
CACHE_SECONDS = 1800
MAX_COMPANIES = 15
# Tests point this at a JSON file of {url: response} instead of the web.
FIXTURE = os.environ.get("CAREER_COPILOT_JOBS_FIXTURE", "")
_cache = {}


def _get(url):
    if FIXTURE:
        with open(FIXTURE, encoding="utf-8") as handle:
            return json.load(handle).get(url)
    hit = _cache.get(url)
    if hit and time.time() - hit[0] < CACHE_SECONDS:
        return hit[1]
    try:
        response = httpx.get(url, timeout=10,
                             headers={"User-Agent": USER_AGENT})
    except httpx.HTTPError:
        return None
    data = response.json() if response.status_code == 200 else None
    _cache[url] = (time.time(), data)
    return data


def _date(value):
    """ISO strings or epoch milliseconds to a date; None if missing."""
    if not value:
        return None
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value / 1000, timezone.utc).date()
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")) \
            .date()
    except ValueError:
        return None


def _normalize(board, slug, raw):
    """One shape for every board. posted is None when unprovable."""
    if board == "greenhouse":
        for job in (raw or {}).get("jobs", []):
            yield {"id": str(job.get("id")), "title": job.get("title", ""),
                   "location": (job.get("location") or {}).get("name", ""),
                   "remote": "remote" in str(job.get("location")).lower(),
                   # updated_at changes on any edit, so it isn't a posting
                   # date. Only first_published proves when it went up.
                   "posted": _date(job.get("first_published")),
                   "url": job.get("absolute_url", "")}
    elif board == "lever":
        for job in raw or []:
            cats = job.get("categories") or {}
            yield {"id": job.get("id", ""), "title": job.get("text", ""),
                   "location": cats.get("location", ""),
                   "remote": job.get("workplaceType") == "remote"
                   or "remote" in cats.get("location", "").lower(),
                   "posted": _date(job.get("createdAt")),
                   "url": job.get("hostedUrl", "")}
    elif board == "ashby":
        for job in (raw or {}).get("jobs", []):
            yield {"id": job.get("id", ""), "title": job.get("title", ""),
                   "location": job.get("location", ""),
                   "remote": bool(job.get("isRemote")),
                   "posted": _date(job.get("publishedAt")),
                   "url": job.get("jobUrl", "")}


def _parse_company(entry):
    """'greenhouse:acme' or {'board': 'greenhouse', 'slug': 'acme'}, or a
    bare slug, which is tried on every board."""
    if isinstance(entry, dict):
        return [(entry.get("board", ""), entry.get("slug", ""))]
    if ":" in entry:
        board, slug = entry.split(":", 1)
        return [(board.strip().lower(), slug.strip().lower())]
    return [(board, entry.strip().lower()) for board in BOARDS]


def _floor(text):
    match = re.search(r"(\d[\d,.]*)\s*(k)?", str(text or ""), re.I)
    if not match:
        return 0
    value = float(match.group(1).replace(",", ""))
    return value * 1000 if match.group(2) or value < 1000 else value


def job_search(user, companies=None, keywords=None, locations=None,
               max_age_days=7, include_seen=False, today=None):
    now = today or date.today()
    profile = journey.profile(user)
    companies = list(companies or []) + profile.get("target_companies", [])
    if not companies:
        return {"error": "Which companies? Give board:slug pairs like "
                         "'greenhouse:acme' or 'lever:globex', or a "
                         "company's job-board name.",
                "linkedin": "For LinkedIn, search there yourself: "
                            "https://www.linkedin.com/jobs/"}
    excluded = {c.lower() for c in profile.get("excluded_companies", [])}
    keywords = [k.lower() for k in (keywords or [])] or \
        [w.lower() for w in profile.get("target_role", "").split()
         if len(w) > 2]
    locations = [l.lower() for l in (locations or [])] or \
        [l.lower() for l in profile.get("locations", [])]
    dealbreakers = " ".join(profile.get("dealbreakers", [])).lower()
    wants = [w.lower() for w in profile.get("wants", []) +
             profile.get("domain_keywords", [])]

    found, dropped, sources = [], {"no_date": 0, "too_old": 0,
                                   "dealbreaker": 0, "no_match": 0}, []
    for entry in companies[:MAX_COMPANIES]:
        for board, slug in _parse_company(entry):
            if board not in BOARDS or not slug or slug in excluded:
                continue
            raw = _get(BOARDS[board].format(slug=slug))
            if raw is None:
                continue
            sources.append(f"{board}:{slug}")
            for job in _normalize(board, slug, raw):
                title, where = job["title"].lower(), job["location"].lower()
                if keywords and not any(k in title for k in keywords):
                    dropped["no_match"] += 1
                    continue
                if locations and not any(
                        (l == "remote" and job["remote"]) or l in where
                        for l in locations):
                    dropped["no_match"] += 1
                    continue
                if ("on-site" in dealbreakers or "onsite" in dealbreakers) \
                        and not job["remote"]:
                    dropped["dealbreaker"] += 1
                    continue
                if job["posted"] is None:
                    dropped["no_date"] += 1
                    continue
                age = (now - job["posted"]).days
                if age > max_age_days:
                    dropped["too_old"] += 1
                    continue
                score = sum(w in title or w in where for w in wants)
                found.append({**job, "company": slug, "board": board,
                              "posted": str(job["posted"]),
                              "age_days": age, "rank": score})
    new = []
    for job in found:
        record_id = f"seen:{job['board']}:{job['company']}:{job['id']}"
        first_time = store.get(user, record_id) is None
        if first_time:
            store.put(user, "seen", {"title": job["title"],
                                     "company": job["company"],
                                     "url": job["url"],
                                     "first_seen": str(now)},
                      record_id=record_id)
        if first_time or include_seen:
            new.append(job)
    new.sort(key=lambda j: (-j["rank"], j["age_days"]))
    result = {"new": new[:20], "new_count": len(new),
              "already_seen": len(found) - len(new), "dropped": dropped,
              "searched": sources, "max_age_days": max_age_days}
    if not sources:
        result["note"] = ("None of those boards answered. Check the board "
                          "name (the part after /boards/ or /postings/ in "
                          "the company's careers link).")
    result["say"] = ("Nothing new since last check." if not new else
                     "Show the top 3 in one line each (title, company, age, "
                     "why it ranks). Offer jd_analyze on one.")
    return result


# ------------------------------------------------------------ jd_analyze

LEVELS = [("principal", "principal"), ("staff", "staff"),
          ("senior", "senior"), ("sr.", "senior"), ("lead", "lead"),
          ("junior", "junior"), ("entry", "entry"), ("intern", "intern")]
PAY = re.compile(r"\$\s?(\d[\d,]*(?:\.\d+)?)\s*(k)?\s*(?:-|–|to)\s*\$?\s?"
                 r"(\d[\d,]*(?:\.\d+)?)\s*(k)?", re.I)
NO_SPONSOR = re.compile(r"(not|unable to|cannot|won't|will not|no)\s+"
                        r"(?:\w+\s+){0,3}sponsor|without sponsorship|"
                        r"sponsorship is not available", re.I)
SPONSOR = re.compile(r"visa sponsorship|sponsor(?:ship)? (?:is )?available|"
                     r"will sponsor|h-?1b", re.I)
YEARS = re.compile(r"(\d+)\+?\s*(?:or more\s+)?years", re.I)
SKILLS = sorted({s for r in ROLES.values() for s in r["core"] + r["edge"]},
                key=len, reverse=True)


def _money(number, k):
    value = float(number.replace(",", ""))
    return value * 1000 if k or value < 1000 else value


def _has_skill(skill, text):
    return re.search(rf"(^|[^a-z0-9]){re.escape(skill)}($|[^a-z0-9])",
                     text) is not None


def jd_analyze(user, text, title="", company="", remember=True):
    low = (text or "").lower()
    head = (title or "").lower() + " " + low[:400]
    profile = journey.profile(user)
    level = next((name for word, name in LEVELS if word in head), "not stated")
    years = sorted({int(y) for y in YEARS.findall(low) if int(y) < 30})
    pay = None
    match = PAY.search(text or "")
    if match:
        low_pay = _money(match.group(1), match.group(2))
        high_pay = _money(match.group(3), match.group(4) or match.group(2))
        pay = {"min": low_pay, "max": high_pay, "source": "posting"}
        floor = _floor(profile.get("comp_floor"))
        if floor:
            pay["vs_floor"] = "below your floor" if high_pay < floor else \
                "meets your floor" if low_pay >= floor else "range crosses " \
                "your floor"
    sponsorship = ("says no sponsorship" if NO_SPONSOR.search(low) else
                   "mentions sponsorship" if SPONSOR.search(low) else
                   "not stated")
    wanted = [s for s in SKILLS if _has_skill(s, low)]
    mine = " ".join(facts.confirmed_statements(user) +
                    profile.get("domain_keywords", []) +
                    [profile.get("current_role", "")]).lower()
    fit = [s for s in wanted if _has_skill(s, mine)]
    gaps = [s for s in wanted if s not in fit]
    honest = [g.lower() for g in profile.get("honest_gaps", [])]
    why = [w for w in profile.get("wants", []) if w.lower() in low]
    breaks = [d for d in profile.get("dealbreakers", [])
              if _breaks(d, low, pay, profile)]
    if breaks:
        verdict = "skip: breaks a dealbreaker"
    elif wanted and len(fit) >= max(1, len(wanted) // 2):
        verdict = "apply"
    elif fit:
        verdict = "stretch: apply if the gaps are learnable fast"
    else:
        verdict = "unclear: tell me your skills to judge fit"
    if remember and wanted:
        evidence.remember_posting(user, title, company, text or "", wanted)
    return {"role": title or "untitled", "company": company,
            "level_read": level, "years_asked": years,
            "pay_read": pay or "not stated",
            "sponsorship_read": sponsorship,
            "why_bother": why, "fit_points": fit[:6],
            "gap_points": gaps[:6],
            "honest_gaps_hit": [g for g in honest if g in low],
            "dealbreakers_hit": breaks, "verdict": verdict,
            "say": "Give the verdict and one reason in a sentence, then the "
                   "top fit and top gap. Pay and sponsorship reads come "
                   "from the posting text only; say so."}


def _breaks(dealbreaker, low, pay, profile):
    d = dealbreaker.lower()
    if "sponsor" in d:
        return bool(NO_SPONSOR.search(low))
    if "on-site" in d or "onsite" in d:
        return "on-site" in low and "remote" not in low
    if "pay" in d and pay:
        return pay.get("vs_floor") == "below your floor"
    return False
