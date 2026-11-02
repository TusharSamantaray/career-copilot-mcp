"""Other connectors that pair with Career Copilot in the user's own chat.

Career Copilot never logs in anywhere. The user connects these in their
assistant, the assistant reads from them, and hands Career Copilot only
the fields it needs.
"""

COMPANIONS = {
    "email": {
        "connectors": "Gmail or Outlook / Microsoft 365 connector in the "
                      "user's assistant",
        "read": "Job-related emails from the last 2-4 weeks: from, subject, "
                "date and a short snippet",
        "hand_to": "inbox_triage(emails), then inbox_triage(apply=true) "
                   "after the user agrees",
    },
    "calendar": {
        "connectors": "Google Calendar or Outlook calendar connector",
        "read": "Upcoming events for the next 2 weeks: subject, start, "
                "organizer",
        "hand_to": "calendar_interviews(events, apply=true)",
    },
    "meetings": {
        "connectors": "Zoom (or Teams / Meet) connector",
        "read": "Upcoming meetings: topic, start time, join link",
        "hand_to": "calendar_interviews(events, apply=true)",
    },
    "finance": {
        "connectors": "A bank-data connector such as a self-hosted Plaid "
                      "MCP, or the user typing rounded balances",
        "read": "Accounts with name, type/subtype and current balance; "
                "investment holdings with symbol and market value",
        "hand_to": "finance_import(accounts, holdings). Never pass account "
                   "numbers, logins or full transaction history",
    },
    "resume": {
        "connectors": "Google Drive, OneDrive or Notion connector, or a "
                      "pasted file",
        "read": "The text of each past resume version",
        "hand_to": "resume_import(text, label) for each, then resume_merge",
    },
    "notes": {
        "connectors": "Notion connector",
        "read": "Nothing by default; write plans or story banks there only "
                "if the user asks",
        "hand_to": "story_add for stories the user confirms",
    },
    "design": {
        "connectors": "Figma connector (for builders of companion views)",
        "read": "Frames from a link the user shares",
        "hand_to": "Not used by Career Copilot tools directly",
    },
}

RULES = [
    "Never ask the user for a password, one-time code or bank login.",
    "Read from the user's own connectors; pass Career Copilot only the "
    "fields listed under 'read'.",
    "Confirm with the user before applying changes to their pipeline.",
    "If a connector isn't available, ask the user to paste or type the "
    "few facts needed instead.",
]
