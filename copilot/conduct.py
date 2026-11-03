"""Ground rules: privacy and terms in plain words, how Career Copilot
speaks, and a checker for text before the user sees or sends it.

Kept outside copilot/knowledge/ on purpose: the weekly improver may
auto-merge knowledge changes, but changes here always need a human review.
"""
import re
from datetime import date

from copilot import store

TERMS_VERSION = "2026-11-03"
DOCS = "https://github.com/TusharSamantaray/career-copilot-mcp/blob/main/docs"

PRIVACY = [
    "Career Copilot keeps only what you tell it: your goals, work history, "
    "applications, reminders, check-ins and any money figures you enter.",
    "Each person's data is in its own private file. Nobody else can see it.",
    "It never asks for or stores passwords, one-time codes or bank logins, "
    "and it never logs in anywhere for you.",
    "Email text you share for sorting is not stored, only the application "
    "update it leads to. Interview titles are kept as reminder text.",
    "Logs record which tool ran and how long it took. Your words, emails, "
    "money figures and keys are hidden from logs.",
    "Anonymous usage counts help improve it. They contain no names or "
    "text, and nothing is reported until at least 5 people share it.",
    "You can see everything with data_export and erase it all with "
    "data_delete at any time.",
    "Your AI assistant (Claude, ChatGPT and so on) also sees this "
    "conversation, under its own privacy policy.",
]

TERMS = [
    "Career Copilot gives general education and drafts. It is not "
    "financial, tax, legal, immigration or medical advice.",
    "It can't promise a job, an interview or any result.",
    "You decide and you send. It never applies, posts or messages anyone "
    "for you.",
    "Only put true things on your resume and in messages. It won't help "
    "invent experience, numbers or credentials.",
    "Don't use it to harass, deceive or discriminate against anyone.",
    "The demo service can change, pause or lose data without notice. Keep "
    "your own copy with data_export.",
    "It is for people aged 16 and over.",
]

CONDUCT = [
    "Stay on the person's career, work, money and life-planning goals. If "
    "asked about something else, say briefly that it's outside what Career "
    "Copilot does, and offer the next useful step.",
    "Be respectful and neutral. Never insult, mock or judge anyone: not "
    "the person, not employers, not other groups.",
    "Never comment on or rank anyone's religion, beliefs, politics, race, "
    "ethnicity, nationality, gender, sexuality, age, disability, health "
    "or family. Mention them only when the person raises them for a "
    "practical reason (for example visa or accommodations), and stay "
    "factual.",
    "No stereotypes. Don't assume what someone can do from who they are.",
    "Say what you know and where it comes from: the person said it, the "
    "Career Copilot knowledge base, or live data. If you don't know, say "
    "so. Never guess and present it as fact.",
    "Label estimates as estimates, with the range and what they depend on.",
    "Use plain, kind and direct words. No profanity, no sarcasm, no jokes "
    "at anyone's expense.",
    "Before showing or drafting a resume line, message or plan the person "
    "may send or rely on, run response_check and fix what it flags.",
]

# ------------------------------------------------------------------ checks
# Each rule: (type, severity, pattern, why, suggestion). "fix" must be
# changed before the text is used; "review" needs a human look.

_W = r"\b{}\b"


def _rule(kind, severity, words, why, suggest):
    pattern = re.compile("|".join(_W.format(w) for w in words), re.I)
    return kind, severity, pattern, why, suggest


RULES = [
    _rule("insult", "fix",
          ["stupid", "idiots?", "idiotic", "morons?", "losers?", "pathetic",
           "worthless",
           # words that are fine in tech ("lazy loading") unless aimed at
           # someone
           "(?:you|they|he|she|we)(?:'re| are| is|'s) (?:so |really )?"
           "(?:lazy|useless|hopeless|clueless|incompetent|dumb)"],
          "Insulting or demeaning word.",
          "Describe the situation or behaviour, not the person."),
    _rule("profanity", "fix",
          ["damn", "crap", "shit\\w*", "fuck\\w*", "bitch\\w*", "bastards?",
           "asshole\\w*", "wtf"],
          "Profanity.", "Use plain words."),
    _rule("overpromise", "fix",
          # Outcome promises only: "guarantee ordering" is engineering, and
          # "not guaranteed" is the honest version.
          ["(?<!not )(?<!n't )(?<!no )guaranteed? (?:to|you|a|an|the|your)?"
           " ?(?:job|offer|interview|hire|hired|results?|success|returns?|"
           "approval|work|land)",
           "(?:job|offer|returns?|results?) (?:is |are )?guaranteed",
           "100% (?:sure|chance|certain)", "can'?t fail",
           "risk[- ]free", "sure thing", "definitely (?:get|land|win)",
           "will (?:surely|certainly) (?:get|land)"],
          "Promises an outcome nobody can promise.",
          "Say what improves the odds, not that it will happen."),
    _rule("biased_wording", "review",
          ["young", "youthful", "energetic young", "digital natives?",
           "recent grad(?:uate)?s? only", "salesman", "salesmen", "chairman",
           "manpower", "man-hours", "guys", "rock ?stars?", "ninjas?",
           "culture fit", "native (?:english )?speakers?", "able[- ]bodied",
           "overqualified", "too old", "he or she", "his or her"],
          "Wording that can signal bias or exclude people.",
          "Use neutral words: 'early-career', 'salesperson', 'chair', "
          "'staff', 'everyone', 'skilled', 'values alignment', 'fluent in "
          "English', the actual physical requirement, 'they'."),
    _rule("personal_trait", "review",
          # Words that also have ordinary work meanings ("race condition",
          # "diagnosed an outage", "conservative estimate") are left out.
          ["religion", "religious", "mosque", "synagogue", "christian",
           "muslim", "hindu", "jewish", "buddhist", "sikh", "atheist",
           "democrats?", "republicans?", "pregnan\\w*", "married",
           "divorced", "maternity", "my kids", "my children",
           "\\d+ years old", "date of birth", "born in \\d{4}",
           "disabilit\\w*", "ethnicity", "racial", "caste",
           "sexual orientation"],
          "Mentions a personal or protected trait.",
          "Leave it out of resumes and messages unless the person chose to "
          "include it for a practical reason."),
]

ADVICE_TOPICS = re.compile(
    r"\b(invest\w*|stocks?|etfs?|crypto\w*|retirement|401k|ira|tax\w*|"
    r"visa|immigration|green card|h-?1b|relocat\w*|mortgage|loan)\b", re.I)
DISCLAIMER = re.compile(r"not (?:financial |legal |tax )?advice|"
                        r"education(?:al)?,? not advice", re.I)
NUMBER = re.compile(r"\$?\d[\d,]*(?:\.\d+)?(?:%|(?:k|m|x)\b)?", re.I)
SENT = {"resume", "message", "cover_letter", "linkedin"}


def _norm(token):
    """Compare numbers by value: '40 minutes' backs '40', '$2M' is '2m'."""
    token = re.sub(r"[\s$,]", "", token.lower())
    return token if token.endswith(("k", "m")) else token.rstrip("%x")


def _confirmed_numbers(user):
    facts = [f.get("fact", "") for f in store.list_kind(user, "experience")
             if f.get("confirmed")]
    return {_norm(n) for fact in facts for n in NUMBER.findall(fact)}


def check(user, text, kind="chat"):
    """Flag wording to fix before the person reads, sends or relies on it.

    kind: chat, plan, resume, message, cover_letter or linkedin. For text
    the person sends (resume, message, cover_letter, linkedin), every
    number must appear in one of their confirmed experience facts.
    """
    text = text or ""
    issues = []
    for rule_type, severity, pattern, why, suggest in RULES:
        if rule_type == "personal_trait" and kind not in SENT:
            continue
        found = sorted({m.group(0).lower() for m in pattern.finditer(text)})
        if found:
            issues.append({"type": rule_type, "severity": severity,
                           "found": found, "why": why, "suggest": suggest})
    if ADVICE_TOPICS.search(text) and not DISCLAIMER.search(text) \
            and kind in {"chat", "plan"}:
        issues.append({"type": "missing_disclaimer", "severity": "fix",
                       "found": sorted({m.group(0).lower() for m in
                                        ADVICE_TOPICS.finditer(text)}),
                       "why": "Money, tax, visa or relocation content needs "
                              "the education-not-advice note.",
                       "suggest": "Add: 'This is general education, not "
                                  "financial, tax or legal advice.'"})
    if kind in SENT:
        allowed = _confirmed_numbers(user)
        years = re.compile(r"^(?:19|20)\d\d$")
        # Years and lone small counts ("3 teams") are left to the person.
        unsupported = sorted({n.strip() for n in NUMBER.findall(text)
                              if _norm(n) not in allowed
                              and not years.match(_norm(n))
                              and not re.fullmatch(r"\d", n.strip())})
        if unsupported:
            issues.append({"type": "unsupported_number", "severity": "fix",
                           "found": unsupported,
                           "why": "These numbers aren't in any confirmed "
                                  "fact, so they may be invented.",
                           "suggest": "Ask the person for the real number "
                                      "and save it with experience_add, or "
                                      "remove it."})
    fixes = sum(1 for i in issues if i["severity"] == "fix")
    return {"ok": fixes == 0, "fix": fixes,
            "review": len(issues) - fixes, "issues": issues,
            "next": "Ready to show." if not issues else
                    "Rewrite the flagged parts, then check again."}


def ground_rules(user, accept=False):
    """The rules, plus whether this person has agreed to the current
    version. accept=True records today's agreement."""
    agreed = [c for c in store.list_kind(user, "consent")
              if c.get("version") == TERMS_VERSION]
    if accept and not agreed:
        body = {"version": TERMS_VERSION, "accepted_on": str(date.today())}
        store.put(user, "consent", body, record_id="terms")
        agreed = [body]
    return {"version": TERMS_VERSION, "accepted": bool(agreed),
            "accepted_on": agreed[-1]["accepted_on"] if agreed else None,
            "privacy": PRIVACY, "terms": TERMS, "how_we_talk": CONDUCT,
            "full_text": {"privacy": f"{DOCS}/PRIVACY.md",
                          "terms": f"{DOCS}/TERMS.md"},
            "show_user": "In three short lines: your data stays yours and "
                         "you can delete it any time; this is education, "
                         "not advice, and no outcome is promised; you "
                         "decide and send everything. Then ask if that's "
                         "OK. Never block someone in crisis."}
