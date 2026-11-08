"""Weekly error report from the anonymous /insights summary.

Reads insights.json (the k-anonymous aggregate the server shares with
the admin key) and writes a short Markdown report of error codes people
reported with report_issue and tools that often fail. Prints nothing
and exits 0 when there's nothing to report. It never proposes code: a
person reads the report and decides (see docs/ENGINEERING.md).

    python agents/triage.py insights.json report.md
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(
    __file__))))
from copilot import errors  # noqa: E402

FAILING = 0.9        # flag tools that succeed less often than this
MIN_CALLS = 10       # ...once they've been called at least this often


def report(summary):
    """Markdown for the week, or None when nothing needs a look."""
    rows = []
    for kind, labels in sorted((summary.get("labels") or {}).items()):
        if not kind.startswith("issue:"):
            continue
        code = kind.split(":", 1)[1]
        meaning, retry, fix = errors.CODES.get(
            code, ("Not a known code.", False, "Check the server log."))
        for item in labels:
            rows.append(f"| `{code}` | `{item['label']}` | {item['users']} "
                        f"| {meaning} | {fix} |")
    failing = [t for t in summary.get("tools") or []
               if t["calls"] >= MIN_CALLS and t["success_rate"] < FAILING]
    if not rows and not failing:
        return None
    out = [f"Anonymous counts from the last {summary.get('since_days', '?')} "
           f"days; each line has at least {summary.get('k_anon', 5)} "
           "different people behind it.", ""]
    if rows:
        out += ["### Errors people reported", "",
                "| Code | Tool | People | Meaning | Suggested fix |",
                "|---|---|---|---|---|", *rows, ""]
    if failing:
        out += ["### Tools that often fail", "",
                "| Tool | Calls | Success | Avg ms |", "|---|---|---|---|"]
        out += [f"| `{t['tool']}` | {t['calls']} | "
                f"{t['success_rate']:.0%} | {t['avg_ms']} |"
                for t in failing]
        out.append("")
    out.append("Search the server log for `crashed:` and the tool name to "
               "find refs. Fix, test, and merge by hand.")
    return "\n".join(out)


if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as handle:
        text = report(json.load(handle))
    if text:
        with open(sys.argv[2], "w", encoding="utf-8") as handle:
            handle.write(text)
        print("report written")
    else:
        print("nothing to report")
