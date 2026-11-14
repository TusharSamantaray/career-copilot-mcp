"""Tiny per-user record store. One row per record.

Where records live:
- SQLite (default): one file per person in COPILOT_DATA_DIR.
- Postgres, when DATABASE_URL is set: one shared table, every row tagged
  with the person's id, so a free hosted database keeps data through
  restarts of a free web host.

With CAREER_COPILOT_MASTER_KEY set, every record body is encrypted
(AES-GCM) with that person's own random data key. Data keys are stored
locked with the master key. Deleting a person destroys their key too, so
an old copy or backup of their records can't be read.
"""
import base64
import hashlib
import json
import os
import sqlite3
import threading
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone

from loguru import logger

DATA_DIR = os.environ.get("COPILOT_DATA_DIR", "./data")
DATABASE_URL = os.environ.get("DATABASE_URL", "")
MASTER_KEY = os.environ.get("CAREER_COPILOT_MASTER_KEY", "")
KEYS_FILE = "_keys.db"          # leading underscore: never a person's file
_keys = {}
KINDS = {"profile", "experience", "story", "application", "resume",
         "account", "holding", "budget", "nudge", "goal", "checkin",
         "consent", "compass", "fact", "seen", "round", "posting",
         "watch", "outbox", "lesson", "deadline", "snapshot",
         "persona", "screen", "survey", "search", "pathway",
         "intro", "intro_sent", "proficiency_evidence"}


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# --------------------------------------------------------------- backends

class SQLiteBackend:
    """One file per person; data keys in _keys.db."""
    name = "sqlite"

    @contextmanager
    def _file(self, user_id):
        """Commit on success and always close, so Windows releases it."""
        os.makedirs(DATA_DIR, exist_ok=True)
        conn = sqlite3.connect(os.path.join(DATA_DIR, f"{user_id}.db"))
        try:
            with conn:
                conn.execute("CREATE TABLE IF NOT EXISTS records (id TEXT "
                             "PRIMARY KEY, kind TEXT, body TEXT, updated "
                             "TEXT)")
                yield conn
        finally:
            conn.close()

    @contextmanager
    def _keys(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        conn = sqlite3.connect(os.path.join(DATA_DIR, KEYS_FILE))
        try:
            with conn:
                conn.execute("CREATE TABLE IF NOT EXISTS keys ("
                             "user TEXT PRIMARY KEY, wrapped BLOB)")
                yield conn
        finally:
            conn.close()

    def put(self, user_id, record_id, kind, body, updated):
        with self._file(user_id) as conn:
            conn.execute("INSERT OR REPLACE INTO records VALUES (?,?,?,?)",
                         (record_id, kind, body, updated))

    def get(self, user_id, record_id):
        with self._file(user_id) as conn:
            row = conn.execute("SELECT body FROM records WHERE id=?",
                               (record_id,)).fetchone()
        return row[0] if row else None

    def delete(self, user_id, record_id):
        with self._file(user_id) as conn:
            return conn.execute("DELETE FROM records WHERE id=?",
                                (record_id,)).rowcount > 0

    def rows(self, user_id, kind=None):
        with self._file(user_id) as conn:
            if kind:
                return conn.execute(
                    "SELECT id, kind, body, updated FROM records WHERE "
                    "kind=? ORDER BY updated", (kind,)).fetchall()
            return conn.execute("SELECT id, kind, body, updated FROM "
                                "records ORDER BY updated").fetchall()

    def delete_user(self, user_id):
        path = os.path.join(DATA_DIR, f"{user_id}.db")
        if os.path.exists(path):
            os.remove(path)
            return True
        return False

    def users(self):
        if not os.path.isdir(DATA_DIR):
            return []
        return [n[:-3] for n in os.listdir(DATA_DIR)
                if n.endswith(".db") and not n.startswith("_")]

    def get_key(self, user_id):
        with self._keys() as conn:
            row = conn.execute("SELECT wrapped FROM keys WHERE user=?",
                               (user_id,)).fetchone()
        return row[0] if row else None

    def put_key(self, user_id, wrapped):
        with self._keys() as conn:
            conn.execute("INSERT INTO keys VALUES (?,?)", (user_id, wrapped))

    def delete_key(self, user_id):
        if os.path.exists(os.path.join(DATA_DIR, KEYS_FILE)):
            with self._keys() as conn:
                conn.execute("DELETE FROM keys WHERE user=?", (user_id,))


class PostgresBackend:
    """One records table keyed by (person, record id); data keys in their
    own table. A small connection pool survives the database sleeping.
    Works with Neon's pooled URL (PgBouncer, transaction mode): every
    statement autocommits, no session state, no prepared statements."""
    name = "postgres"

    def __init__(self, url):
        from psycopg_pool import ConnectionPool
        self.pool = ConnectionPool(url, min_size=0, max_size=4, open=True,
                                   check=ConnectionPool.check_connection,
                                   kwargs={"autocommit": True,
                                           "prepare_threshold": None})
        self._ready = False
        self._lock = threading.Lock()

    @contextmanager
    def _conn(self):
        with self.pool.connection() as conn:
            if not self._ready:
                with self._lock:
                    conn.execute(
                        "CREATE TABLE IF NOT EXISTS cc_records (user_id TEXT "
                        "NOT NULL, id TEXT NOT NULL, kind TEXT NOT NULL, "
                        "body TEXT NOT NULL, updated TEXT NOT NULL, "
                        "PRIMARY KEY (user_id, id))")
                    conn.execute("CREATE INDEX IF NOT EXISTS cc_records_kind "
                                 "ON cc_records (user_id, kind, updated)")
                    conn.execute("CREATE TABLE IF NOT EXISTS cc_keys (user_id "
                                 "TEXT PRIMARY KEY, wrapped BYTEA NOT NULL)")
                    self._ready = True
            yield conn

    def put(self, user_id, record_id, kind, body, updated):
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO cc_records VALUES (%s,%s,%s,%s,%s) ON CONFLICT "
                "(user_id, id) DO UPDATE SET kind=EXCLUDED.kind, "
                "body=EXCLUDED.body, updated=EXCLUDED.updated",
                (user_id, record_id, kind, body, updated))

    def get(self, user_id, record_id):
        with self._conn() as conn:
            row = conn.execute("SELECT body FROM cc_records WHERE user_id=%s "
                               "AND id=%s", (user_id, record_id)).fetchone()
        return row[0] if row else None

    def delete(self, user_id, record_id):
        with self._conn() as conn:
            return conn.execute("DELETE FROM cc_records WHERE user_id=%s AND "
                                "id=%s", (user_id, record_id)).rowcount > 0

    def rows(self, user_id, kind=None):
        with self._conn() as conn:
            if kind:
                return conn.execute(
                    "SELECT id, kind, body, updated FROM cc_records WHERE "
                    "user_id=%s AND kind=%s ORDER BY updated",
                    (user_id, kind)).fetchall()
            return conn.execute(
                "SELECT id, kind, body, updated FROM cc_records WHERE "
                "user_id=%s ORDER BY updated", (user_id,)).fetchall()

    def delete_user(self, user_id):
        with self._conn() as conn:
            return conn.execute("DELETE FROM cc_records WHERE user_id=%s",
                                (user_id,)).rowcount > 0

    def users(self):
        with self._conn() as conn:
            return [r[0] for r in conn.execute(
                "SELECT DISTINCT user_id FROM cc_records").fetchall()]

    def get_key(self, user_id):
        with self._conn() as conn:
            row = conn.execute("SELECT wrapped FROM cc_keys WHERE user_id=%s",
                               (user_id,)).fetchone()
        return bytes(row[0]) if row else None

    def put_key(self, user_id, wrapped):
        with self._conn() as conn:
            conn.execute("INSERT INTO cc_keys VALUES (%s,%s) ON CONFLICT "
                         "(user_id) DO NOTHING", (user_id, wrapped))

    def delete_key(self, user_id):
        with self._conn() as conn:
            conn.execute("DELETE FROM cc_keys WHERE user_id=%s", (user_id,))


BACKEND = PostgresBackend(DATABASE_URL) if DATABASE_URL else SQLiteBackend()


# ------------------------------------------------------------- encryption

def _aesgcm(key):
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    return AESGCM(key)


def _master():
    return hashlib.sha256(MASTER_KEY.encode()).digest()


def _data_key(user_id, create):
    if user_id in _keys:
        return _keys[user_id]
    wrapped = BACKEND.get_key(user_id)
    if wrapped is None and create:
        key, nonce = os.urandom(32), os.urandom(12)
        BACKEND.put_key(user_id, nonce + _aesgcm(_master()).encrypt(
            nonce, key, user_id.encode()))
        wrapped = BACKEND.get_key(user_id)   # another worker may have won
    if wrapped is None:
        raise PermissionError("This person's data key is gone, so the data "
                              "can't be read.")
    key = _aesgcm(_master()).decrypt(wrapped[:12], wrapped[12:],
                                     user_id.encode())
    _keys[user_id] = key
    return key


def _seal(user_id, record_id, body):
    text = json.dumps(body)
    if not MASTER_KEY:
        return text
    nonce = os.urandom(12)
    sealed = _aesgcm(_data_key(user_id, create=True)).encrypt(
        nonce, text.encode(), record_id.encode())
    return "enc:" + base64.b64encode(nonce + sealed).decode()


def _open(user_id, record_id, stored):
    if not stored.startswith("enc:"):
        return json.loads(stored)      # written before encryption was on
    raw = base64.b64decode(stored[4:])
    plain = _aesgcm(_data_key(user_id, create=False)).decrypt(
        raw[:12], raw[12:], record_id.encode())
    return json.loads(plain)


def _forget_key(user_id):
    _keys.pop(user_id, None)
    BACKEND.delete_key(user_id)


# ----------------------------------------------------------------- records

def put(user_id, kind, body, record_id=None):
    assert kind in KINDS, f"unknown kind {kind}"
    record_id = record_id or uuid.uuid4().hex[:8]
    BACKEND.put(user_id, record_id, kind, _seal(user_id, record_id, body),
                _now())
    return record_id


def get(user_id, record_id):
    stored = BACKEND.get(user_id, record_id)
    return _open(user_id, record_id, stored) if stored is not None else None


def delete(user_id, record_id):
    return BACKEND.delete(user_id, record_id)


def _decode(user_id, rows):
    records = []
    for rid, kind, body, updated in rows:
        try:
            records.append((kind, {"id": rid, **_open(user_id, rid, body),
                                   "updated": updated}))
        except PermissionError:
            raise
        except Exception:
            # One damaged or misplaced row must not hide all the others.
            logger.warning(f"skipped a {kind} record that failed to decrypt")
    return records


def list_kind(user_id, kind):
    return [r for _, r in _decode(user_id, BACKEND.rows(user_id, kind))]


def export_all(user_id):
    grouped = {kind: [] for kind in sorted(KINDS)}
    for kind, record in _decode(user_id, BACKEND.rows(user_id)):
        grouped.setdefault(kind, []).append(record)
    return grouped


def users():
    """Every person with stored records (for background watches)."""
    return BACKEND.users()


HIDDEN = {"id", "updated", "superseded_by", "skipped"}


def _cell(value):
    if isinstance(value, list):
        return ", ".join(_cell(v) for v in value)
    if isinstance(value, dict):
        return "; ".join(f"{k}: {_cell(v)}" for k, v in value.items())
    return str(value).replace("\n", " ")


def markdown(user_id):
    """Everything stored for this person as a readable Markdown page."""
    lines = ["# My Career Copilot data", "",
             "A readable copy of everything stored about you. Confirmed "
             "and unsure facts are labelled.", ""]
    for kind, rows in export_all(user_id).items():
        if not rows:
            continue
        lines += [f"## {kind.title()} ({len(rows)})", ""]
        for row in rows:
            shown = {k: v for k, v in row.items()
                     if k not in HIDDEN and v not in ("", None, [], {})}
            lines.append("- " + " | ".join(f"**{k}**: {_cell(v)}"
                                          for k, v in shown.items()))
        lines.append("")
    return "\n".join(lines)


def delete_all(user_id):
    _forget_key(user_id)        # any old copy of the data is now unreadable
    return BACKEND.delete_user(user_id)
