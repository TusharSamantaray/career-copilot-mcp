"""Interview rounds, question bank, loop formats, prep checklist and
message templates. General guidance for any candidate."""

QUESTIONS = [
    # round, question, likely, why they ask, how to answer
    ("recruiter", "Tell me about yourself.", True,
     "Checks you can frame yourself in 90 seconds and match the resume.",
     "Current role, the one thing you own, the one before it, then what "
     "you want next. Stop at 90 seconds."),
    ("recruiter", "Why are you looking?", True,
     "Screens for red flags.",
     "One factual sentence about why you left, the same wording every "
     "time, then pivot to what you want next. Never criticise a former "
     "employer."),
    ("recruiter", "What are your compensation expectations?", True,
     "Anchors you before you know the band.",
     "Ask for their range first. If pushed, give a range for the level "
     "you're targeting, not your last salary."),
    ("recruiter", "Do you need visa sponsorship?", False,
     "A hard filter at some companies.",
     "Say it plainly and early, with the exact status and what you need. "
     "It's routine for employers that sponsor."),
    ("recruiter", "What level are you targeting?", True,
     "Decides which opening and pay band you're slotted into.",
     "Map your last level to theirs, then argue one step up on scope. "
     "Don't agree to a level on the first call."),
    ("recruiter", "Are you interviewing elsewhere?", True,
     "Calibrates urgency.",
     "Say you're in a few processes and happy to move efficiently. Never "
     "say you have nothing else going."),
    ("hiring_manager", "Walk me through the project you're proudest of.",
     True, "The main event: depth, ownership and judgement.",
     "Start with why it existed and the decision you made, then how it "
     "worked, then what you'd do differently."),
    ("hiring_manager", "How did you get buy-in for a big change?", True,
     "Influence without authority, the senior-level differentiator.",
     "Who pushed back, what evidence changed their mind, what you "
     "conceded."),
    ("hiring_manager", "Tell me about a time you failed.", True,
     "Wants a real failure, not a humblebrag.",
     "A real cost, your fault, and what you changed afterwards so it "
     "couldn't happen again."),
    ("hiring_manager", "Tell me about a disagreement with a colleague.",
     True, "Everyone picks a disagreement they won easily.",
     "Pick one where you were partly wrong. Show what changed your mind "
     "and what you held firm on."),
    ("hiring_manager", "What's the most ambiguous thing you've run?",
     False, "Senior roles are measured on working without a spec.",
     "A problem nobody assigned you: how you found it, scoped it and got "
     "time for it."),
    ("hiring_manager", "Tell me about mentoring someone.", False,
     "Volume numbers aren't impact.",
     "One person, what they couldn't do before, what they can do now."),
    ("technical", "Walk through how you'd solve this, out loud.", True,
     "Silence while thinking is the most common failure.",
     "Restate the problem, ask about inputs and edge cases, say the "
     "approach and its cost before writing anything."),
    ("technical", "How would this scale to 10x?", True,
     "Tests whether you know your own bottleneck.",
     "Name the bottleneck before they ask, usually the datastore or "
     "fan-out, then the fix and its trade-off."),
    ("resume_defense", "Pick any resume line: what exactly did you do?",
     True, "Every line is an invitation to dig.",
     "Know the mechanism, the number's denominator, and where your part "
     "ended and teammates' began. Say the boundary first."),
    ("resume_defense", "That number: over what period, and versus what?",
     False, "A metric without a baseline means little.",
     "Have the time frame, the baseline and how it was measured."),
    ("closing", "Do you have questions for us?", True,
     "Signals interest and seniority.",
     "Two questions per round, tailored to the interviewer: the team's "
     "hardest problem, how success is measured in 6 months, what the "
     "last person in the role moved on to."),
]

ROUNDS = sorted({q[0] for q in QUESTIONS})

LOOP_FORMATS = {
    "big_tech_algorithmic": "Recruiter, coding phone screen, then 4-5 "
        "rounds: 2-3 coding, 1-2 system design, 1 behavioural. Speed and "
        "consistency across rounds matter; a committee may review.",
    "values_heavy": "Every round mixes technical work with behavioural "
        "questions on the company's stated values, so stories carry "
        "about half the weight. Often one independent 'bar' interviewer.",
    "practical": "Longer applied coding (sometimes debugging an existing "
        "codebase) and design weighted to production concerns: retries, "
        "idempotency, data consistency.",
    "enterprise": "Recruiter, hiring manager, then coding, design, often "
        "a low-level/object design round, and a separate values round.",
    "startup": "Fewer rounds, more weight on the hiring manager and a "
        "founder chat; often a take-home or pairing. Confirm level, pay "
        "and any sponsorship in the first call.",
    "non_technical": "Recruiter, hiring manager, a case study, "
        "presentation or work sample, then a panel. Prepare the work "
        "sample like a real deliverable.",
}

PREP_CHECKLIST = {
    "story_bank": ["Write 8-10 stories in situation-task-action-result "
                   "form", "Cut each to 90 seconds out loud",
                   "Map each story to 3 question framings",
                   "Include a real failure, a disagreement and mentoring"],
    "resume_defense": ["Write out the mechanism behind every claim",
                       "Know every number's baseline and period",
                       "Say where your part ended, unprompted",
                       "Have someone attack each line"],
    "skills_practice": ["Practise the core skills for your target role "
                        "(see skills_gap)", "Do timed sets under real "
                        "conditions", "Narrate out loud while working"],
    "company_prep": ["Research product, news and the team for each "
                     "interview", "Prepare 2 questions per round",
                     "Research pay bands; never give a number first"],
    "mock_loops": ["Do back-to-back mocks like a real loop day",
                   "Record and review: list your 5 worst habits",
                   "Redo one mock focused only on those habits"],
}

TEMPLATES = {
    "thank_you": ("Thank you: {role} interview",
        "Hi {name},\n\nThank you for your time today. I enjoyed learning "
        "about {detail}, and it made me more excited about the {role} role "
        "at {company}.\n\nLooking forward to the next steps.\n\nBest,\n"
        "{me}"),
    "follow_up": ("Following up: {role} at {company}",
        "Hi {name},\n\nI wanted to follow up on the {role} role. I'm still "
        "very interested and happy to share anything else that would help. "
        "Is there an update on next steps?\n\nThanks,\n{me}"),
    "assessment_extension": ("Assessment timing: {role}",
        "Hi {name},\n\nThank you for sending the assessment for the {role} "
        "role. I'd like to give it my full attention; could I have a few "
        "more days, until {detail}?\n\nThank you,\n{me}"),
    "recruiter_reply": ("Re: {role} at {company}",
        "Hi {name},\n\nThanks for reaching out. I'm actively exploring new "
        "roles and the {role} position sounds like a strong fit. Could we "
        "find 20 minutes this week? My availability: {detail}.\n\nBest,\n"
        "{me}"),
    "level_question": ("Question about the {role} role",
        "Hi {name},\n\nBefore we schedule the loop, could you share which "
        "level this opening maps to and its pay band? I want to make sure "
        "we're aligned on scope.\n\nThanks,\n{me}"),
    "referral_request": ("Would you be open to referring me?",
        "Hi {name},\n\nI'm applying for the {role} role at {company} and "
        "think my background in {detail} is a strong match. Would you be "
        "comfortable referring me? I can send my resume and a short "
        "summary to make it easy.\n\nThank you,\n{me}"),
    "offer_negotiation": ("{role} offer",
        "Hi {name},\n\nThank you for the offer; I'm excited about joining "
        "{company}. Before I decide, I'd like to discuss the package. "
        "Based on the scope of the role and {detail}, is there flexibility "
        "on the total compensation?\n\nBest,\n{me}"),
    "withdraw": ("Withdrawing from the {role} process",
        "Hi {name},\n\nThank you for your time and consideration. I've "
        "decided to withdraw from the {role} process. I really appreciated "
        "the conversations and hope our paths cross again.\n\nBest,\n{me}"),
}

STORY_THEMES = {
    "ownership": ["ownership", "own", "proud", "drove", "end to end"],
    "conflict": ["disagree", "conflict", "pushback", "push back",
                 "difficult colleague", "tension"],
    "failure": ["fail", "mistake", "wrong", "regret", "went badly"],
    "ambiguity": ["ambiguous", "unclear", "no spec", "uncertain"],
    "influence": ["buy-in", "persuade", "convince", "influence",
                  "stakeholder"],
    "leadership": ["lead", "led", "team", "mentor", "coach", "grow"],
    "impact": ["impact", "result", "metric", "biggest", "achievement"],
    "customer": ["customer", "user", "client"],
    "speed": ["deadline", "fast", "pressure", "urgent", "quickly"],
}
