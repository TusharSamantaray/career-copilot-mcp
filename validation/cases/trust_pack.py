"""The ground rules are a disclosure a cautious assistant can verify."""
import re

from copilot import conduct

ID = "trust_pack"
TITLE = "Ground rules as disclosure, with a machine-readable data statement"
BACKLOG = "B-043"
BEFORE = ("Ground rules mixed terms with orders to the assistant ('ask if "
          "that's OK', 'never block'), and data handling was only prose.")

ORDERS = re.compile(r"\b(call|ask (?:if|them)|you must|then ask|never "
                    r"block)\b", re.I)


def run(user, measure):
    first = conduct.ground_rules(user)
    measure("agreement asked for before anything is saved",
            first["accepted"], False)
    stored = first["data_handling"]["stored"]
    measure("data rows that say what, where, how long and who can read",
            sum({"what", "where", "kept_for", "who_can_read"} <= set(r)
                for r in stored), len(stored))
    measure("things never stored are listed",
            len(first["data_handling"]["never_stored"]) >= 4, True)
    told = " ".join(first["summary"] + first["how_career_copilot_talks"])
    measure("orders to the assistant in the disclosure",
            len(ORDERS.findall(told)), 0)
    measure("fields that steer the assistant (show_user, reply_style)",
            len({"show_user", "reply_style"} & set(first)), 0)
    measure("summary is three lines", len(first["summary"]), 3)
    agreed = conduct.ground_rules(user, accept=True)
    measure("agreement recorded for this version",
            (agreed["accepted"], agreed["version"]),
            (True, conduct.TERMS_VERSION))
