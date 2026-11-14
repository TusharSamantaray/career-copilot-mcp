"""Fair-use limits for the hosted server, per person.

Two limits, both counted on the person's hashed id (never a name):

- a burst limit: at most PER_MINUTE calls in any 60 seconds, which stops
  a runaway assistant loop or a script hammering the server;
- a daily quota: at most PER_DAY calls per UTC day, which caps what any
  one account can cost.

Counts live in memory. A restart resets them, which is fine: they are a
seatbelt, not a bill. Local (stdio) mode has no limits.
"""
import math
import os
import time
from collections import deque

PER_MINUTE = int(os.environ.get("CAREER_COPILOT_RATE_PER_MINUTE", "60"))
PER_DAY = int(os.environ.get("CAREER_COPILOT_DAILY_QUOTA", "1500"))
DAY = 86400


class Limits:
    def __init__(self, per_minute=PER_MINUTE, per_day=PER_DAY,
                 clock=time.time):
        self.per_minute, self.per_day, self.clock = per_minute, per_day, clock
        self._day = None
        self._recent = {}         # person -> times of calls in the last 60s
        self._today = {}          # person -> calls today
        self._limited = set()     # people limited today (count shown only)
        self._out_for_day = set()  # people who used the whole daily quota
        self._noted = set()       # (person, code) already logged today

    def check(self, person):
        """Count one call. Returns None if it may go ahead. Over a limit,
        returns (code, seconds to wait, whether this is the person's first
        refusal of that kind today). A refused call isn't counted, so
        waiting always works."""
        now = self.clock()
        day = int(now // DAY)
        if day != self._day:
            self._day, self._today = day, {}
            self._limited, self._out_for_day, self._noted = set(), set(), set()
            self._recent = {p: q for p, q in self._recent.items()
                            if q and q[-1] > now - 60}
        if self.per_day and self._today.get(person, 0) >= self.per_day:
            self._out_for_day.add(person)
            return self._refuse(person, "DAILY_LIMIT", (day + 1) * DAY - now)
        recent = self._recent.setdefault(person, deque())
        while recent and recent[0] <= now - 60:
            recent.popleft()
        if self.per_minute and len(recent) >= self.per_minute:
            return self._refuse(person, "RATE_LIMITED", recent[0] + 60 - now)
        recent.append(now)
        self._today[person] = self._today.get(person, 0) + 1
        return None

    def _refuse(self, person, code, wait):
        first = (person, code) not in self._noted
        self._noted.add((person, code))
        self._limited.add(person)
        return code, max(1, math.ceil(wait)), first

    def summary(self):
        """For /health: the limits and how many people hit one today.
        Never who."""
        today = self._day == int(self.clock() // DAY)
        return {"per_minute": self.per_minute, "per_day": self.per_day,
                "people_limited_today": len(self._limited) if today else 0,
                "people_out_for_today":
                    len(self._out_for_day) if today else 0}
