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
    with _connect() as conn:
        conn.execute("INSERT INTO signals VALUES (?,?,?,?,?,?)",
                     (kind, label, _who(user_id), str(date.today()),
                      int(ok), round(ms, 1)))


def forget(user_id):
    """Remove one user's signals (called by data_delete)."""
    if not ENABLED or not os.path.exists(DB_PATH):
        return
    with _connect() as conn:
        conn.execute("DELETE FROM signals WHERE who=?", (_who(user_id),))


def summary(since_days=30):
    """Aggregates only, with every label behind the K_ANON threshold."""
    if not os.path.exists(DB_PATH):
        return {"k_anon": K_ANON, "tools": [], "labels": {}}
    cutoff = str(date.fromordinal(date.today().toordinal() - since_days))
    with _connect() as conn:
        tools = conn.execute(
            "SELECT label, COUNT(*), COUNT(DISTINCT who), "
            "AVG(ok), AVG(ms) FROM signals WHERE kind='tool' AND day>=? "
            "GROUP BY label ORDER BY COUNT(*) DESC", (cutoff,)).fetchall()
        labels = conn.execute(
            "SELECT kind, label, COUNT(DISTINCT who) AS users, "
            "AVG(ok) FROM signals WHERE kind!='tool' AND day>=? "
            "GROUP BY kind, label HAVING users>=? ORDER BY users DESC",
            (cutoff, K_ANON)).fetchall()
    out = {"since_days": since_days, "k_anon": K_ANON,
           "tools": [{"tool": t, "calls": n, "users": u,
                      "success_rate": round(ok, 3), "avg_ms": round(ms, 1)}
                     for t, n, u, ok, ms in tools if u >= K_ANON],
           "labels": {}}
    for kind, label, users, ok in labels:
        out["labels"].setdefault(kind, []).append(
            {"label": label, "users": users, "positive_rate": round(ok, 3)})
    return out
