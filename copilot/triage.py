"""Classify job-search emails and calendar events into pipeline updates.

Works on plain dicts, so the source can be the user's own Gmail/Outlook
connector, an Outlook sync through the vault, or pasted text. Email bodies
are read in memory only; just company, role, status and dates are kept.
"""
import re
from datetime import date, datetime, timedelta

ATS_DOMAINS = ("greenhouse", "lever.co", "myworkday", "workday", "ashby",
               "smartrecruiters", "icims", "jobvite", "taleo", "hackerrank",
               "codesignal", "codility", "successfactors", "bamboohr",
               "linkedin", "indeed", "gmail", "outlook", "yahoo", "hotmail")
SENDER_NOISE = re.compile(
    r"\b(careers?|recruit(ing|ment|er)?|talent( acquisition)?|jobs?|"
    r"hiring|team|hr|people|no-?reply|notifications?|via \w+|"
    r"university|the)\b", re.I)

RULES = [
    ("offer", r"pleased to offer|offer letter|offer of employment|"
              r"extend (you )?an offer"),
    ("rejection", r"unfortunately|not (be )?moving forward|move forward "
                  r"with other|pursue other candidates|position has been "
                  r"filled|not selected|decided not to proceed|will not be "
                  r"proceeding|other applicants"),
    ("assessment", r"hackerrank|codesignal|codility|online assessment|"
                   r"coding (challenge|assessment)|take-?home|"
                   r"assessment invitation|complete (the|your) assessment"),
    ("interview", r"\binterview|phone screen|onsite|on-site|schedule (a|"
                  r"your|some) time|your availability|invitation:|"
                  r"meet with|hiring manager (call|screen)|next round"),
    ("applied", r"thank(s| you) for (applying|your application|your "
                r"interest)|application (received|submitted)|we('ve| have)"
                r" received your application"),
    ("outreach", r"came across your (profile|background)|reaching out|"
                 r"exciting opportunity|open to (a )?(new )?(role|"
                 r"opportunit)|would you be interested"),
]
COMPANY_PATTERNS = [
    r"^([A-Z][\w&.\-]{1,30}(?: [A-Z][\w&.\-]+){0,2}) (?:coding|online|"
    r"technical|take-home) (?:assessment|challenge|test)",
    r"(?:assessment|challenge|test|interview) (?:for|from|with) "
    r"([A-Z][\w&.\-]{1,30}(?: [A-Z][\w&.\-]+){0,2})(?:[!,.:;]| |$)",
    r"(?:applying|application|apply|interest) (?:to|at|with|for a role "
    r"at) ([A-Z][\w&.\- ]{1,40}?)(?:[!,.:;]| for | -|$)",
    r"(?:from|at|join) ([A-Z][\w&.\-]{1,30}(?: [A-Z][\w&.\-]+){0,2})"
    r"(?:[!,.:;]| team| recruiting|$)",
    r"^([A-Z][\w&.\- ]{1,40}?) (?:-|\||:) ",
]
ROLE_PATTERN = re.compile(
    r"(?:for (?:the |our )?|role[: ]+|position[: ]+)((?:senior |staff |"
    r"lead |principal |junior )?[A-Z][\w/&+\- ]{2,50}?(?:engineer|developer"
    r"|manager|analyst|designer|scientist|specialist|lead|architect|"
    r"associate|consultant|representative|executive|nurse|coordinator))",
    re.I)
REQ_PATTERN = re.compile(r"\b(?:req(?:uisition)?|job id|job #)\.?\s*"
                         r"(?:id|no\.?|number|#)?\s*[:#]?\s*([A-Z0-9][A-Z0-9-]"
                         r"{2,})", re.I)
EXPIRY_IN = re.compile(r"(?:expires?|due|complete it|within) (?:in )?"
                       r"(\d{1,2}) (business )?days?", re.I)
EXPIRY_ON = re.compile(r"(?:expires?|due|by) (?:on )?(\d{4}-\d{2}-\d{2})",
                       re.I)


def _parse_date(value):
    if isinstance(value, date):
        return value if not isinstance(value, datetime) else value.date()
    text = str(value or "")[:19]
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(text[:len(fmt) + 2], fmt).date()
        except ValueError:
            continue
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        return date.today()


def company_of(sender, subject, body=""):
    for text in (subject, body[:300]):
        for pattern in COMPANY_PATTERNS:
            m = re.search(pattern, text or "")
            if m:
                name = m.group(1).strip(" -.")
                if 1 < len(name) <= 40 and not SENDER_NOISE.fullmatch(name):
                    return name
    display, _, address = (sender or "").partition("<")
    display = SENDER_NOISE.sub("", display.replace('"', "")).strip(" -@,.")
    platform = any(ats.split(".")[0] in display.lower().replace(" ", "")
                   for ats in ATS_DOMAINS) if display else False
    if display and "@" not in display and not platform:
        return re.sub(r"\s+", " ", display)
    domain = (address or sender).split("@")[-1].strip("> ").lower()
    root = domain.split(".")[-2] if domain.count(".") >= 1 else domain
    if root and not any(ats in domain for ats in ATS_DOMAINS):
        return root.capitalize()
    return None


def classify_email(email):
    subject = email.get("subject", "")
    body = email.get("snippet") or email.get("body", "")
    text = f"{subject}\n{body}"
    category = next((name for name, pattern in RULES
                     if re.search(pattern, text, re.I)), "other")
    received = _parse_date(email.get("date"))
    item = {"category": category,
            "company": company_of(email.get("from", ""), subject, body),
            "date": str(received)}
    role = ROLE_PATTERN.search(text)
    if role:
        item["role"] = role.group(1).strip()
    req = REQ_PATTERN.search(text)
    if req:
        item["req_id"] = req.group(1).upper()
    if category == "assessment":
        m_on, m_in = EXPIRY_ON.search(text), EXPIRY_IN.search(text)
        if m_on:
            item["expires"] = m_on.group(1)
        elif m_in:
            days = int(m_in.group(1))
            item["expires"] = str(received + timedelta(
                days=days + (days // 5) * 2 if m_in.group(2) else days))
    return item


STATUS_FOR = {"applied": "applied", "assessment": "assessment",
              "interview": "interviewing", "offer": "offer",
              "rejection": "rejected"}
RANK = {"saved": 0, "applied": 1, "assessment": 2, "interviewing": 3,
        "offer": 4, "rejected": 5, "withdrawn": 5}


OPEN = ("saved", "applied", "assessment", "interviewing", "offer")


def _rejection_target(item, pipeline):
    """A rejection closes a loop only when it clearly names that loop.
    Returns (row, None), (row, note) when matched by company alone, or
    (None, candidates) when the person has to say which one."""
    rows = [r for r in pipeline if r["company"].lower() ==
            item["company"].lower() and r.get("status") in OPEN]
    if not rows:
        return None, None
    req, role = item.get("req_id", ""), item.get("role", "").lower()
    if req:
        hits = [r for r in rows if r.get("req_id", "").upper() == req]
        if hits:
            return hits[0], None
    if role:
        hits = [r for r in rows if role in r.get("role", "").lower()
                or r.get("role", "").lower() in role]
        if len(hits) == 1:
            return hits[0], None
    if len(rows) == 1 and not (req and rows[0].get("req_id")) and not (
            role and rows[0].get("role")):
        return rows[0], "Matched by company only; check it's this role."
    return None, [{"application_id": r.get("id"), "role": r.get("role"),
                   "req_id": r.get("req_id", "")} for r in rows]


def plan_updates(items, pipeline):
    """Turn classified emails into proposed pipeline changes. Never moves
    a row backwards (e.g. a late 'thanks for applying' after an
    interview). A rejection only closes the application it names."""
    by_company = {}
    for row in pipeline:
        by_company.setdefault(row["company"].lower(), row)
    proposals, seen = [], set()
    for item in sorted(items, key=lambda i: i["date"]):
        status = STATUS_FOR.get(item["category"])
        if not status or not item.get("company"):
            continue
        key = (item["company"].lower(), status)
        if status == "rejected":
            key += (item.get("req_id", ""), item.get("role", ""))
        if key in seen:
            continue
        seen.add(key)
        if status == "rejected" and item["company"].lower() in {
                r["company"].lower() for r in pipeline}:
            target, extra = _rejection_target(item, pipeline)
            if target is None and extra:
                proposals.append({"action": "confirm",
                                  "company": item["company"],
                                  "status": "rejected",
                                  "candidates": extra,
                                  "because": "rejection that doesn't name "
                                             "the role or req id"})
                continue
            if target is not None:
                proposal = {"action": "application_update",
                            "application_id": target.get("id"),
                            "company": target["company"],
                            "status": "rejected", "due_date": "",
                            "because": "rejection"}
                if extra:
                    proposal["check"] = extra
                proposals.append(proposal)
                target["status"] = "rejected"
            continue
        row = by_company.get(item["company"].lower())
        due = item.get("expires", "")
        if row is None:
            proposal = {"action": "application_log",
                        "company": item["company"],
                        "role": item.get("role", "Unknown role"),
                        "status": status, "due_date": due,
                        "because": item["category"]}
            proposals.append(proposal)
            by_company[item["company"].lower()] = {
                "company": item["company"], "status": status,
                "_proposal": proposal}
        elif "_proposal" in row:
            # Same batch already creates this row: upgrade it in place.
            if RANK[status] > RANK[row["status"]] or status == "rejected":
                row["_proposal"].update(status=status, because=item[
                    "category"], due_date=due or row["_proposal"]["due_date"])
                row["status"] = status
        elif RANK[status] > RANK.get(row["status"], 0) or (
                status == "rejected" and row["status"] != "rejected"):
            proposals.append({"action": "application_update",
                              "application_id": row.get("id"),
                              "company": row["company"], "status": status,
                              "due_date": due, "because": item["category"]})
            row["status"] = status
    return proposals


INTERVIEW_WORDS = re.compile(r"interview|screen|onsite|on-site|loop|"
                             r"hiring manager|recruiter|technical|panel|"
                             r"assessment|case study", re.I)


def interviews_from_events(events, pipeline):
    """Calendar events that look like interviews, matched to pipeline
    companies where possible."""
    companies = {row["company"].lower(): row for row in pipeline}
    found = []
    for ev in events:
        subject = ev.get("subject") or ev.get("topic") or ""
        if not INTERVIEW_WORDS.search(subject):
            continue
        start = ev.get("start") or ev.get("start_time") or ""
        if isinstance(start, dict):
            start = start.get("dateTime", "")
        match = next((row for name, row in companies.items()
                      if name and name in subject.lower()), None)
        found.append({"subject": subject[:120], "date": str(_parse_date(start)),
                      "company": match["company"] if match else
                      company_of(ev.get("organizer", ""), subject),
                      "application_id": match.get("id") if match else None,
                      "join_url": ev.get("join_url") or "",
                      "source": ev.get("source", "calendar")})
    return found
