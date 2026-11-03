# Blueprint: from tools to a whole journey

Version 2026-11-03. Where Career Copilot goes after Spec v2, and why.
Each piece has a backlog id ([BACKLOG.md](BACKLOG.md)).

## 1. Where other job-search connectors stop

| Gap | What goes wrong | Our answer |
|---|---|---|
| No journey | Every call starts from zero; the assistant re-asks and gives advice that doesn't fit the moment | `journey_state` (built) |
| Claims have no source | A rewrite turns "helped with" into "led, cut cost 40%" | Fact record with source and confidence (B-015) |
| Wrong idea of ATS | Keyword "scores" sold as the filter. Real filters are knock-out questions (authorization, location, years) and recruiter search; parsers break on tables, columns and headers | `ats_profile_check` per platform (B-019) |
| Interviews are one status | Round 2 can't build on round 1; stories get repeated to the same panel | Round log and next-round prep (B-017) |
| Story banks are storage | No view of which competencies lack a strong story | `story_coverage` (B-018) |
| No background work | MCP can't start a conversation, so watches are faked or missing | Watches plus an outbox read at the next chat (B-020) |
| Browser automation | Breaks site terms, triggers bot checks, needs passwords, acts in the person's name | Not doing it. Public job-board endpoints and links only |
| Conflicts hidden | Resume versions disagree and a tool silently picks one | `fact_conflicts` (B-015) |

## 2. Design rules for every new tool

- Structured output, and every tool marked read-only or not.
- Writes take `apply`: `false` previews, `true` saves.
- Anything that makes a claim carries `supports: [fact_id]`.
- The model proposes; the server checks. Generated text is never trusted.
- Dealbreakers filter; preferences only rank.

## 3. The tools

### 3.1 Fact record (B-015): the foundation

`fact_add(statement, source: said|imported|inferred, source_ref,
role_ref, ownership: owned|led|contributed|observed, metrics:[{value,
unit, baseline, approx}], confidence: confirmed|unsure, apply)` returns
`fact_id` and any `conflicts` (date, metric, title, ownership) with the
question to ask.

- "About 40%" is stored with `approx: true` and may appear only as "~40%".
- Inferred facts never become confirmed without a dated, explicit yes.
- Experience, resume bullets and stories become views over facts.

### 3.2 Skill gaps from evidence (B-016)

`skill_gap_evidence(target{role_family, level, posting_ids},
window_days=90, min_postings=15)` returns the sample size and date range,
and per skill: demand (share of postings), required or preferred,
evidence (proven, claimed, none), supporting facts, and gap cost.

- Built only on postings the person has seen and their own outcome log
  (which resume version went where, what came back). It says so.
- Refuses to conclude below `min_postings`.
- Skill names normalized by a reviewed synonym list; embeddings may only
  suggest new entries.

### 3.3 Tailoring with guardrails (B-015 then `resume_patch`)

`resume_patch(resume_version_id, posting_id, edits:[{op, target_line,
text, supports:[fact_id]}], apply)` returns accepted edits, rejected edits
with the rule and the one question to ask, keyword coverage before and
after, and a new version id (never overwrites).

Server checks per edit:
1. Every number matches a cited fact by value.
2. No verb stronger than the fact's ownership ("contributed" can't become
   "led").
3. No merging two facts into a claim nobody made.
4. Nothing from the person's honest-gaps list.
5. No keyword without a supporting fact, none repeated more than twice.

### 3.4 Interview state (B-017)

`loop_round_log(loop_id = company + req id, round{n, format, date,
panel:[{role, focus_area}]}, questions:[{text, competency, story_id,
self_rating, follow_ups}], feedback:[{text, source:
recruiter_said|interviewer_said|self_read}], apply)`

`loop_next_round_prep(loop_id, next_round_format, known_panel)` returns
covered and uncovered competencies, a story plan with reuse risk
(same panelist, same company), weak spots, and one thing to do today.

- A rejection closes a loop only when title and req id both match.
- Panel tracked by role and focus, not names.
- Recruiter feedback outranks self-read.
- Round dates checked against the calendar before prep starts.

### 3.5 Story coverage (B-018)

A story-by-competency grid. Each story is scored on having a number,
clear ownership, a result, and whether it would hold up under follow-up
questions. Returns the gaps and the one story to write next.

### 3.6 ATS checks (B-019)

`ats_profile_check(posting_id, resume_version_id)` returns the platform
(read from the URL), parse risks, likely knock-outs from the posting text,
the person's answers on file, platform quirks, and a verdict: ready, fix
first, or knock-out risk. Platform rules live in `knowledge/` so they can
change weekly without code.

### 3.7 Watches and outbox (B-020)

`watch_create(kind: new_postings|assessment_expiry|follow_up_due|deadline,
query, cadence)` and `digest_get()` (read-only, only what's new since the
last read, and silent when nothing is). A server scheduler writes to the
outbox; the assistant reads it at the next chat or on the host's own
schedule. Watches find; they never send to anyone else.

## 4. Privacy and outside systems

| Mode | Key | Protects | Costs |
|---|---|---|---|
| Local | OS keychain, encrypted SQLite | Data at rest, a lost laptop | Moving devices needs export and import |
| Hosted, standard | Per-person data key, wrapped by a cloud key service | Leaked disks and backups; deleting a key makes backups unreadable | The operator can still read data while serving it |
| Hosted, sensitive fields | Pay history, work authorization and leaving reason encrypted with a key only the person holds | Those fields, even from the operator | Can't be filtered server-side; keep a plain yes/no flag for filters like sponsorship |

True end-to-end encryption isn't possible for a server that computes over
the data. Say so plainly. Next step for us: per-person data keys (B-021),
after persistent storage (B-008).

Outside systems:
- **LinkedIn:** no job-seeker API, and automating it breaks its terms.
  Links only; profile text by paste or "Save to PDF".
- **Indeed:** the public search API is closed to new users. Use the
  person's job-alert emails through their own email connector.
- **Greenhouse, Lever, Ashby:** public, read-only posting endpoints with
  dates. Our discovery layer (B-005). Applying through them needs the
  employer's key, so we never do it.
- **Workday, iCIMS, Taleo:** no candidate API. Polite, cached reads of
  public posting pages, or a link.
- One adapter per source with its own rate limit and cache; postings
  normalized with `posted_at` and `source_url`; no provable date means
  the posting is dropped.
- No third-party tokens stored on the server. Email and calendar stay in
  the person's own connectors.

## 5. Trade-offs we accept

1. Strict truth checks reject some fair edits. One extra question is
   cheaper than a made-up claim.
2. Public endpoints cover fewer roles than scraping, but they're legal,
   don't get accounts banned, and their dates can be trusted.
3. Rules live on the server (testable, same in every assistant); wording
   stays with the model.
4. Watches can find things alone but never act alone.

## 6. Order

| Step | Pieces |
|---|---|
| Built | journey_state, profile_from_text, direction_options, response_check in drafts, GitHub sign-in, fact record and conflicts (B-015, first version) |
| Next | Make experience and resume bullets views over facts |
| Then | job_search (B-005), resume_patch on facts, ats_profile_check (B-019) |
| Then | Loop rounds (B-017), story coverage (B-018), skill gaps from evidence (B-016) |
| Later | Watches and outbox (B-020), persistent storage (B-008), per-person keys (B-021) |
