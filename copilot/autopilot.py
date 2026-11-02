"""Rules that turn pipeline changes into the right reminders, so nothing
slips: follow-ups, assessment deadlines, interview prep, thank-yous,
offers. Each rule has a stable key, so re-running never duplicates."""
from datetime import date, timedelta

from copilot import store
from copilot import triage


def add_business_days(day, n):
    while n > 0:
        day += timedelta(days=1)
        if day.weekday() < 5:
            n -= 1
    return day


def ensure_nudge(user, key, title, due, note=""):
    for n in store.list_kind(user, "nudge"):
        if n.get("auto_key") == key:
            if not n["done"] and n["due"] != str(due):
                n["due"] = str(due)
                store.put(user, "nudge", n, record_id=n["id"])
            return n["id"]
    body = {"title": title, "due": str(due), "repeat_days": 0,
            "note": note, "done": False, "auto_key": key}
    return store.put(user, "nudge", body)


def on_application(user, app_id, row, today=None):
    """Create the reminders this pipeline row now needs."""
    now = today or date.today()
    company, status = row["company"], row["status"]
    due = date.fromisoformat(row["due_date"]) if row.get("due_date") else None
    made = []
    if status == "applied":
        made.append(ensure_nudge(user, f"{app_id}:followup",
                    f"Follow up with {company} if you haven't heard back",
                    add_business_days(now, 7)))
    elif status == "assessment" and due:
        made.append(ensure_nudge(user, f"{app_id}:assessment",
                    f"Finish the {company} assessment (due {due})",
                    max(now, due - timedelta(days=2)),
                    "Ask for an extension if you need one: message_draft "
                    "kind=assessment_extension"))
    elif status == "interviewing" and due:
        made.append(ensure_nudge(user, f"{app_id}:prep:{due}",
                    f"Prep for {company}: research, 3 stories, 2 questions",
                    max(now, due - timedelta(days=1))))
        made.append(ensure_nudge(user, f"{app_id}:thanks:{due}",
                    f"Send {company} a thank-you note", due,
                    "message_draft kind=thank_you"))
        made.append(ensure_nudge(user, f"{app_id}:after:{due}",
                    f"Follow up with {company} if no news",
                    add_business_days(due, 3)))
    elif status == "offer":
        made.append(ensure_nudge(user, f"{app_id}:offer",
                    f"Review the {company} offer; negotiate before "
                    "accepting", now + timedelta(days=1),
                    "Never accept on the call. message_draft "
                    "kind=offer_negotiation"))
    return made


def apply_proposals(user, proposals, today=None):
    """Execute triage proposals against the pipeline, with reminders."""
    done = []
    for p in proposals:
        if p["action"] == "application_log":
            row = {"company": p["company"], "role": p["role"],
                   "status": p["status"], "next_action": p["because"],
                   "due_date": p.get("due_date", "")}
            app_id = store.put(user, "application", row)
        else:
            app_id = p["application_id"]
            row = store.get(user, app_id)
            if row is None:
                continue
            row["status"] = p["status"]
            if p.get("due_date"):
                row["due_date"] = p["due_date"]
            store.put(user, "application", row, record_id=app_id)
        on_application(user, app_id, row, today)
        done.append({"company": row["company"], "status": row["status"]})
    return done


def pipeline_rows(user):
    return store.list_kind(user, "application")


def triage_emails(user, emails, apply=False, today=None):
    items = [triage.classify_email(e) for e in emails]
    proposals = triage.plan_updates(items, pipeline_rows(user))
    counts = {}
    for item in items:
        counts[item["category"]] = counts.get(item["category"], 0) + 1
    result = {"emails": len(items), "by_category": counts,
              "proposals": proposals}
    if apply:
        result["applied"] = apply_proposals(user, proposals, today)
    else:
        result["next"] = ("Show the proposals to the user; call again with "
                          "apply=true once they agree.")
    return result


def interviews_from_calendar(user, events, apply=False, today=None):
    found = triage.interviews_from_events(events, pipeline_rows(user))
    if apply:
        for f in found:
            if f["application_id"]:
                row = store.get(user, f["application_id"])
                row["status"], row["due_date"] = "interviewing", f["date"]
                store.put(user, "application", row,
                          record_id=f["application_id"])
                on_application(user, f["application_id"], row, today)
            else:
                ensure_nudge(user, f"cal:{f['subject']}:{f['date']}",
                             f"Prep for: {f['subject']}",
                             date.fromisoformat(f["date"])
                             - timedelta(days=1))
    return {"interviews": found, "applied": apply}
