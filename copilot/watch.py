"""Watches and an outbox. MCP can't start a conversation, so a watch finds
things (new postings, reminders coming due) and leaves them in the
person's outbox; the assistant reads it at the next chat with digest_get.
Watches find; they never send anything to anyone.
"""
import os
import threading
import time
from datetime import date, timedelta

from loguru import logger

from copilot import jobs
from copilot import nudges
from copilot import store

KINDS = ("new_postings", "assessment_expiry", "follow_up_due", "deadline")
CADENCE_DAYS = {"daily": 1, "weekly": 7}
TITLE_WORD = {"assessment_expiry": "assessment", "follow_up_due": "follow"}


def watch_create(user, kind, query=None, cadence="daily"):
    if kind not in KINDS:
        return {"error": f"kind must be one of {KINDS}"}
    if cadence not in CADENCE_DAYS:
        return {"error": f"cadence must be one of {sorted(CADENCE_DAYS)}"}
    query = query or {}
    if kind == "new_postings" and not (query.get("companies") or
                                       _profile_companies(user)):
        return {"error": "A postings watch needs companies (e.g. "
                         "'greenhouse:acme') or target companies on the "
                         "profile."}
    body = {"kind": kind, "cadence": cadence,
            "query": {k: query[k] for k in ("companies", "keywords",
                                            "locations", "max_age_days")
                      if k in query},
            "last_run": None}
    return {"id": store.put(user, "watch", body), **body}


def _profile_companies(user):
    rows = store.list_kind(user, "profile")
    return rows[-1].get("target_companies", []) if rows else []


def watches(user, remove_id=""):
    """List watches; with remove_id, remove that one first."""
    result = {}
    if remove_id:
        row = store.get(user, remove_id)
        if row is None or row.get("kind") not in KINDS:
            return {"error": "no such watch"}
        result["removed"] = store.delete(user, remove_id)
    result["watches"] = [{k: w.get(k) for k in ("id", "kind", "cadence",
                                                "query", "last_run")}
                         for w in store.list_kind(user, "watch")]
    return result


def _post(user, kind, text, ref, now):
    record_id = f"outbox:{kind}:{ref}"
    if store.get(user, record_id) is None:
        store.put(user, "outbox", {"kind": kind, "text": text[:200],
                                   "day": str(now), "read": False},
                  record_id=record_id)
        return 1
    return 0


def run_due(user, today=None):
    """Run every watch whose cadence has come round. Returns how many new
    outbox items were left."""
    now = today or date.today()
    added = 0
    for w in store.list_kind(user, "watch"):
        last = date.fromisoformat(w["last_run"]) if w.get("last_run") \
            else None
        if last and now - last < timedelta(days=CADENCE_DAYS[w["cadence"]]):
            continue
        if w["kind"] == "new_postings":
            q = w["query"]
            found = jobs.job_search(user, q.get("companies"),
                                    q.get("keywords"), q.get("locations"),
                                    q.get("max_age_days", 7), False, now)
            for job in found.get("new", []):
                added += _post(user, "new_posting",
                               f"New: {job['title']} at {job['company']} "
                               f"(posted {job['posted']}) {job['url']}",
                               f"{job['board']}:{job['company']}:{job['id']}",
                               now)
        else:
            due = nudges.nudges_due(user, now, within_days=2)
            word = TITLE_WORD.get(w["kind"])
            for bucket in ("overdue", "due_today", "upcoming"):
                for item in due[bucket]:
                    if word and word not in item["title"].lower():
                        continue
                    added += _post(user, w["kind"],
                                   f"{item['title']} (due {item['due']})",
                                   f"{item['id']}:{item['due']}", now)
        w["last_run"] = str(now)
        store.put(user, "watch", {k: v for k, v in w.items()
                                  if k not in ("id", "updated")},
                  record_id=w["id"])
    return added


def digest_get(user, today=None):
    """Run due watches, then hand over everything unread, once."""
    run_due(user, today)
    unread = [o for o in store.list_kind(user, "outbox") if not o["read"]]
    for item in unread:
        store.put(user, "outbox", {**{k: v for k, v in item.items()
                                      if k not in ("id", "updated")},
                                   "read": True}, record_id=item["id"])
    items = [{"kind": o["kind"], "text": o["text"], "day": o["day"]}
             for o in unread]
    return {"items": items, "count": len(items),
            "watches": len(store.list_kind(user, "watch")),
            "say": "Nothing new." if not items else
                   "Mention the most urgent item in one line and offer it "
                   "as today's step. Don't list them all."}


def start_scheduler(data_dir, minutes):
    """Optional: run watches for every person between chats while the
    server is awake. Off unless CAREER_COPILOT_WATCH_MINUTES is set."""
    def loop():
        while True:
            time.sleep(minutes * 60)
            for name in os.listdir(data_dir):
                if name.endswith(".db"):
                    try:
                        run_due(name[:-3])
                    except Exception:      # one bad file never stops others
                        logger.exception("watch run failed")
    thread = threading.Thread(target=loop, daemon=True, name="watches")
    thread.start()
    return thread
