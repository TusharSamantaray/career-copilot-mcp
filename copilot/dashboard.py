"""The personal dashboard: one self-contained HTML file built from the
user's own data. Saved on their own device in local mode; returned as HTML
so the assistant can show it as an artifact everywhere else."""
import json
import os
from datetime import date, datetime, timezone
from pathlib import Path

from copilot import coach, finance, guide, nudges, prep, store

TEMPLATE = Path(__file__).with_name("dashboard.html")
STATUS_COLUMNS = [("applied", "Applied"), ("assessment", "Assessment"),
                  ("interviewing", "Interviewing"), ("offer", "Offer"),
                  ("closed", "Closed")]


def _pipeline(user):
    columns = {key: [] for key, _ in STATUS_COLUMNS}
    for row in store.list_kind(user, "application"):
        status = row["status"]
        key = "closed" if status in ("rejected", "withdrawn") else (
            "applied" if status == "saved" else status)
        columns.setdefault(key, []).append(
            {"company": row["company"], "role": row["role"],
             "status": status, "next": row.get("next_action", ""),
             "due": row.get("due_date", "")})
    return [{"key": k, "label": label, "items": columns.get(k, [])}
            for k, label in STATUS_COLUMNS]


def build_data(user, today=None):
    now = today or date.today()
    profile_rows = store.list_kind(user, "profile")
    profile = profile_rows[-1] if profile_rows else {}
    has_accounts = bool(store.list_kind(user, "account"))
    money = finance.dashboard(user, today=now) if has_accounts else None
    goals = finance.goals_review(user, today=now)
    stories = prep.story_match(user, "")
    return {
        "generated_at": datetime.now(timezone.utc).strftime(
            "%Y-%m-%d %H:%M UTC"),
        "today": str(now),
        "profile": {k: profile.get(k, "") for k in (
            "target_role", "current_role", "level", "industry", "country",
            "location", "goals")},
        "momentum": coach.momentum(user, now),
        "step": coach.daily_step(user, "medium", "", now),
        "due": nudges.nudges_due(user, now, within_days=3),
        "pipeline": _pipeline(user),
        "stories": {"count": stories["story_count"],
                    "missing": stories["missing_themes"]},
        "money": money and {k: money.get(k) for k in (
            "net_worth", "accessible", "locked", "illiquid", "debt",
            "monthly_burn", "runway_months", "stale_balances",
            "portfolio_flags")},
        "goals": goals.get("goals", []),
        "next": guide.next_steps(user)["next"],
    }


def render(data):
    payload = json.dumps(data).replace("</", "<\\/")
    return TEMPLATE.read_text(encoding="utf-8").replace("__DATA__", payload)


def save_local(html, folder=None):
    folder = Path(folder or os.environ.get(
        "CAREER_COPILOT_DASHBOARD_DIR", Path.home() / "CareerCopilot"))
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "dashboard.html"
    path.write_text(html, encoding="utf-8")
    return str(path)
