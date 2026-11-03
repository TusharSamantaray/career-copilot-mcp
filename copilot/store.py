"""Tiny per-user record store on SQLite. One row per record.

With CAREER_COPILOT_MASTER_KEY set, every record body is encrypted
(AES-GCM) with that person's own random data key. Data keys live in
_keys.db, each locked with the master key. Deleting a person destroys
their key too, so an old copy of their file can't be read.
"""
import base64
import hashlib
import json
import os
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone

from loguru import logger

DATA_DIR = os.environ.get("COPILOT_DATA_DIR", "./data")
MASTER_KEY = os.environ.get("CAREER_COPILOT_MASTER_KEY", "")
KEYS_FILE = "_keys.db"          # leading underscore: never a person's file
_keys = {}
KINDS = {"profile", "experience", "story", "application", "resume",
         "account", "holding", "budget", "nudge", "goal", "checkin",
         "consent", "compass", "fact", "seen", "round", "posting",
         "watch", "outbox"}


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


# ------------------------------------------------------------- encryption

def _aesgcm(key):
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    return AESGCM(key)


def _master():
    return hashlib.sha256(MASTER_KEY.encode()).digest()


@contextmanager
def _keys_db():
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(os.path.join(DATA_DIR, KEYS_FILE))
    try:
        with conn:
            conn.execute("CREATE TABLE IF NOT EXISTS keys ("
                         "user TEXT PRIMARY KEY, wrapped BLOB)")
            yield conn
    finally:
        conn.close()


def _data_key(user_id, create):
    if user_id in _keys:
        return _keys[user_id]
    with _keys_db() as conn:
        row = conn.execute("SELECT wrapped FROM keys WHERE user=?",
                           (user_id,)).fetchone()
        if row:
            nonce, sealed = row[0][:12], row[0][12:]
            key = _aesgcm(_master()).decrypt(nonce, sealed, user_id.encode())
        elif create:
            key, nonce = os.urandom(32), os.urandom(12)
            sealed = _aesgcm(_master()).encrypt(nonce, key, user_id.encode())
            conn.execute("INSERT INTO keys VALUES (?,?)",
                         (user_id, nonce + sealed))
        else:
            raise PermissionError("This person's data key is gone, so the "
                                  "data can't be read.")
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
    if os.path.exists(os.path.join(DATA_DIR, KEYS_FILE)):
        with _keys_db() as conn:
            conn.execute("DELETE FROM keys WHERE user=?", (user_id,))


# ----------------------------------------------------------------- records

def put(user_id, kind, body, record_id=None):
    assert kind in KINDS, f"unknown kind {kind}"
    record_id = record_id or uuid.uuid4().hex[:8]
    with _connect(user_id) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO records VALUES (?,?,?,?)",
            (record_id, kind, _seal(user_id, record_id, body), _now()),
        )
    return record_id


def get(user_id, record_id):
    with _connect(user_id) as conn:
        row = conn.execute(
            "SELECT body FROM records WHERE id=?", (record_id,)
        ).fetchone()
    return _open(user_id, record_id, row[0]) if row else None


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
    records = []
    for rid, body, updated in rows:
        try:
            records.append({"id": rid, **_open(user_id, rid, body),
                            "updated": updated})
        except PermissionError:
            raise
        except Exception:
            # One damaged or misplaced row must not hide all the others.
            logger.warning(f"skipped a {kind} record that failed to decrypt")
    return records


def export_all(user_id):
    return {kind: list_kind(user_id, kind) for kind in sorted(KINDS)}


def delete_all(user_id):
    path = os.path.join(DATA_DIR, f"{user_id}.db")
    _forget_key(user_id)        # any old copy of the file is now unreadable
    if os.path.exists(path):
        os.remove(path)
        return True
    return False
