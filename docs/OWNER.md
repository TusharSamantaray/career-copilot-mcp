# Owner's runbook

Everything you need to pick Career Copilot back up. No secrets live here.
The values are in Render → career-copilot → Environment.

## What's live

| Thing | Where |
|---|---|
| Code | https://github.com/TusharSamantaray/career-copilot-mcp (pushes to `main` deploy on their own) |
| Hosted server | https://career-copilot-cg2k.onrender.com, Render free plan |
| Connector address (share this) | `https://career-copilot-cg2k.onrender.com/mcp` |
| Sign-in | GitHub OAuth app "Career Copilot", callback `/auth/callback` |
| Health check | https://career-copilot-cg2k.onrender.com/health |
| Keep-awake | GitHub Action `keep-awake.yml`, repo variable `HEALTH_URL` |
| Local copy (Claude Code) | The uvx one-liner in [CONNECT.md](CONNECT.md), data in `~/CareerCopilot/` |

## Settings in Render (names only)

| Setting | What it does |
|---|---|
| `CAREER_COPILOT_GITHUB_CLIENT_ID`, `_SECRET` | Turn on GitHub sign-in. When set, API keys are ignored |
| `CAREER_COPILOT_ALLOWED_GITHUB_USERS` | Invite list: GitHub usernames, comma-separated |
| `CAREER_COPILOT_JWT_KEY` | Keeps sign-ins valid across restarts. Changing it signs everyone out |
| `CAREER_COPILOT_USER_SALT` | Mixed into each person's storage id. **Never change it**: everyone's data would seem to vanish |
| `CAREER_COPILOT_MASTER_KEY` | Encrypts everyone's data, each with their own key. Add a long random value once. **Never change it**: stored data would become unreadable |
| `CAREER_COPILOT_API_KEY` | Old fallback, unused while sign-in is on. Safe to delete |
| `CAREER_COPILOT_INSIGHTS_SALT`, `CAREER_COPILOT_ADMIN_KEY` | Anonymous usage counts and the `/insights` page |

## Everyday tasks

- **Invite a friend:** add their GitHub username to
  `CAREER_COPILOT_ALLOWED_GITHUB_USERS`, save, and send them the
  connector address and [CONNECT.md](CONNECT.md).
- **Remove someone:** take their username out and save.
- **Connect a new app:** add a custom connector with the plain address
  and sign in with GitHub. Leave the OAuth fields empty in claude.ai.
- **Asked to reconnect?** It shouldn't happen after restarts any more.
  It does if `CAREER_COPILOT_JWT_KEY` or the GitHub app secret changes,
  or after a year without use. Click Connect once.
- **See which tools ran:** in a chat, expand the tool blocks. On the
  server, open Render → Logs and search `tool call`. Logs never show your
  words.
- **Test as a stranger:** sign in with a second GitHub account, added to
  the invite list.

## Working with Claude on it

- Open the project folder in VS Code with Claude Code. It reads
  `CLAUDE.md` first: the working agreement, the spec and the rules.
- Tell it a problem or idea in plain words. It adds it to
  [BACKLOG.md](BACKLOG.md), fixes it, runs every test, updates the
  [changelog](../CHANGELOG.md) with a **Try it** line, and commits.
- Say **"release"** when you want a version number and tag.
- Changes to ground rules, privacy, terms or sign-in always wait for your
  OK.

## Known limits

- The free plan wipes data on every restart or deploy (fix: B-008).
- Privacy notice and terms are plain-English drafts. Have a lawyer review
  them before taking paying users (B-010).
- The old `server.py` prototype is still in your local folder, outside
  git. Delete it when convenient (B-012).
