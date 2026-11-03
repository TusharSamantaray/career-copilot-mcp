"""Applicant tracking systems: how to spot them and what trips them up.

Most rejections come from knock-out questions (work authorization,
location, years, degree, clearance) and recruiter keyword search, not
from an automatic score. Parsers mostly fail on layout.
"""

# URL fragment -> platform.
PLATFORMS = {
    "greenhouse.io": "greenhouse", "lever.co": "lever",
    "ashbyhq.com": "ashby", "myworkdayjobs.com": "workday",
    "workday.com": "workday", "icims.com": "icims",
    "taleo.net": "taleo", "smartrecruiters.com": "smartrecruiters",
    "jobvite.com": "jobvite", "bamboohr.com": "bamboohr",
}

QUIRKS = {
    "greenhouse": ["Keeps your file as uploaded; recruiters read the PDF.",
                   "Custom questions often include work authorization and "
                   "location; answer them the same way every time."],
    "lever": ["Parses the resume into a profile; check name, email and "
              "current title after upload.",
              "One application can be considered for several roles."],
    "ashby": ["Clean parser; knock-out questions are common on the form."],
    "workday": ["Re-parses your resume into fields you must check by hand: "
                "dates, titles and employers often land wrong.",
                "Needs an account per company; keep one password manager "
                "entry each (Career Copilot never stores them).",
                "Some companies cap applications or add a cool-down before "
                "you can reapply."],
    "icims": ["Older parser: tables, columns and text boxes are often lost.",
              "Long forms; save drafts as you go."],
    "taleo": ["Oldest common parser: use a single column, plain headings and "
              "simple dates.", "Expect to retype work history."],
    "smartrecruiters": ["Parses well; check the skills it pulled out."],
    "jobvite": ["Check parsed dates and titles before submitting."],
    "bamboohr": ["Small-company system; people read it directly."],
    "unknown": ["Use one column, standard headings and simple dates to be "
                "safe anywhere."],
}

# Parsers that struggle with layout, so layout risks matter more.
STRICT_PARSERS = {"workday", "icims", "taleo", "jobvite", "unknown"}

STANDARD_HEADINGS = ("experience", "education", "skills")

KNOCKOUTS = {
    "work_authorization": [r"authori[sz]ed to work", r"sponsor",
                           r"work permit", r"citizenship", r"visa"],
    "location": [r"must (?:be )?(?:located|based|live)", r"on-?site",
                 r"relocat", r"in[- ]office", r"hybrid"],
    "years": [r"\d+\+?\s*(?:or more\s+)?years"],
    "degree": [r"bachelor'?s", r"master'?s", r"ph\.?d", r"degree required",
               r"\bbs\b|\bms\b|\bba\b"],
    "clearance": [r"clearance", r"secret\b", r"ts/sci"],
}
