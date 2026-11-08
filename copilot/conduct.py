"""Ground rules: privacy and terms in plain words, how Career Copilot
speaks, and a checker for text before the user sees or sends it.

Kept outside copilot/knowledge/ on purpose: the weekly improver may
auto-merge knowledge changes, but changes here always need a human review.
"""
import re
from datetime import date

from copilot import facts as fact_record
from copilot import store

TERMS_VERSION = "2026-11-08.15"
DOCS = "https://github.com/TusharSamantaray/career-copilot-mcp/blob/main/docs"

# How every reply sounds. People act on short, clear direction; long
# answers get skimmed and dropped.
REPLY_STYLE = [
    "Short: 2 to 4 short sentences, under 80 words. No headings, no essays.",
    "One step: give exactly one next thing to do, sized to their energy. "
    "Keep the rest for later and mention it only if they ask.",
    "One question: end with one question, with 2 to 4 options when that "
    "helps. 'Not sure' and 'skip' are always fine answers.",
    "Direction, not a lecture: say what to do and why in one line. Explain "
    "more only when they ask ('tell me more').",
    "Lists only for things they asked for (a draft, a short list), with at "
    "most 3 items.",
]
MAX_CHAT_WORDS = 90

PRIVACY = [
    "Career Copilot keeps only what you tell it: your goals, work history, "
    "applications, reminders, check-ins and any money figures you enter.",
    "Each person's data is in its own private file. Nobody else can see "
    "it, unless you publish your anonymous persona: then signed-in people "
    "searching for candidates see that one view, and nothing else.",
    "Signing in with GitHub shares only your public profile. Career "
    "Copilot never sees your password and stores your GitHub id only as a "
    "scrambled code.",
    "It never asks for or stores passwords, one-time codes or bank logins, "
    "and it never logs in anywhere for you.",
    "Email text you share for sorting is not stored, only the application "
    "update it leads to. Drafts you approve to send are not stored either. Interview titles are kept as reminder text.",
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
    "You decide what is sent. It never applies for you, and nothing is "
    "sent, posted or scheduled unless you say yes to that exact text. "
    "Your own connected app (like Gmail) does the sending; Career Copilot "
    "never sends anything itself.",
    "Only put true things on your resume and in messages. It won't help "
    "invent experience, numbers or credentials.",
    "Don't use it to harass, deceive or discriminate against anyone.",
    "If you search for candidates, use what a persona shows only to judge "
    "their work. Don't try to work out who they are or reach them outside "
    "an introduction they agree to.",
    "The free demo keeps data in a managed database, but it can change or "
    "pause without notice and no backup is promised. Keep your own copy "
    "with data_export.",
    "It is for people aged 16 and over.",
]

# How Career Copilot is built to talk, stated as facts about the product
# (a disclosure), not as orders to the assistant reading it.
CONDUCT = [
    "Career Copilot keeps replies short: one small step and one question "
    "at a time.",
    "It stays on career, work, money and life-planning goals, and says so "
    "when something is outside what it does.",
    "It is respectful and neutral, and never insults, mocks or judges "
    "anyone: not the person, not employers, not other groups.",
    "It does not comment on or rank anyone's religion, beliefs, politics, "
    "race, ethnicity, nationality, gender, sexuality, age, disability, "
    "health or family, unless the person raises one for a practical "
    "reason (for example visa or accommodations), and then it stays "
    "factual.",
    "It does not assume what someone can do from who they are.",
    "It says where a fact comes from (the person, its knowledge base or "
    "live data), says 'I don't know' instead of guessing, and labels "
    "estimates with their range.",
    "It uses plain, kind, direct words: no profanity, sarcasm or jokes at "
    "anyone's expense.",
    "Resume lines, messages and plans the person may send or rely on are "
    "checked by response_check first.",
]

# Machine-readable data handling: what is stored, where, for how long and
# who can read it. Shown by ground_rules before anything is saved, served
# as the copilot://data-handling resource and at GET /data-handling.
YOURS = "your data file: one per person, on this server (hosted) or your "         "own computer (local)"
DATA_HANDLING = {
    "version": TERMS_VERSION,
    "stored": [
        {"what": "Profile answers, wants, dealbreakers and honest gaps",
         "where": YOURS, "kept_for": "until you delete it",
         "who_can_read": "only you"},
        {"what": "Work facts, stories, resume text and resume versions",
         "where": YOURS, "kept_for": "until you delete it",
         "who_can_read": "only you"},
        {"what": "Applications, interview rounds, reminders, deadlines, "
                 "watches and roles already shown to you",
         "where": YOURS, "kept_for": "until you delete it",
         "who_can_read": "only you"},
        {"what": "Postings you analyze: title, company and skills asked, "
                 "never the full text",
         "where": YOURS, "kept_for": "until you delete it",
         "who_can_read": "only you"},
        {"what": "Money figures you enter or import (no account numbers)",
         "where": YOURS, "kept_for": "until you delete it",
         "who_can_read": "only you"},
        {"what": "Check-ins, energy level and steps done",
         "where": YOURS, "kept_for": "until you delete it",
         "who_can_read": "only you"},
        {"what": "Your anonymous persona, only if you publish it: target "
                 "role, level, experience range, locations, and confirmed "
                 "work facts with the skills they prove (employer names, "
                 "emails, links and phone numbers removed)",
         "where": YOURS, "kept_for": "until you unpublish or delete it",
         "who_can_read": "only you until you publish; then signed-in "
                         "people searching for candidates"},
        {"what": "If you search for candidates: how many questions you "
                 "asked each persona and when, and the role and skills "
                 "each search asked for (never the questions or the "
                 "postings you paste)",
         "where": YOURS, "kept_for": "until you delete it",
         "who_can_read": "only you; the role and skills are counted, "
                         "unnamed, in the demand digest for 90 days"},
        {"what": "If you answer the hiring survey: your answers and the "
                 "company name you chose to give",
         "where": YOURS, "kept_for": "until you delete it",
         "who_can_read": "you; the roles and skills in them, with your "
                         "company name if given, appear in the demand "
                         "digest that signed-in people can read"},
        {"what": "Your pathway: the direction you picked and its steps",
         "where": YOURS, "kept_for": "until you delete it",
         "who_can_read": "only you"},
        {"what": "The date you agreed to these terms",
         "where": YOURS, "kept_for": "until you delete it",
         "who_can_read": "only you"},
    ],
    "never_stored": [
        "passwords, one-time codes and bank logins",
        "email text shared for sorting (only the update it leads to)",
        "messages you approve to send",
        "account numbers and bank ids",
        "your GitHub username or name (only a salted hash of your GitHub "
        "user number)",
        "in a persona: your name, contact details, photo, age, gender, "
        "salary, work authorization or employer names",
    ],
    "logs": {"what": "which tool ran, when, how long, and error codes",
             "hidden": "your words, emails, money figures, notes and keys",
             "kept_for": "rolling files, deleted over time"},
    "usage_counts": {"what": "anonymous counts such as 'this tool failed'",
                     "identity": "salted hashes, text cleaned of names, "
                                 "emails and numbers",
                     "reported_after": "at least 5 different people"},
    "encryption": "hosted records can be encrypted with a key per person; "
                  "deleting your data destroys the key",
    "your_controls": {"see_everything": "data_export or data_mirror",
                      "delete_everything": "data_delete",
                      "say_no": "decline the terms and nothing about you "
                                "is saved"},
    "others_involved": [
        {"who": "your AI assistant", "sees": "the conversation, under its "
                                            "own privacy policy"},
        {"who": "GitHub", "sees": "that you signed in"},
        {"who": "the host and database host", "sees": "the hosted "
                                                     "records and logs"},
    ],
    "full_text": f"{DOCS}/PRIVACY.md",
}

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
           "catholic", "protestant", "mormon", "evangelical", "church",
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


LIST_ITEM = re.compile(r"^\s*(?:[-*•]|\d+[.)])\s+", re.M)
HEADING = re.compile(r"^\s*(?:#+\s|\*\*[^*\n]+\*\*:?\s*$)", re.M)


def _style_issues(text):
    """Chat replies: short, one question, few list items, no headings."""
    issues = []
    words = len(text.split())
    if words > MAX_CHAT_WORDS:
        issues.append({"type": "too_long", "severity": "fix",
                       "found": [f"{words} words"],
                       "why": "Long replies get skimmed and not acted on.",
                       "suggest": f"Cut to under {MAX_CHAT_WORDS} words: one "
                                  "step, one reason, one question."})
    questions = text.count("?")
    if questions > 1:
        issues.append({"type": "many_questions", "severity": "fix",
                       "found": [f"{questions} questions"],
                       "why": "Several questions at once are hard to answer.",
                       "suggest": "Ask only the most useful one."})
    items = len(LIST_ITEM.findall(text))
    if items > 3:
        issues.append({"type": "too_many_items", "severity": "fix",
                       "found": [f"{items} list items"],
                       "why": "A long list reads like a lecture.",
                       "suggest": "Keep the first step; offer the rest "
                                  "later."})
    if HEADING.search(text):
        issues.append({"type": "heading", "severity": "fix",
                       "found": ["heading"],
                       "why": "Headings make a chat reply feel like a "
                              "document.",
                       "suggest": "Write it as a short message."})
    return issues


def _norm(token):
    """Compare numbers by value: '40 minutes' backs '40', '$2M' is '2m'."""
    token = re.sub(r"[\s$,]", "", token.lower())
    return token if token.endswith(("k", "m")) else token.rstrip("%x")


def _confirmed_numbers(user):
    facts = [f.get("fact", "") for f in store.list_kind(user, "experience")
             if f.get("confirmed")] + fact_record.confirmed_statements(user)
    return {_norm(n) for fact in facts for n in NUMBER.findall(fact)}


def check(user, text, kind="chat"):
    """Flag wording to fix before the person reads, sends or relies on it.

    kind: chat, plan, resume, message, cover_letter or linkedin. Chat
    replies must also be short, with one question and few list items. For
    text the person sends (resume, message, cover_letter, linkedin), every
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
    if kind == "chat":
        issues += _style_issues(text)
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


SUMMARY = [
    "Your data stays in your own file; see it with data_export and delete "
    "it any time with data_delete.",
    "This is education and drafts, not professional advice, and no "
    "outcome is promised.",
    "Nothing is sent, posted or scheduled without your yes to the exact "
    "text.",
]


def ground_rules(user, accept=False):
    """A disclosure: privacy, terms, data handling and how Career Copilot
    talks, plus whether this person agreed to the current version.
    accept=True records today's agreement. Nothing here directs the
    assistant; it states what the product does."""
    agreed = [c for c in store.list_kind(user, "consent")
              if c.get("version") == TERMS_VERSION]
    if accept and not agreed:
        body = {"version": TERMS_VERSION, "accepted_on": str(date.today())}
        store.put(user, "consent", body, record_id="terms")
        agreed = [body]
    return {"version": TERMS_VERSION, "accepted": bool(agreed),
            "accepted_on": agreed[-1]["accepted_on"] if agreed else None,
            "summary": SUMMARY, "privacy": PRIVACY, "terms": TERMS,
            "data_handling": DATA_HANDLING, "how_career_copilot_talks":
            CONDUCT,
            "full_text": {"privacy": f"{DOCS}/PRIVACY.md",
                          "terms": f"{DOCS}/TERMS.md"}}
