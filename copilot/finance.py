"""Personal finance: accounts, holdings, budget, runway and layoff fund."""
import math
from datetime import date

from copilot import store
from copilot.knowledge.money import DISCLAIMER

# kind -> bucket. Debt balances are stored as positive amounts owed.
ACCOUNT_KINDS = {
    "cash": "accessible", "brokerage": "accessible", "foreign": "accessible",
    "retirement": "locked", "hsa": "locked", "property": "illiquid",
    "debt": "debt", "other": "accessible",
}
STALE_DAYS = 30
CONCENTRATION_LIMIT = 0.10


def _key(prefix, name):
    return f"{prefix}:{name.strip().lower()}"


def account_set(user, name, kind, balance, as_of="", today=None):
    if kind not in ACCOUNT_KINDS:
        return {"error": f"kind must be one of {sorted(ACCOUNT_KINDS)}"}
    as_of = as_of or str(today or date.today())
    try:
        date.fromisoformat(as_of)
    except ValueError:
        return {"error": "as_of must be YYYY-MM-DD"}
    body ={"name": name, "kind": kind, "balance": float(balance),
            "as_of": as_of}
    store.put(user, "account", body, record_id=_key("acct", name))
    return {"saved": True, "bucket": ACCOUNT_KINDS[kind]}


def account_remove(user, name):
    return {"removed": store.delete(user, _key("acct", name))}


def holding_set(user, symbol, value, kind="stock", employer=False):
    if kind not in ("stock", "fund"):
        return {"error": "kind must be 'stock' or 'fund'"}
    body = {"symbol": symbol.upper(), "value": float(value), "kind": kind,
            "employer": bool(employer)}
    store.put(user, "holding", body, record_id=_key("hold", symbol))
    return {"saved": True}


def budget_set(user, category, current, target):
    body = {"category": category, "current": float(current),
            "target": float(target)}
    store.put(user, "budget", body, record_id=_key("budget", category))
    return {"saved": True}


RETIREMENT_WORDS = ("401", "403", "457", "ira", "roth", "pension",
                    "retirement", "rrsp", "tfsa", "sipp", "superannuation",
                    "provident", "epf", "nps")


def _kind_of(account):
    """Map a connector's account (e.g. Plaid type/subtype) to our kinds."""
    kind = str(account.get("kind") or "").lower()
    if kind in ACCOUNT_KINDS:
        return kind
    typ = str(account.get("type") or "").lower()
    sub = str(account.get("subtype") or "").lower()
    name = str(account.get("name") or "").lower()
    if "hsa" in (sub, name) or "health savings" in name:
        return "hsa"
    if any(w in f"{sub} {name}" for w in RETIREMENT_WORDS):
        return "retirement"
    if typ in ("credit", "loan") or sub in ("credit card", "mortgage",
                                            "student", "auto"):
        return "debt"
    if typ in ("investment", "brokerage") or sub in ("brokerage",):
        return "brokerage"
    if typ in ("depository", "cash") or sub in ("checking", "savings",
                                                "money market", "cd"):
        return "cash"
    return "other"


def _balance_of(account):
    bal = account.get("balance")
    if isinstance(bal, dict):
        bal = bal.get("current", bal.get("available"))
    return abs(float(bal or 0))


def finance_import(user, accounts, holdings=None, today=None):
    """Bulk-load accounts and holdings handed over from another connector.

    Keeps only a display name, kind and balance; account numbers, masks
    and ids are dropped.
    """
    as_of = str(today or date.today())
    imported, skipped = [], 0
    for acct in accounts or []:
        name = " ".join(str(p) for p in (acct.get("institution"),
                        acct.get("name") or acct.get("official_name")) if p)
        if not name:
            skipped += 1
            continue
        kind = _kind_of(acct)
        account_set(user, name, kind, _balance_of(acct), as_of)
        imported.append({"name": name, "kind": kind})
    held = 0
    for h in holdings or []:
        symbol = h.get("symbol") or h.get("name")
        value = h.get("market_value", h.get("value"))
        if not symbol or value is None:
            continue
        typ = str(h.get("type") or h.get("kind") or "").lower()
        kind = "fund" if any(w in typ for w in ("etf", "fund", "mutual")) \
            else "stock"
        holding_set(user, str(symbol)[:20], value, kind,
                    bool(h.get("employer")))
        held += 1
    return {"accounts_imported": imported, "accounts_skipped": skipped,
            "holdings_imported": held,
            "note": "Only names, kinds and balances were kept. Run "
                    "finance_dashboard to see the picture."}


def portfolio_check(user):
    holdings = store.list_kind(user, "holding")
    total = sum(h["value"] for h in holdings)
    if not total:
        return {"note": "No holdings yet. Add them with finance_holding_set."}
    rows, flags = [], []
    for h in sorted(holdings, key=lambda h: -h["value"]):
        weight = h["value"] / total
        rows.append({"symbol": h["symbol"], "kind": h["kind"],
                     "weight_pct": round(weight * 100, 1)})
        if h["kind"] == "stock" and weight > CONCENTRATION_LIMIT:
            flags.append(f"{h['symbol']} is {weight:.0%} of holdings, above "
                         f"the {CONCENTRATION_LIMIT:.0%} single-stock "
                         "guideline.")
        if h["employer"]:
            flags.append(f"{h['symbol']} is employer stock: job and savings "
                         "share one risk.")
    funds = sum(h["value"] for h in holdings if h["kind"] == "fund")
    return {"total": round(total, 2), "holdings": rows,
            "fund_share_pct": round(funds / total * 100, 1),
            "flags": flags or ["No concentration flags."],
            "disclaimer": DISCLAIMER}


def _monthly_burn(user):
    return sum(b["current"] for b in store.list_kind(user, "budget"))


def dashboard(user, monthly_burn=0.0, today=None):
    now = today or date.today()
    accounts = store.list_kind(user, "account")
    buckets = {"accessible": 0.0, "locked": 0.0, "illiquid": 0.0,
               "debt": 0.0}
    cash, stale = 0.0, []
    for acct in accounts:
        buckets[ACCOUNT_KINDS[acct["kind"]]] += acct["balance"]
        if acct["kind"] == "cash":
            cash += acct["balance"]
        age = (now - date.fromisoformat(acct["as_of"])).days
        if age > STALE_DAYS:
            stale.append(f"{acct['name']} ({age} days old)")
    burn = monthly_burn or _monthly_burn(user)
    net_worth = (buckets["accessible"] + buckets["locked"]
                 + buckets["illiquid"] - buckets["debt"])
    result = {
        "net_worth": round(net_worth, 2),
        "accessible": round(buckets["accessible"], 2),
        "locked": round(buckets["locked"], 2),
        "illiquid": round(buckets["illiquid"], 2),
        "debt": round(buckets["debt"], 2),
        "cash": round(cash, 2),
        "monthly_burn": round(burn, 2),
        "stale_balances": stale,
        "accounts": [{"name": a["name"], "kind": a["kind"],
                      "balance": a["balance"], "as_of": a["as_of"]}
                     for a in accounts],
    }
    if burn:
        result["runway_months"] = {
            "cash_only": round(cash / burn, 1),
            "all_accessible": round(buckets["accessible"] / burn, 1),
        }
        result["note"] = ("Runway counts accessible money only. Locked "
                          "money (retirement, HSA) carries taxes and "
                          "penalties to touch early.")
    else:
        result["note"] = ("Set monthly_burn or add a budget with "
                          "finance_budget_set to see runway.")
    portfolio = portfolio_check(user)
    if "flags" in portfolio:
        result["portfolio_flags"] = portfolio["flags"]
    result["disclaimer"] = DISCLAIMER
    return result


def budget_review(user):
    rows = store.list_kind(user, "budget")
    if not rows:
        return {"note": "No budget yet. Add categories with "
                        "finance_budget_set."}
    now = sum(r["current"] for r in rows)
    target = sum(r["target"] for r in rows)
    accessible = sum(a["balance"] for a in store.list_kind(user, "account")
                     if ACCOUNT_KINDS[a["kind"]] == "accessible")
    cuts = sorted(({"category": r["category"],
                    "saves": round(r["current"] - r["target"], 2)}
                   for r in rows if r["current"] > r["target"]),
                  key=lambda c: -c["saves"])
    result = {"current_monthly": round(now, 2),
              "target_monthly": round(target, 2),
              "monthly_savings": round(now - target, 2),
              "biggest_cuts": cuts}
    if accessible and now and target:
        result["runway_months_now"] = round(accessible / now, 1)
        result["runway_months_at_target"] = round(accessible / target, 1)
    return result


def _months_between(start, end):
    return (end.year - start.year) * 12 + end.month - start.month


def goal_set(user, name, target_amount, target_date, saved=0.0):
    try:
        date.fromisoformat(target_date)
    except ValueError:
        return {"error": "target_date must be YYYY-MM-DD"}
    body = {"name": name, "target_amount": float(target_amount),
            "target_date": target_date, "saved": float(saved)}
    store.put(user, "goal", body, record_id=_key("goal", name))
    return {"saved": True}


def goals_review(user, monthly_budget=0.0, today=None):
    """Monthly saving each goal needs, and whether the budget covers it."""
    now = today or date.today()
    rows = []
    for g in sorted(store.list_kind(user, "goal"),
                    key=lambda g: g["target_date"]):
        left = max(g["target_amount"] - g["saved"], 0)
        months = max(_months_between(now,
                                     date.fromisoformat(g["target_date"])), 1)
        rows.append({"name": g["name"], "target_date": g["target_date"],
                     "remaining": round(left, 2), "months_left": months,
                     "monthly_needed": round(left / months, 2),
                     "progress_pct": round(g["saved"] / g["target_amount"]
                                           * 100, 1)
                     if g["target_amount"] else 100.0})
    if not rows:
        return {"note": "No goals yet. Add one with goal_set (e.g. "
                        "emergency fund, home deposit, course fees)."}
    total = round(sum(r["monthly_needed"] for r in rows), 2)
    result = {"goals": rows, "total_monthly_needed": total}
    if monthly_budget:
        result["monthly_budget"] = monthly_budget
        result["on_track"] = monthly_budget >= total
        if not result["on_track"]:
            result["note"] = ("Budget falls short. Push the latest goal's "
                              "date out, lower a target, or raise savings.")
    return result


def future_projection(current_savings, monthly_saving, years,
                      target_amount=0.0, inflation=0.03):
    """Compound growth at three return rates, in today's money too."""
    scenarios = {}
    for label, rate in (("cautious", 0.03), ("balanced", 0.05),
                        ("growth", 0.07)):
        r = rate / 12
        balance, reached = current_savings, None
        for month in range(1, int(years * 12) + 1):
            balance = balance * (1 + r) + monthly_saving
            if target_amount and reached is None and balance >= target_amount:
                reached = round(month / 12, 1)
        real = balance / (1 + inflation) ** years
        scenarios[label] = {"annual_return_pct": rate * 100,
                            "future_value": round(balance, 2),
                            "in_todays_money": round(real, 2)}
        if target_amount:
            scenarios[label]["years_to_target"] = reached
    contributed = current_savings + monthly_saving * 12 * years
    return {"years": years, "total_contributed": round(contributed, 2),
            "scenarios": scenarios,
            "note": "Illustrative only: real returns vary year to year and "
                    "can be negative. Returns are before fees and taxes.",
            "disclaimer": DISCLAIMER}


def layoff_fund_plan(monthly_core_spend, current_fund, monthly_saving,
                     target_months=6, status_tied_to_job=False):
    months = max(target_months, 9) if status_tied_to_job else target_months
    target = monthly_core_spend * months
    gap = max(target - current_fund, 0)
    result = {
        "target_months": months,
        "target_fund": round(target, 2),
        "current_fund": round(current_fund, 2),
        "gap": round(gap, 2),
        "months_covered_now": round(current_fund / monthly_core_spend, 1)
        if monthly_core_spend else None,
    }
    if gap == 0:
        result["status"] = "Fully funded. Invest new savings instead."
    elif monthly_saving > 0:
        result["months_to_goal"] = math.ceil(gap / monthly_saving)
    else:
        result["status"] = "Set a monthly saving amount to reach the goal."
    if status_tied_to_job:
        result["note"] = ("Your status depends on employment, so the target "
                          "is at least 9 months: searches can outlast a "
                          "grace period.")
    result["disclaimer"] = DISCLAIMER
    return result
