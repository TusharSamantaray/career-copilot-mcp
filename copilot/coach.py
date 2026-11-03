"""The soul of Career Copilot: one small step a day, sized to energy.

Picks the single most useful tiny action from what's actually due and the
user's goals, tracks a forgiving streak ("never skip twice"), celebrates
finished steps, and puts safety first when someone is struggling.
"""
import random
from datetime import date, timedelta

from copilot import guide
from copilot import nudges
from copilot import store
from copilot.knowledge.coach import (CELEBRATE, CRISIS_SUPPORT,
                                     CRISIS_WORDS, STEPS)

ENERGY = ("low", "medium", "high")
TRACK_OF = {"Find the right job": "job",
            "Move into a different role": "career_move",
            "Improve my finances": "finance",
            "Plan for the future": "future",
            "Getting started": "job"}


def in_crisis(text):
    low = (text or "").lower()
    return any(word in low for word in CRISIS_WORDS)


def _checkins(user):
    return {c["day"]: c for c in store.list_kind(user, "checkin")}


def momentum(user, today=None):
    """Streak with grace: one rest day never breaks it; two in a row do."""
    now = today or date.today()
    days = {date.fromisoformat(d) for d, c in _checkins(user).items()
            if c.get("done")}
    streak, cursor, gaps = 0, now, 0
    if cursor not in days:
        cursor -= timedelta(days=1)       # today isn't over yet
    while gaps < 2 and cursor >= now - timedelta(days=366):
        if cursor in days:
            streak += 1
            gaps = 0
        else:
            gaps += 1
        cursor -= timedelta(days=1)
    week = sum(1 for d in days if now - timedelta(days=6) <= d <= now)
    return {"streak_days": streak, "active_days_this_week": week,
            "done_today": now in days}


def _pick_due(user, now):
    due = nudges.nudges_due(user, now, within_days=1)
    for bucket in ("overdue", "due_today", "upcoming"):
        if due[bucket]:
            item = due[bucket][0]
            return {"step": item["title"], "why": f"It's {bucket.replace('_', ' ')}.",
                    "source": item["source"], "id": item["id"]}
    return None


def daily_step(user, energy="medium", mood="", today=None):
    """The one thing to do today."""
    now = today or date.today()
    if in_crisis(mood):
        return {"crisis": True, **CRISIS_SUPPORT}
    energy = energy if energy in ENERGY else "medium"
    status = momentum(user, now)
    if status["done_today"]:
        return {"already_done": True, **status,
                "message": "You've already done your step today. Anything "
                           "more is a bonus, and resting is fine too."}
    seed = random.Random(f"{user}:{now}")    # stable within a day
    pick = _pick_due(user, now) if energy != "low" else None
    if pick is None:
        nxt = guide.next_steps(user)["next"]
        track = TRACK_OF.get(nxt[0]["track"], "job") if nxt else "job"
        if energy == "low" and mood and seed.random() < 0.5:
            track = "wellbeing"
        pick = {"step": seed.choice(STEPS[track][energy]), "track": track,
                "why": "Small and doable at your energy today."}
        if nxt and energy != "low":
            pick["bigger_option"] = f"{nxt[0]['action']} (use "\
                                    f"{nxt[0]['use']})"
    return {"today": str(now), "energy": energy, "one_step": pick,
            **status,
            "say": "Offer this one step warmly, in a sentence or two. If it "
                   "feels too big, shrink it further. Call step_done when "
                   "they finish."}


def step_done(user, note="", today=None):
    now = today or date.today()
    store.put(user, "checkin", {"day": str(now), "done": True,
                                "note": note[:200]},
              record_id=f"checkin:{now}")
    status = momentum(user, now)
    seed = random.Random(f"{user}:{now}:done")
    msg = seed.choice(CELEBRATE)
    if status["streak_days"] in (3, 7, 14, 30, 60, 100):
        msg += f" {status['streak_days']} days of momentum!"
    return {"message": msg, **status,
            "tomorrow": "Same deal: one small thing. Rest is allowed, just "
                        "never twice in a row."}
