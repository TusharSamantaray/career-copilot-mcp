# Architecture

How Career Copilot is built, as of November 2026. Every diagram answers
one question, stated above it. The diagrams render on GitHub.

## How to read the diagrams

Colours mean the same thing on every page in these docs. Each box has a
coloured outline and a faint tint of the same colour; the text keeps the
page's own colour, so diagrams read on white and black backgrounds alike.
Shape and line style carry meaning too, so the diagrams still work
without colour.

| Colour | Means | Examples |
|---|---|---|
| 🟦 Blue | The person and their own tools | You, your AI assistant, your Gmail or calendar connector |
| 🟩 Green | Career Copilot itself | Tools, rules, the server |
| 🟨 Amber | Stored data (cylinders) | Postgres on Neon, local SQLite files, the knowledge base |
| ⬜ Grey | Outside services Career Copilot talks to | GitHub sign-in, job boards, World Bank |
| 🟪 Purple | Safety and truth checks | `response_check`, encryption, the invite list |
| 🟥 Red, dashed | Things it never does | Ask for passwords, apply or message for you |

For anyone adding a diagram, copy these lines:

```text
classDef person  fill:#3B82F61A,stroke:#3B82F6,stroke-width:1.5px
classDef copilot fill:#10B9811A,stroke:#10B981,stroke-width:1.5px
classDef store   fill:#F59E0B1A,stroke:#F59E0B,stroke-width:1.5px
classDef ext     fill:#94A3B81A,stroke:#94A3B8,stroke-width:1.5px
classDef guard   fill:#A855F71A,stroke:#A855F7,stroke-width:1.5px
classDef never   fill:#EF44441A,stroke:#EF4444,stroke-width:1.5px,stroke-dasharray:4 3
```

Don't set a text `color`; leaving it out is what keeps text readable in
both themes. Sequence diagrams use `box rgba(…, 0.08)` with the same
colours.

## 1. What talks to what

*Question: where does each part live, and who calls whom?*

```mermaid
flowchart LR
  classDef person fill:#3B82F61A,stroke:#3B82F6,stroke-width:1.5px
  classDef copilot fill:#10B9811A,stroke:#10B981,stroke-width:1.5px
  classDef store fill:#F59E0B1A,stroke:#F59E0B,stroke-width:1.5px
  classDef ext fill:#94A3B81A,stroke:#94A3B8,stroke-width:1.5px
  classDef guard fill:#A855F71A,stroke:#A855F7,stroke-width:1.5px
  classDef never fill:#EF44441A,stroke:#EF4444,stroke-width:1.5px,stroke-dasharray:4 3

  you(["You"]):::person
  ai["Your AI assistant<br/>Claude · ChatGPT · Muse"]:::person
  own["Your connectors<br/>Gmail · Calendar · Drive"]:::person

  subgraph server["Career Copilot server · FastMCP on Render"]
    auth["Sign-in check<br/>stateless GitHub tokens"]:::guard
    tools["92 tools<br/>journey · facts · search · prep · deadlines · money"]:::copilot
    checks["Truth and conduct checks<br/>response_check · ownership_check"]:::guard
  end

  db[("Your records<br/>Neon Postgres, encrypted")]:::store
  kb[("Knowledge<br/>roles · prep · ATS rules")]:::store
  gh["GitHub<br/>sign-in only"]:::ext
  boards["Public job boards<br/>Greenhouse · Lever · Ashby"]:::ext
  never["Never: passwords,<br/>applying, messaging"]:::never

  you <--> ai
  ai <--> own
  ai -- "MCP over HTTPS" --> auth --> tools
  tools --> checks
  tools --> db
  tools --> kb
  auth -. "who are you?" .-> gh
  tools -. "read-only" .-> boards
  tools -.- never
```

- **No AI model on the server.** Your assistant does the talking; the
  server stores, checks and remembers. That keeps it nearly free to run.
- **Your connectors stay yours.** The assistant reads your email or
  calendar and passes only the needed fields to tools like
  `inbox_triage`. Career Copilot never logs in to them.
- **Local mode.** `app.py --stdio` runs the same tools on your computer,
  with SQLite files in `~/CareerCopilot/` and no sign-in.

## 2. One request, step by step

*Question: what happens between your question and the answer?*

```mermaid
sequenceDiagram
  autonumber
  box rgba(59,130,246,0.08) Your side
    participant A as Your assistant
  end
  box rgba(16,185,129,0.08) Career Copilot
    participant S as Sign-in check
    participant M as Audit middleware
    participant T as Tool
  end
  box rgba(245,158,11,0.08) Storage
    participant D as Neon Postgres
  end
  A->>S: call tool, with your sealed token
  S->>S: unseal token, check expiry
  S->>M: you are user gh_… (a hash)
  M->>M: invite list, log tool name only (your words masked)
  M->>T: run the tool
  T->>D: read or write, each record encrypted with your key
  D-->>T: rows
  T-->>A: short result plus "say" hint (one step, one question)
```

## 3. Signing in once, staying signed in

*Question: why doesn't a restart log you out?*

The free host wipes its disk on every restart, so nothing about sign-in
is stored on it. Everything travels sealed (encrypted and signed) with a
key kept in the host's settings, which survive restarts.

```mermaid
sequenceDiagram
  autonumber
  box rgba(59,130,246,0.08) Your side
    participant A as Your assistant
  end
  box rgba(16,185,129,0.08) Career Copilot
    participant C as Sign-in endpoints
  end
  box rgba(148,163,184,0.08) Outside
    participant G as GitHub
  end
  A->>C: register (first connect)
  C-->>A: client id = the app's details, sealed
  A->>C: authorize
  C-->>A: go to GitHub, state = this sign-in, sealed
  A->>G: you approve "public profile only"
  G-->>C: code
  C->>G: who is this?
  G-->>C: GitHub id and username
  Note over C: GitHub's token is dropped here
  C-->>A: our code (sealed id, 5 min)
  A->>C: swap code for tokens (PKCE checked)
  C-->>A: access token 30 days, refresh 1 year, both sealed
```

Code: [copilot/signin.py](../copilot/signin.py). Test that proves it:
`tests/test_oauth.py` signs in, wipes the disk, restarts, and uses the
same token.

## 4. How your data is stored and protected

*Question: what exactly sits in the database, and what happens when you
delete it?*

```mermaid
flowchart LR
  classDef copilot fill:#10B9811A,stroke:#10B981,stroke-width:1.5px
  classDef store fill:#F59E0B1A,stroke:#F59E0B,stroke-width:1.5px
  classDef guard fill:#A855F71A,stroke:#A855F7,stroke-width:1.5px
  classDef ext fill:#94A3B81A,stroke:#94A3B8,stroke-width:1.5px

  rec["A record<br/>e.g. one fact"]:::copilot
  key["Your data key<br/>random, one per person"]:::guard
  master["Master key<br/>in Render settings only"]:::ext
  rows[("cc_records<br/>user_id · id · kind · enc:…")]:::store
  keys[("cc_keys<br/>user_id · wrapped key")]:::store

  rec -- "AES-GCM, bound to the record id" --> rows
  key -. encrypts .-> rec
  master -- "locks" --> key
  key --> keys
```

- **Per person.** Every row carries your user id (a salted hash of your
  GitHub id, never your name). Nobody else's queries can reach it.
- **Delete means gone.** `data_delete` removes your data key first, then
  your rows. Even an old backup of the rows can't be read afterwards.
- **Two backends, same code.** Postgres when `DATABASE_URL` is set
  (hosted), SQLite files otherwise (local). Code:
  [copilot/store.py](../copilot/store.py).

## 5. From what you say to what you send

*Question: how does a claim end up on a resume without being invented?*

```mermaid
flowchart LR
  classDef person fill:#3B82F61A,stroke:#3B82F6,stroke-width:1.5px
  classDef copilot fill:#10B9811A,stroke:#10B981,stroke-width:1.5px
  classDef store fill:#F59E0B1A,stroke:#F59E0B,stroke-width:1.5px
  classDef guard fill:#A855F71A,stroke:#A855F7,stroke-width:1.5px

  said["You said it"]:::person
  resume["Old resumes"]:::person
  guess["Assistant's guess"]:::person
  facts[("Fact record<br/>source · ownership · numbers")]:::store
  conflict{"Two versions<br/>disagree?"}:::guard
  ask["You choose<br/>fact_resolve"]:::person
  confirmed["Confirmed facts only"]:::copilot
  draft["Resume line · letter · message"]:::copilot
  check["response_check<br/>numbers · promises · bias"]:::guard
  you["You edit and send"]:::person

  said -- confirmed --> facts
  resume -- unsure --> facts
  guess -- "unsure, never confirmed" --> facts
  facts --> conflict
  conflict -- yes --> ask --> facts
  conflict -- no --> confirmed --> draft --> check --> you
```

## 6. Where you are on the journey

*Question: how does Career Copilot decide what to ask or offer next?*

`journey_state` works out your stage from what's saved, then returns one
question or one step. The stages are in the [spec](SPEC.md#2-journey-stages);
this is how the code moves between them.

```mermaid
stateDiagram-v2
  direction LR
  [*] --> Orient: nothing saved yet
  Orient --> Foundation: target role, wants or hard no's saved
  Foundation --> Search: 3+ confirmed facts or a resume
  Search --> Prepare: an assessment or interview logged
  Prepare --> Decide: an offer logged
  Prepare --> Search: loop closed
  Decide --> Orient: role accepted, next cycle
  note right of Search
    A deadline under 60 days away
    turns on fast-track in any stage
  end note
```

## 7. Finding jobs without noise

*Question: why do some postings never show up?*

```mermaid
flowchart LR
  classDef ext fill:#94A3B81A,stroke:#94A3B8,stroke-width:1.5px
  classDef copilot fill:#10B9811A,stroke:#10B981,stroke-width:1.5px
  classDef guard fill:#A855F71A,stroke:#A855F7,stroke-width:1.5px
  classDef store fill:#F59E0B1A,stroke:#F59E0B,stroke-width:1.5px
  classDef never fill:#EF44441A,stroke:#EF4444,stroke-width:1.5px,stroke-dasharray:4 3

  boards["Greenhouse · Lever · Ashby<br/>public, read-only"]:::ext
  norm["One shape<br/>title · place · remote · posted"]:::copilot
  nodate["No provable post date"]:::never
  old["Older than 7 days"]:::never
  hardno["Breaks a hard no<br/>or excluded company"]:::never
  seen[("Already shown to you")]:::store
  rank["Rank by your wants<br/>freshest first in fast-track"]:::guard
  out["New roles only<br/>or 'nothing new'"]:::copilot

  boards --> norm
  norm -.-> nodate
  norm -.-> old
  norm -.-> hardno
  norm --> seen
  seen -- new --> rank --> out
```

Greenhouse's `updated_at` changes on any edit, so only `first_published`
counts as a posting date. Code: [copilot/jobs.py](../copilot/jobs.py).

## 8. Improving itself, safely

*Question: how does the knowledge base get better without anyone
breaking it?*

```mermaid
flowchart LR
  classDef copilot fill:#10B9811A,stroke:#10B981,stroke-width:1.5px
  classDef store fill:#F59E0B1A,stroke:#F59E0B,stroke-width:1.5px
  classDef guard fill:#A855F71A,stroke:#A855F7,stroke-width:1.5px
  classDef person fill:#3B82F61A,stroke:#3B82F6,stroke-width:1.5px

  use["Tool errors, missing roles, ratings"]:::copilot
  sig[("Anonymous signals<br/>salted, 5+ people")]:::store
  bot["Weekly GitHub Action<br/>edits copilot/knowledge/ only"]:::copilot
  tests["All test suites<br/>+ personal-data and injection checks"]:::guard
  merge["Auto-merge and redeploy"]:::copilot
  human["Pull request for the owner"]:::person

  use --> sig --> bot --> tests
  tests -- "knowledge only, all green" --> merge
  tests -- "anything else" --> human
```

The ground rules (`copilot/conduct.py`) sit outside `copilot/knowledge/`
on purpose, so the bot can never weaken them.

## 9. The choices, in one table

| Layer | Choice | Why |
|---|---|---|
| Protocol | MCP: streamable HTTP and stdio | Works with every major assistant |
| Server | Python 3.11+, FastMCP 2.x | Small, typed, quick to change |
| Hosting | Render free plan | Deploys from GitHub on every push |
| Sign-in | GitHub OAuth, stateless, invite list | Plain URL, survives restarts, no passwords |
| Storage | Neon Postgres (free) hosted, SQLite local | Data survives restarts; local stays private |
| Encryption | AES-GCM per person, key wrapped by a master key | Delete destroys the key |
| Knowledge | Plain Python data plus validation tests | Easy to review, safe to auto-edit |
| Tests | 9 suites in CI, plus Postgres and encrypted runs | See [ENGINEERING.md](ENGINEERING.md) |
