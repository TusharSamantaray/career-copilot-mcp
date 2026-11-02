# Architecture

These diagrams render on GitHub, and the investor deck uses the same
picture.

## 1. System overview

```mermaid
flowchart LR
  subgraph U["The user's world"]
    person(["Person in transition"])
    ai["Their AI assistant<br/>Claude · ChatGPT · Gemini · Cursor · Muse"]
    own["Their own connectors<br/>Gmail · Outlook · Calendar · Zoom · Figma · Notion"]
  end

  subgraph M["Marketplace (MCPize)"]
    gw["Gateway<br/>subscriber key · quotas · billing"]
  end

  subgraph S["Career Copilot MCP server (FastMCP, MCPHosting)"]
    soul["Soul / coach<br/>daily_step · step_done · life_compass"]
    career["Career engine<br/>roles · career_move · where_to_move · resume · LinkedIn"]
    auto["Autopilot<br/>inbox_triage · calendar_interviews · reminders"]
    prep["Interview prep<br/>stories · questions · patterns · system design"]
    money["Money and future<br/>dashboard · layoff fund · goals · projections"]
    kb[("Knowledge base<br/>copilot/knowledge/*.py")]
    db[("Per-user store<br/>SQLite → Postgres")]
    sig[("Anonymous signals<br/>k-anonymous")]
  end

  wb["World Bank API<br/>live macro data"]
  gh["GitHub Actions<br/>weekly improver"]

  person <--> ai
  ai <--> own
  ai -- "MCP over HTTPS" --> gw --> S
  ai -. "local stdio, free" .-> S
  soul & career & auto & prep & money --> db
  soul & career & prep & money --> kb
  S --> sig
  money --> wb
  sig -- "/insights (admin key)" --> gh
  gh -- "tested PR, knowledge only" --> kb
```

**Why this shape keeps it cheap and puts the user in charge:**

- **No LLM on our side.** The user's own assistant does the reasoning and
  the talking. The server only stores data, applies rules and serves
  knowledge, so our cost per user is close to zero.
- **No inbox or calendar credentials.** The assistant reads mail and events
  through the connectors the user already trusts, then hands just the
  relevant items to `inbox_triage` and `calendar_interviews`.
- **A local mode.** `app.py --stdio` runs everything on the user's own
  machine for free.

## 2. The daily loop (the soul)

```mermaid
sequenceDiagram
  participant P as Person
  participant A as AI assistant
  participant C as Career Copilot
  P->>A: "hey" (or opens a check-in)
  A->>C: nudges_due + daily_step(energy)
  C-->>A: ONE step sized to energy, streak, what's due
  A->>P: "Low energy? Just save one posting today."
  P->>A: "done"
  A->>C: step_done
  C-->>A: celebration + momentum
  A->>P: "That counts. 4 days of momentum."
```

## 3. The job-search autopilot

```mermaid
flowchart LR
  mail["Emails via the user's connector"] --> tri["inbox_triage<br/>applied · rejection · interview · assessment · offer"]
  cal["Calendar / Zoom events"] --> ci["calendar_interviews"]
  tri -- "user approves" --> pipe[("Pipeline")]
  ci --> pipe
  pipe --> rules["Autopilot rules"]
  rules --> n1["Follow up in 7 business days"]
  rules --> n2["Assessment due in 2 days"]
  rules --> n3["Prep the day before"]
  rules --> n4["Thank-you note the same day"]
  rules --> n5["Negotiate before accepting"]
  n1 & n2 & n3 & n4 & n5 --> step["daily_step picks the one that matters most today"]
  step --> ics["calendar_export: real alerts on any calendar"]
```

## 4. Self-improvement (no one has to maintain it)

```mermaid
flowchart LR
  use["Tool calls, misses, feedback"] --> sig[("Signals<br/>scrubbed, salted, k ≥ 5")]
  sig --> wk["Weekly GitHub Action<br/>Claude edits copilot/knowledge/ only"]
  wk --> t["5 test suites<br/>+ PII + injection checks"]
  t -- "knowledge-only and green" --> merge["Auto-merge → redeploy"]
  t -- "anything else" --> pr["PR for a human"]
```

## 5. How to implement it

| Layer | Choice | Why |
|---|---|---|
| Protocol | MCP, streamable HTTP plus stdio | Works with every major assistant |
| Server | Python, FastMCP 2.x | Small, typed, fast to build |
| Auth | API key per subscriber; OAuth 2.1 next | Marketplace-friendly now, web clients later |
| Storage | SQLite per user, then managed Postgres | Simple POC, durable at scale |
| Knowledge | Plain Python data plus validation tests | Diffable, testable, safe to auto-edit |
| Hosting | MCPHosting ($0–$49/mo) | Deploys from GitHub on every push |
| Billing | MCPize (keeps 20%) | Payments, tax and discovery handled |
| Improvement | GitHub Actions plus Claude, weekly | Hands-off, tested, guarded |
