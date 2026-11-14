"""Company research and the one-page brief (GitHub #34, #35).

company_research gathers public facts about one company, each with its
source: the company's own words from its home page, its public job
board (open roles, locations, newest posting date), and facts the
assistant found with its own web search, which must carry a link. A fact
without a link is listed as unverified and can't go on a one-pager.
Nothing is stored: the record goes back to the assistant, which passes
it to one_pager_build.

one_pager_build turns that record and the person's confirmed facts into
a one-page brief. The assistant writes the lines; this module checks
that every line cites a source, every number appears in a cited source,
the wording passes response_check, and it fits on one page. Then it lays
it out as print-ready HTML (save as PDF from the browser).

Fetching is read-only and careful: https only, a public host name (no IP
addresses, nothing that resolves to a private network), no redirects
off the site, a size cap and a short timeout.
"""
import hashlib
import html
import ipaddress
import json
import os
import re
import socket
from datetime import date

import httpx

from copilot import conduct
from copilot import facts
from copilot import jobs

KINDS = ("what_they_do", "service_line", "size", "offices",
         "differentiator", "news", "hiring_context", "other")
WANTED = ("what_they_do", "service_line", "differentiator", "news",
          "hiring_context")
HOST = re.compile(r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}")
MAX_BYTES = 400_000
# Tests point this at a JSON file of {url: page} instead of the web.
WEB_FIXTURE = os.environ.get("CAREER_COPILOT_WEB_FIXTURE", "")
BOARD_PAGES = {"greenhouse": "https://boards.greenhouse.io/{slug}",
               "lever": "https://jobs.lever.co/{slug}",
               "ashby": "https://jobs.ashbyhq.com/{slug}"}
META = re.compile(r"<meta\s+[^>]*?(?:name|property)\s*=\s*[\"']"
                  r"(description|og:description|og:site_name)[\"'][^>]*?"
                  r"content\s*=\s*[\"']([^\"']{3,600})[\"']", re.I | re.S)
META_REV = re.compile(r"<meta\s+[^>]*?content\s*=\s*[\"']([^\"']{3,600})"
                      r"[\"'][^>]*?(?:name|property)\s*=\s*[\"']"
                      r"(description|og:description|og:site_name)[\"']",
                      re.I | re.S)
TITLE = re.compile(r"<title[^>]*>([^<]{2,200})</title>", re.I)


# --------------------------------------------------------------- fetching

def _public(host):
    """True only for a real public host name: no IP literals, and every
    address it resolves to is on the public internet."""
    if not HOST.fullmatch(host or ""):
        return False
    try:
        infos = socket.getaddrinfo(host, 443, proto=socket.IPPROTO_TCP)
    except OSError:
        return False
    return bool(infos) and all(
        ipaddress.ip_address(i[4][0].split("%")[0]).is_global for i in infos)


def _fetch(url):
    """The page's text, or None. Follows one redirect, and only within
    the same site (example.com to www.example.com)."""
    if WEB_FIXTURE:
        with open(WEB_FIXTURE, encoding="utf-8") as handle:
            return json.load(handle).get(url)
    for _ in range(2):
        host = httpx.URL(url).host
        if not url.startswith("https://") or not _public(host):
            return None
        try:
            with httpx.stream("GET", url, timeout=8, follow_redirects=False,
                              headers={"User-Agent": jobs.USER_AGENT}) as r:
                if r.status_code in (301, 302, 303, 307, 308):
                    nxt = str(r.url.join(r.headers.get("location", "")))
                    new = httpx.URL(nxt).host
                    if not (new == host or new.endswith("." + host)
                            or host.endswith("." + new)):
                        return None
                    url = nxt
                    continue
                if r.status_code != 200:
                    return None
                body = b""
                for chunk in r.iter_bytes():
                    body += chunk
                    if len(body) > MAX_BYTES:
                        break
                return body[:MAX_BYTES].decode(r.encoding or "utf-8",
                                               errors="replace")
        except (httpx.HTTPError, ValueError):
            return None
    return None


fetch_page = _fetch           # tests swap this for canned pages


def _domain(value):
    value = (value or "").strip().lower()
    value = re.sub(r"^[a-z]+://", "", value).split("/")[0].split(":")[0]
    return value if HOST.fullmatch(value) else ""


def _id(kind, statement):
    return "c" + hashlib.sha256(f"{kind}|{statement}".encode()) \
        .hexdigest()[:6]


def _clean(text, limit=300):
    text = re.sub(r"\s+", " ", html.unescape(text or "")).strip()
    return text[:limit].rstrip()


def _homepage(domain):
    url = f"https://{domain}/"
    page = fetch_page(url)
    if not page:
        return [], f"Couldn't read {url} (offline, blocked or not public)."
    meta = {}
    for name, content in META.findall(page):
        meta.setdefault(name.lower(), content)
    for content, name in META_REV.findall(page):
        meta.setdefault(name.lower(), content)
    title = TITLE.search(page)
    words = meta.get("description") or meta.get("og:description")
    out = []
    if words:
        out.append({"kind": "what_they_do",
                    "statement": f"In their own words: \"{_clean(words)}\"",
                    "source": url, "how": "their website"})
    elif title:
        out.append({"kind": "what_they_do",
                    "statement": f"Home page title: \"{_clean(title.group(1))}\"",
                    "source": url, "how": "their website"})
    return out, None


def _slugs(company, domain):
    base = domain.split(".")[-2] if domain.count(".") >= 1 else ""
    name = re.sub(r"[^a-z0-9]", "", company.lower())
    dashed = re.sub(r"[^a-z0-9]+", "-", company.lower()).strip("-")
    return list(dict.fromkeys(s for s in (base, name, dashed) if s))


def _hiring(company, domain):
    for slug in _slugs(company, domain):
        for board, api in jobs.BOARDS.items():
            roles = list(jobs._normalize(board, slug,
                                         jobs._get(api.format(slug=slug))))
            if not roles:
                continue
            dated = sorted(r["posted"] for r in roles if r["posted"])
            places = [r["location"] for r in roles if r["location"]]
            top = sorted(set(places), key=lambda p: -places.count(p))[:3]
            titles = [r["title"] for r in roles][:5]
            text = (f"{len(roles)} open roles on their public "
                    f"{board.title()} board")
            if top:
                text += f", mostly in {', '.join(top)}"
            if dated:
                text += f"; newest posted {dated[-1].isoformat()}"
            return [{"kind": "hiring_context", "statement": text + ".",
                     "source": BOARD_PAGES[board].format(slug=slug),
                     "how": "public job board",
                     "check": "Matched by name: make sure it's their board."},
                    {"kind": "hiring_context",
                     "statement": "Roles open now include: "
                                  + "; ".join(titles) + ".",
                     "source": BOARD_PAGES[board].format(slug=slug),
                     "how": "public job board"}]
    return []


# ---------------------------------------------------------------- research

def research(company, domain="", found=None, fetch=True, today=None):
    """A sourced record of public facts about one company."""
    company = _clean(company, 80)
    if not company:
        return {"error": "Which company? Give its name, and its website "
                         "if you know it."}
    domain = _domain(domain)
    today = today or date.today()
    record, unverified, notes = [], [], []
    if fetch and domain:
        site, problem = _homepage(domain)
        record += site
        if problem:
            notes.append(problem)
    if fetch:
        record += _hiring(company, domain)
    for item in found or []:
        if not isinstance(item, dict):
            item = {"statement": str(item)}
        statement = _clean(item.get("statement", ""))
        if not statement:
            continue
        kind = item.get("kind") if item.get("kind") in KINDS else "other"
        source = str(item.get("source", "")).strip()
        if not re.match(r"https://\S+$", source):
            unverified.append({"kind": kind, "statement": statement,
                               "why": "No https link to where it's said."})
            continue
        record.append({"kind": kind, "statement": statement,
                       "source": source[:300], "how": "found by search"})
    seen, unique = set(), []
    for fact in record:
        key = fact["statement"].lower()
        if key not in seen:
            seen.add(key)
            unique.append({"id": _id(fact["kind"], fact["statement"]),
                           **fact})
    have = {f["kind"] for f in unique}
    gaps = [k for k in WANTED if k not in have]
    queries = {"what_they_do": f"{company} what we do",
               "service_line": f"{company} services",
               "differentiator": f"{company} approach OR methodology",
               "news": f"{company} news {today.year}",
               "hiring_context": f"{company} careers"}
    return {
        "company": company, "domain": domain or None,
        "as_of": today.isoformat(), "facts": unique,
        "unverified": unverified, "gaps": gaps,
        "search_next": [queries[g] for g in gaps],
        "notes": notes,
        "stored": "Nothing. Pass this record to one_pager_build.",
        "say": "Say what they do in one line, with the source. For any "
               "gap, search the web and call again with found=[{kind, "
               "statement, source}]. Never fill a gap from memory.",
    }


# --------------------------------------------------------------- one-pager

SECTIONS = {
    "fit": "The fit",
    "plugs_in": "How I plug into your system",
    "what_changes": "What changes, by line",
    "why_now": "Why this, why now",
    "offer": "The offer",
}
MAX_WORDS = 380
MAX_LINE_WORDS = 45
MAX_LINES = 4


def _words(text):
    return {w for w in re.findall(r"[a-z]{4,}", (text or "").lower())}


def _numbers(text):
    years = re.compile(r"^(?:19|20)\d\d$")
    return {conduct._norm(n) for n in conduct.NUMBER.findall(text or "")
            if not years.match(conduct._norm(n))
            and not re.fullmatch(r"\d", n.strip())}


def _sources(user, record):
    known = {}
    for f in (record or {}).get("facts", []):
        if f.get("id") and f.get("source", "").startswith("https://"):
            known[f["id"]] = {"statement": f.get("statement", ""),
                              "source": f["source"], "whose": "company"}
    for f in facts.confirmed_facts(user):
        known["f" + str(f["id"])] = {"statement": f["statement"],
                                     "source": "your confirmed work history",
                                     "whose": "you"}
    return known


def _material(user, record, role, known):
    company_facts = {k: v for k, v in known.items() if v["whose"] == "company"}
    mine = {k: v for k, v in known.items() if v["whose"] == "you"}
    target = " ".join(v["statement"] for v in company_facts.values()) + \
        " " + role

    def best(text, n=2):
        want = _words(text)
        ranked = sorted(mine, key=lambda k: -len(_words(mine[k]["statement"])
                                                 & want))
        return [k for k in ranked[:n] if _words(mine[k]["statement"]) & want]

    lines = [k for k, v in company_facts.items()
             if any(f["id"] == k and f["kind"] in ("service_line",
                                                    "what_they_do")
                    for f in record.get("facts", []))]
    why = [f["id"] for f in record.get("facts", [])
           if f.get("kind") in ("news", "differentiator", "hiring_context")
           and f["id"] in known]
    return {
        # Nothing overlaps in wording: offer their facts anyway, and let
        # the assistant ask which one fits.
        "fit": best(target, 3) or list(mine)[:3],
        "plugs_in": [{"company": k, "you": best(company_facts[k]["statement"],
                                                1)} for k in lines[:3]],
        "what_changes": [{"company": k,
                          "you": best(company_facts[k]["statement"], 1)}
                         for k in lines[:3]],
        "why_now": why[:3],
        "offer": "Use the person's own words for what they propose (for "
                 "example a 20-minute call). Pass it as offer.",
    }


def one_pager(user, record, role="", lines=None, offer="", me=""):
    """Draft mode (no lines): the sourced material per section. Build
    mode: check every line and lay out one printable page."""
    if not isinstance(record, dict) or not record.get("company"):
        return {"error": "Pass the record from company_research."}
    known = _sources(user, record)
    company = _clean(record["company"], 80)
    if not any(v["whose"] == "you" for v in known.values()):
        return {"error": "No confirmed facts about your work yet, so there's "
                         "nothing true to put on the page.",
                "ask": "What's one thing you did in your last role that "
                       "fits this company? I'll read it back to confirm."}
    if not lines:
        return {"mode": "draft", "company": company, "sections": SECTIONS,
                "material": _material(user, record, role, known),
                "sources": known,
                "write": f"Write 1 to {MAX_LINES} short lines per section "
                         f"(under {MAX_LINE_WORDS} words each, "
                         f"{MAX_WORDS} in all). Each line cites the source "
                         "ids it rests on. Use a number only if a cited "
                         "source has it. Then call again with lines=[{"
                         "section, text, sources}] and offer.",
                "stored": "Nothing."}
    problems, built = [], {k: [] for k in SECTIONS}
    total = 0
    offer = _clean(offer, 200)
    lines = list(lines)
    if offer:
        known["offer"] = {"statement": offer, "source": "your offer",
                          "whose": "you"}
        if not any((x or {}).get("section") == "offer" for x in lines):
            lines.append({"section": "offer", "text": offer,
                          "sources": ["offer"]})
    for n, line in enumerate(lines, 1):
        section = (line or {}).get("section", "")
        text = _clean((line or {}).get("text", ""), 400)
        cited = [s for s in (line or {}).get("sources", []) if s]
        if section not in SECTIONS:
            problems.append(f"Line {n}: section must be one of "
                            f"{list(SECTIONS)}.")
            continue
        if not text:
            continue
        missing = [s for s in cited if s not in known]
        if not cited or missing:
            problems.append(f"Line {n} ('{text[:40]}…') needs sources from "
                            "the record or your confirmed facts"
                            + (f"; unknown: {missing}" if missing else "")
                            + ".")
            continue
        backed = set().union(*(_numbers(known[s]["statement"])
                               for s in cited))
        loose = sorted(_numbers(text) - backed)
        if loose:
            problems.append(f"Line {n}: {loose} isn't in any source it "
                            "cites. Remove it or cite where it's from.")
        count = len(text.split())
        if count > MAX_LINE_WORDS:
            problems.append(f"Line {n} has {count} words; keep it under "
                            f"{MAX_LINE_WORDS}.")
        total += count
        check = conduct.check(user, text, "cover_letter")
        for issue in check["issues"]:
            if issue["type"] == "unsupported_number":
                continue        # checked above against the cited sources
            if issue["severity"] == "fix":
                problems.append(f"Line {n}: {issue['why']} "
                                f"({', '.join(issue['found'])})")
        built[section].append((text, cited))
    for key, items in built.items():
        if len(items) > MAX_LINES:
            problems.append(f"{SECTIONS[key]} has {len(items)} lines; keep "
                            f"it to {MAX_LINES}.")
    if total > MAX_WORDS:
        problems.append(f"{total} words won't fit one page; cut to "
                        f"{MAX_WORDS}.")
    empty = [SECTIONS[k] for k in ("fit", "offer") if not built[k]]
    if empty:
        problems.append(f"Missing: {', '.join(empty)}.")
    if problems:
        return {"ok": False, "problems": problems,
                "next": "Fix these, then call again. No page until it "
                        "passes."}
    page, used = _render(company, role, me, built, known)
    return {"ok": True, "html": page, "words": total, "sources_used": used,
            "say": "Show the html as an artifact titled with the company "
                   "name. It's sized to one page: to get a PDF, open it and "
                   "print or save as PDF. The person reviews it before it "
                   "goes anywhere.",
            "stored": "Nothing."}


def _render(company, role, me, built, known):
    order, notes = [], {}
    for items in built.values():
        for _, cited in items:
            for s in cited:
                if s not in notes and known[s]["whose"] == "company":
                    notes[s] = len(notes) + 1
                    order.append(s)
    esc = html.escape
    parts = []
    for key, title in SECTIONS.items():
        if not built[key]:
            continue
        rows = "".join(
            "<li>" + esc(text) + "".join(
                f"<sup>{notes[s]}</sup>" for s in cited if s in notes)
            + "</li>" for text, cited in built[key])
        parts.append(f"<section><h2>{esc(title)}</h2><ul>{rows}</ul>"
                     "</section>")
    foot = "".join(f"<li>{esc(known[s]['source'])}</li>" for s in order)
    heading = esc(f"{me + ' for ' if me else ''}{company}")
    sub = esc(role) if role else "A one-page brief"
    page = (
        "<!doctype html><html lang=en><meta charset=utf-8>"
        f"<title>{heading}</title><style>"
        "@page{size:auto;margin:14mm}"
        ":root{--fg:#17201b;--muted:#5b655f;--line:#d9ded9;--accent:#1f7a55}"
        "body{margin:0;color:var(--fg);background:#fff;"
        "font:10.5pt/1.45 system-ui,-apple-system,'Segoe UI',sans-serif}"
        "main{max-width:180mm;margin:0 auto;padding:10mm 0}"
        "h1{font-size:19pt;margin:0}p.sub{margin:.2rem 0 1rem;"
        "color:var(--muted)}h2{font-size:10pt;text-transform:uppercase;"
        "letter-spacing:.06em;color:var(--accent);margin:0 0 .3rem}"
        "section{padding:.55rem 0;border-top:1px solid var(--line)}"
        "ul{margin:0;padding-left:1.1rem}li{margin:.15rem 0}"
        "sup{color:var(--muted);font-size:7pt;margin-left:1px}"
        "footer{border-top:1px solid var(--line);margin-top:.6rem;"
        "padding-top:.4rem;font-size:7.5pt;color:var(--muted)}"
        "footer ol{margin:0;padding-left:1rem;overflow-wrap:anywhere}"
        "@media print{main{padding:0}}</style><body><main>"
        f"<h1>{heading}</h1><p class=sub>{sub}</p>{''.join(parts)}"
        "<footer>Sources: company facts are public, linked below. Lines "
        "about me come from my own confirmed work history."
        f"{'<ol>' + foot + '</ol>' if foot else ''}</footer>"
        "</main></body></html>")
    return page, order
