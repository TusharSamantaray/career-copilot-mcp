"""What's actually known about visa sponsorship for one role.

Evidence comes from the posting text (quoted, never paraphrased) and
from what the person logged on their applications (what a recruiter
said). Public filing data is offered as links only: past filings show
an employer has sponsored before, not that it will for this role.
"Unstated" is a valid answer; nothing here ever assumes yes.
"""
import re

from copilot import journey, store

NO = re.compile(r"(?:not|unable to|cannot|can't|won't|will not|no|does not|"
                r"doesn't)\s+(?:\w+\s+){0,3}(?:sponsor|support (?:visa|h-?1b))"
                r"|without (?:visa )?sponsorship|sponsorship is not "
                r"available|must be (?:legally )?authori[sz]ed to work "
                r"(?:\w+\s+){0,4}without", re.I)
YES = re.compile(r"visa sponsorship (?:is )?(?:available|offered|provided)|"
                 r"(?:we|will|can|happy to) sponsor|sponsorship (?:is )?"
                 r"available|h-?1b transfers? (?:are )?(?:supported|welcome)"
                 r"|(?:support|offer) (?:visa|h-?1b) sponsorship", re.I)
MENTION = re.compile(r"sponsor|h-?1b|visa|work authori[sz]ation", re.I)

FILINGS = [
    {"source": "USCIS H-1B Employer Data Hub",
     "url": "https://www.uscis.gov/tools/reports-and-studies/"
            "h-1b-employer-data-hub",
     "shows": "H-1B petitions approved or denied, by employer and year"},
    {"source": "US Department of Labor, LCA disclosure data",
     "url": "https://www.dol.gov/agencies/eta/foreign-labor/performance",
     "shows": "Labor condition applications, with job titles and wages"},
]


def _sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", text or "")
            if s.strip()]


def needs_sponsorship(profile):
    said = " ".join([profile.get("work_authorization", "")] +
                    profile.get("dealbreakers", [])).lower()
    return bool(re.search(r"sponsor|h-?1b|visa", said))


def verify(user, company, role="", posting_text="", application_id="",
           save=False):
    evidence = []
    for sentence in _sentences(posting_text):
        if NO.search(sentence):
            evidence.append({"from": "posting", "signal": "no",
                             "quote": sentence[:240]})
        elif YES.search(sentence):
            evidence.append({"from": "posting", "signal": "yes",
                             "quote": sentence[:240]})
        elif MENTION.search(sentence):
            evidence.append({"from": "posting", "signal": "unclear",
                             "quote": sentence[:240]})
    name = company.strip().lower()
    apps = [a for a in store.list_kind(user, "application")
            if a.get("company", "").strip().lower() == name]
    for app in apps:
        if app.get("sponsorship") in ("yes", "no"):
            evidence.append({"from": "your application log",
                             "signal": app["sponsorship"],
                             "quote": f"{app.get('role', '')}: you logged "
                                      f"sponsorship as {app['sponsorship']}"})
    signals = {e["signal"] for e in evidence}
    if "no" in signals:
        answer = "no"
    elif "yes" in signals:
        answer = "yes"
    else:
        answer = "unstated"
    explicit = any(e["from"] == "posting" and e["signal"] == answer
                   for e in evidence)
    confidence = ("high" if explicit else
                  "medium" if answer in ("yes", "no") else "low")
    profile = journey.profile(user)
    result = {
        "company": company, "role": role, "answer": answer,
        "confidence": confidence, "evidence": evidence,
        "conflict": {"yes", "no"} <= signals,
        "matters_for_you": needs_sponsorship(profile),
        "public_filings": FILINGS,
        "note": "Education, not legal advice. Filing data shows past "
                "sponsorship by an employer, not a promise for this role.",
    }
    if result["conflict"]:
        result["say"] = ("Sources disagree. Ask the recruiter once, as a "
                         "plain fact, and log the answer.")
    elif answer == "unstated":
        result["say"] = ("The posting doesn't say. Ask the recruiter once, "
                         "early, as a plain fact: 'I'll need H-1B transfer "
                         "support. Is that possible for this role?'")
    else:
        result["say"] = (f"The {'posting' if explicit else 'log'} says "
                         f"{answer}. Quote it rather than paraphrasing.")
    if save and application_id and answer in ("yes", "no") and explicit:
        row = store.get(user, application_id)
        if row is None:
            result["saved"] = {"error": "no such application"}
        else:
            row["sponsorship"] = answer
            store.put(user, "application", row, record_id=application_id)
            result["saved"] = {"application_id": application_id,
                               "sponsorship": answer}
    return result
