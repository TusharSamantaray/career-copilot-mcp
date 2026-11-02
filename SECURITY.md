# Security and privacy

## Report a problem

Please don't open a public issue for a security or privacy problem. Use
GitHub's private reporting instead: **Security → Report a vulnerability** on
this repo. You should hear back within 7 days.

## What Career Copilot does to stay safe

- **No passwords and no logins.** It never asks for or stores credentials
  for email, calendar, LinkedIn or banks.
- **Your data is separate from everyone else's.** In hosted mode, each API
  key gets its own SQLite file. In local mode, everything stays on your
  computer.
- **Logs hide your data.** API keys, money figures, emails, notes and lists
  are masked before anything is logged.
- **Usage signals are anonymous.** User IDs are salted hashes, labels are
  scrubbed, and nothing is reported until at least 5 different users share
  it (k-anonymity).
- **You can leave at any time.** `data_export` gives you all your data, and
  `data_delete` removes it, including your anonymous signals.
- **Automated edits are guarded.** The weekly improver may only change
  `copilot/knowledge/`, and only when every test passes, including the
  personal-data and prompt-injection checks.
