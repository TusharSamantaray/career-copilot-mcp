# Backlog

## Open
- B-001 [P0] journey_state tool (spec part 3). From: spec v2.
- B-002 [P0] Make target_role optional in profile_save and add
  wants, dealbreakers, schedule, honest gaps. From: spec v2; confirmed
  in code review.
- B-003 [P0] Persist life_compass answers. From: spec v2; confirmed in
  code review.
- B-004 [P0] profile_from_text and direction_options.
  From: spec v2.
- B-005 [P0] job_search on public job-board endpoints, then
  jd_analyze. From: spec v2.
- B-006 [P1] Move hosted key from URL to header or OAuth.
  From: README review.
- B-007 [P1] Run response_check inside message_draft and
  resume_build_draft, so their output is checked even if the assistant
  forgets. From: code review.
- B-008 [P1] Persistent storage for the hosted version (paid disk or
  Postgres). The free demo loses data on every restart. From: Render
  setup.
- B-009 [P1] Replace the demo API key in Render, since it was shared in a
  chat. From: claude.ai connector setup.
- B-010 [P2] Lawyer review of docs/PRIVACY.md and docs/TERMS.md before
  paid users. From: ground rules work.
- B-011 [P2] Add Spec v2 as docs/SPEC.md (current file is v1).
  From: CLAUDE.md.
- B-012 [P2] Delete the old prototype server.py from the project
  folder (it's untracked). From: repo setup.

## Done
- B-000 Ground rules (privacy, terms, conduct) and response_check.
  From: owner request, 2026-11-03.
