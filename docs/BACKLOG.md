# Backlog

## Open
- B-010 [P2] Lawyer review of docs/PRIVACY.md and docs/TERMS.md before
  paid users. From: ground rules work.
- B-026 [P1] resume_tailor (resume_patch): edits cite fact ids; server
  rejects unsupported numbers, ownership inflation, merged claims,
  honest-gap hits. From: spec v2 and blueprint.
- B-029 [P1] sponsorship_verify: posting text plus public filing data,
  as education. From: spec v2.
- B-034 [P2] Dashboard action strip. From: spec v2.
- B-012 [P2] Delete the old prototype server.py from the project
  folder (it's untracked). From: repo setup.



## Done
- B-040 Neon password reset and the new pooled DATABASE_URL set in
  Render by the owner; live /health reports postgres. From: Neon setup.
- B-008 Free persistent storage: Postgres backend (DATABASE_URL, Neon
  free plan), encryption unchanged, tested in CI against a real Postgres
  and through a wiped-disk restart. Owner adds DATABASE_URL in Render.
  From: Render setup and owner testing.
- B-039 Asked to reconnect on every new chat: sign-in state lived on the
  free host's wiped disk. Replaced with stateless sign-in
  (copilot/signin.py); tested through a restart with a wiped disk.
  From: owner testing, 2026-11-03.
- B-030 deadline_add (best case, conservative), fast-track in
  journey_state and job_search ordering; acceptance test B. From: spec v2.
- B-038 Acceptance test A scripted in tests/test_acceptance.py, in CI.
  From: spec v2.
- B-036 data_mirror: Markdown copy, saved locally in stdio mode.
  From: spec v2.
- B-028 cover_letter_draft: two best-matching confirmed facts, voice,
  response_check. From: spec v2.
- B-035 recruiter_find: search links only. From: spec v2.
- B-031 study_plan loop_format (one rotation per LOOP_FORMATS entry,
  tested to stay in sync). From: spec v2.
- B-037 pipeline_digest sponsorship column (overdue already existed);
  application_log takes sponsorship. From: spec v2.
- B-033 lessons (add, list; latest three in next-round prep). From:
  spec v2.
- B-032 message_draft voice (plain, warm, formal), saved on the profile.
  From: spec v2.
- B-027 ats_keyword_check (covered, missing but true, gaps; honest gaps
  never offered). From: spec v2.
- B-025 ownership_check: owner verbs need matching fact ownership.
  From: spec v2.
- B-009 Old API key removed from Render by the owner (sign-in ignores
  keys anyway). From: claude.ai connector setup.
- B-011 Spec v2 in docs/SPEC.md (condensed, with status); v1 archived.
  Remaining spec gaps added as B-025 to B-038. From: CLAUDE.md.
- B-021 Per-person data keys (AES-GCM, wrapped by
  CAREER_COPILOT_MASTER_KEY), crypto-shred on delete, plain rows still
  read. Owner must add the key to the existing Render service. From:
  blueprint.
- B-020 watch_create, watches, digest_get; outbox read once; optional
  scheduler (CAREER_COPILOT_WATCH_MINUTES). From: blueprint.
- B-016 skill_gap_evidence (analyzed postings, required vs preferred,
  proven/claimed/none, gap cost) and the resume outcome log
  (resume_label on applications). From: blueprint.
- B-024 Next-round prep checks the round is on the calendar. From:
  B-017.
- B-023 Rejections close only the application whose role or req id they
  name; unclear ones come back as "confirm". application_log takes
  req_id. From: B-017.
- B-018 story_coverage: competency grid, four-check strength, gaps,
  next story, unconfirmed numbers flagged. From: blueprint.
- B-017 loop_round_log and loop_next_round_prep (req-id loop key, panel
  by role, feedback source ranking, reuse risk). From: blueprint.
- B-019 ats_profile_check with platform rules in knowledge/ats.py
  (validated by test_knowledge). From: blueprint.
- B-005 job_search (Greenhouse, Lever, Ashby; provable dates; filters;
  seen-dedup) and jd_analyze. Owner OK'd outbound reads on 2026-11-03.
  From: spec v2.
- B-022 experience_add and resume_import write facts (numbers parsed,
  duplicates merged, version conflicts raised); resume_build_draft reads
  confirmed facts. Stories link to facts in B-018. From: B-015.
- B-014 New-user testing: sign in with a second GitHub account on the
  invite list (docs/OWNER.md). From: owner testing.
- B-015 Fact record (source, ownership, metrics, confirmed or unsure),
  fact_conflicts and fact_resolve; response_check reads it. From:
  blueprint.
- B-006 GitHub sign-in with a plain URL; keys ignored when it's on.
  Owner chose GitHub on 2026-11-03. From: README review.
- B-004 profile_from_text (read back, then save) and direction_options
  (2-3 directions with fit, distance, gaps, risk, first test).
  From: spec v2.
- B-007 message_draft and resume_build_draft run response_check on
  their own output. From: code review.
- B-001 journey_state: two ways in, one question at a time, read-back
  after three answers. From: spec v2 and owner.
- B-002 profile_save relaxed and merging, with lists and confidence.
  From: spec v2.
- B-003 life_compass saves answers. From: spec v2.
- B-013 Replies too long and generic; host persona took over. Make
  replies short, one step, one question. From: owner testing in Claude.
- B-000 Ground rules (privacy, terms, conduct) and response_check.
  From: owner request, 2026-11-03.
