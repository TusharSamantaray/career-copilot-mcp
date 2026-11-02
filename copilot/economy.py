"""Live macro indicators from the World Bank API (free, no key)."""
import time

import httpx

from copilot.knowledge.money import WORLD_BANK_INDICATORS

API = "https://api.worldbank.org/v2/country/{country}/indicator/{code}"
CACHE_SECONDS = 6 * 3600
_cache = {}


async def _fetch(client, country, code):
    key = (country, code)
    hit = _cache.get(key)
    if hit and time.time() - hit[0] < CACHE_SECONDS:
        return hit[1]
    resp = await client.get(API.format(country=country, code=code),
                            params={"format": "json", "mrv": 5})
    resp.raise_for_status()
    payload = resp.json()
    if len(payload) < 2 or not payload[1]:
        raise ValueError(f"no data for {country}/{code}")
    series = [{"year": row["date"], "value": row["value"]}
              for row in payload[1] if row["value"] is not None]
    country_name = payload[1][0]["country"]["value"]
    _cache[key] = (time.time(), (country_name, series))
    return country_name, series


async def indicators(country="USA", names=None):
    names = names or list(WORLD_BANK_INDICATORS)
    unknown = [n for n in names if n not in WORLD_BANK_INDICATORS]
    if unknown:
        return {"error": f"unknown indicators {unknown}",
                "available": sorted(WORLD_BANK_INDICATORS)}
    out = {"country": country.upper(), "source": "World Bank Open Data",
           "indicators": {}}
    async with httpx.AsyncClient(timeout=10) as client:
        for name in names:
            code, label = WORLD_BANK_INDICATORS[name]
            try:
                country_name, series = await _fetch(client, country, code)
            except (httpx.HTTPError, ValueError, KeyError) as exc:
                out["indicators"][name] = {"label": label,
                                           "error": str(exc)[:120]}
                continue
            out["country_name"] = country_name
            out["indicators"][name] = {
                "label": label,
                "latest": series[0] if series else None,
                "history": series}
    out["note"] = ("Annual data; the latest year can lag 1-2 years. Use "
                   "economy_guide to interpret it.")
    return out
