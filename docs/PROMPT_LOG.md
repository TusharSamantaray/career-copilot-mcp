# Prompt log

What the owner asked, what was done, and how to check it.
Newest first. Never include secrets or personal details.

### 2026-11-09 | v0.3.0-dev
**Asked:** The last build failed; check what's wrong.
**Did:** CI on the latest commit passed; the failure was the scheduled
"Improve knowledge" workflow. No repository secrets are set, so its
fetch hit an empty URL (curl exit 3). Added a setup check that skips all
steps with a notice when secrets are missing, curl retries like the error
report, and the verify gate now runs all 9 suites plus validation and
the simulation.
**Files:** `.github/workflows/improve.yml`, `docs/ENGINEERING.md`.
**Tests:** see commit.
**Try it:** Actions → Improve knowledge → Run workflow: green, "Skipped".
**Open:** set the secrets to turn the improver on (needs B-050 to see
much); the owner decides.

### 2026-11-09 | v0.3.0-dev
**Asked:** Is all the technical documentation up to date? Make sure it's
accurate.
**Did:** Checked every guide against the code (tool, resource and prompt
counts were already right: 105, 9, 17). Fixed: the architecture claim
that nobody else's queries reach your data; a new diagram for personas,
search and reveal; README layout (10 missing modules), test lists, the
"source is public" line, local install and Deploy needing repo access;
spec data model and build status; tour and connect examples; setup test
list; engineering suite rows; docs index; simulation check count (10).
LICENSE wording flagged for the owner (B-066), not changed.
**Files:** `README.md`, `docs/ARCHITECTURE.md`, `docs/SPEC.md`,
`docs/CONNECT.md`, `docs/SETUP.md`, `docs/TOUR.md`, `docs/OWNER.md`,
`docs/ENGINEERING.md`, `docs/README.md`, `docs/BACKLOG.md`.
**Tests:** see commit (docs only).
**Try it:** open `docs/ARCHITECTURE.md`, section 9.
**Open:** B-066 license wording; B-067 sharing with friends.

### 2026-11-08 | v0.3.0-dev
**Asked:** (Found by the simulation.) The digest listed the same
recruiter twice for one skill.
**Did:** demand.digest groups by role and skill; a person counts once;
sources listed as a sorted list; pathway reasons name all sources.
**Files:** `copilot/demand.py`, `app.py`, `tests/test_http.py`,
`validation/cases/demand_pathway.py`, `simulation/run.py`.
**Tests:** see commit.
**Try it:** "What are recruiters asking for in data engineering?"
**Open:** nothing.

### 2026-11-08 | v0.3.0-dev
**Asked:** A simulation of 5 users creating profiles and 2 recruiters
with a dummy job description finding them; a way to test it locally.
**Did:** simulation/run.py starts the real server with one API key per
made-up person (7), then runs every step over MCP: ground rules,
profiles, confirmed facts with a planted employer, email and phone,
persona previews (one line hidden, one kept private), survey, search
with must-haves, chat (skill, identity and salary questions), intros
(one yes, one no), reveal, demand digest and a pathway. Nine checks;
REPORT.md tells the story. --serve keeps the server up for Claude
Code; --check runs in CI and before commits.
**Files:** `simulation/`, `.github/workflows/ci.yml`, `.gitignore`,
`README.md`, `docs/ENGINEERING.md`.
**Tests:** see commit.
**Try it:** `uv run simulation/run.py`, then open simulation/REPORT.md.
**Open:** the run showed the demand digest counting one recruiter twice
for a skill (survey and search as separate rows); fixed next.

### 2026-11-08 | v0.3.0-dev
**Asked:** Wrap up the remaining issues; identity reveal (#16).
**Did:** copilot/intro.py: persona_intro (company, role, checked
message; a request in the owner's file and a sent note in the
recruiter's), persona_intros (received and sent, who confirmed, screen
count), identity_reveal (either side confirms with what to share, or
declines; nothing shared until both confirm; each side's contact stays
in its own file; reveal noted on the persona with after_screen).
Direct lane only. TERMS_VERSION 2026-11-08.16.
**Files:** `copilot/intro.py`, `app.py`, `copilot/conduct.py`,
`docs/PRIVACY.md`, `docs/TERMS.md`, `tests/test_http.py`,
`validation/cases/identity_reveal.py`.
**Tests:** see commit.
**Try it:** "Any introduction requests?", then "Yes, share my name and
email".
**Open:** the agency lane (an agency holds identity until the offer) is
the owner's call (B-062).

### 2026-11-08 | v0.3.0-dev
**Asked:** Wrap up the remaining issues; the survey, demand digest and
pathways from #14 (folded into #13).
**Did:** copilot/demand.py: versioned SURVEYS (v1, three questions);
recruiter_survey saves answers in the recruiter's own file, company
optional; persona_search notes role and skills asked; demand_digest
counts distinct people per role and skill over 90 days, with who and
source, never candidate data; pathway_build guided (proof of demanded
skills already held first, then up to 4 demanded gaps, every step with
its reason, no step without one) or immediate (roles asking for what
they already prove); pathway_next one step at a time.
TERMS_VERSION 2026-11-08.15.
**Files:** `copilot/demand.py`, `copilot/recruiter.py`, `app.py`,
`copilot/conduct.py`, `docs/PRIVACY.md`, `tests/test_http.py`,
`validation/cases/demand_pathway.py`.
**Tests:** see commit.
**Try it:** "Build my pathway to backend engineer".
**Open:** inbox_triage patterns aren't a demand source yet (email text
isn't stored, so only counts could be used). A minimum count before a
signal shows could be added once there are more recruiters.

### 2026-11-08 | v0.3.0-dev
**Asked:** Wrap up the remaining issues; recruiter search (#13).
**Did:** copilot/recruiter.py: persona_search (skills from the posting
plus must_have and nice_to_have; must_have filters, ranked by coverage
then evidence weighted by ownership; location keeps matches there or
remote; top 5; the searcher's own persona left out; no pay echoed) and
persona_chat (answers only from evidence lines; identity and salary
questions refused; counts questions per persona in the asker's file,
never the text). No new website: recruiters are invited users of the
same connector; find_candidates starter prompt; owner runbook has the
recruiter message. Terms line on fair use of personas;
TERMS_VERSION 2026-11-08.14.
**Files:** `copilot/recruiter.py`, `app.py`, `copilot/conduct.py`,
`docs/PRIVACY.md`, `docs/TERMS.md`, `docs/OWNER.md`,
`tests/test_http.py`, `validation/cases/recruiter_search.py`.
**Tests:** see commit.
**Try it:** from a second invited account, "I'm hiring", paste a
posting, "it must have Python".
**Open:** a job link isn't fetched; the recruiter pastes the posting
text. Survey, demand digest and pathways follow (B-061).

### 2026-11-08 | v0.3.0-dev
**Asked:** Wrap up the remaining issues; persona v1 (#12).
**Did:** copilot/persona.py: a view over confirmed facts and confirmed
profile fields; employer names (from facts, experience, company lists
and snapshot avoid_terms), emails, links, handles and phone numbers
scrubbed; personal-trait lines left out; experience as a range; skills
only when a confirmed fact proves them. persona_publish previews with a
preview_id and publishes only that exact view on accept;
persona_unpublish hides or deletes. Stored in the person's own file.
The new validation case caught "Catholic" missing from the trait words;
added it and four others. Privacy notice section and terms line;
TERMS_VERSION 2026-11-08.13.
**Files:** `copilot/persona.py`, `copilot/conduct.py`, `app.py`,
`copilot/store.py`, `docs/PRIVACY.md`, `docs/TERMS.md`,
`tests/test_soul.py`, `validation/cases/persona_privacy.py`.
**Tests:** see commit.
**Try it:** "Show me what my anonymous persona would look like".
**Open:** names inside fact text (a manager's first name) can't be
detected; the preview and hide are the safeguard.

### 2026-11-08 | v0.3.0-dev
**Asked:** Wrap up the remaining issues; first, the trust pack (#4).
**Did:** Machine-readable DATA_HANDLING in conduct.py (what, where,
kept_for, who_can_read; never_stored; logs; usage counts; controls),
returned by ground_rules, the copilot://data-handling resource and an
unauthenticated GET /data-handling. ground_rules rewritten as a
disclosure: a three-line summary and statements, no show_user or
reply_style directives. TERMS_VERSION 2026-11-08.12 (owner asked for
issue #4, which calls for this change).
**Files:** `copilot/conduct.py`, `app.py`, `docs/PRIVACY.md`,
`docs/TERMS.md`, `tests/test_soul.py`, `tests/test_http.py`,
`validation/cases/trust_pack.py`.
**Tests:** see commit.
**Try it:** open /data-handling, or ask "What data do you keep about
me, and where?".
**Open:** nothing enforces "shown before the first save" in code; the
server instructions call ground_rules first.

### 2026-11-08 | v0.3.0-dev
**Asked:** A place in the repo to track improvements: validation or
benchmarking.
**Did:** validation/ with run.py, cases/ (resume_rebuild modelled on
the owner's rebuild with invented text; outreach_gate), RESULTS.md
scoreboard and HISTORY.md (row only when a score changes). Added to CI
and to the working agreement in CLAUDE.md.
**Files:** `validation/`, `.github/workflows/ci.yml`, `CLAUDE.md`,
`README.md`, `docs/ENGINEERING.md`.
**Tests:** see commit.
**Try it:** open validation/RESULTS.md.
**Open:** older improvements (resume_tailor, sponsorship_verify,
job_search) can get cases too; added as needed.

### 2026-11-08 | v0.3.0-dev
**Asked:** Check the timeline against the owner's own resume proof.
**Did:** Compared the proof's checks with resume_snapshot. Changed the
summary check to "leads with a number" (the proof's own measure), added
avoid_terms for internal names, stopped counting education as roles,
added role count and percent change to the proof. The proof itself
stays out of the repo (it has contact details).
**Files:** `copilot/timeline.py`, `app.py`, `tests/test_soul.py`,
`docs/ENGINEERING.md`.
**Tests:** see commit.
**Try it:** snapshot two versions with avoid_terms, then "Show how my
resume improved".
**Open:** story arc and "pinned first bullet" from the proof aren't
measured; they're judgment calls.

### 2026-11-08 | v0.3.0-dev
**Asked:** Model sending like Muse: draft, review, then send only on
the person's yes, from their own linked apps; store nothing. Also:
keep sign-in invite-only and the source private; fold the recruiter
survey into the recruiter view; persona access without a new website.
**Did:** outreach_review and outreach_approve (copilot/outreach.py): a
signed, stateless seal over the exact text, recipient and channel, 30
minutes, consent=True required; the person's own connector sends and
the assistant verifies. Weakness check (performance plan, urgency, visa
deadline). Terms, privacy notice, server instructions and principle 6
updated; TERMS_VERSION 2026-11-08.11 (owner OK). Decisions recorded in
the backlog (B-042 done, B-054 folded into B-053).
**Files:** `copilot/outreach.py`, `app.py`, `copilot/conduct.py`,
`docs/TERMS.md`, `docs/PRIVACY.md`, `CLAUDE.md`, `docs/SPEC.md`,
`docs/BACKLOG.md`, `docs/ENGINEERING.md`, `tests/test_soul.py`.
**Tests:** see commit.
**Try it:** with Gmail connected, "Draft a thank-you email to the
recruiter and send it after I check it".
**Open:** the server can't stop a host from calling Gmail directly; it
only approves the exact reviewed text (written down in ENGINEERING.md).

### 2026-11-08 | v0.3.0-dev
**Asked:** Continue on the updated GitHub issues and new features.
**Did:** Resume timeline (GitHub #7, B-051): four tools over a new
append-only "snapshot" record. Checks are computed from saved text
(level tags, numbers no confirmed fact holds, summary style); branches
and regressions show in the timeline; the proof is Markdown with the
final resume appended and response_check on it. rendered_file masked in
logs. New GitHub issues #8 to #16 added as B-052 to B-058, waiting on
the owner (they share data between people or send for the person).
**Files:** `copilot/timeline.py`, `app.py`, `copilot/store.py`,
`tests/test_soul.py`, `docs/BACKLOG.md`, `docs/SPEC.md`, `docs/TOUR.md`.
**Tests:** see commit.
**Try it:** "Snapshot my resume as September", again as October, then
"Show how my resume improved".
**Open:** screenshots aren't rendered by the server (a file path per
version instead); "org names" check from the issue left out (no reliable
way to tell an internal team name from a real one).

### 2026-11-07 | v0.3.0-dev
**Asked:** Keep resolving open issues (B-046).
**Did:** Weekly error report: agents/triage.py turns the /insights
summary into Markdown (issue codes with the fix from errors.py, tools
under 90% success after 10 calls), and .github/workflows/triage.yml
opens or comments on one "Error report" issue. No pull requests or
deploys, by decision. list_changed after deploys recorded as not
applicable. New suite tests/test_triage.py, in CI and the local run.
**Files:** `agents/triage.py`, `.github/workflows/triage.yml`,
`.github/workflows/ci.yml`, `tests/test_triage.py`, `docs/OWNER.md`,
`docs/ENGINEERING.md`.
**Tests:** see commit.
**Try it:** Actions → Error report → Run workflow.
**Open:** reports appear only with 5+ people and B-050 on.

### 2026-11-07 | v0.3.0-dev
**Asked:** Keep resolving open issues (B-046 investigation).
**Did:** Found that anonymous counts (insights) lived in a local SQLite
file, wiped on every free-host restart, so the weekly improver and
report_issue counts saw almost nothing. Added an opt-in Postgres store
(cc_signals table, same hashing and k-anonymity, 400-day pruning there,
floats for JSON), /health `insights`, Postgres CI checks. Off by default:
keeping counts longer is a privacy-behaviour change, so the owner decides
(B-050).
**Files:** `copilot/insights.py`, `app.py`, `tests/test_postgres.py`,
`tests/pg_reset.py`, `tests/test_oauth.py`, `docs/SETUP.md`,
`docs/OWNER.md`.
**Tests:** see commit; Postgres checks run in CI.
**Try it:** open /health and look for "insights".
**Open:** B-050 owner decision; then B-046 triage.

### 2026-11-07 | v0.3.0-dev
**Asked:** Keep resolving open issues (B-034 next).
**Did:** Dashboard action strip: `action_strip` in copilot/dashboard.py
ranks live applications (overdue, due in two days, no next step,
sponsorship unknown when the person needs it), five at most with a
"+N more" line; rendered at the top of Today and Pipeline. A "no reply
in N days" rule was left out: applications don't record when they were
sent, so it couldn't be computed honestly. Spec build order now fully
done; stale "persistent disk" line removed.
**Files:** `copilot/dashboard.py`, `copilot/dashboard.html`,
`copilot/sponsorship.py`, `tests/test_soul.py`, `docs/SPEC.md`.
**Tests:** see commit.
**Try it:** "Show my dashboard".
**Open:** B-046 next.

### 2026-11-07 | v0.3.0-dev
**Asked:** Keep resolving open issues (B-029 next).
**Did:** sponsorship_verify: classifies each posting sentence as no, yes
or unclear and quotes it; adds what the person logged on applications;
answer is no if any source says no, yes only with explicit evidence,
otherwise unstated; conflicts flagged; save=true writes an explicit
posting answer to an application. USCIS and DOL filing links as
education. 88 tools; spec build status updated.
**Files:** `copilot/sponsorship.py`, `app.py`, `tests/test_soul.py`,
`docs/SPEC.md`, `docs/BACKLOG.md`.
**Tests:** see commit.
**Try it:** paste a posting and ask "Does this company sponsor visas?"
**Open:** B-034 and B-046 next.

### 2026-11-07 | v0.3.0-dev
**Asked:** Keep resolving open issues, with docs and logs in each commit.
**Did:** resume_tailor (B-026): the assistant proposes lines with the
fact ids they rest on; the server blocks unconfirmed or missing facts,
unsupported numbers, ownership inflation, merged claims across jobs,
honest gaps and invented keywords, runs response_check on accepted
lines, and can save them as a resume version. Found while testing: tool
crashes skipped INTERNAL_ERROR (B-047), and a date-dependent test
(B-048: today on inbox_triage and calendar_interviews). Spec status,
counts (87 tools) and the engineering table updated.
**Files:** `copilot/tailor.py`, `app.py`, `tests/test_soul.py`,
`docs/SPEC.md`, `docs/ENGINEERING.md`, `docs/BACKLOG.md`.
**Tests:** see commit.
**Try it:** paste a posting and say "Tailor my resume for this and save
it as Acme v1".
**Open:** B-029, B-034, B-046 next; B-042 and B-043 wait on the owner.

### 2026-11-04 | v0.3.0-dev
**Asked:** Continue the gap spec: self-healing v1 (issue 8).
**Did:** Stable error codes (`copilot/errors.py`) on every tool and
resource error: AUTH_REQUIRED, NOT_INVITED, UNKNOWN_TOOL,
UNKNOWN_RESOURCE, BAD_ARGUMENTS (field names, never values),
INTERNAL_ERROR (with a ref also written to the log). Found and fixed:
unknown tools and validation errors were logged as crashes and shown as
"Internal error". New `report_issue` tool (anonymous counts of code, tool
and app family). Job boards answering with non-JSON no longer break a
search. Error code table and retry rule in CONNECT.md. error_code and
client_hint are masked in logs. 86 tools.
**Files:** `copilot/errors.py`, `app.py`, `copilot/jobs.py`,
`tests/test_soul.py`, `tests/test_http.py`, `docs/CONNECT.md`.
**Tests:** see commit.
**Try it:** "Call the tool no_such_tool", then "What does that error mean?"
**Open:** B-046 (triage Action, list_changed) waits on real reports.

### 2026-11-04 | v0.3.0-dev
**Asked:** Build the next tasks from the gap spec (sections 1-6 were
already built; section 7 is the tester incident).
**Did:** Issue 6: test_oauth passes here and in CI, so not reproduced,
but found the callback could crash on an unreachable GitHub or a non-JSON
reply; now a 502 page, error kind logged. Test adds a garbled-reply case
and keeps its fake GitHub off any proxy. Issue 5: /health reports
invite_only (never names). Issue 2: tester message in OWNER.md (repo is
private, so it offers access instead of a link). Issues 1, 3, 10 recorded
as decisions in ENGINEERING.md; 7, 8, 9 added as B-043, B-045, B-046.
**Files:** `copilot/signin.py`, `app.py`, `tests/test_oauth.py`,
`docs/OWNER.md`, `docs/ENGINEERING.md`, `docs/BACKLOG.md`.
**Tests:** see commit.
**Try it:** open /health on the live server and look for invite_only.
**Open:** B-042 (who may sign in) and B-043 (public or private source,
ground_rules rewrite) are owner decisions.

### 2026-11-04 | v0.3.0-dev
**Asked:** The diagrams look washed out and ugly; use a simple, elegant
palette that's visible on both white and black backgrounds.
**Did:** Replaced the light-fill, dark-text classes with translucent
tints (10% alpha) and mid-tone outlines, and removed forced text colours
so each theme keeps its own text colour. Sequence diagram boxes use 8%
tints. Pink became purple and orange became red. The legend in
ARCHITECTURE.md now includes copy-paste class lines for new diagrams.
**Files:** `README.md`, `docs/ARCHITECTURE.md`, `docs/ENGINEERING.md`,
`docs/CONNECT.md`, `docs/SETUP.md`, `docs/SPEC.md`, `docs/TOUR.md`.
**Tests:** see commit; docs only.
**Try it:** open docs/ARCHITECTURE.md on GitHub in light, then dark theme.
**Open:** no local Mermaid renderer available, so check the look on GitHub.

### 2026-11-03 | v0.3.0-dev
**Asked:** Make testing, problems and fixes easy to find; bring all docs
up to date with meaningful Mermaid diagrams and a proper colour scheme.
**Did:** New `docs/ENGINEERING.md` (test flow, suite table, acceptance
tests, test hygiene, timeline, before/after of the free-host problems,
16 problems with cause, fix and guard, engineer FAQ). Rewrote
`docs/ARCHITECTURE.md` (legend plus 8 diagrams, each with its question).
Coloured and refreshed the README diagrams; added diagrams to CONNECT
(which way to connect), SETUP (free hosting pieces), SPEC (build
status), TOUR (rewritten for current features). Updated the `tour`
prompt to match. Okabe-Ito palette with dark text on light fills.
Working agreement now asks for an ENGINEERING row per fixed problem.
**Files:** `docs/ENGINEERING.md`, `docs/ARCHITECTURE.md`, `README.md`,
`docs/CONNECT.md`, `docs/SETUP.md`, `docs/SPEC.md`, `docs/TOUR.md`,
`docs/README.md`, `app.py`, `CLAUDE.md`.
**Tests:** 8 suites passed, 0 failed.
**Try it:** open docs/ENGINEERING.md on GitHub.
**Open:** couldn't render-check the diagrams locally (running the Mermaid
CLI was blocked); syntax reviewed by hand. PRIVACY.md wording left as is
to avoid another ground-rules version.

### 2026-11-03 | v0.3.0-dev
**Asked:** Owner OK'd correcting the privacy text; asked whether Neon's
free plan deletes data after 6 hours.
**Did:** Explained: "history retention 6 hours" is the point-in-time
restore window, not deletion. Updated the demo-server lines in
PRIVACY.md, TERMS.md and conduct.TERMS (data in a managed database;
still free, keep a copy). Ground rules version 2026-11-03.10.
**Files:** `docs/PRIVACY.md`, `docs/TERMS.md`, `copilot/conduct.py`.
**Tests:** 8 suites passed, 0 failed.
**Try it:** "what happens to my data if the server restarts?"
**Open:** none.

### 2026-11-03 | v0.3.0-dev
**Asked:** Owner reset the Neon password and set the new pooled
DATABASE_URL in Render.
**Did:** Confirmed the live server reports `"storage": "postgres"`.
Closed B-040.
**Files:** `docs/BACKLOG.md`.
**Tests:** 8 suites passed, 0 failed (docs only).
**Try it:** save something, let this deploy finish, ask for it back.
**Open:** none.

### 2026-11-03 | v0.3.0-dev
**Asked:** Set the app up on Neon (generic Neon prompt) with the owner's
connection strings.
**Did:** Skipped the template's `neon init`/`neon deploy` (JavaScript
scaffolding; the strings were already provided). Per the Neon Postgres
skill, a long-running web app uses the pooled (-pooler) URL; set
psycopg `prepare_threshold=None` for PgBouncer transaction mode. Ran a
non-destructive smoke test on the real Neon database through the pooler:
writes, reads, lists past the prepare threshold, rows encrypted, delete
removes rows and key, and the app over MCP keeps data through a disk
wipe; then cleaned up. `/health` now reports the storage backend.
**Files:** `copilot/store.py`, `app.py`, `tests/test_http.py`.
**Tests:** 8 suites passed, 0 failed; Neon smoke test passed.
**Try it:** add DATABASE_URL (pooled) in Render; /health shows postgres.
**Open:** B-040 rotate the Neon password (it was shared in a chat).

### 2026-11-03 | v0.3.0-dev
**Asked:** The account looked empty after signing in; fix storage for
free.
**Did:** The account wasn't new: the same GitHub id maps to the same
storage id; the free host's disk had been wiped by restarts. Added a
Postgres backend to `copilot/store.py` (used when DATABASE_URL is set):
one `cc_records` table keyed by (user_id, id) and a `cc_keys` table for
wrapped data keys; encryption and every public function unchanged;
`store.users()` replaces listing files for background watches. Startup
names the storage and never prints the URL. New
`tests/test_postgres.py` (per-person rows, encryption, delete, a fresh
process after a disk wipe still sees data, URL never printed); the main
and acceptance suites also pass on Postgres, plain and encrypted. CI has
a Postgres job. Docs: Neon steps in SETUP.md, runbook, privacy notice
names the database host (2026-11-03.9). New dependency
`psycopg[binary,pool]`.
**Files:** `copilot/store.py`, `copilot/watch.py`, `app.py`,
`tests/test_postgres.py`, `tests/pg_reset.py`, `tests/test_soul.py`,
`tests/test_acceptance.py`, `.github/workflows/ci.yml`, `render.yaml`,
`pyproject.toml`, `requirements.txt`, `uv.lock`, docs.
**Tests:** 8 suites passed locally (Postgres suite skips without a
database); Postgres, soul and acceptance passed on a local Postgres.
**Try it:** add DATABASE_URL in Render, save something, restart, check.
**Open:** data saved before this is already gone and must be re-entered
once.

### 2026-11-03 | v0.3.0-dev
**Asked:** claude.ai asks to reconnect on every new chat. Keep it free,
sign up once.
**Did:** Cause: FastMCP's OAuth proxy keeps client registrations and
token mappings on disk; the free host wipes the disk on every sleep,
restart and deploy (25+ deploys today, and the keep-awake cron only ran
once). Replaced it with `copilot/signin.py`: client registration sealed
into the client id (HMAC), sign-in state sealed into the GitHub `state`,
codes and tokens are Fernet-sealed with the GitHub id and login, keyed
from CAREER_COPILOT_JWT_KEY. GitHub's token is used once and dropped.
Invite list checked at sign-in and on every call. Tokens 30 days,
refresh a year. `tests/test_oauth.py` now runs a full sign-in against a
fake GitHub, wipes the disk, restarts, and checks the same token and
refresh still work.
**Files:** `copilot/signin.py`, `app.py`, `tests/test_oauth.py`,
`docs/SETUP.md`, `docs/OWNER.md`.
**Tests:** 8 suites passed, 0 failed.
**Try it:** reconnect once; a new chat the next day shouldn't ask again.
**Open:** saved data is still wiped on restart on the free plan; tokens
can't be revoked one by one (remove from the invite list instead).

### 2026-11-03 | v0.3.0-dev
**Asked:** Trim the backlog down.
**Did:** Refreshed counts (85 tools, 8 resources, 16 prompts) in README
and CLAUDE.md, and the build-status table in docs/SPEC.md. Open now:
B-008 (owner: paid disk), B-010 (owner: lawyer), B-012 (owner: delete
server.py), B-026 resume_tailor, B-029 sponsorship_verify, B-034
dashboard action strip.
**Files:** `README.md`, `CLAUDE.md`, `docs/SPEC.md`.
**Tests:** 8 suites passed, 0 failed (docs only).
**Try it:** open docs/SPEC.md section 7.
**Open:** the six items above.

### 2026-11-03 | v0.3.0-dev
**Asked:** Low-hanging backlog items.
**Did:** B-030: `deadline_add` (refuses a conservative date later than
the best case), `copilot/deadlines.py` fast-track (on within 60 days of
the conservative date), shown in `journey_state`; `job_search` sorts
freshest first when on. Server instructions say to announce fast-track.
Acceptance test B added. Privacy notice lists deadlines (2026-11-03.8).
**Files:** `copilot/deadlines.py`, `copilot/journey.py`, `copilot/jobs.py`,
`copilot/store.py`, `app.py`, `tests/test_acceptance.py`,
`copilot/conduct.py`, `docs/PRIVACY.md`, `docs/TERMS.md`, `docs/SPEC.md`.
**Tests:** 8 suites passed, 0 failed.
**Try it:** "I was laid off; last day in 10 days, 60-day grace period".
**Open:** none.

### 2026-11-03 | v0.3.0-dev
**Asked:** Low-hanging backlog items.
**Did:** B-038: `tests/test_acceptance.py` runs acceptance test A as one
scripted conversation on a fresh server (consent, two doors, three
answers, compass answer saved as a want, 2-3 directions, one picked,
every profile line labelled, at most five questions). Added to CI.
**Files:** `tests/test_acceptance.py`, `.github/workflows/ci.yml`,
`README.md`, `docs/SPEC.md`.
**Tests:** 8 suites passed, 0 failed.
**Try it:** "I don't know what I want" in a new chat.
**Open:** acceptance test B waits on B-030.

### 2026-11-03 | v0.3.0-dev
**Asked:** Low-hanging backlog items.
**Did:** B-036 `data_mirror`: `store.markdown` renders every kind as a
readable page (ids and internals hidden); local mode writes
`~/CareerCopilot/my-data.md`. Tests now set CAREER_COPILOT_HOME so they
never write to the real home folder.
**Files:** `copilot/store.py`, `app.py`, `tests/test_soul.py`.
**Tests:** 7 suites passed, 0 failed.
**Try it:** "Show me everything you know about me".
**Open:** the mirror is written on request, not on every change.

### 2026-11-03 | v0.3.0-dev
**Asked:** Low-hanging backlog items.
**Did:** B-028 `cover_letter_draft`: picks the two confirmed facts with
the most word overlap with the posting, quotes them as stated, applies
the voice, and returns response_check as `check`. Asks for a fact when
none is confirmed.
**Files:** `copilot/prep.py`, `app.py`, `tests/test_soul.py`.
**Tests:** 7 suites passed, 0 failed.
**Try it:** "Draft a cover letter for the Data Analyst role at Acme".
**Open:** none.

### 2026-11-03 | v0.3.0-dev
**Asked:** Low-hanging backlog items.
**Did:** B-035 `recruiter_find`: LinkedIn people-search and web-search
links for recruiters and the hiring manager; no fetching, no sending.
**Files:** `copilot/jobs.py`, `app.py`, `tests/test_soul.py`.
**Tests:** 7 suites passed, 0 failed.
**Try it:** "Who's the recruiter for data roles at Acme?"
**Open:** none.

### 2026-11-03 | v0.3.0-dev
**Asked:** Low-hanging backlog items.
**Did:** B-031: `study_plan` takes loop_format and rotates day types
(coding, design, stories, practical, work sample, case) per format;
default unchanged. A test keeps the rotations in sync with LOOP_FORMATS.
**Files:** `copilot/prep.py`, `app.py`, `tests/test_soul.py`.
**Tests:** 7 suites passed, 0 failed.
**Try it:** "Plan my prep for a values-heavy loop on the 14th".
**Open:** none.

### 2026-11-03 | v0.3.0-dev
**Asked:** Low-hanging backlog items.
**Did:** B-037: `application_log` takes sponsorship (yes, no, unknown);
`pipeline_digest` adds a sponsorship block (unknown, says no) only when
the profile's dealbreakers mention sponsorship. Overdue was already
there.
**Files:** `app.py`, `tests/test_soul.py`.
**Tests:** 7 suites passed, 0 failed.
**Try it:** "What's my pipeline today?" with a sponsorship dealbreaker.
**Open:** none.

### 2026-11-03 | v0.3.0-dev
**Asked:** Low-hanging backlog items.
**Did:** B-033 `lessons` (add, list) and the latest three in
`loop_next_round_prep`. Masked more argument names in logs (add, bullet,
answer, posting_text, resume_text) with tests. Privacy notice lists
lessons (2026-11-03.7).
**Files:** `copilot/loops.py`, `copilot/store.py`, `app.py`,
`copilot/conduct.py`, `docs/PRIVACY.md`, `docs/TERMS.md`,
`tests/test_soul.py`.
**Tests:** 7 suites passed, 0 failed.
**Try it:** "Lesson from Acme: lead with the number".
**Open:** none.

### 2026-11-03 | v0.3.0-dev
**Asked:** Low-hanging backlog items.
**Did:** B-032: `message_draft` takes voice (plain, warm, formal) or the
profile's saved voice; only greeting, opening and sign-off change.
`profile_save` takes voice.
**Files:** `copilot/prep.py`, `copilot/journey.py`, `app.py`,
`tests/test_soul.py`.
**Tests:** 7 suites passed, 0 failed.
**Try it:** "Write my notes in a formal voice", then a thank-you note.
**Open:** none.

### 2026-11-03 | v0.3.0-dev
**Asked:** Low-hanging backlog items.
**Did:** B-027 `ats_keyword_check`: posting skills split into covered,
missing but true (confirmed facts or profile keywords, minus honest
gaps) and missing and a gap.
**Files:** `copilot/ats.py`, `app.py`, `tests/test_soul.py`.
**Tests:** 7 suites passed, 0 failed.
**Try it:** paste a posting, "which keywords am I missing?".
**Open:** none.

### 2026-11-03 | v0.3.0-dev
**Asked:** Do the low-hanging backlog items and trim it down. Owner did
the Render steps (master key, old API key removed).
**Did:** B-025 `ownership_check`: a strong verb needs at least that
ownership in the closest fact; otherwise a softer verb or the "wrote,
led or fixed?" question. Closed B-009 on the owner's word. `server.py`
is still in the folder, so B-012 stays open.
**Files:** `copilot/facts.py`, `app.py`, `tests/test_soul.py`.
**Tests:** 7 suites passed, 0 failed.
**Try it:** "Check this line: Architected our billing platform".
**Open:** B-012 (owner deletes server.py).

### 2026-11-03 | v0.3.0-dev
**Asked:** Continue the backlog.
**Did:** B-011: wrote `docs/SPEC.md` as Spec v2, condensed from CLAUDE.md
part 3, with build and acceptance-test status; moved v1 to
`docs/archive/SPEC-v1.md` and fixed links. Added the spec's remaining
gaps to the backlog as B-025 to B-038.
**Files:** `docs/SPEC.md`, `docs/archive/SPEC-v1.md`, `docs/BACKLOG.md`,
`docs/README.md`, `docs/SETUP.md`, `CLAUDE.md`.
**Tests:** 7 suites passed, 0 failed (docs only).
**Try it:** open docs/SPEC.md, section 7.
**Open:** the full Spec v2 text from the owner's document is still not in
the repo.

### 2026-11-03 | v0.3.0-dev
**Asked:** Continue the backlog.
**Did:** B-008, code side: in HTTP mode FASTMCP_HOME defaults to
`<COPILOT_DATA_DIR>/_fastmcp`, so FastMCP's encrypted sign-in store sits
with the data and one disk keeps both. SETUP.md has the paid-disk steps
and render.yaml snippet. Left open for the owner's spending decision.
**Files:** `app.py`, `tests/test_oauth.py`, `docs/SETUP.md`.
**Tests:** 7 suites passed, 0 failed.
**Try it:** owner reads "Keep data across restarts" in SETUP.md.
**Open:** needs the owner to choose the paid disk.

### 2026-11-03 | v0.3.0-dev
**Asked:** Continue the backlog.
**Did:** B-021: with CAREER_COPILOT_MASTER_KEY set, each record body is
AES-GCM encrypted with the person's own random data key, bound to the
record id; data keys live in `_keys.db`, wrapped by the master key and
bound to the person. `delete_all` destroys the key first. Rows written
before encryption still read; a row that fails to decrypt is skipped
with a warning (no content). New `cryptography` dependency. CI runs the
main suite a second time encrypted. render.yaml generates the key for
new deploys. Privacy notice updated (2026-11-03.6).
**Files:** `copilot/store.py`, `copilot/watch.py`, `tests/test_crypto.py`,
`.github/workflows/ci.yml`, `render.yaml`, `pyproject.toml`,
`requirements.txt`, `uv.lock`, `docs/SETUP.md`, `docs/OWNER.md`,
`docs/PRIVACY.md`, `docs/TERMS.md`, `copilot/conduct.py`, `README.md`.
**Tests:** 7 suites passed, 0 failed; soul, http and features also pass
encrypted.
**Try it:** owner adds the master key in Render; data export still works.
**Open:** the existing Render service needs the key added by hand. If it
is ever changed, stored data can't be read.

### 2026-11-03 | v0.3.0-dev
**Asked:** Continue the backlog.
**Did:** B-020: `watch_create` (new_postings, assessment_expiry,
follow_up_due, deadline; daily or weekly), `watches` (list, remove),
`digest_get` (runs due watches, returns unread outbox items once, quiet
when empty). Optional background runs with
CAREER_COPILOT_WATCH_MINUTES. Server instructions call digest_get at
session start when watches exist. Privacy notice updated (2026-11-03.5).
**Files:** `copilot/watch.py`, `copilot/store.py`, `app.py`,
`copilot/conduct.py`, `docs/PRIVACY.md`, `docs/TERMS.md`,
`docs/SETUP.md`, `tests/test_soul.py`.
**Tests:** 6 suites passed, 0 failed.
**Try it:** "Watch greenhouse:anthropic for new engineering roles,
daily", then a new chat the next day.
**Open:** on the free plan the server sleeps without keep-awake, so
watches mostly run when a chat opens.

### 2026-11-03 | v0.3.0-dev
**Asked:** Continue the backlog.
**Did:** B-016: `jd_analyze` keeps a short "posting" record (title,
company, required and preferred skills; no text). `skill_gap_evidence`
ranks skills by demand x missing evidence, refuses below min_postings,
and reports reply rate per resume version (new `resume_label` on
`application_log`) once a version has 5 applications. Privacy notice
updated (version 2026-11-03.4).
**Files:** `copilot/evidence.py`, `copilot/jobs.py`, `copilot/store.py`,
`app.py`, `copilot/conduct.py`, `docs/PRIVACY.md`, `docs/TERMS.md`,
`tests/test_soul.py`.
**Tests:** 6 suites passed, 0 failed.
**Try it:** analyze five postings, then "what skill gap is costing me
most?"
**Open:** none.

### 2026-11-03 | v0.3.0-dev
**Asked:** Continue the backlog.
**Did:** B-024: `loop_next_round_prep` takes calendar events from the
person's own calendar connector and reports on_calendar (with the date),
not_on_calendar (confirm with the recruiter first) or not_checked.
Fixed the previous log entry's version label.
**Files:** `copilot/loops.py`, `app.py`, `tests/test_soul.py`.
**Tests:** 6 suites passed, 0 failed.
**Try it:** "Prep me for round 2 at Acme" with your calendar connected.
**Open:** none.

### 2026-11-03 | v0.3.0-dev
**Asked:** Continue the backlog.
**Did:** B-023: triage reads a req id from emails; a rejection updates
only the open application at that company whose req id or role matches;
a lone application matched by company alone carries a "check" note;
otherwise a "confirm" proposal lists the candidates and apply skips it.
`application_log` takes `req_id`. Split the calendar date check into
B-024.
**Files:** `copilot/triage.py`, `copilot/autopilot.py`, `app.py`,
`tests/test_soul.py`.
**Tests:** 6 suites passed, 0 failed.
**Try it:** two roles at one company, then a vague rejection email.
**Open:** B-024.

### 2026-11-03 | v0.3.0-dev
**Asked:** Continue the backlog.
**Did:** B-018: `story_coverage` (grid of stories by competency, strength
on four checks, gaps, next story, story numbers not in confirmed facts).
Added B-023 (rejection_triage) found while doing B-017.
**Files:** `copilot/prep.py`, `app.py`, `tests/test_soul.py`.
**Tests:** 6 suites passed, 0 failed.
**Try it:** "Which interview stories am I missing?"
**Open:** none.

### 2026-11-03 | v0.3.0-dev
**Asked:** Continue the backlog.
**Did:** B-017: `loop_round_log` (loop key = company + req id, panel by
role and focus, questions with competency auto-tagged, feedback with
source; preview then apply) and `loop_next_round_prep` (covered and
open competencies, a story per gap preferring ones not yet told, reuse
risk same_panelist or same_company, weak spots, one thing today).
**Files:** `copilot/loops.py`, `app.py`, `copilot/store.py`,
`tests/test_soul.py`, `README.md`, `CLAUDE.md`.
**Tests:** 6 suites passed, 0 failed.
**Try it:** describe round 1 and ask for round 2 prep.
**Open:** rejection_triage (close a loop only on matching title and req
id) and checking round dates against the calendar are still to do.

### 2026-11-03 | v0.3.0-dev
**Asked:** Continue the backlog.
**Did:** B-019: `ats_profile_check` (platform from URL, parse risks,
knock-outs vs answers on file, quirks, verdict). Platform rules live in
`copilot/knowledge/ats.py` so the weekly bot can refresh them; a new
knowledge check keeps every platform covered and every pattern valid.
**Files:** `copilot/ats.py`, `copilot/knowledge/ats.py`, `app.py`,
`tests/test_soul.py`, `tests/test_knowledge.py`.
**Tests:** 6 suites passed, 0 failed.
**Try it:** "Anything to fix before I apply?" with a posting and link.
**Open:** degree and clearance aren't profile fields yet, so they always
show as "need an answer" when a posting asks.

### 2026-11-03 | v0.3.0-dev
**Asked:** Continue the backlog (owner said implement all of it, which
covers the outbound job-board reads B-005 was waiting on).
**Did:** `job_search` reads Greenhouse (first_published), Lever
(createdAt) and Ashby (publishedAt) public boards; drops undated and old
postings and counts why; filters excluded companies, locations,
on-site dealbreaker; ranks by wants; records every role shown in a new
"seen" kind. `jd_analyze` reads level, years, pay vs floor, sponsorship,
fit and gaps from confirmed facts, and a verdict. Checked the three live
boards return those date fields. Privacy notice lists job boards
(version 2026-11-03.3).
**Files:** `copilot/jobs.py`, `app.py`, `copilot/store.py`,
`copilot/conduct.py`, `tests/test_soul.py`, `docs/PRIVACY.md`,
`docs/TERMS.md`, `README.md`, `CLAUDE.md`.
**Tests:** 6 suites passed, 0 failed (acceptance test E added).
**Try it:** "Find new engineering roles at greenhouse:anthropic", twice.
**Open:** company names must be given as board names; no lookup of
which board a company uses yet beyond trying all three.

### 2026-11-03 | v0.3.0-dev
**Asked:** Implement the whole backlog, one item at a time.
**Did:** B-022: `experience_add` also writes a fact (said; confirmed or
unsure); `resume_import` turns each bullet into an imported, unsure fact
with parsed numbers, merges identical bullets (`also_in`) and reports
version conflicts; `resume_build_draft` includes confirmed facts.
**Files:** `copilot/facts.py`, `copilot/careers.py`, `app.py`,
`tests/test_soul.py`.
**Tests:** 6 suites passed, 0 failed.
**Try it:** import two resume versions with different numbers for one
line.
**Open:** stories link to facts with B-018.

### 2026-11-03 | v0.3.0-dev
**Asked:** Write the instructions down so the owner can come back later.
GitHub sign-in is now set up on Render.
**Did:** Checked the live server: sign-in on, no-sign-in and key URLs
refused, apps can register and reach the consent page. Wrote
`docs/OWNER.md` (what's live, setting names, everyday tasks, working with
Claude, limits). B-014 closed: test with a second GitHub account.
**Files:** `docs/OWNER.md`, `CLAUDE.md`, `docs/README.md`,
`docs/BACKLOG.md`.
**Tests:** 6 suites passed, 0 failed (docs only).
**Try it:** open docs/OWNER.md on GitHub.
**Open:** ChatGPT's sign-in path is untested.

### 2026-11-03 | v0.3.0-dev
**Asked:** Build the blueprint's foundation next.
**Did:** B-015 first version: `fact_add` (source, ownership, metrics,
confirmed or unsure; preview shows conflicts), `fact_conflicts`,
`fact_resolve`. Inferred facts can't be confirmed. `response_check` now
also accepts numbers from confirmed, current facts, so a retired number
fails. This reads a new data source inside the existing rule; no rule
text changed, so no new ground-rules version.
**Files:** `copilot/facts.py`, `copilot/conduct.py`, `copilot/store.py`,
`app.py`, `tests/test_soul.py`, `docs/BLUEPRINT.md`.
**Tests:** 6 suites passed, 0 failed (acceptance test C added).
**Try it:** describe two resumes that disagree on a date and a number.
**Open:** experience_add and resume_import don't write facts yet (B-022).

### 2026-11-03 | v0.3.0-dev
**Asked:** Save the next-generation blueprint, update the docs, and make
the main README user-first with setup at the top.
**Did:** Wrote `docs/BLUEPRINT.md` (gaps, tool designs, privacy modes,
trade-offs, order) and added B-015 to B-021 to the backlog. Rewrote the
README: setup first (hosted with GitHub sign-in, local, host your own),
then the first chat, what to ask, how it talks, dashboard, privacy, how
it works, and a developer section at the end.
**Files:** `README.md`, `docs/BLUEPRINT.md`, `docs/BACKLOG.md`,
`docs/README.md`.
**Tests:** 6 suites passed, 0 failed (docs only).
**Try it:** open the repo page on GitHub; the first section should be
"Start in two minutes".
**Open:** the demo address in the README is invite-only until the
owner sets the invite list.

### 2026-11-03 | v0.3.0-dev
**Asked:** The connector URL has the API key in it. Make it a generic
URL. Owner chose Sign in with GitHub.
**Did:** GitHub OAuth through FastMCP's GitHubProvider (scope read:user
only). Storage id is a salted hash of the GitHub user id. Optional
invite list. API keys and ?key= URLs are refused when sign-in is on.
Privacy notice and ground rules updated (version 2026-11-03.2).
render.yaml, CONNECT.md and SETUP.md updated with the GitHub app steps.
**Files:** `app.py`, `tests/test_oauth.py`, `render.yaml`,
`.github/workflows/ci.yml`, `copilot/conduct.py`, `docs/PRIVACY.md`,
`docs/TERMS.md`, `docs/CONNECT.md`, `docs/SETUP.md`.
**Tests:** 6 suites passed, 0 failed.
**Try it:** after the owner adds the GitHub app id and secret in Render,
add `https://career-copilot-cg2k.onrender.com/mcp` in claude.ai.
**Open:** a full sign-in can only be tested with the real GitHub app.
Each MCP request checks the token with GitHub, which adds a little delay.
Restarts on the free plan may ask people to sign in again.

### 2026-11-03 | v0.3.0-dev
**Asked:** Keep picking up backlog items.
**Did:** B-004: `profile_from_text` returns a read-back first and saves
only with apply=true; `direction_options` gives 2-3 directions with fit,
distance, gaps, risk and a first test. journey_state now points
"working, want a change" to direction_options.
**Files:** `copilot/journey.py`, `app.py`, `tests/test_soul.py`,
`CLAUDE.md`, `README.md`.
**Tests:** 5 suites passed, 0 failed.
**Try it:** "I'm good at SQL, Python and dashboards. What directions
could I test?"
**Open:** directions come from the built-in role list, so very niche
roles won't show up.

### 2026-11-03 | v0.3.0-dev
**Asked:** Keep picking up backlog items.
**Did:** B-007: `message_draft` returns a `check` with the response_check
result; `resume_build_draft` ends with a check line.
**Files:** `app.py`, `tests/test_soul.py`, `tests/test_poc.py`.
**Tests:** 5 suites passed, 0 failed.
**Try it:** ask for a thank-you note that says "guaranteed hire" and
"cut costs by 85%". Both parts should be flagged.
**Open:** none.

### 2026-11-03 | v0.3.0-dev
**Asked:** A guided start: the person either says what's on their mind
or answers starter questions, and a path builds from there.
**Did:** Added `journey_state` (stage, known facts with confirmed or
unsure labels, missing fields, the one next question or step). Made
`profile_save` optional-everything and merging, with wants,
dealbreakers, places, companies, keywords, schedule, honest gaps,
unsure and skip. `life_compass` now saves answers. Server instructions
call journey_state first. Three new starter prompts.
**Files:** `copilot/journey.py`, `app.py`, `copilot/coach.py`,
`copilot/store.py`, `tests/test_soul.py`, `CLAUDE.md`, `README.md`.
**Tests:** 5 suites passed, 0 failed.
**Try it:** new chat, "get started", pick "ask me questions".
**Open:** profile_from_text and direction_options (B-004) are next; for
now the assistant extracts facts itself and reads them back.

### 2026-11-03 | v0.3.0-dev
**Asked:** Replies feel generic and too long, and the host assistant's
persona takes over. Make them short, simple, one step at a time.
**Did:** Put a reply style at the top of the server instructions (short,
one step, one question, Career Copilot's voice over any persona). Added
length, question-count, list and heading checks to `response_check` for
chat. `next_steps` and `daily_step` now say to offer one step only.
Ground rules version bumped to 2026-11-03.1 (owner asked for the change).
**Files:** `copilot/conduct.py`, `app.py`, `copilot/guide.py`,
`copilot/coach.py`, `tests/test_soul.py`, `docs/TERMS.md`,
`docs/PRIVACY.md`.
**Tests:** 5 suites passed, 0 failed.
**Try it:** new chat, "What's up next for me, Career Copilot?". One step,
one question.
**Open:** the host assistant can still choose to ignore the style; the
instructions ask, they can't force it.

### 2026-11-03 | v0.3.0-dev
**Asked:** Adopt the next-version working file. Add standard privacy and
user-agreement guidance, and make sure responses stay on task, unbiased,
respectful and free of made-up facts.
**Did:** Saved the working file as `CLAUDE.md` and created the changelog,
this log and the backlog. Reviewed the code against the spec (findings
below). Added `ground_rules` (privacy, terms, conduct, one-time
agreement) and `response_check` (flags insults, profanity, promises,
biased wording, personal traits, missing advice notes and unconfirmed
numbers). Updated the server instructions so every assistant follows the
rules. Wrote `docs/PRIVACY.md` and `docs/TERMS.md`.
**Files:** `copilot/conduct.py`, `app.py`, `copilot/store.py`,
`tests/test_soul.py`, `tests/test_knowledge.py`, `docs/PRIVACY.md`,
`docs/TERMS.md`, `CLAUDE.md`, `CHANGELOG.md`, `docs/BACKLOG.md`.
**Tests:** 5 suites passed, 0 failed.
**Try it:** in a new chat, say "get started", then "check this resume
line: Grew revenue 300% and guaranteed results for 50 clients".
**Open:** the full Spec v2 isn't in the repo yet (`docs/SPEC.md` is still
v1). The privacy and terms texts need a lawyer's review before paid use.

Code review findings (first session):
- Confirmed: `profile_save` requires `target_role`, so someone with no
  direction can't start a profile (B-002).
- Confirmed: `life_compass` takes no arguments and saves nothing (B-003).
- Confirmed: hosted access accepts the key in the URL. claude.ai now
  also offers request headers, so a header works there (B-006).
- Corrected: the baseline is 0.3.0, not 0.1.0. It has 60 tools, 7
  resources and 13 prompts; now 62 tools and 8 resources.
- New: `message_draft` and `resume_build_draft` don't run the new
  response check on their own output yet (B-007).
- New: the hosted demo loses data on every restart (B-008).
- New: the demo key was shared in a chat and should be replaced (B-009).
- Tools today: application_log, application_update, calendar_export,
  calendar_interviews, career_move, coding_pattern, companions,
  contribution_check, contribution_framework, daily_step, dashboard,
  data_delete, data_export, economy_guide, economy_indicators,
  experience_add, experience_list, feedback, finance_account_remove,
  finance_account_set, finance_budget_review, finance_budget_set,
  finance_dashboard, finance_holding_set, finance_import,
  future_projection, goal_set, goals_review, ground_rules, inbox_triage,
  interview_questions, invest_guide, layoff_fund_plan, layoff_playbook,
  life_compass, linkedin_review, message_draft, next_steps, nudge_add,
  nudge_done, nudges_due, pipeline_digest, portfolio_check,
  prep_checklist, profile_get, profile_save, response_check,
  resume_build_draft, resume_import, resume_merge, resume_score,
  resume_sections, resume_versions, role_match, runway_calc, skills_gap,
  step_done, story_add, story_match, study_plan, system_design,
  where_to_move.
- Resources: copilot://calendar.ics, copilot://connect,
  copilot://ground-rules, copilot://patterns, copilot://pipeline,
  copilot://roles, copilot://rubric, ui://career-copilot/dashboard.
- Prompts: build_my_resume, change_careers, daily_checkin,
  find_my_role, get_started, i_just_got_laid_off, import_my_resumes,
  money_checkup, plan_my_future, plan_my_prep, review_my_linkedin,
  should_i_move, tour.

### 2026-11-03 | planning
**Asked:** Review the connector against real search lessons and
write a journey-first spec that starts from zero.
**Did:** Wrote Product Spec v2 (stages, first conversation, gaps,
rules, data model, build order, acceptance tests).
**Files:** none in code.
**Tests:** not applicable.
**Try it:** read the spec; start with the gap list.
**Open:** code not reviewed yet.
