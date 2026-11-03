# Backlog

## Open
- B-005 [P0] job_search on public job-board endpoints, then
  jd_analyze. From: spec v2.
- B-008 [P1] Persistent storage for the hosted version (paid disk or
  Postgres). The free demo loses data on every restart. From: Render
  setup.
- B-009 [P1] Replace the demo API key in Render, since it was shared in a
  chat. Becomes harmless once GitHub sign-in is on (keys are ignored);
  still delete or rotate it. From: claude.ai connector setup.
- B-010 [P2] Lawyer review of docs/PRIVACY.md and docs/TERMS.md before
  paid users. From: ground rules work.
- B-011 [P2] Add Spec v2 as docs/SPEC.md (current file is v1).
  From: CLAUDE.md.
- B-012 [P2] Delete the old prototype server.py from the project
  folder (it's untracked). From: repo setup.

- B-022 [P1] Make experience, resume bullets and stories views over the
  fact record, and import resume bullets as facts. From: B-015.
- B-016 [P1] skill_gap_evidence from postings seen and the outcome log.
  From: blueprint.
- B-017 [P1] Interview rounds: loop_round_log and loop_next_round_prep.
  From: blueprint.
- B-018 [P1] story_coverage grid across competencies. From: blueprint.
- B-019 [P1] ats_profile_check: platform, parse risks, knock-outs.
  From: blueprint.
- B-020 [P2] Watches and an outbox read at the next chat. From: blueprint.
- B-021 [P2] Per-person data keys for hosted storage. From: blueprint.

## Done
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
