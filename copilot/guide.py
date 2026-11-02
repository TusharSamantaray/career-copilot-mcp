"""Onboarding and next-step guidance, driven by what the user has stored."""
from copilot import store

TRACKS = {
    "job": "Find the right job",
    "career_move": "Move into a different role",
    "finance": "Improve my finances",
    "future": "Plan for the future",
}


def _counts(user):
    return {kind: len(store.list_kind(user, kind))
            for kind in ("experience", "resume", "application", "nudge",
                         "account", "budget", "goal", "holding")}


def next_steps(user, goals=None):
    profile_rows = store.list_kind(user, "profile")
    profile = profile_rows[-1] if profile_rows else {}
    wanted = goals or [g.strip() for g in
                       profile.get("goals", "").split(",") if g.strip()]
    wanted = [g for g in wanted if g in TRACKS] or list(TRACKS)
    c = _counts(user)

    checks = []    # (track, done?, action, tool or prompt)
    checks.append(("all", bool(profile),
                   "Tell me your current role, target role, experience, "
                   "country and goals", "profile_save"))
    checks += [
        ("job", c["experience"] >= 3,
         "Capture at least 3 confirmed achievements from past jobs",
         "prompt: build_my_resume"),
        ("job", c["resume"] > 0,
         "Paste your previous resumes so the best bullets can be merged",
         "prompt: import_my_resumes"),
        ("job", False, "Check which roles fit your skills best",
         "prompt: find_my_role"),
        ("job", False, "Review your LinkedIn for your target role",
         "prompt: review_my_linkedin"),
        ("job", c["application"] > 0, "Start tracking applications",
         "application_log"),
        ("job", c["nudge"] > 0, "Set a prep schedule with reminders",
         "prompt: plan_my_prep"),
        ("career_move", False,
         "See what carries over to your target role and what to learn",
         "career_move"),
        ("finance", c["account"] > 0,
         "Add your accounts for a net worth and runway dashboard",
         "prompt: money_checkup"),
        ("finance", c["budget"] > 0,
         "Set a monthly budget with current and target spend",
         "finance_budget_set"),
        ("finance", c["holding"] > 0,
         "Add investments to check concentration risk",
         "finance_holding_set"),
        ("future", c["goal"] > 0,
         "Set savings goals: emergency fund, home, education, retirement",
         "goal_set"),
        ("future", False, "Project where your savings could be in 10-30 "
         "years", "future_projection"),
    ]
    relevant = [ch for ch in checks if ch[0] == "all" or ch[0] in wanted]
    todo = [{"track": TRACKS.get(t, "Getting started"), "action": a,
             "use": u} for t, done, a, u in relevant if not done]
    done = [a for t, d, a, u in relevant if d]
    return {"goals": [TRACKS[g] for g in wanted],
            "next": todo[:3], "remaining": todo[3:], "done": done,
            "tip": "Call nudges_due at the start of each session to see "
                   "what's due."}
