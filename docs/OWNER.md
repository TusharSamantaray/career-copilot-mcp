# Owner's runbook

Everything you need to pick Career Copilot back up. No secrets live here.
The values are in Render → career-copilot → Environment.

## What's live

| Thing | Where |
|---|---|
| Code | https://github.com/TusharSamantaray/career-copilot-mcp (pushes to `main` deploy on their own) |
| Hosted server | https://career-copilot-cg2k.onrender.com, Render free plan |
| Try-it page (share this link) | https://career-copilot-cg2k.onrender.com/ : the address to copy, setup for Claude and ChatGPT, what to say first, privacy and terms |
| Connector address | `https://career-copilot-cg2k.onrender.com/mcp` |
| Sign-in | GitHub OAuth app "Career Copilot", callback `/auth/callback` |
| Health check | https://career-copilot-cg2k.onrender.com/health |
| Keep-awake | GitHub Action `keep-awake.yml` (repo variable `HEALTH_URL`, also the abuse alarm), plus a free uptime pinger: see "Keep it awake" |
| Local copy (Claude Code) | The uvx one-liner in [CONNECT.md](CONNECT.md), data in `~/CareerCopilot/`. Works only for people with read access while the repo is private |
| Local test with made-up people | `uv run simulation/run.py --serve`, see [simulation/README.md](../simulation/README.md) |

## Settings in Render (names only)

| Setting | What it does |
|---|---|
| `CAREER_COPILOT_GITHUB_CLIENT_ID`, `_SECRET` | Turn on GitHub sign-in. When set, API keys are ignored |
| `CAREER_COPILOT_ALLOWED_GITHUB_USERS` | Invite list: GitHub usernames, comma-separated |
| `CAREER_COPILOT_JWT_KEY` | Keeps sign-ins valid across restarts. Changing it signs everyone out |
| `CAREER_COPILOT_USER_SALT` | Mixed into each person's storage id. **Never change it**: everyone's data would seem to vanish |
| `DATABASE_URL` | Where data lives (Neon free Postgres), so restarts don't wipe it. Contains a password: keep it only in Render |
| `CAREER_COPILOT_MASTER_KEY` | Encrypts everyone's data, each with their own key. Add a long random value once. **Never change it**: stored data would become unreadable |
| `CAREER_COPILOT_API_KEY` | Old fallback, unused while sign-in is on. Safe to delete |
| `CAREER_COPILOT_INSIGHTS_SALT`, `CAREER_COPILOT_ADMIN_KEY` | Anonymous usage counts and the `/insights` page |
| `CAREER_COPILOT_RATE_PER_MINUTE`, `CAREER_COPILOT_DAILY_QUOTA` | Fair-use limits per person: 60 calls a minute and 1,500 a day unless set. `0` turns one off |
| `CAREER_COPILOT_TRIAL_DAILY_CALLS`, `_NEW_PER_DAY`, `_MAX_PEOPLE`, `_STORAGE_MB` | Free-trial capacity for the whole server: 20,000 calls a day, 30 new people a day, 300 people, 400 MB unless set. See "Free-trial capacity" |
| `CAREER_COPILOT_INSIGHTS_STORE` | Not set (or `file`): anonymous counts are wiped on every restart, so the weekly improver sees little. `database`: kept in Neon for 400 days. Your call (B-050); `/health` shows which |

## Everyday tasks

- **Invite a friend:** add their GitHub username to
  `CAREER_COPILOT_ALLOWED_GITHUB_USERS`, save, and send them the
  connector address and [CONNECT.md](CONNECT.md).
- **Let a recruiter in:** exactly the same as inviting a friend: no
  separate site or account type. They connect the same address in their
  own AI assistant and say "I'm hiring" (the `find_candidates` starter).
  They see published anonymous personas only, never anyone's name,
  contacts or salary. Send them the recruiter message below.
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
- **Weekly error report:** on Mondays, GitHub opens (or adds to) an
  issue labelled `triage` when people reported errors or a tool keeps
  failing. It uses the same secrets as the weekly improver
  (`INSIGHTS_URL`, `INSIGHTS_ADMIN_KEY`). Run it any time from Actions →
  Error report → Run workflow. It only reports once 5 different people
  share a problem, and it needs B-050 turned on to see past a restart.
- **Is it invite-only right now?** Open the health check. `"invite_only":
  true` means only people on your list can sign in; `false` means anyone
  with a GitHub account can. It never shows who is on the list.

## Keep it awake

Render's free plan sleeps after 15 idle minutes, and waking takes 30 to
60 seconds, long enough for a first connect to give up. The Keep awake
GitHub Action pings every 10 minutes on paper, but GitHub delays and
skips scheduled runs on quiet repos: on 2026-11-13/14 it actually ran
every 3 to 8 hours (GitHub #24). So add a free pinger too (5 minutes,
once, your account):

1. Sign up at cron-job.org (free) or UptimeRobot (free plan, 5-minute
   checks, and it emails you when the server is down).
2. Add a check for `https://career-copilot-cg2k.onrender.com/health`,
   every 5 minutes (cron-job.org can do every 10; under 15 is enough).
3. Next day, open `/health` cold: it should answer in a second or two.

Keep the GitHub Action anyway: it carries the abuse alarm and the
trial-capacity alarm. Everything stays on free plans: no card, no
upgrade. A cold start of up to a minute is the price of free.

## Open sign-in to everyone (GitHub #25)

Fair-use limits and the abuse alarm are in place, so this is now a
settings change, done when you choose:

1. Render → Environment: delete `CAREER_COPILOT_ALLOWED_GITHUB_USERS`,
   save (it restarts).
2. `/health` should say `"invite_only": false`.
3. Ask someone you never added to connect. It should just work.
4. In the tester message below, drop "It's invite-only, and I've added
   your GitHub username." To go back, add the setting again.

## Fair use and the abuse alarm

Each person may make 60 calls a minute and 1,500 a day (a long, busy
session is about 200). Over the minute limit, their assistant is told to
wait a few seconds; over the daily one, to come back after midnight UTC.
Nobody else is affected, and nothing is lost. `/health` shows the limits
and how many people hit one today, never who.

**If the abuse alarm fires** (the Keep awake run fails with "Unusual
use", and GitHub emails you):

1. Render → Logs, search `limit reached`. Each line names a hashed id
   (like `gh_3fa1…`), never a person.
2. One id, once: probably an assistant stuck in a loop. Nothing to do.
3. One id, every day, or many ids at once: someone is scripting it.
   While the server is invite-only, take people off the list. If it's
   open, turn the invite list back on, or lower
   `CAREER_COPILOT_DAILY_QUOTA`.

Counts reset when the server restarts, so a restart also clears the
alarm.

## Free-trial capacity (B-082)

The trial runs on Render's free web service and Neon's free Postgres,
and nothing is ever paid for. So the server limits itself before the
free plans run out:

| Limit | Default | Setting in Render |
|---|---|---|
| Calls per day, everyone together | 20,000 | `CAREER_COPILOT_TRIAL_DAILY_CALLS` |
| New people per day | 30 | `CAREER_COPILOT_TRIAL_NEW_PER_DAY` |
| People in total | 300 | `CAREER_COPILOT_TRIAL_MAX_PEOPLE` |
| Database size before new people pause | 400 MB (Neon free is 512 MB) | `CAREER_COPILOT_TRIAL_STORAGE_MB` |

`0` turns a limit off. What people see:

- **New people paused** (a people cap or the storage line): people
  already in carry on. A newcomer's assistant gets a plain note, "The
  free trial isn't taking new people right now", and nothing is saved
  about them. The try-it page says "Not taking new people right now".
- **Full for today** (the day's calls are used): everyone gets "The free
  trial is full for today... It reopens at midnight UTC. Nothing is
  lost." The page says the same.
- In both cases exporting and deleting data still work. It's a note,
  not an error, so assistants don't retry in a loop.

Where to look: `/health` → `trial` shows the counts (never who). The
Keep awake run warns when new people are paused, and fails (GitHub
emails you) when the day is full. Render → Logs, search `trial full`.

If you see it often: raise a limit only while Neon's dashboard (Usage)
shows room. Counts reset at midnight UTC and on a restart.

## Message to send a tester

Add their GitHub username to the invite list first, then send this.
It says exactly what happens, so a careful assistant can check it before
connecting.

> Hi! I'd love your help testing Career Copilot, a career coach that
> plugs into your AI assistant (Claude, ChatGPT and others).
>
> 1. Open https://career-copilot-cg2k.onrender.com/ and follow the
>    three steps there (copy the address, add it to your assistant, say
>    one sentence). The connector address is
>    `https://career-copilot-cg2k.onrender.com/mcp`.
> 2. When you connect, click **Allow and sign in with GitHub**. It
>    only reads your public GitHub profile (username and id), to keep
>    your data separate from everyone else's. No API key, no password.
>    It's invite-only, and I've added your GitHub username.
> 3. Say "Show me the ground rules", then "I don't know what I want".
>
> Want to check it first? `https://career-copilot-cg2k.onrender.com/health`
> shows the version, the sign-in method (`github-oauth`), and whether
> it's invite-only. The privacy notice and terms are at `/privacy` and
> `/terms` on the same server. The source code is private for now; ask
> me if you'd like read access. The free server
> sleeps when idle, so the first connect can take up to a minute.
>
> If something breaks, tell me what you said and what you saw.

## Message to send a recruiter

Add their GitHub username to the invite list first.

> Hi! Career Copilot lets you find candidates by their verified work,
> not their resume. People choose to publish an anonymous persona:
> skills, and the work that proves them. No names, contacts or salary.
>
> 1. In your AI assistant, add a custom connector with this address:
>    `https://career-copilot-cg2k.onrender.com/mcp`, and sign in with
>    GitHub (public profile only; it's invite-only and you're on it).
> 2. Say "I'm hiring", paste a job posting, and say what the role must
>    have. You'll get up to 5 anonymous personas, each with proof lines.
> 3. Ask one a question, like "What have they built with Kafka?".
>    Answers come only from their verified work.
>
> Nobody is contacted automatically, and a persona can't tell you who
> they are.

If you make the repository public, swap the source line in the tester
message for its link.

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

- Without `DATABASE_URL`, the free plan wipes data on every restart or
  deploy. With it (Neon free), data stays.
- Privacy notice and terms are plain-English drafts. Have a lawyer review
  them before taking paying users (B-010).
- The old `server.py` prototype is still in your local folder, outside
  git. Delete it when convenient (B-012).
