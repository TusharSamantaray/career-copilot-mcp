"""The free trial slows down politely instead of running out of its
free plans: a plain note, never a crash, and data can always leave."""
from copilot import capacity
from copilot import welcome

ID = "trial_capacity"
TITLE = "Free trial stays inside free hosting, and says so plainly when full"
BACKLOG = "B-082"
BEFORE = ("Nothing capped the server as a whole: a busy day could use up "
          "the free database's storage or monthly compute, and people "
          "would see failures instead of an explanation.")


def run(user, measure):
    now = [3 * 86400 + 3600.0]
    cap = capacity.Capacity(people=lambda: ["in1", "in2"],
                            storage_mb=lambda: 5.0, daily_calls=5,
                            new_per_day=1, max_people=10, storage_cap=400,
                            clock=lambda: now[0])
    cap.check("in1")
    cap.check("new1")
    new2 = cap.check("new2")
    measure("a new person past today's cap gets a plain note",
            bool(new2) and "isn't taking new people" in new2[1], True)
    measure("people already in carry on", cap.check("in2"), None)
    cap.check("in1")
    cap.check("in1")
    day = cap.check("in2")
    measure("a used-up day says when it reopens",
            bool(day) and "midnight UTC" in day[1], True)
    measure("export and delete still work when full",
            (cap.check("in1", "data_export"), cap.check("in1", "data_delete")),
            (None, None))
    measure("status counts never name anyone",
            any(p in str(cap.summary()) for p in ("in1", "in2", "new1")),
            False)
    now[0] += 86400
    measure("reopens after midnight UTC", cap.check("new2"), None)
    full = welcome.home("https://demo.example/mcp", False, 60, 1500,
                        "full_today")
    measure("try-it page shows the trial status",
            "Trial status: Full for today" in full, True)
    measure("payment or upgrade asked of visitors",
            any(w in full.lower() for w in ("credit card", "upgrade",
                                             "subscribe")), False)
