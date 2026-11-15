"""Free-trial capacity: keep the hosted server inside its free plans.

The demo runs on free hosting (Render free web service, Neon free
Postgres), and nobody pays for anything. This guard makes sure the
server slows down politely instead of running out:

- a server-wide daily budget of calls, so a busy day can't burn the
  free database's monthly compute;
- a cap on new people per day and on people in total, so storage
  stays well inside the free plan;
- a storage ceiling, checked at most every few minutes.

People already in the trial keep working when only the new-people caps
are hit. When the whole day's budget is used, everyone gets the same
plain note: the trial is full today, nothing is lost, it reopens at
midnight UTC. Exporting and deleting data always work.

Counts live in memory and use hashed ids only, never names. Set any
limit to 0 to turn it off. Local (stdio) mode has no limits.
"""
import math
import os
import time

DAY = 86400
DAILY_CALLS = int(os.environ.get("CAREER_COPILOT_TRIAL_DAILY_CALLS",
                                 "20000"))
NEW_PER_DAY = int(os.environ.get("CAREER_COPILOT_TRIAL_NEW_PER_DAY", "30"))
MAX_PEOPLE = int(os.environ.get("CAREER_COPILOT_TRIAL_MAX_PEOPLE", "300"))
STORAGE_MB = int(os.environ.get("CAREER_COPILOT_TRIAL_STORAGE_MB", "400"))
STORAGE_EVERY = 600            # seconds between storage checks
# Always allowed, so a person can take or remove their data even when full.
ALWAYS = {"data_export", "data_delete", "data_mirror"}


class Capacity:
    def __init__(self, people=lambda: [], storage_mb=lambda: 0.0,
                 daily_calls=DAILY_CALLS, new_per_day=NEW_PER_DAY,
                 max_people=MAX_PEOPLE, storage_cap=STORAGE_MB,
                 clock=time.time):
        self.people, self.storage_mb, self.clock = people, storage_mb, clock
        self.daily_calls, self.new_per_day = daily_calls, new_per_day
        self.max_people, self.storage_cap = max_people, storage_cap
        self._known = None        # hashed ids with data, plus admitted ones
        self._day = None
        self._calls = 0
        self._new = 0
        self._turned_away = 0
        self._storage = (None, 0.0)   # (when checked, MB)
        self._noted = set()

    def _roll(self, now):
        day = int(now // DAY)
        if day != self._day:
            self._day, self._calls, self._new = day, 0, 0
            self._turned_away, self._noted = 0, set()

    def _storage_now(self, now):
        when, mb = self._storage
        if when is None or now - when >= STORAGE_EVERY:
            try:
                mb = float(self.storage_mb())
            except Exception:       # a sleeping database: keep the last value
                pass
            self._storage = (now, mb)
        return self._storage[1]

    def _until_midnight(self, now):
        return max(1, math.ceil(((self._day + 1) * DAY - now) / 3600))

    def check(self, person, tool=""):
        """Count one call. None if it may go ahead, else (reason, note,
        first time this reason came up today)."""
        now = self.clock()
        self._roll(now)
        if tool in ALWAYS:
            return None
        hours = self._until_midnight(now)
        if self.daily_calls and self._calls >= self.daily_calls:
            return self._full("day", (
                "The free trial is full for today: it runs on free servers "
                "with a daily budget, and today's is used up. Nothing is "
                f"lost. It reopens at midnight UTC, in about {hours} hours."))
        if self._known is None:
            try:
                self._known = set(self.people())
            except Exception:
                self._known = set()
        if person not in self._known:
            reason = None
            if self.max_people and len(self._known) >= self.max_people:
                reason = "people"
            elif self.new_per_day and self._new >= self.new_per_day:
                reason = "new_today"
            elif self.storage_cap and \
                    self._storage_now(now) >= self.storage_cap:
                reason = "storage"
            if reason:
                self._turned_away += 1
                later = (f"Try again after midnight UTC, in about {hours} "
                         "hours." if reason == "new_today" else
                         "Ask the person who shared the link when it "
                         "reopens.")
                return self._full(reason, (
                    "The free trial isn't taking new people right now, so "
                    "it stays fast for those already using it. Nothing was "
                    f"saved about you. {later}"))
            self._known.add(person)
            self._new += 1
        self._calls += 1
        return None

    def _full(self, reason, note):
        first = reason not in self._noted
        self._noted.add(reason)
        return reason, note, first

    def status(self):
        """For the home page: one of open, new_paused, full_today. Uses
        only what's already in memory, so it never wakes the database."""
        now = self.clock()
        self._roll(now)
        if self.daily_calls and self._calls >= self.daily_calls:
            return "full_today"
        known = len(self._known or ())
        if (self.max_people and known >= self.max_people) or \
                (self.new_per_day and self._new >= self.new_per_day) or \
                (self.storage_cap and self._storage[1] >= self.storage_cap):
            return "new_paused"
        return "open"

    def summary(self):
        """For /health: counts only, never who."""
        self._roll(self.clock())
        return {"status": self.status(),
                "calls_today": self._calls, "daily_calls": self.daily_calls,
                "new_today": self._new, "new_per_day": self.new_per_day,
                "people": len(self._known) if self._known is not None
                else None, "max_people": self.max_people,
                "storage_mb": round(self._storage[1], 1),
                "storage_cap_mb": self.storage_cap,
                "turned_away_today": self._turned_away}
