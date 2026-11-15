"""Stable error codes, so an assistant knows whether to retry, reconnect
or stop, and so a person can report a problem without sending anything
personal.

Every tool or resource error starts with its code in brackets, e.g.
"[AUTH_REQUIRED] Sign in with GitHub." The wording after it may change;
the code never does. report_issue looks codes up here.
"""
import re
import secrets

# code: (what happened, should the assistant retry?, what to do)
CODES = {
    "AUTH_REQUIRED": (
        "The request had no valid sign-in.", False,
        "Reconnect the connector and sign in with GitHub. If it keeps "
        "asking, the owner may have changed the sign-in key."),
    "NOT_INVITED": (
        "Signed in, but this GitHub username isn't on the invite list.",
        False, "Ask the owner to add your GitHub username, then reconnect."),
    "UNKNOWN_TOOL": (
        "The assistant called a tool this server doesn't have, usually "
        "because its tool list is out of date after an update.", False,
        "Refresh the tool list: disconnect and reconnect the connector, "
        "or start a new chat."),
    "UNKNOWN_RESOURCE": (
        "The assistant asked for a resource this server doesn't have.",
        False, "Refresh the connector, as for UNKNOWN_TOOL."),
    "BAD_ARGUMENTS": (
        "A tool was called with a missing or wrongly typed value.", False,
        "The message names the fields. Call the tool again with them "
        "fixed; if the assistant keeps doing it, refresh the tool list."),
    "RATE_LIMITED": (
        "Too many requests from this account in one minute.", True,
        "Wait the seconds the message names, then carry on. Nothing was "
        "lost. If it keeps happening, the assistant may be stuck in a "
        "loop: start a new chat."),
    "DAILY_LIMIT": (
        "This account used today's fair-use quota.", False,
        "It resets at midnight UTC. Your data is safe. If you need more, "
        "tell the owner with report_issue."),
    "TRIAL_FULL": (
        "The free trial is at capacity: today's shared budget is used, or "
        "it isn't taking new people for now.", False,
        "Not an error and nothing was lost. Come back after midnight UTC, "
        "or ask the person who shared the link. Exporting and deleting "
        "your data still work."),
    "INTERNAL_ERROR": (
        "Something failed on the server. It was logged with a reference.",
        True, "Try once more after a few seconds. If it fails again, report "
        "it with report_issue and the ref, and try a different step for "
        "now."),
}

# Hosts people actually connect from. Anything else is "other", so a
# hint can never carry a name or other personal text.
CLIENTS = ("claude", "chatgpt", "cursor", "vscode", "copilot", "muse",
           "gemini", "windsurf", "zed")

_CODE = re.compile(r"\[([A-Z_]+)\]")


def message(code, text):
    return f"[{code}] {text}"


def new_ref():
    """Short reference shown to the person and written to the log."""
    return secrets.token_hex(3)


def field_errors(error):
    """Field names and problem kinds from a validation error, never the
    values sent (those can be personal)."""
    try:
        problems = [f"{'.'.join(str(p) for p in e['loc']) or 'input'} "
                    f"({e['type'].replace('_', ' ')})"
                    for e in error.errors()]
    except Exception:
        return "one or more values"
    return ", ".join(problems[:5]) or "one or more values"


def client_family(hint):
    hint = (hint or "").lower()
    return next((name for name in CLIENTS if name in hint), "other")


def lookup(code_or_text):
    """Find a code by name, or inside a pasted error message."""
    text = (code_or_text or "").strip()
    found = _CODE.search(text)
    code = (found.group(1) if found else text).upper()
    return code if code in CODES else None
