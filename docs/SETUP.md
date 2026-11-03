# Career Copilot MCP: Setup and Deployment

This guide takes you from a fresh clone to a paid listing. The steps are in
order. Commands are for Windows PowerShell, with macOS/Linux versions where
they differ.

## 1. Prerequisites

| Tool | Install (Windows) | Check |
|---|---|---|
| Python 3.11+ | `winget install Python.Python.3.11` | `python --version` |
| uv | `winget install astral-sh.uv` | `uv --version` |
| git | `winget install Git.Git` | `git --version` |
| GitHub CLI | `winget install GitHub.cli` | `gh --version` |

Open a new terminal after installing, so the tools are on `PATH`.

## 1a. One-command setup (Windows)

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup.ps1          # everything
powershell -ExecutionPolicy Bypass -File scripts/setup.ps1 -Test    # plus all tests
powershell -ExecutionPolicy Bypass -File scripts/setup.ps1 -SkipReason
```

The script is safe to re-run. It:
1. installs git, gh and uv if they're missing;
2. runs `uv sync`;
3. registers the `career-copilot` and `reason` MCP servers for this
   project;
4. installs the Reason CLI and joins Reason Network, with a browser
   sign-in.

## 2. Run locally

```powershell
git clone https://github.com/TusharSamantaray/career-copilot-mcp.git
cd career-copilot-mcp
uv sync                                 # creates .venv and installs dependencies
```

Generate an API key for local use:

```powershell
uv run python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copy `.env.example` to `.env` and paste the key into
`CAREER_COPILOT_API_KEY`. Then start the server:

```powershell
uv run --env-file .env app.py           # HTTP on http://localhost:8080/mcp
```

The startup log shows the version, the MCP protocol version, the endpoints
and the tool count. Check the server is up:

```powershell
curl.exe http://localhost:8080/health   # {"status":"ok","version":"0.3.0"}
```

## 3. Run the tests

```powershell
uv run tests/test_poc.py        # core tools, over stdio
uv run tests/test_features.py   # finance, resumes, roles, prep, nudges, economy
uv run tests/test_http.py       # health, key required, wrong key rejected,
                                # data isolation, keys never logged
uv run tests/test_knowledge.py  # knowledge is valid, no personal data
uv run tests/test_soul.py       # coach, safety, relocation, intake, dashboard
```

Each one should end with `ALL PASSED`.

## 4. Connect an AI client

[CONNECT.md](CONNECT.md) covers every client: Claude Code, Claude Desktop,
Claude.ai, ChatGPT, Cursor, VS Code, Gemini CLI and Windsurf. The common
cases:

**Claude Code, local (stdio, no key needed):**

```powershell
claude mcp add career-copilot -- uv run --directory C:\path\to\career-copilot-mcp app.py --stdio
```

**Claude Code, remote (HTTP, with key):**

```powershell
claude mcp add --transport http career-copilot https://<your-endpoint>/mcp --header "Authorization: Bearer <key>"
```

**Claude Desktop** (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "career-copilot": {
      "command": "uv",
      "args": ["run", "--directory", "C:\\path\\to\\career-copilot-mcp", "app.py", "--stdio"]
    }
  }
}
```

To try it, ask the assistant *"I just got laid off"* or
*"Help me build my resume."*

## 5. Configuration

| Variable | Required | Default | Meaning |
|---|---|---|---|
| `CAREER_COPILOT_API_KEY` | Yes, for HTTP | none | Valid keys, comma-separated |
| `PORT` | No | `8080` | HTTP port (hosts usually set this) |
| `HOST` | No | `0.0.0.0` | Bind address |
| `COPILOT_DATA_DIR` | No | `./data` | Where per-user SQLite files live |
| `CAREER_COPILOT_LOG_DIR` | No | `logs` | Rolling log directory |
| `CAREER_COPILOT_LOG_LEVEL` | No | `INFO` | `DEBUG` for more detail |
| `CAREER_COPILOT_USER_HEADER` | No | none | Gateway header that names the subscriber |
| `CAREER_COPILOT_ALLOW_OPEN` | No | off | `1` allows HTTP without a key. **Local testing only** |
| `CAREER_COPILOT_INSIGHTS_SALT` | Yes, in production | none | Random secret for anonymous signal hashes |
| `CAREER_COPILOT_ADMIN_KEY` | For self-improvement | none | Unlocks `GET /insights` for the weekly improver |
| `CAREER_COPILOT_K_ANON` | No | `5` | Distinct users needed before a label is reported |
| `CAREER_COPILOT_INSIGHTS` | No | `1` | `0` turns anonymous signals off |

## 5a. Turn on self-improvement (one-time, then hands-off)

1. On MCPHosting, set `CAREER_COPILOT_INSIGHTS_SALT` and
   `CAREER_COPILOT_ADMIN_KEY` to two new random strings.
2. In GitHub, go to the repo → Settings → Secrets and variables → Actions
   and add:
   - `ANTHROPIC_API_KEY`
   - `INSIGHTS_URL` (`https://<your-endpoint>/insights`)
   - `INSIGHTS_ADMIN_KEY` (the same value as the admin key above)
3. Install the Claude GitHub app on the repo (run `/install-github-app` in
   Claude Code), so `claude-code-action` can run.
4. Run **Actions → Improve knowledge → Run workflow** once to check it.
   After that it runs every Monday on its own.

Knowledge-only improvements merge and deploy automatically. Anything else
waits as a pull request labelled `needs-review`, and GitHub emails you.

## 6. Free demo hosting (Render)

This is the fastest way to use Career Copilot on claude.ai, ChatGPT and
your phone. It's free and needs no credit card.

1. Click **Deploy to Render** in the README, or open
   `https://render.com/deploy?repo=https://github.com/TusharSamantaray/career-copilot-mcp`.
2. Sign in with GitHub, then click **Deploy Blueprint**. Render reads
   `render.yaml`, installs everything and generates the secret key. This
   takes about 3 minutes.
3. Open the **career-copilot** service:
   - Copy the address at the top (`https://career-copilot-xxxx.onrender.com`).
   - Go to **Environment** and copy the value of `CAREER_COPILOT_API_KEY`.
4. Your connector URL is:
   ```
   https://career-copilot-xxxx.onrender.com/mcp?key=<CAREER_COPILOT_API_KEY>
   ```
   Add it to claude.ai or ChatGPT ([CONNECT.md](CONNECT.md)). Connectors
   added on claude.ai also work in the Claude mobile app.
5. Optional, but best before a demo: in GitHub, go to Settings → Secrets
   and variables → Actions → **Variables** and add `HEALTH_URL` =
   `https://career-copilot-xxxx.onrender.com/health`. The **Keep awake**
   workflow then pings the server every 10 minutes, so it never falls
   asleep.

**Giving demo access to other people:** give each person their own key, so
their data stays separate. In Render → Environment, change
`CAREER_COPILOT_API_KEY` to a comma-separated list, for example
`<your-key>,demo-ana-7f3k,demo-ben-9x2q`, and save. Render redeploys by
itself. Each person uses their own `?key=`. To remove someone, delete their
key.

**Free plan limits:**

| Limit | What it means |
|---|---|
| Sleeps after 15 idle minutes | The first request then takes 30–60 seconds. Keep awake (step 5) avoids this |
| No persistent disk | Saved data is wiped on every redeploy or restart. Fine for demos, not for real users |
| 750 hours a month | Enough for one service running all month |

For real users, move to a paid plan with a disk, or to MCPHosting
(below), or switch storage to Postgres (SPEC Phase 2).

## 6b. Deploy to MCPHosting

MCPHosting builds from your GitHub repo and redeploys on every push.

1. Sign in to MCPHosting and create a new project.
2. Connect GitHub and select `career-copilot-mcp`, branch `main`.
3. Runtime: **Python / FastMCP**. If it asks for commands:
   - Install: `pip install -r requirements.txt` (or `uv sync` if offered)
   - Start: `python app.py`
4. Environment variables: set `CAREER_COPILOT_API_KEY` to a newly
   generated key. Don't reuse your local one. Leave `PORT` to the host
   unless it asks.
5. Transport: **HTTP**. Endpoint path: `/mcp`. Health check: `/health`.
6. Deploy, then confirm:
   ```powershell
   curl.exe https://<your-project-url>/health
   ```
7. Connect Claude Code to the live URL with the remote command in
   section 4, and call `profile_get`.
8. In the logs view, you should see the startup lines, then
   `tool call: profile_get ...` and `tool done: profile_get in N ms`.

The Free plan allows 500 requests a month, which is enough for testing.
Move to Pro ($19/mo, 50,000 requests) before you take paying users (see
SPEC section 7).

**Data durability:** Ask MCPHosting support whether project disk survives
redeploys. If it doesn't, every push wipes user data. Keep paid users off
the server until this is answered or storage moves to Postgres (SPEC
Phase 2).

## 7. List on MCPize

1. In the MCPize developer dashboard, choose **new server**.
2. **Endpoint:** the MCPHosting URL ending in `/mcp`. If MCPize only offers
   its own hosting, you can deploy there from the same GitHub repo instead,
   since the code doesn't change.
3. **Upstream auth:** find out what MCPize sends to your server.
   - *If each subscriber's key is passed through:* add the keys to
     `CAREER_COPILOT_API_KEY`, or ask MCPize for a way to validate them.
   - *If MCPize sends one shared secret and a subscriber ID header:* put
     the secret in `CAREER_COPILOT_API_KEY` and the header name in
     `CAREER_COPILOT_USER_HEADER`.
4. **Pricing:** start with the plans in SPEC section 7.4.
5. **Listing copy:** use the "What it is" section of the SPEC. Add
   screenshots of a resume score and a pipeline digest.
6. **Before going live:** buy two test subscriptions. Save a profile with
   one and confirm the other can't see it. If the second one sees the
   first's data, the identity setup in step 3 is wrong.

## 8. Operations

| Task | How |
|---|---|
| Ship a change | `git commit` and `git push` (MCPHosting redeploys automatically) |
| Rotate a key | Set `CAREER_COPILOT_API_KEY=new,old`, deploy, move clients over, then remove `old` |
| Read logs | MCPHosting log view (stdout), or `logs/mcp_server.log` locally |
| More detail | `CAREER_COPILOT_LOG_LEVEL=DEBUG` |
| A user asks for their data | They call `data_export` or `data_delete` from their AI client |

## 9. Troubleshooting

| Symptom | Cause and fix |
|---|---|
| Server exits with `CAREER_COPILOT_API_KEY is not set` | Set the key in the host's environment |
| Client shows `Unauthorized` | Header missing or key wrong. Check `Authorization: Bearer <key>` |
| `/health` works but `/mcp` returns 404 | Client URL is missing `/mcp` |
| Stdio client hangs or shows garbage | Something is printing to stdout. Logs already go to stderr in `--stdio` mode |
| User data gone after deploy | Host disk isn't persistent (section 6) |
| `uv` not found | Open a new terminal after installing |
