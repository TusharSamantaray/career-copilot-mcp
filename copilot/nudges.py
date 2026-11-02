"""Reminders the assistant surfaces, plus a calendar export.

MCP servers can't push messages into a chat, so nudges surface when the
assistant calls nudges_due. For real alarms, import calendar_ics.
"""
from datetime import date, datetime, timedelta, timezone

from copilot import store


def nudge_add(user, title, due, repeat_days=0, note=""):
    try:
        date.fromisoformat(due)
    except ValueError:
        return {"error": "due must be YYYY-MM-DD"}
    body ={"title": title, "due": due, "repeat_days": int(repeat_days),
            "note": note, "done": False}
    return {"id": store.put(user, "nudge", body)}


def _open(user):
    return [n for n in store.list_kind(user, "nudge") if not n["done"]]


def nudges_due(user, today=None, within_days=2):
    now = today or date.today()
    overdue, due_today, upcoming = [], [], []
    items = [{"id": n["id"], "title": n["title"], "due": n["due"],
              "note": n["note"], "source": "nudge"} for n in _open(user)]
    for app in store.list_kind(user, "application"):
        if app["due_date"] and app["status"] not in ("rejected",
                                                     "withdrawn"):
            items.append({"id": app["id"],
                          "title": f"{app['company']}: "
                                   f"{app['next_action'] or app['status']}",
                          "due": app["due_date"], "note": app["role"],
                          "source": "application"})
    for item in sorted(items, key=lambda i: i["due"]):
        due = date.fromisoformat(item["due"])
        if due < now:
            overdue.append(item)
        elif due == now:
            due_today.append(item)
        elif due <= now + timedelta(days=within_days):
            upcoming.append(item)
    return {"today": str(now), "overdue": overdue, "due_today": due_today,
            "upcoming": upcoming}


def nudge_done(user, nudge_id, today=None):
    row = store.get(user, nudge_id)
    if row is None or "repeat_days" not in row:
        return {"error": "no such nudge"}
    now = today or date.today()
    if row["repeat_days"]:
        due = date.fromisoformat(row["due"])
        while due <= now:
            due += timedelta(days=row["repeat_days"])
        row["due"] = str(due)
        store.put(user, "nudge", row, record_id=nudge_id)
        return {"done": True, "next_due": row["due"]}
    row["done"] = True
    store.put(user, "nudge", row, record_id=nudge_id)
    return {"done": True}


def plan_to_nudges(user, plan):
    ids = [nudge_add(user, "; ".join(day["items"][:2]), day["date"])["id"]
           for day in plan]
    return {"nudges_created": len(ids)}


def _ics_escape(text):
    return (text.replace("\\", "\\\\").replace(";", "\\;")
            .replace(",", "\\,").replace("\n", "\\n"))


def calendar_ics(user):
    """An iCalendar file of open nudges and application deadlines."""
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0",
             "PRODID:-//Career Copilot//EN", "CALSCALE:GREGORIAN"]
    events = [(n["id"], n["title"], n["due"], n["note"], n["repeat_days"])
              for n in _open(user)]
    events += [(a["id"], f"{a['company']}: {a['next_action'] or a['status']}",
                a["due_date"], a["role"], 0)
               for a in store.list_kind(user, "application")
               if a["due_date"] and a["status"] not in ("rejected",
                                                        "withdrawn")]
    for uid, title, due, note, repeat in events:
        day = date.fromisoformat(due)
        lines += ["BEGIN:VEVENT", f"UID:{uid}@career-copilot",
                  f"DTSTAMP:{stamp}",
                  f"DTSTART;VALUE=DATE:{day:%Y%m%d}",
                  f"DTEND;VALUE=DATE:{day + timedelta(days=1):%Y%m%d}",
                  f"SUMMARY:{_ics_escape(title)}"]
        if note:
            lines.append(f"DESCRIPTION:{_ics_escape(note)}")
        if repeat:
            lines.append(f"RRULE:FREQ=DAILY;INTERVAL={repeat}")
        lines += ["BEGIN:VALARM", "ACTION:DISPLAY",
                  f"DESCRIPTION:{_ics_escape(title)}",
                  "TRIGGER:-PT15H", "END:VALARM", "END:VEVENT"]
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"
