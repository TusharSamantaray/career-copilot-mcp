"""The weekly error report: says what broke, stays quiet otherwise."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "agents"))
import triage  # noqa: E402

quiet = {"since_days": 7, "k_anon": 5, "labels": {
    "unmet_role": [{"label": "pastry chef", "users": 6}]},
    "tools": [{"tool": "job_search", "calls": 40, "users": 9,
               "success_rate": 0.97, "avg_ms": 120.0},
              {"tool": "rare_tool", "calls": 3, "users": 5,
               "success_rate": 0.0, "avg_ms": 5.0}]}
assert triage.report(quiet) is None, "reported a healthy week"
print("healthy week (and rarely used tools) stay quiet: OK")

busy = {"since_days": 7, "k_anon": 5, "labels": {
    "issue:UNKNOWN_TOOL": [{"label": "other", "users": 7}],
    "issue:INTERNAL_ERROR": [{"label": "job_search", "users": 5}]},
    "tools": [{"tool": "job_search", "calls": 50, "users": 12,
               "success_rate": 0.8, "avg_ms": 900.0}]}
text = triage.report(busy)
assert "`INTERNAL_ERROR` | `job_search` | 5" in text, text
assert "reconnect" in text.lower(), "no fix for UNKNOWN_TOOL"
assert "| `job_search` | 50 | 80% |" in text, text
assert "at least 5 different people" in text
print("busy week lists codes, tools, people and the fix: OK")
print("ALL PASSED")
