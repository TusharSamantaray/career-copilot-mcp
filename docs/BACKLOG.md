# Backlog

## Open
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

- B-014 [P1] A true new-user test needs its own key, since the profile
  belongs to the key. Add a one-step "start over" or a demo key per
  tester. From: owner testing.

## Done
- B-001 journey_state: two ways in, one question at a time, read-back
  after three answers. From: spec v2 and owner.
- B-002 profile_save relaxed and merging, with lists and confidence.
  From: spec v2.
- B-003 life_compass saves answers. From: spec v2.
- B-013 Replies too long and generic; host persona took over. Make
  replies short, one step, one question. From: owner testing in Claude.
- B-000 Ground rules (privacy, terms, conduct) and response_check.
  From: owner request, 2026-11-03.
