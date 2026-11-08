# Validation

Where we prove each improvement worked, with numbers, and keep the
record.

Tests (in `tests/`) answer "is anything broken?". Validation answers
"did this improvement do what we said, and by how much?" Each case
replays one improvement with made-up people and measures it the way you
would check it by hand.

| File | What it is |
|---|---|
| [RESULTS.md](RESULTS.md) | Latest scoreboard: every case, every measure, expected against measured |
| [HISTORY.md](HISTORY.md) | One dated row each time a case's score changes, so you can see when each improvement landed |
| `cases/` | One file per improvement, named after what it proves |
| `run.py` | Runs every case and updates both files |

## Run it

    uv run validation/run.py           # run, update RESULTS.md and HISTORY.md
    uv run validation/run.py --check   # run only (CI); fails if any case fails

It runs before every commit together with the tests, and in CI.

## Add a case when an improvement lands

Create `cases/<short_name>.py` with:

- `ID`, `TITLE`, `BACKLOG` (the backlog id it proves) and `BEFORE` (how
  things were before, in one plain sentence);
- `run(user, measure)`, which uses the Career Copilot modules directly
  and calls `measure("what you checked", measured, expected)` for each
  check.

Rules:

- **Made-up people only.** When a case copies a real result (like the
  owner's own resume rebuild), copy its shape, never its text, names,
  numbers or contact details.
- **Measure, don't claim.** Every number comes from running the code.
- **Keep old cases.** A case that drops a point is a regression; fix the
  code, not the case, unless the owner changes the rule.

## Cases today

| Case | Proves | Backlog |
|---|---|---|
| `resume_rebuild` | A four-version rebuild: invented bullets, level tags and internal names gone, summary led by numbers, same roles, tighter, and a branch that brought problems back is flagged | B-051 |
| `outreach_gate` | Nothing is approved to send without a yes to the exact text, edits and expired approvals are refused, and nothing is stored | B-056 |
