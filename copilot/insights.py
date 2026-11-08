"""Anonymous, aggregate usage signals that drive self-improvement.

Privacy rules, enforced here:
- No free text and no personal data. Users appear only as an HMAC of
  their storage id with a server-side salt, so insight rows can't be
  joined back to anyone's records.
- Short labels (e.g. a requested role name) are scrubbed to letters and
  capped at 40 characters; anything that still looks like an email, URL or
  number is dropped.
- A label is reported only once K_ANON distinct users have sent it.
Disable entirely with CAREER_COPILOT_INSIGHTS=0.

Where they live: a local file by default. On a free host that file is
wiped on every restart, so the owner can keep the counts in the hosted
database instead (CAREER_COPILOT_INSIGHTS_STORE=database, with
DATABASE_URL set). There, counts older than RETENTION_DAYS are dropped.
"""
import hashlib
import hmac
import os
import re
import sqlite3
from contextlib import contextmanager
from datetime import date

ENABLED = os.environ.get("CAREER_COPILOT_INSIGHTS", "1") != "0"
DB_PATH = os.path.join(os.environ.get("COPILOT_DATA_DIR", "./data"),
                       "_insights.db")
SALT = os.environ.get("CAREER_COPILOT_INSIGHTS_SALT", "")
K_ANON = int(os.environ.get("CAREER_COPILOT_K_ANON", "5"))
FEEDBACK_REASONS = ("helpful", "wrong", "missing_info", "confusing",
                    "too_generic", "not_my_country", "missing_role")
MAX_LABEL = 40
STORE = os.environ.get("CAREER_COPILOT_INSIGHTS_STORE", "file")
RETENTION_DAYS = 400
_pg_ready = False


def _database():
    """The hosted database backend when the owner chose it, else None."""
    if STORE != "database":
        return None
    from copilot import store
    return store.BACKEND if store.BACKEND.name == "postgres" else None


def _run(sql, params=(), fetch=False):
    """One statement against wherever the counts live."""
    global _pg_ready
    db = _database()
    if db is None:
        with _connect() as conn:
            rows = conn.execute(sql.replace("{T}", "signals"), params)
            return rows.fetchall() if fetch else None
    with db._conn() as conn:
        if not _pg_ready:
            conn.execute("CREATE TABLE IF NOT EXISTS cc_signals (kind TEXT, "
                         "label TEXT, who TEXT, day TEXT, ok INTEGER, "
                         "ms REAL)")
            _pg_ready = True
        rows = conn.execute(sql.replace("{T}", "cc_signals")
                            .replace("?", "%s"), params)
        return rows.fetchall() if fetch else None


def location():
    return "database" if _database() is not None else "file"


@contextmanager
def _connect():
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    try:
        with conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS signals ("
                "kind TEXT, label TEXT, who TEXT, day TEXT, ok INTEGER, "
                "ms REAL)")
            yield conn
    finally:
        conn.close()


def _who(user_id):
    key = (SALT or "career-copilot-default-salt").encode()
    return hmac.new(key, user_id.encode(), hashlib.sha256).hexdigest()[:16]


def scrub(label):
    """A short, lowercase, letters-only label, or None if it looks
    personal (email, URL, digits) or is empty."""
    if not label or re.search(r"@|https?:|www\.|\d", label):
        return None
    clean = re.sub(r"[^a-zA-Z &/+-]", " ", label).lower()
    clean = re.sub(r"\s+", " ", clean).strip()[:MAX_LABEL]
    return clean or None


def record(kind, label, user_id, ok=True, ms=0.0):
    if not ENABLED:
        return
    label = scrub(label) if kind != "tool" else label
    if not label:
        return
    _run("INSERT INTO {T} VALUES (?,?,?,?,?,?)",
         (kind, label, _who(user_id), str(date.today()), int(ok),
          round(ms, 1)))


def forget(user_id):
    """Remove one user's signals (called by data_delete)."""
    if not ENABLED or (_database() is None and not os.path.exists(DB_PATH)):
        return
    _run("DELETE FROM {T} WHERE who=?", (_who(user_id),))


def summary(since_days=30):
    """Aggregates only, with every label behind the K_ANON threshold."""
    if _database() is None and not os.path.exists(DB_PATH):
        return {"k_anon": K_ANON, "tools": [], "labels": {}}
    today = date.today().toordinal()
    cutoff = str(date.fromordinal(today - since_days))
    if _database() is not None:
        _run("DELETE FROM {T} WHERE day<?",
             (str(date.fromordinal(today - RETENTION_DAYS)),))
    tools = _run(
        "SELECT label, COUNT(*), COUNT(DISTINCT who), "
        "AVG(ok), AVG(ms) FROM {T} WHERE kind='tool' AND day>=? "
        "GROUP BY label ORDER BY COUNT(*) DESC", (cutoff,), fetch=True)
    labels = _run(
        "SELECT kind, label, COUNT(DISTINCT who) AS users, "
        "AVG(ok) FROM {T} WHERE kind!='tool' AND day>=? "
        "GROUP BY kind, label HAVING COUNT(DISTINCT who)>=? "
        "ORDER BY users DESC", (cutoff, K_ANON), fetch=True)
    out = {"since_days": since_days, "k_anon": K_ANON,
           "tools": [{"tool": t, "calls": n, "users": u,
                      "success_rate": round(float(ok), 3),
                      "avg_ms": round(float(ms), 1)}
                     for t, n, u, ok, ms in tools if u >= K_ANON],
           "labels": {}}
    for kind, label, users, ok in labels:
        out["labels"].setdefault(kind, []).append(
            {"label": label, "users": users,
             "positive_rate": round(float(ok), 3)})
    return out
