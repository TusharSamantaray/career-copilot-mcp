# Career Copilot: AI working file

Read this fully at the start of every session. It has four parts:
1. Working agreement (how you work)
2. First-session setup (create the log files)
3. Product spec, condensed (what we are building)
4. File templates (used by part 2)

Full spec lives in the owner's Claude doc "Career Copilot: Product Spec
v2 (journey-first)". Save a copy as `docs/SPEC.md` when available.

---

## 1. Working agreement

The owner tests the product and decides what to improve. The owner does
NOT review code. Make every change easy to test and easy to understand
without reading code.

### After every change set, before every commit

1. Run the full test suite. Never commit with a failing test.
   Report pass and fail counts to the owner.
2. Update `CHANGELOG.md` under `## [Unreleased]`:
   - Group under Added, Changed, Fixed, Removed, Security, Knowledge.
   - Write for someone who never reads code: what they will notice.
   - Every Added or Changed line ends with **Try it:** an exact thing
     to say to the connector and what should happen.
3. Add an entry to the top of `docs/PROMPT_LOG.md` (template below).
4. Commit with a Conventional Commit prefix: feat, fix, docs, test,
   refactor, chore. Put the changelog line in the commit body.

Small commits, one idea each. Never bundle unrelated work.

### Versions and releases

- Version lives in `pyproject.toml`. Semantic versions, stay on 0.x.
- Patch for fixes, minor for new tools or behavior.
- Only the owner says "release". Then: move `[Unreleased]` into a dated
  version heading, bump the version, commit, tag `vX.Y.Z`, and start a
  fresh empty `[Unreleased]`.

### Backlog

When the owner reports a problem or idea, add it to `docs/BACKLOG.md`
with the next free id, one line, and where it came from.
Reference the id in the changelog line that fixes it. Move finished
items to Done.

### Guardrails

- Never ask for, log or store passwords, one-time codes, bank logins.
- Never commit secrets. Keep `.env` out of git.
- Never put secrets, keys, real user data or personal details in the
  changelog, prompt log or commit messages.
- Do not change the license, authentication or privacy behavior without
  asking first, and say why in plain words.
- Product rules in part 3 are not optional. If a request conflicts
  with them, stop and ask.
- If code differs from the spec, say so and update one of them in the
  same change.
- The ground rules (privacy summary, terms, how Career Copilot talks,
  and `response_check`) live in `copilot/conduct.py`, outside
  `copilot/knowledge/`, so the weekly bot can't auto-merge changes to
  them. Changing them, or `docs/PRIVACY.md` and `docs/TERMS.md`, needs
  the owner's OK and a new `TERMS_VERSION`.

### End of every session, tell the owner three things

1. What changed, in two lines.
2. How to test it: the exact **Try it** prompt.
3. What you suggest improving next, and why.

---

## 2. First-session setup

If any of these are missing, create them from the templates in part 4:
`CHANGELOG.md`, `docs/PROMPT_LOG.md`, `docs/BACKLOG.md`.

Then, before changing any feature, review the codebase once and write
a plain-language report to the owner:
- Confirm or correct the items marked "to verify" in part 3.
- Confirm the baseline entry in the changelog.
- List the tools, resources and prompts that exist today.
Add the report's findings to the backlog. Then start with backlog
B-001.

(Done on 2026-11-03. See `docs/PROMPT_LOG.md`.)

---

## 3. Product spec, condensed

### The soul

Career Copilot meets a person wherever they are, works out what they
actually want from their career, and builds their profile out of the
conversation, so nobody fills in a form before getting help.
It is a remote MCP server (Python, SQLite, one file per user).

Six principles:
1. Ask before assuming. One question at a time. Save answers at once.
2. Any way in: pasted resume, free-text talk, one sentence, or "I
   don't know". None is required.
3. The profile builds as a side effect. Every fact is confirmed or
   unsure. Unconfirmed facts never reach a resume, letter or message.
4. Depth follows progress. Show only tools that fit the stage.
5. One small step per session, sized to the person's energy.
6. The person decides and sends. Draft, rank, explain. Never apply,
   post or message for them. Never ask for a password.

### Journey stages (not gates; people can skip or go back)

| Stage | Question | Moves on when |
|---|---|---|
| Orient | What should I go for? | Direction chosen or dealbreakers set |
| Foundation | What can I truthfully claim? | Confirmed facts cover recent roles; resume exists |
| Search | Where do I apply, and why? | A screen or assessment is scheduled |
| Prepare | How do I pass this loop? | A loop ends or an offer arrives |
| Decide and grow | Which offer, what next? | Role accepted; cycle restarts |

"Steady the ground" runs at any stage: a near deadline turns on
fast-track mode (runway first, shorter plans, search sorted by time
to offer).

### First conversation (zero start)

Six ways in: no direction (life_compass), just lost the job (3 quick
questions, runway_calc, 72-hour plan), has a resume (import, score,
3 questions on weak bullets), talks it out (extract facts, read back,
person confirms), has a target (save filters, go to search), wants a
field switch (career_move).

Opening order:
1. One sentence of promise, then one question: where are you now?
   (starting out / between jobs / working but want change /
   interviewing). Free text always allowed.
2. Energy check (low, medium, high).
3. Branch into one of the six paths.
4. No more than five questions before giving something useful back.
5. The mirror: read the profile back with confirmed or unsure labels.
6. Exactly one next step.

Question rules: one at a time; two to four options plus free text;
"not sure" and "skip" are valid and saved as unknown; never re-ask
known facts; sensitive items (work authorization, pay history, reason
for leaving) only when a feature needs them, with the reason stated.
Dealbreakers filter results; preferences only rank them.

### Rules every tool enforces

Truth: only confirmed facts on resumes and drafts; no invented
numbers; per-person honest-gaps list that tailoring tools respect;
ownership check (wrote, led or fixed?) before owner verbs; raise
conflicts when sources disagree.

Discovery: a posting needs a provable posting date from an official
board; default freshness 7 days; dealbreakers filter, preferences rank;
pay below floor is flagged, not hidden; record every role shown and
report only new ones; only public job-board endpoints and career pages
(for LinkedIn, return a link, do not automate).

Acting: never apply, post or send; per-message approval; plain direct
voice by default, person can change it; one factual wording for why
they left a job, always true if asked directly; needs like sponsorship
stated once, as a filter.

State: verify interview status against the calendar; match role title
and requisition number before closing a loop from a rejection;
deadlines hold a best case and a conservative date, plan on the
conservative one.

Care: one step a day sized to energy, no guilt; money, tax, visa and
relocation output is education, not advice; self-harm or feeling
unsafe stops career talk and shows support first.

Conduct: ground rules shown and agreed at the start (ground_rules);
stay on task; respectful and neutral; no comments on personal traits
unless the person raises them for a practical reason; say where facts
come from and "I don't know" instead of guessing; every draft the
person may send or rely on passes response_check.

### What exists today (verified in code on 2026-11-03)

73 tools, 8 resources, 16 prompts. Facts: fact_add, fact_conflicts,
fact_resolve. Discovery: job_search, jd_analyze, ats_profile_check. Loops:
loop_round_log, loop_next_round_prep. Orient: journey_state, life_compass,
direction_options, profile_from_text, career_move,
where_to_move, role_match, skills_gap, next_steps. Foundation:
profile_save, resume_import, resume_merge, resume_score,
resume_build_draft, experience_add, contribution_check, story_add,
linkedin_review. Search: application_log, application_update,
pipeline_digest, inbox_triage, message_draft, calendar_interviews.
Prepare: interview_questions, coding_pattern, system_design,
study_plan, prep_checklist, nudge_add. Steady: layoff_playbook,
runway_calc, layoff_fund_plan, finance tools. Glue: daily_step,
step_done, dashboard, companions, ground_rules, response_check,
data_export, data_delete, feedback.

Verified:
- profile_save no longer requires target_role; it merges answers one at
  a time, with wants, dealbreakers, honest gaps and confirmed or unsure
  labels (B-002 done).
- life_compass saves each answer, and can add it as a want or
  dealbreaker (B-003 done). journey_state is called first (B-001 done).
- Hosted access uses GitHub sign-in (OAuth, read:user) with an invite
  list; API keys and ?key= URLs are refused while it's on. Live since
  2026-11-03 (B-006 done). Owner runbook: `docs/OWNER.md`.
- License is "all rights reserved", source-available, in the owner's
  name. Decided by the owner on 2026-11-03.

### Gaps, by priority (P0 = journey cannot run from zero without it)

P0:
- journey_state (new): stage, known facts with confidence, missing
  facts, best next question. Called first every session.
- profile_save relaxed: target_role optional; add wants, dealbreakers,
  locations, target and excluded companies, domain keywords, daily
  schedule, honest gaps, confidence per field.
- life_compass persisted: save each answer as a want or dealbreaker.
- profile_from_text (new): store facts Claude extracted, only after
  the person confirms each one.
- direction_options (new): 2 to 3 directions with fit, distance, gaps,
  risk and a first test. Level and positioning are decisions to test,
  not labels to assign.
- job_search (new): discovery with hard filters, provable posting
  date, dedup, silent when nothing is new.
- jd_analyze (new): what the role is, level read, pay read, sponsorship
  read, why bother, fit points, gap points, verdict.

P1:
- Fact record and fact_conflicts; ownership_check; resume_tailor and
  ats_keyword_check; resume outcome log (which version went where,
  what came back); sponsorship_verify; cover_letter_draft; loop_enrich
  (recruiter, format, band, req id); rejection_triage; deadline_add
  and fast_track mode; format-aware study_plan; message_draft voice.

P2:
- recruiter_find; lessons list; dashboard action strip;
  pipeline_digest sponsorship and overdue columns.

### Data model change

New record: Fact = statement, source (said, imported, inferred),
confidence (confirmed or unsure), confirmed on, supports. Profile,
experience, resume bullets and stories become views over facts.
New records: Role seen, Deadline (best case and conservative), Lesson.
Changed: Profile (lists, schedule), Loop (Muse fields), Resume version
(outcome log).

### Privacy defaults

Sensitive items optional and asked only when needed. Never ingest chat
history unless pasted. Email text read for triage is never stored.
One data file per person, full export, one-step delete. Local-first
mode with a readable Markdown mirror is the goal. Full text:
`docs/PRIVACY.md` and `docs/TERMS.md`.

### Build order

1. Zero-start spine: journey_state, relaxed profile_save, persisted
   life_compass, profile_from_text, direction_options, rewritten server
   instructions, starter prompts.
2. Foundation integrity: Fact, fact_conflicts, ownership_check,
   outcome log, resume_tailor, ats_keyword_check.
3. Search loop: job_search, jd_analyze, loop_enrich, rejection_triage,
   cover_letter_draft, sponsorship_verify.
4. Pressure mode: deadline_add, fast_track, study_plan format, lessons.
5. Hardening: auth, local-first mirror, dashboard strip, recruiter_find.

Server instructions change: replace "run the get_started flow" with
"call journey_state first" (after ground_rules). Add: never more than
five questions before giving something back; read the profile back with
confidence labels before saving as confirmed; when a deadline is near,
switch to fast-track and say so.

Starter prompts: "I don't know what I want", "I just lost my job",
"Here's my resume", "Let me describe my work", "I know my target",
"I have an interview coming up".

### Acceptance tests (scripted conversations, synthetic users)

- A Lost: "I don't know what I want", no resume. Within five questions:
  2 to 3 directions with reasons, one picked, saved profile with every
  line labeled confirmed or unsure.
- B On a clock: "I just got laid off" with a last day and a deadline.
  Dated timeline in the first reply; deadline holds a conservative date;
  first step fits in one hour.
- C Three resumes: versions disagree on a date and a number. Both
  conflicts raised and resolved by the person; merged resume has no
  number that no source supports.
- D Talks it out: rambling free text about two jobs. Facts read back,
  edited, and only then saved as confirmed.
- E Knows the target: role, locations, pay floor, sponsorship need.
  No result breaks a dealbreaker; each has a dated source; a second run
  the same day returns nothing new.
- F Distress: mentions feeling unsafe. Career talk stops; support first.
- G Conduct: a draft with an insult, a promised outcome, biased wording
  or an invented number fails response_check; the fixed draft passes.
  (Covered by `tests/test_soul.py`.)

Add these as automated tests as each feature lands.

---

## 4. File templates (for part 2)

### docs/PROMPT_LOG.md entry

    ### YYYY-MM-DD HH:MM | vX.Y.Z-dev
    **Asked:** the request in one or two plain lines.
    **Did:** what changed, in plain words.
    **Files:** the main files touched.
    **Tests:** counts, e.g. 143 passed, 0 failed.
    **Try it:** how the owner can check it.
    **Open:** anything left, unclear or skipped.

### CHANGELOG.md and docs/BACKLOG.md

Created on 2026-11-03. Follow the existing structure in each file.
