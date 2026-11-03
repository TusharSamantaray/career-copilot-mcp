# Career Copilot MCP: System Specification (v1, archived)

Version 0.3.0, November 2026. **Archived:** replaced by
[Spec v2](../SPEC.md). Still useful for the cost model (section 7);
auth (section 4) is out of date: hosted access now uses GitHub sign-in.

## 1. What it is

Career Copilot is a remote MCP server for **anyone, in any field and any
country**, who wants to find the right job, move careers, improve their
finances or plan for the future. Plugged into an AI assistant (Claude,
ChatGPT, Cursor or any MCP client), it gives the assistant a memory and a
toolset. It runs **interactively**:

- The `get_started` prompt onboards a new user one question at a time.
- `next_steps` reads what the user has set up and proposes their next
  three actions for the goals they chose.

What it covers:

- **Career moves.** Distance to the target role, transferable skills,
  gaps, stepping-stone roles and a timeline. 19 roles across engineering,
  product, data, design, project management, marketing, sales, customer
  success, operations, finance and HR.
- **Planning for the future.** Savings goals with the monthly amount each
  needs, and long-term projections at three return rates, also in today's
  money.

- **Profile and verified work history.** Each fact is marked confirmed or
  not, and only confirmed facts reach a resume.
- **Resumes.** Import past versions, merge the best bullets, score, draft,
  and get section advice by level.
- **Work contributions.** A coach that finds what a bullet is missing
  (ownership, scale, result) and asks the user for it.
- **LinkedIn review** of pasted profile text, with no scraping.
- **Role fit and skills gaps.** Which roles fit, what a target level needs,
  what the interview loop tests, and what moves pay.
- **Interview prep.** 23 coding patterns, the system design framework and
  14 components, and day-by-day study plans.
- **Schedules and nudges.** Reminders, a "what's due" digest, and a
  calendar export with alerts.
- **Application pipeline** with a daily digest.
- **Finance dashboard.** Net worth, accessible vs locked money, runway,
  stale balances, concentration flags and budget cuts.
- **Layoff readiness.** Runway calculator, emergency-fund plan and a
  playbook.
- **Investing education** grounded in the evidence.
- **World Economy OS.** How the economy reaches prices, markets and jobs,
  plus live World Bank indicators.
- **Data export and deletion** on request.

The server holds the data and the rules. The user's AI assistant does the
conversation. That split is why the server needs no LLM of its own and
costs very little to run.

## 1a. The soul

The server's instructions give every connected assistant one persona: a
warm, honest companion whose job is to find the user's best next move in
career and life, and help them take it one small step at a time.

| Behaviour | How it's built |
|---|---|
| One step a day, sized to energy | `daily_step(energy, mood)`: what's due first, otherwise a tiny step for the user's goals (5 minutes on low energy, about 45 on high) |
| Momentum, not guilt | `step_done` tracks a streak where one rest day is fine and two in a row reset it. Celebrations come at 3, 7, 14, 30, 60 and 100 days |
| Thinks bigger for them | `career_move` and `where_to_move` are offered when a new role or city would help growth. The user decides |
| Helps the lost find direction | `life_compass`: reflection questions, one at a time |
| Safety first | Crisis words in `mood` return support lines (988, Samaritans, Tele-MANAS, findahelpline.com) instead of a task |
| Never acts behind their back | Messages are drafts only. Pipeline changes from email wait for the user's yes (`apply=true`) |
| Just a connector | No third-party logins, no password vault, no OAuth to other services. Email, calendar, meetings and bank balances come from the user's own connectors in the same chat (`companions`), or are pasted. Only the needed fields are passed, and ids and account numbers are dropped (`finance_import`) |

See [WHY.md](WHY.md) for the story, [TOUR.md](TOUR.md) for the guided
tour, and [ARCHITECTURE.md](ARCHITECTURE.md) for the diagrams.

## 2. Architecture

```
 User's AI client                  MCPize                  MCPHosting
 (Claude, ChatGPT,   HTTPS    +------------------+  HTTPS  +---------------------+
  Cursor, ...)     -------->  | Gateway          | ------> | app.py (FastMCP)    |
                   API key    | - subscriber key |  /mcp   |  AuthAndAudit       |
                              | - quotas, usage  |         |   middleware        |
                              | - Stripe billing |         |  59 tools, 6 res.,  |
                              +------------------+         |  13 prompts         |
                                                           |  /health            |
                                                           +----------+----------+
                                                                      |
                                                    +-----------------+-------------+
                                                    | store.py: one SQLite file    |
                                                    |   per user (data/<hash>.db)  |
                                                    | logs/mcp_server.log, rolling |
                                                    +------------------------------+
```

| Component | File | Responsibility |
|---|---|---|
| MCP server | `app.py` | Registers tools, resources and prompts. HTTP transport on `:8080/mcp`, `/health` |
| Auth and audit | `app.py` (`AuthAndAudit`) | API key check, per-call logs, timers, error containment |
| Guidance | `copilot/guide.py` | Onboarding state and next-step suggestions per goal |
| Careers | `copilot/careers.py` | Resume versions and merge, contribution check, LinkedIn review, role fit, skills gap, career moves |
| Finance | `copilot/finance.py` | Accounts, holdings, budget, dashboard, portfolio check, layoff fund, goals, projections |
| Prep | `copilot/prep.py` | Coding-pattern matching, system design lookup, study plans |
| Nudges | `copilot/nudges.py` | Reminders, due digest, `.ics` export |
| Economy | `copilot/economy.py` | World Bank API client, cached 6 hours |
| Knowledge | `copilot/knowledge/` | Static content: patterns, system design, roles and levels, money guides, client setup |
| Storage | `copilot/store.py` | Per-user SQLite record store, export, delete |
| Scoring | `copilot/scoring.py` | Ten-check heuristic resume rubric |
| Dashboard | `copilot/dashboard.py`, `copilot/dashboard.html` | Builds the user's dashboard page from their data; saved on their device in local mode |
| Tests | `tests/` (5 suites) | Every tool over stdio with exact-value checks; HTTP auth and isolation; knowledge validity; coach, safety and log hygiene |

**Outbound network.** The only outbound call is `economy_indicators` to
`api.worldbank.org`, a public API that needs no key. User data is never
sent anywhere.

**Transport.** Streamable HTTP (`transport="http"`), host `0.0.0.0`, port
`$PORT` or 8080. Endpoint `/mcp`. `--stdio` runs the same server locally for
Claude Desktop or Claude Code.

## 3. MCP surface

**Tools (59).** Write actions are marked W.

| Area | Tools |
|---|---|
| Your connectors | `companions`, `finance_import` (W) |
| Coach | `daily_step`, `step_done` (W), `life_compass` |
| Relocation | `where_to_move` |
| Autopilot | `inbox_triage` (W with apply), `calendar_interviews` (W with apply). Pipeline changes auto-create reminders |
| Interviews | `interview_questions`, `story_add` (W), `story_match`, `prep_checklist`, `message_draft` |
| Guidance | `next_steps`, `feedback` (W, anonymous counts only) |
| Profile & history | `profile_get`, `profile_save` (W), `experience_add` (W), `experience_list` |
| Resumes | `resume_import` (W), `resume_versions`, `resume_merge`, `resume_score`, `resume_build_draft`, `resume_sections` |
| Contributions | `contribution_framework`, `contribution_check` |
| LinkedIn | `linkedin_review` (works on pasted text or the PDF export, never scrapes) |
| Roles & pay | `role_match`, `skills_gap`, `career_move` |
| Prep | `coding_pattern`, `system_design`, `study_plan` (W when saving nudges) |
| Nudges | `nudge_add` (W), `nudges_due`, `nudge_done` (W), `calendar_export` |
| Pipeline | `application_log` (W), `application_update` (W), `pipeline_digest` |
| Finance | `finance_account_set` (W), `finance_account_remove` (W), `finance_holding_set` (W), `finance_budget_set` (W), `finance_dashboard`, `finance_budget_review`, `portfolio_check` |
| Future | `goal_set` (W), `goals_review`, `future_projection` |
| Layoffs | `runway_calc`, `layoff_fund_plan`, `layoff_playbook` |
| Investing | `invest_guide` |
| Economy | `economy_guide`, `economy_indicators` (live) |
| Data | `data_export`, `data_delete` (W, needs `confirm=true`) |

**Resources.**
- `copilot://rubric`: the scoring rubric.
- `copilot://pipeline`: the user's application rows.
- `copilot://calendar.ics`: reminders and deadlines as a calendar feed.
- `copilot://connect`: setup steps for each client.
- `copilot://patterns`: the pattern index.
- `copilot://roles`: the role catalogue.

**Prompts (starter chips).** `get_started`, `change_careers`,
`plan_my_future`, `build_my_resume`, `i_just_got_laid_off`,
`import_my_resumes`, `review_my_linkedin`, `find_my_role`, `plan_my_prep`,
`money_checkup`.

**How the finance dashboard works.**
- Accounts fall into four buckets:
  - *accessible*: cash, brokerage, foreign;
  - *locked*: retirement, HSA (taxes and penalties to touch);
  - *illiquid*: property;
  - *debt*.
- Runway is reported twice: on cash alone, and on all accessible money.
- Balances older than 30 days are flagged as stale.
- Any single stock over 10% of holdings, and any employer stock, raises a
  concentration flag.

**Why nudges are pull-based.** MCP servers can't push messages into a chat.
Nudges reach the user two ways:
- The server's instructions tell the assistant to call `nudges_due` at the
  start of each session.
- `calendar_export` produces an `.ics` file with alerts, so the user gets
  real notifications from their own calendar.

## 4. Authentication and identity

1. Every tool call and resource read passes through `AuthAndAudit` before it
   runs.
2. The caller must send `Authorization: Bearer <key>` or `X-API-Key: <key>`.
   Valid keys come from `CAREER_COPILOT_API_KEY` (comma-separated, so keys
   can be rotated with no downtime). The comparison runs in constant time
   (`hmac.compare_digest`).
3. Without a key the call fails with `Unauthorized`. In HTTP mode the server
   **refuses to start** if no key is configured, unless
   `CAREER_COPILOT_ALLOW_OPEN=1` is set for local testing.
4. **Data namespace.** Each user's records live in a file named after a
   SHA-256 hash of their key, plus the subscriber header if one is
   configured. Raw keys are never stored or logged.
5. `/health` is open, so the host can run liveness checks.

**Open question: how MCPize identifies subscribers.** MCPize gives each
subscriber an API key and enforces quotas at its gateway. Its public docs
do not say what it forwards to an upstream server: no header names, and no
shared secret.

- **If the gateway passes each subscriber's key or ID through:** isolation
  works as built. For an ID header, set `CAREER_COPILOT_USER_HEADER` to its
  name.
- **If the gateway sends one shared key for all traffic:** every subscriber
  would share one data namespace.

Resolve this in the MCPize developer dashboard before taking paid users,
then check it with two test subscriptions.

## 5. Data and privacy

- **What's stored, per user:**
  - profile and experience facts;
  - imported resume versions, which hold the text the user pasted;
  - applications and reminders;
  - finance records: account names and balances, holdings, budget lines.

  `resume_score` and `linkedin_review` keep nothing.
- **Financial data is sensitive.** Ask for balances as rounded numbers.
  Never ask for account numbers or credentials; no tool takes them.
- **Logs** keep tool names, user hashes, timings and arguments. Secrets,
  work authorization and **every money amount** (`balance`, `value`,
  `current`, `target` and so on) are masked. Long text, such as a pasted
  resume or LinkedIn profile, is logged only as its length.
  `test_features.py` checks that no amount reaches the log.
- **User rights:** `data_export` returns everything and `data_delete`
  removes the user's file.
- **Disclaimers:** every money output and the investing guides carry an
  "education, not advice" disclaimer. `runway_calc` says to confirm visa
  timelines with an attorney. This keeps the product on the education side
  of the line between financial education and regulated investment
  advice. Get a legal review before marketing it as "advice".
- **Storage durability risk:** MCPHosting's public page does not say whether
  disk survives a redeploy. Until that is confirmed, treat SQLite as
  possibly lost on each deploy. Phase 2 moves storage to a managed Postgres
  (section 9).

## 6. Logging and observability

| Event | Example line |
|---|---|
| Startup | `Career Copilot 0.2.0 starting` / `fastmcp 2.x, MCP protocol 2025-xx-xx, transport streamable-http` / endpoints, tool count, key count |
| Request | `tool call: application_log user=u_3f2a... args={'company': 'Acme', ...}` |
| Timer | `tool done: application_log in 4.2 ms` |
| Denied | `tool denied: profile_get (bad or missing key)` |
| Handled error | `tool error: X after 1.3 ms: ...` |
| Crash | `tool crashed: X after 2.0 ms` plus a full traceback. The client gets a generic error and the server keeps running |

Logs go to stdout, which the host's log viewer reads, and to
`logs/mcp_server.log`. The file rotates at 10 MB and keeps 10 files. Writes
are queued so a slow disk never blocks a request.

## 6a. Self-improvement loop (runs unattended)

```
 users' assistants ──► server ──(anonymous signals)──► _insights.db
                                                        │ GET /insights (admin key,
                                                        ▼ k-anonymous aggregates)
 GitHub Actions, weekly ──► Claude edits copilot/knowledge/ ──► all 5 test suites
                                                        │
                       copilot/knowledge/ only + all green ─────┼──► auto-merge ──► MCPHosting redeploys
                       anything else ───────────────────┴──► PR labelled needs-review
```

**What's collected** (`copilot/insights.py`):
- each tool call's name, success and latency;
- lookups that found nothing: unknown roles, patterns, design topics,
  guides;
- `feedback` ratings, with a reason picked from a fixed list.

**Privacy guarantees, enforced in code and tests:**
- **No free text, ever.** Labels are scrubbed to lowercase letters, max 40
  characters. Anything with an `@`, a URL or digits is dropped.
- **Users can't be identified.** Each user appears only as an HMAC of their
  storage id with a server-side salt (`CAREER_COPILOT_INSIGHTS_SALT`), so
  insight rows can't be joined back to anyone's records.
- **Labels are k-anonymous.** A label is reported only once
  `CAREER_COPILOT_K_ANON` distinct users have sent it (default 5).
- **Deletion covers signals.** `data_delete` also erases the user's
  signals.
- **Operators can opt out.** `CAREER_COPILOT_INSIGHTS=0` turns signals off
  entirely.
- **The endpoint is locked.** `/insights` returns 404 unless
  `CAREER_COPILOT_ADMIN_KEY` is set, and 401 without it.

**What the improver may do** (`agents/IMPROVE.md`):
- add common roles users asked for (at most 3 a week);
- add aliases and recognition signals;
- clarify guides that users rated poorly;
- log every change with the signal that justified it in
  `copilot/knowledge/CHANGELOG.md`.

**Safety rails:**
- `test_knowledge.py` checks structure and cross-references, keeps
  disclaimers in place, and rejects personal data and instruction-like
  text. Knowledge text reaches every user's assistant, so a poisoned label
  must never become a prompt injection.
- All 4 suites run on the changed code.
- A path guard auto-merges only changes confined to `copilot/knowledge/`.
- Any other change becomes a pull request labelled `needs-review`.
- `GITHUB_TOKEN` can't modify workflows, so the improver can't loosen its
  own rails.

**Cost.** One Claude run a week, about 40 turns at most on Sonnet. That's
usually well under a few dollars a month, billed to your Anthropic API key.

## 7. Costs

### 7.1 Fixed and running costs

| Item | Cost | Notes |
|---|---|---|
| MCPHosting Free | $0/mo | 2 projects, 20 builds, **500 MCP requests/mo** |
| MCPHosting Pro | $19/mo | 10 projects, 200 builds, **50,000 requests/mo**, request history |
| MCPHosting Team | $49/mo | 30 projects, 1,000 builds, **250,000 requests/mo** |
| MCPize | 20% of each sale | You keep 80%. The fee covers Stripe processing, tax, support, fraud checks and promotion. Paid out monthly via Stripe Connect |
| GitHub | $0 | Public repo |
| LLM tokens | $0 | The user's AI client runs the model. The server makes no LLM calls |
| Domain (optional) | about $10-15/yr | Only if you want a custom URL |

Prices come from mcphosting.io and mcpize.com as of November 2026. Check
them again before you launch.

### 7.2 Usage model (assumptions)

An MCP session sends overhead requests (`initialize`, `tools/list`) before
the tool calls. MCPHosting doesn't say which requests count, so this model
assumes all of them do.

- Active subscriber: 20 sessions a month, 3 overhead plus 8 tool calls
  each. That comes to **about 220 requests per subscriber per month**.
- Subscriber price: **$9/month** (proposed), which nets **$7.20** after
  MCPize's 20%.

### 7.3 Scenarios

| Paying subscribers | Requests/mo | MCPHosting plan | Gross | Net after MCPize | Hosting | Monthly profit |
|---|---|---|---|---|---|---|
| 2 (beta) | 440 | Free | $18 | $14.40 | $0 | $14.40 |
| 25 | 5,500 | Pro | $225 | $180 | $19 | $161 |
| 200 | 44,000 | Pro | $1,800 | $1,440 | $19 | $1,421 |
| 1,000 | 220,000 | Team | $9,000 | $7,200 | $49 | $7,151 |

**Break-even on Pro is 3 paying subscribers.** The Free plan carries about
2 active users, so move to Pro before a public launch.

### 7.4 Proposed subscriber plans

| Plan | Price | Includes |
|---|---|---|
| Free trial | $0, 7 days | Every tool, to drive conversion |
| Pro | $9/mo | Every tool, fair-use quota of about 1,000 calls/mo |
| Layoff Sprint | $19 once, 30 days | Pro plus priority on runway and pipeline features (Phase 2 nudges) |

These are starting points. MCPize supports monthly plans with included
usage and overage rates.

## 8. Limitations of v0.3

- Resume, contribution and LinkedIn checks are heuristics (verbs, numbers,
  keywords), not model judgment. The user's AI assistant supplies the
  judgment and the rewriting.
- The role catalogue covers 19 common office and tech roles. Trades,
  healthcare, education and public-sector roles aren't in it yet, though
  contribution coaching, resumes, goals and finance work for anyone. Pay
  guidance is levers and sources, not salary numbers, because the server
  has no verified comp data.
- Finance guides use US accounts as examples (401(k), HSA, COBRA). The
  dashboard itself is currency- and country-neutral.
- Market data is annual World Bank indicators, which lag 1-2 years. There
  are no live prices.
- Nudges are pull-based plus an `.ics` export. There is no server push.
- Claude.ai and ChatGPT web connectors can't send the API-key header, so
  they connect through the marketplace URL until OAuth lands.
- SQLite on the host's disk, with durability unconfirmed (section 5).
- Identity depends on how the MCPize gateway forwards subscribers
  (section 4).
- No rate limiting inside the server. MCPize quotas cover that for now.

## 9. Roadmap

| Phase | Scope |
|---|---|
| 2: Durable and multi-tenant | Managed Postgres in place of SQLite, confirmed gateway identity, OAuth 2.1 so Claude.ai and ChatGPT connect directly |
| 3: Search | `roles_search` over Greenhouse, Lever and Ashby public job feeds, matched to the profile and skills gap |
| 4: Proactive | Hosted calendar feed URL (subscribe once, always current), recruiter-email triage, resume export to PDF/DOCX |
| 5: Quality | LLM-graded scoring via client sampling, more roles, verified comp ranges from a licensed data source |
