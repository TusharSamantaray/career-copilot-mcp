"""The public pages a stranger sees: a "Try Career Copilot" page at /,
and the privacy notice and terms at /privacy and /terms.

The repository is private, so links into GitHub 404 for anyone the owner
hasn't invited. These pages are served by the server itself, so a link
shared with a friend always works. Static text only; nothing about any
person, and no outside scripts, fonts or trackers.
"""
import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TEMPLATE = ROOT / "welcome.html"
DOCS = ROOT.parent / "docs"
PAGES = {"privacy": "PRIVACY.md", "terms": "TERMS.md"}
LINKS = {"PRIVACY.md": "/privacy", "TERMS.md": "/terms"}
# Same as the sign-in pages: never framed, never cached, no referrer.
HEADERS = {"X-Frame-Options": "DENY",
           "Content-Security-Policy": "frame-ancestors 'none'",
           "Cache-Control": "no-store", "Referrer-Policy": "no-referrer"}
PROMISES = [
    "Only you can read your data. Export or delete it any time.",
    "Nothing is sent, posted or scheduled without your yes to the exact "
    "text.",
    "It never applies for you and never asks for a password.",
    "Only facts you confirm go on a resume. No invented numbers.",
    "Education and drafts, not professional advice.",
]


STATUS = {
    "open": ("ok", "Open: room for new people today."),
    "new_paused": ("warn", "Not taking new people right now, so it stays "
                   "fast for those already in. Check back later."),
    "full_today": ("warn", "Full for today: the free servers' daily budget "
                   "is used. It reopens at midnight UTC. Nothing is lost."),
}


def home(mcp_url, invite_only, per_minute, per_day, status="open"):
    """The try-it page, filled in for this server."""
    url = html.escape(mcp_url)
    tone, words = STATUS.get(status, STATUS["open"])
    access = ("<p class='warn'>Invite-only for now. Send your GitHub "
              "username to the person who shared this link, and they'll "
              "add you.</p>" if invite_only else
              "<p class='note'>Open to anyone with a GitHub account. Each "
              "person gets their own private, encrypted space.</p>")
    page = TEMPLATE.read_text(encoding="utf-8")
    for key, value in {
        "MCP_URL": url, "ACCESS_NOTE": access,
        "PROMISES": "".join(f"<li>{html.escape(p)}</li>" for p in PROMISES),
        "PER_MINUTE": str(per_minute), "PER_DAY": f"{per_day:,}",
        "STATUS": f"<p class='status {tone}'>Trial status: "
                  f"{html.escape(words)}</p>",
    }.items():
        page = page.replace("{{" + key + "}}", value)
    return page


def _inline(text):
    text = html.escape(text, quote=False)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)

    def link(match):
        label, target = match.group(1), match.group(2)
        target = LINKS.get(target.split("#")[0], target)
        if not target.startswith(("/", "https://", "http://")):
            return label             # a repo-relative link: keep the words
        return f"<a href='{html.escape(target)}'>{label}</a>"
    return re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", link, text)


def markdown(text):
    """Just enough Markdown for PRIVACY.md and TERMS.md: headings,
    paragraphs, bullet and numbered lists, tables, bold, code, links."""
    out, para, items, table = [], [], [], []

    def flush():
        if para:
            out.append(f"<p>{_inline(' '.join(para))}</p>")
            para.clear()
        if items:
            tag = "ol" if items[0][0] else "ul"
            out.append(f"<{tag}>" + "".join(
                f"<li>{_inline(t)}</li>" for _, t in items) + f"</{tag}>")
            items.clear()
        if table:
            rows = [r for r in table if not re.fullmatch(r"[|\s:-]+", r)]
            cells = [[c.strip() for c in r.strip().strip("|").split("|")]
                     for r in rows]
            head = "".join(f"<th>{_inline(c)}</th>" for c in cells[0])
            body = "".join("<tr>" + "".join(f"<td>{_inline(c)}</td>"
                                            for c in row) + "</tr>"
                           for row in cells[1:])
            out.append(f"<div class='t'><table><tr>{head}</tr>{body}"
                       "</table></div>")
            table.clear()

    for line in text.splitlines():
        heading = re.match(r"(#{1,4})\s+(.*)", line)
        bullet = re.match(r"\s*(?:([-*])|(\d+)[.)])\s+(.*)", line)
        if not line.strip():
            flush()
        elif heading:
            flush()
            level = len(heading.group(1))
            out.append(f"<h{level}>{_inline(heading.group(2))}</h{level}>")
        elif line.lstrip().startswith("|"):
            if para or items:
                flush()
            table.append(line)
        elif bullet:
            if para or table:
                flush()
            items.append((bool(bullet.group(2)), bullet.group(3)))
        elif items and line.startswith(" "):
            items[-1] = (items[-1][0], items[-1][1] + " " + line.strip())
        else:
            para.append(line.strip())
    flush()
    return "\n".join(out)


def document(name):
    """The privacy notice or terms as a readable page; None if this
    install has no docs folder (a packaged local install)."""
    path = DOCS / PAGES[name]
    if not path.exists():
        return None
    body = markdown(path.read_text(encoding="utf-8"))
    title = "Privacy" if name == "privacy" else "Terms"
    return (
        "<!doctype html><html lang=en><meta charset=utf-8>"
        "<meta name=viewport content='width=device-width,initial-scale=1'>"
        f"<title>Career Copilot: {title}</title><style>"
        ":root{--bg:#f7f6f2;--fg:#1d1f1c;--muted:#5d625a;--line:#e3e1d8;"
        "--accent:#1f7a55}@media (prefers-color-scheme:dark){:root{"
        "--bg:#141614;--fg:#ecebe6;--muted:#a3a89f;--line:#2e322d;"
        "--accent:#5cc497;color-scheme:dark}}"
        "body{margin:0;background:var(--bg);color:var(--fg);"
        "font:16px/1.6 system-ui,-apple-system,'Segoe UI',sans-serif}"
        "main{max-width:44rem;margin:0 auto;padding:2.5rem 16px 4rem}"
        "h1{line-height:1.2}h2{margin-top:2rem}a{color:var(--accent)}"
        ".t{overflow-x:auto}table{border-collapse:collapse;width:100%;"
        "font-size:.93rem}th,td{border-bottom:1px solid var(--line);"
        "text-align:left;vertical-align:top;padding:.45rem .5rem}"
        "nav{font-size:.9rem;color:var(--muted)}</style>"
        "<body><main><nav><a href='/'>← Career Copilot</a></nav>"
        f"{body}</main></body></html>")
