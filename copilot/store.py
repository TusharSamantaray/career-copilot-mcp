"""Tiny per-user record store on SQLite. One row per record."""
import json
import os
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone

DATA_DIR = os.environ.get("COPILOT_DATA_DIR", "./data")
KINDS = {"profile", "experience", "story", "application", "resume",
         "account", "holding", "budget", "nudge", "goal", "checkin",
         "consent", "compass"}


@contextmanager
def _connect(user_id):
    """Commit on success and always close, so Windows releases the file."""
    os.makedirs(DATA_DIR, exist_ok=True)
    path = os.path.join(DATA_DIR, f"{user_id}.db")
    conn = sqlite3.connect(path)
    try:
        with conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS records ("
                "id TEXT PRIMARY KEY, kind TEXT, body TEXT, updated TEXT)"
            )
            yield conn
    finally:
        conn.close()


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def put(user_id, kind, body, record_id=None):
    assert kind in KINDS, f"unknown kind {kind}"
    record_id = record_id or uuid.uuid4().hex[:8]
    with _connect(user_id) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO records VALUES (?,?,?,?)",
            (record_id, kind, json.dumps(body), _now()),
        )
    return record_id


def get(user_id, record_id):
    with _connect(user_id) as conn:
        row = conn.execute(
            "SELECT body FROM records WHERE id=?", (record_id,)
        ).fetchone()
    return json.loads(row[0]) if row else None


def delete(user_id, record_id):
    with _connect(user_id) as conn:
        cur = conn.execute("DELETE FROM records WHERE id=?", (record_id,))
    return cur.rowcount > 0


def list_kind(user_id, kind):
    with _connect(user_id) as conn:
        rows = conn.execute(
            "SELECT id, body, updated FROM records WHERE kind=? "
            "ORDER BY updated",
            (kind,),
        ).fetchall()
    return [
        {"id": rid, **json.loads(body), "updated": updated}
        for rid, body, updated in rows
    ]


def export_all(user_id):
    return {kind: list_kind(user_id, kind) for kind in sorted(KINDS)}


def delete_all(user_id):
    path = os.path.join(DATA_DIR, f"{user_id}.db")
    if os.path.exists(path):
        os.remove(path)
        return True
    return False
