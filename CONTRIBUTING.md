# Contributing

Thanks for helping. Career Copilot is small on purpose, so keep changes
small too.

## Set up

```bash
uv sync
```

Then run the five test suites (see the README, section 11). All of them
must end with `ALL PASSED` before you open a pull request.

## Where changes go

| Change | Where |
|---|---|
| New roles, patterns, places, coach lines, interview questions | `copilot/knowledge/`, plus a line in `copilot/knowledge/CHANGELOG.md` |
| New or changed logic | The matching module in `copilot/`, plus a test in `tests/` |
| A new tool | `app.py` (keep it thin and call into `copilot/`), plus a test |
| Docs | `docs/`, in plain, simple English |

## Rules

1. **No personal data.** No real names, employers, money figures, visa or
   health details, in code, tests or examples. Use made-up names like Acme
   or Globex. `tests/test_knowledge.py` checks for this.
2. **No passwords and no logins.** Career Copilot never signs in to
   anything for the user. Mail, calendar and bank data come from the
   user's own connectors, through their AI assistant.
3. **Drafts only.** Tools may draft messages, but they never send them.
4. **Education, not advice.** Money, tax, visa and relocation outputs must
   say so.
5. **No new dependencies** unless they're really needed. Say why in the PR.

## Automated changes

A weekly GitHub Action may open pull requests that only touch
`copilot/knowledge/`. If the tests pass, they merge automatically. Any other
automated change waits for a human review (label `needs-review`).
