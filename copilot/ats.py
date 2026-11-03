"""Pre-apply check for a posting's tracking system: which platform, what
in the resume its parser may lose, and which knock-out questions to have
an honest answer ready for."""
import re

from copilot import journey
from copilot import store
from copilot.knowledge.ats import (KNOCKOUTS, PLATFORMS, QUIRKS,
                                   STANDARD_HEADINGS, STRICT_PARSERS)

DATE_STYLES = {
    "month name": re.compile(r"\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|"
                             r"nov|dec)[a-z]*\.? \d{4}\b", re.I),
    "mm/yyyy": re.compile(r"\b\d{1,2}/\d{4}\b"),
    "yyyy-mm": re.compile(r"\b\d{4}-\d{2}\b"),
}


def platform_of(url):
    low = (url or "").lower()
    return next((name for frag, name in PLATFORMS.items() if frag in low),
                "unknown")


def parse_risks(text, platform):
    lines = text.splitlines()
    risks = []
    if any(line.count("|") >= 2 or "\t" in line.strip() for line in lines):
        risks.append("Table or tab columns: many parsers read across them "
                     "and scramble the order.")
    if any(re.search(r"\S {4,}\S", line) for line in lines):
        risks.append("Two columns side by side: put everything in one "
                     "column.")
    if re.search(r"[★●■✔☀-➿]", text):
        risks.append("Icons or symbols: parsers drop or garble them; use "
                     "plain words.")
    styles = [name for name, rx in DATE_STYLES.items() if rx.search(text)]
    if len(styles) > 1:
        risks.append(f"Mixed date formats ({', '.join(styles)}): pick one, "
                     "like 'Jan 2024'.")
    low = text.lower()
    missing = [h for h in STANDARD_HEADINGS if h not in low]
    if missing:
        risks.append(f"No standard heading for {', '.join(missing)}: "
                     "parsers look for these words.")
    if not re.search(r"[\w.+-]+@[\w-]+\.\w+", text):
        risks.append("No email in the body text: contact details in a page "
                     "header are often skipped.")
    if platform not in STRICT_PARSERS and risks:
        risks.append(f"{platform.title()} usually keeps your file as-is, so "
                     "these matter less here, but fix them for other "
                     "systems.")
    return risks


def _answers_on_file(profile, kinds):
    on_file = {
        "work_authorization": profile.get("work_authorization") or None,
        "location": profile.get("location") or
        ", ".join(profile.get("locations", [])) or None,
        "years": profile.get("years_experience") or None,
        "degree": None, "clearance": None,
    }
    return {k: on_file[k] for k in kinds}


def ats_keyword_check(user, posting_text, resume_text="", resume_label=""):
    """Posting keywords split three ways: already on the resume, missing
    but true (backed by a confirmed fact or the profile), and real gaps
    that must not be added."""
    from copilot import facts, jobs
    if not resume_text:
        versions = store.list_kind(user, "resume")
        if resume_label:
            versions = [v for v in versions if v["label"] == resume_label]
        resume_text = versions[-1]["text"] if versions else ""
    posting, resume = (posting_text or "").lower(), resume_text.lower()
    profile = journey.profile(user)
    backed = " ".join(facts.confirmed_statements(user) +
                      profile.get("domain_keywords", [])).lower()
    honest = {g.lower() for g in profile.get("honest_gaps", [])}
    wanted = [s for s in jobs.SKILLS if jobs._has_skill(s, posting)]
    covered = [s for s in wanted if jobs._has_skill(s, resume)]
    true_missing = [s for s in wanted if s not in covered
                    and jobs._has_skill(s, backed) and s not in honest]
    gaps = [s for s in wanted if s not in covered and s not in true_missing]
    return {"covered": covered, "missing_but_true": true_missing,
            "missing_and_gap": gaps,
            "coverage": f"{len(covered)}/{len(wanted)}" if wanted else "n/a",
            "say": "Offer to add the missing-but-true keywords inside real "
                   "bullets (not a keyword list). Never add the gaps; offer "
                   "one way to close the top gap instead."}


def ats_profile_check(user, posting_text="", posting_url="",
                      resume_text="", resume_label=""):
    platform = platform_of(posting_url)
    if not resume_text:
        versions = store.list_kind(user, "resume")
        if resume_label:
            versions = [v for v in versions if v["label"] == resume_label]
        resume_text = versions[-1]["text"] if versions else ""
    low = (posting_text or "").lower()
    knockouts = {kind: sorted({m.group(0) for p in patterns
                               for m in re.finditer(p, low)})
                 for kind, patterns in KNOCKOUTS.items()}
    knockouts = {k: v for k, v in knockouts.items() if v}
    profile = journey.profile(user)
    answers = _answers_on_file(profile, knockouts)
    unanswered = [k for k, v in answers.items() if v is None]
    risks = parse_risks(resume_text, platform) if resume_text else \
        ["No resume to check: paste one or import it first."]
    serious = platform in STRICT_PARSERS and any(
        "column" in r.lower() or "table" in r.lower() for r in risks)
    if unanswered:
        verdict = "knockout_risk"
    elif serious or not resume_text:
        verdict = "fix_first"
    else:
        verdict = "ready"
    return {"platform": platform, "parse_risks": risks,
            "likely_knockouts": knockouts, "answers_on_file": answers,
            "need_an_answer": unanswered,
            "platform_quirks": QUIRKS[platform], "verdict": verdict,
            "say": "Give the verdict and the single most important fix. "
                   "For knock-out questions, help them prepare a true "
                   "answer; never suggest a false one."}
