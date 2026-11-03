"""Deadlines with two dates, and fast-track mode.

Every deadline holds a best case and a conservative date; plans use the
conservative one. When one is close, fast-track turns on: runway first,
shorter plans, freshest roles first.
"""
from datetime import date

from copilot import store

FAST_TRACK_DAYS = 60


def deadline_add(user, title, best_case, conservative, why=""):
    try:
        best, safe = date.fromisoformat(best_case), \
            date.fromisoformat(conservative)
    except ValueError:
        return {"error": "dates must be YYYY-MM-DD"}
    if safe > best:
        return {"error": "The conservative date can't be later than the "
                         "best case. Plan on the earlier one."}
    body = {"title": title[:120], "best_case": str(best),
            "conservative": str(safe), "why": why[:200]}
    return {"id": store.put(user, "deadline", body), **body,
            "plan_on": str(safe)}


def fast_track(user, today=None):
    """On when any deadline's conservative date is within 60 days."""
    now = today or date.today()
    upcoming = sorted(
        (d for d in store.list_kind(user, "deadline")
         if date.fromisoformat(d["conservative"]) >= now),
        key=lambda d: d["conservative"])
    if not upcoming:
        return {"on": False}
    nearest = upcoming[0]
    days = (date.fromisoformat(nearest["conservative"]) - now).days
    if days > FAST_TRACK_DAYS:
        return {"on": False, "nearest": nearest["title"], "days_left": days}
    return {"on": True, "deadline": nearest["title"],
            "plan_on": nearest["conservative"],
            "best_case": nearest["best_case"], "days_left": days,
            "do": "Say fast-track is on and why, in one line. Runway first, "
                  "shorter plans, freshest roles first."}
