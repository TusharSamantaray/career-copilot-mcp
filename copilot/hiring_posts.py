"""Rank hiring posts the person pasted (GitHub #33).

People find the best leads in hiring posts on LinkedIn: a recruiter or
founder saying "we're hiring". Career Copilot never logs in to LinkedIn
or scrolls a feed (spec: for LinkedIn, links only, never automated). The
person copies posts in, by hand or with their own browser tool, and this
reads them: who posted, the role, company, location, pay, how to reach
them, the link and the date. Then it ranks them for this person.

- Not a hiring post: set aside.
- Older than 7 days: dropped (the freshness rule). Date unknown: kept,
  flagged, ranked lower.
- Breaks a dealbreaker: filtered out, with the reason.
- Pay below their floor, outside their places, or a stretch: flagged,
  never hidden.

Nothing is stored. The posts name real people, so they never reach the
log either.
"""
import re
from datetime import date, timedelta

from copilot import jobs
from copilot import journey

FRESH_DAYS = 7
HIRING = re.compile(
    r"#hiring\b|\bwe(?:'re|’re| are) hiring\b|\bi(?:'m|’m| am) hiring\b|"
    r"\bis hiring\b|\bnow hiring\b|\bhiring (?:a|an|for|our)\b|"
    r"\blooking for (?:a|an|our)\b|\bjoin (?:our|my|the) team\b|"
    r"\bopen (?:role|position)s?\b|\bjob opening\b|\bwe(?:'re|’re| are) "
    r"looking for\b", re.I)
ROLE_WORD = (r"(?:Engineer|Developer|Scientist|Analyst|Manager|Designer|"
             r"Architect|Lead|Director|Recruiter|Consultant|Specialist|"
             r"Researcher|Administrator|Associate|Coordinator|Strategist|"
             r"Writer|Marketer|SRE|PM)")
ROLE = re.compile(
    r"\b((?:(?:Senior|Sr\.?|Staff|Principal|Lead|Junior|Jr\.?|Founding|"
    r"Head of)\s+)?(?:[A-Z][A-Za-z+/#.&-]*\s+){0,3}" + ROLE_WORD + r")s?\b")
COMPANY = [
    re.compile(r"\b(?:at|@|join)\s+((?:[A-Z][\w&.'-]*)(?:\s+[A-Z][\w&.'-]*)"
               r"{0,2})"),
    re.compile(r"((?:[A-Z][\w&.'-]*)(?:\s+[A-Z][\w&.'-]*){0,2})\s+is "
               r"hiring"),
]
PLACE = re.compile(r"\b(?:in|based in|located in|location:?)\s+([A-Z][a-z]+"
                   r"(?:[ ,]+[A-Z][a-zA-Z]+){0,2})")
PAY = re.compile(r"([$£€])\s?(\d[\d,]*(?:\.\d+)?)\s*(k)?\s*(?:-|–|to)\s*"
                 r"[$£€]?\s?(\d[\d,]*(?:\.\d+)?)\s*(k)?", re.I)
EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
DM = re.compile(r"\b(?:DM me|message me|send me a (?:DM|message)|drop me a "
                r"(?:DM|message)|inbox me|reach out)\b", re.I)
URL = re.compile(r"https://[^\s)>\]]+")
AGO = re.compile(r"(?:^|\n)\s*(\d{1,2})\s*(mo|m|h|d|w|y)\s*(?:•|·|ago|\n|$)")
AGO_WORDS = re.compile(r"\b(\d{1,2})\s+(minute|hour|day|week|month|year)s?"
                       r"\s+ago\b", re.I)
ISO = re.compile(r"\b(20\d\d)-(\d\d)-(\d\d)\b")
NAME = re.compile(r"^[A-Z][a-zA-Z'’-]+(?:\s+[A-Z][a-zA-Z'’.-]+){1,3}$")
DAYS = {"m": 0, "minute": 0, "h": 0, "hour": 0, "d": 1, "day": 1, "w": 7,
        "week": 7, "mo": 30, "month": 30, "y": 365, "year": 365}
NOT_COMPANY = {"our", "the", "my", "a", "an", "we", "i", "us", "remote"}


def _age(text, today):
    """Days since it was posted, or None if the post doesn't say."""
    match = AGO.search(text) or AGO_WORDS.search(text)
    if match:
        return int(match.group(1)) * DAYS[match.group(2).lower()]
    if re.search(r"\byesterday\b", text, re.I):
        return 1
    iso = ISO.search(text)
    if iso:
        try:
            return (today - date(*map(int, iso.groups()))).days
        except ValueError:
            return None
    return None


def _poster(text):
    first = next((ln.strip() for ln in text.splitlines() if ln.strip()), "")
    first = re.split(r"\s*[•·|(]", first)[0].strip()
    if NAME.match(first) and not re.search(ROLE_WORD, first):
        return first
    return None


def _company(text):
    for pattern in COMPANY:
        for match in pattern.finditer(text):
            name = match.group(1).strip(" .,'")
            if name.lower() not in NOT_COMPANY and not re.fullmatch(
                    ROLE_WORD + "s?", name):
                return name
    return None


def _role(text):
    hire = HIRING.search(text)
    after = text[hire.start():] if hire else text
    match = ROLE.search(after) or ROLE.search(text)
    return match.group(1).strip() if match else None


def parse(text, today=None):
    """One post's fields. None for anything the post doesn't say."""
    today = today or date.today()
    pay = PAY.search(text)
    low = text.lower()
    remote = ("remote" if re.search(r"\bremote\b", low) else
              "hybrid" if "hybrid" in low else
              "on-site" if re.search(r"\bon-?site\b|in[- ]office", low)
              else None)
    place = PLACE.search(text)
    urls = URL.findall(text)
    post_url = next((u for u in urls if "linkedin.com/posts/" in u
                     or "linkedin.com/feed/update/" in u), None)
    email = EMAIL.search(text)
    age = _age(text, today)
    return {
        "poster": _poster(text), "role": _role(text),
        "company": _company(text),
        "location": " · ".join(x for x in (place.group(1) if place else None,
                                           remote) if x) or None,
        "pay": (f"{pay.group(1)}{pay.group(2)}{pay.group(3) or ''}–"
                f"{pay.group(1)}{pay.group(4)}{pay.group(5) or ''}"
                if pay else None),
        "contact": (email.group(0) if email else
                    "DM the poster" if DM.search(text) else None),
        "url": post_url or (urls[0] if urls else None),
        "posted": (today - timedelta(days=age)).isoformat()
        if age is not None else None,
        "age_days": age,
    }


def _pay_floor(post_text, profile):
    """jd_analyze reads $ ranges; read £ and € the same way."""
    pay = PAY.search(post_text)
    floor = jobs._floor(profile.get("comp_floor"))
    if not pay or not floor:
        return None
    high = jobs._money(pay.group(4), pay.group(5) or pay.group(3))
    low = jobs._money(pay.group(2), pay.group(3))
    return ("below your floor" if high < floor else
            "meets your floor" if low >= floor else "crosses your floor")


def rank(user, posts, top=5, today=None):
    if isinstance(today, str) and today:
        today = date.fromisoformat(today)
    today = today or date.today()
    profile = journey.profile(user)
    places = [p.lower() for p in profile.get("locations", [])]
    ranked, dropped, not_hiring = [], [], []
    for n, text in enumerate(posts or [], 1):
        text = str(text or "")[:6000]
        if not HIRING.search(text):
            not_hiring.append(n)
            continue
        post = parse(text, today)
        if post["age_days"] is not None and post["age_days"] > FRESH_DAYS:
            dropped.append({"n": n, "role": post["role"],
                            "why": f"posted {post['age_days']} days ago "
                                   f"(older than {FRESH_DAYS})"})
            continue
        read = jobs.jd_analyze(user, text, post["role"] or "",
                               post["company"] or "", remember=False)
        if read["dealbreakers_hit"]:
            dropped.append({"n": n, "role": post["role"],
                            "why": "breaks your dealbreaker: "
                                   + ", ".join(read["dealbreakers_hit"])})
            continue
        flags, score = [], {"apply": 3, "stretch": 2}.get(
            read["verdict"].split(":")[0], 1)
        wanted = len(read["fit_points"]) + len(read["gap_points"])
        score += len(read["fit_points"]) / wanted if wanted else 0
        if read["verdict"].startswith("stretch"):
            flags.append("stretch")
        pay_read = _pay_floor(text, profile)
        if pay_read == "below your floor":
            flags.append("pay below your floor")
            score -= 0.5
        if post["age_days"] is None:
            flags.append("date unknown: check it's recent")
            score -= 1
        elif post["age_days"] <= 2:
            score += 0.5
        where = (post["location"] or "").lower()
        if places and where and not any(p in where for p in places) \
                and "remote" not in where:
            flags.append("outside your places")
            score -= 1
        if read["sponsorship_read"] != "not stated":
            flags.append(f"sponsorship: {read['sponsorship_read']}")
        fits = ", ".join(read["fit_points"][:3])
        gaps = ", ".join(read["gap_points"][:2])
        reason = (f"Fits: {fits}" if fits else "No clear skill match yet") \
            + (f"; gap: {gaps}" if gaps else "") + "."
        ranked.append({"n": n, **post, "verdict": read["verdict"],
                       "fit_reason": reason, "flags": flags,
                       "_score": round(score, 2)})
    ranked.sort(key=lambda p: (-p["_score"], p["age_days"] or 99))
    for post in ranked:
        post.pop("_score")
    return {
        "top": ranked[:max(1, top)], "more": max(0, len(ranked) - top),
        "filtered_out": dropped, "not_hiring_posts": not_hiring,
        "stored": "Nothing. The posts aren't kept or logged.",
        "say": "Show the top 3, each in one line: role, company, the fit "
               "reason and any flag. Say how many were filtered and why in "
               "one line. The person picks which to pursue; nobody is "
               "contacted from here.",
    }
