# Prompt log

What the owner asked, what was done, and how to check it.
Newest first. Never include secrets or personal details.

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
