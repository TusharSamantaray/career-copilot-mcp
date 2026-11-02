"""The coach's voice: tiny steps sized to energy, kind words, safety net.

The philosophy: most people who arrive here are lost, tired or anxious.
Big plans paralyse them. One small, finished thing a day moves a life.
Rest days are allowed; the rule is "never skip twice", not "never skip".
"""

PRINCIPLES = [
    "One thing a day is enough. Small and finished beats big and planned.",
    "Match the step to today's energy, not to yesterday's ambition.",
    "Rest is part of the plan. Never skip twice in a row.",
    "Progress is measured in steps taken, not in outcomes you can't "
    "control (replies, offers).",
    "Be honest and kind at once: name the hard thing, then shrink it.",
    "The user decides. Offer a recommendation, never pressure.",
]

# Tiny steps by track and energy. Each fits the time in its label.
STEPS = {
    "job": {
        "low": ["Save one job posting that looks interesting (5 min)",
                "Write one line about something you're proud of at work "
                "(5 min)",
                "Reply to one recruiter or contact message (5 min)"],
        "medium": ["Apply to one role you saved (20 min)",
                   "Rewrite one resume bullet with a number in it (15 min)",
                   "Send one follow-up or thank-you note (10 min)"],
        "high": ["Apply to three roles (45 min)",
                 "Do one timed practice interview question out loud "
                 "(30 min)",
                 "Ask one person for a referral (20 min)"],
    },
    "career_move": {
        "low": ["Read one job description in the field you want (5 min)",
                "List three skills you already have that would carry over "
                "(5 min)"],
        "medium": ["Do one lesson of a course for your top skill gap "
                   "(20 min)",
                   "Message one person who already does the job (15 min)"],
        "high": ["Build a small piece of portfolio work (45 min)",
                 "Have a 20-minute call with someone in the field"],
    },
    "finance": {
        "low": ["Check one account balance and note it (5 min)",
                "Cancel one subscription you don't use (5 min)"],
        "medium": ["Add your accounts to the dashboard (15 min)",
                   "Set a target for your biggest spending category "
                   "(15 min)"],
        "high": ["Review a month of spending and set the budget (45 min)",
                 "Set up an automatic transfer to savings (20 min)"],
    },
    "future": {
        "low": ["Write down one thing you want your life to have in 3 years "
                "(5 min)"],
        "medium": ["Set one savings goal with an amount and a date (15 min)",
                   "Answer the life compass questions (20 min)"],
        "high": ["Make a one-page plan for the next 12 months (45 min)"],
    },
    "wellbeing": {
        "low": ["Take a 10-minute walk outside", "Drink a glass of water "
                "and eat something real", "Text one friend"],
        "medium": ["Cook one proper meal", "Tidy one small space"],
        "high": ["Do a workout or a long walk", "Spend an hour on "
                 "something just for fun"],
    },
}

CELEBRATE = [
    "Done. That's a real step, not a small one.",
    "Nice. Momentum is built exactly like this.",
    "That counts. You moved today.",
    "Good work. Future you will thank you for this one.",
]

COMPASS = [
    "What does a good ordinary Tuesday look like for you in two years?",
    "Which part of your past work gave you energy, and which drained it?",
    "What matters more right now: money, stability, growth, or freedom?",
    "Where would you live if your job could be anywhere?",
    "What's one fear that's making this harder than it needs to be?",
    "Who are three people whose careers you'd happily have?",
]

CRISIS_WORDS = ["suicide", "suicidal", "kill myself", "end my life",
                "end it all", "self-harm", "self harm", "hurt myself",
                "no reason to live", "can't go on", "cant go on",
                "want to die"]

CRISIS_SUPPORT = {
    "message": "I'm really glad you told me. You don't have to carry this "
               "alone, and a job search can wait. Please reach out to "
               "someone right now.",
    "resources": [
        "If you are in immediate danger, call your local emergency number.",
        "US: call or text 988 (Suicide and Crisis Lifeline).",
        "UK and Ireland: call Samaritans on 116 123.",
        "India: call Tele-MANAS on 14416.",
        "Anywhere else: findahelpline.com lists free, confidential lines.",
    ],
    "next": "When you're ready, the only step for today is talking to a "
            "person you trust.",
}
