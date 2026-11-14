"""A stranger with the shared link can get from zero to connected."""
import re

from copilot import welcome

ID = "front_door"
TITLE = "Try-it page and readable privacy and terms for people without repo access"
BACKLOG = "B-076"
BEFORE = ("The server's address showed 'Not Found', and the privacy notice "
          "and terms lived only in the private repository.")


def run(user, measure):
    open_page = welcome.home("https://demo.example/mcp", False, 60, 1500)
    invite_page = welcome.home("https://demo.example/mcp", True, 60, 1500)
    measure("connector address shown to copy",
            "https://demo.example/mcp</code>" in open_page, True)
    measure("assistants with setup steps (Claude, ChatGPT, editors)",
            len(re.findall(r"<summary>", open_page)), 3)
    say = open_page.split('class="say">')[1].split("</ul>")[0]
    measure("starter phrases offered (the spec's six ways in)",
            say.count("<li>"), 6)
    measure("unfilled placeholders", len(re.findall(r"{{\w+}}", open_page)),
            0)
    measure("invite-only told plainly only when it's on",
            ("Invite-only" in invite_page, "Invite-only" in open_page),
            (True, False))
    measure("outside scripts, fonts or trackers",
            len(re.findall(r"<(?:script|link)[^>]+(?:src|href)=", open_page)),
            0)
    for name in ("privacy", "terms"):
        page = welcome.document(name) or ""
        measure(f"{name} readable from the server", "<h1>" in page, True)
        measure(f"{name} links into the private repo",
                len(re.findall(r"blob/main", page)), 0)
