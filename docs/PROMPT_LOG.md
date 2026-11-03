# Prompt log

What the owner asked, what was done, and how to check it.
Newest first. Never include secrets or personal details.

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
