"""Where to move for a role: ranks job hubs by field and priorities."""
from copilot import careers
from copilot.knowledge.careers import ROLES
from copilot.knowledge.places import CAUTIONS, COUNTRY_ALIASES, HUBS

PRIORITIES = ("low_cost", "big_market", "stay_in_country", "english")
ENGLISH = {"US", "CA", "GB", "IE", "IN", "SG", "AU", "AE"}


def _country(code):
    code = (code or "").strip()
    return COUNTRY_ALIASES.get(code.lower(), code.upper()[:2]) if code else ""


def where_to_move(target_role, country="", priorities=None,
                  open_to_abroad=False):
    role_key = careers.resolve_role(target_role)
    if not role_key:
        return {"error": f"Unknown role. Try one of {sorted(ROLES)}"}
    family = ROLES[role_key]["family"]
    home = _country(country)
    prefs = [p for p in (priorities or []) if p in PRIORITIES]
    ranked = []
    for city, cc, families, cost, note in HUBS:
        if home and not open_to_abroad and cc != home:
            continue
        if family not in families:
            continue
        score = 3 + (2 if families[0] == family else 0)
        reasons = [f"strong {family} market"]
        if "low_cost" in prefs:
            score += 3 - cost
            if cost == 1:
                reasons.append("lower cost of living")
        if "big_market" in prefs and len(families) >= 4:
            score += 2
            reasons.append("large, varied job market")
        if home and cc == home:
            score += 2
            reasons.append("no visa needed")
        if "english" in prefs and cc in ENGLISH:
            score += 1
        ranked.append({"city": city, "country": cc, "cost_tier": cost,
                       "score": score, "why": reasons, "note": note})
    ranked.sort(key=lambda r: -r["score"])
    if home and open_to_abroad:
        # They asked about abroad, so always show the best two there.
        local = [r for r in ranked if r["country"] == home][:3]
        abroad = [r for r in ranked if r["country"] != home]
        ranked = local + abroad[:5 - len(local)]
    out = {"role": ROLES[role_key]["title"], "family": family,
           "options": ranked[:5], "remote_first": "Before moving, apply to "
           "remote roles too: you keep your home costs and still reach "
           "bigger markets.", "cautions": CAUTIONS}
    if not ranked:
        out["note"] = ("No listed hub in that country is strong for this "
                       "field. Try open_to_abroad=true, or focus on remote "
                       "roles.")
    return out
