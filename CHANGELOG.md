# Changelog

All notable changes to Career Copilot. Newest first.
Every Added or Changed line has a **Try it:** line.

## [Unreleased]

### Added
- A fact record (B-015). Every claim about your work is kept with where
  it came from (you said it, an old resume, or a guess), your part in it
  (owned, led, contributed) and its numbers. When two resumes disagree
  on a date or a number, it asks you which is right instead of picking
  one. Only the version you keep can appear in drafts.
  **Try it:** say "My 2024 resume says I cut pipeline time by 35% at
  Initech (2021-2024), but my 2025 one says 55% and starts in 2022."
  It should flag both the date and the number and ask which is right.
- Talk it out (B-004). Describe your work in your own words; Career
  Copilot reads the facts back with confirmed or unsure labels and saves
  them only after you agree.
  **Try it:** say "Let me just describe my work: I was an analyst at a
  retailer for three years, I built their weekly sales report, and I
  never want a fully on-site job again". It should read back a short list
  and ask if anything needs changing before saving.
- Direction options (B-004). Not sure where to go? You get 2 or 3
  directions, each with why it fits, how far it is, the gaps, the risk
  and a small test you can do this week.
  **Try it:** say "I'm good at SQL, Python and dashboards. What
  directions could I test?". You should get 2 or 3 one-line options and
  one question: which to try.
- A guided start (B-001). Each session begins by checking where you are.
  A first-timer gets two ways in: say what's on your mind, or answer a
  few quick questions one at a time. After about three answers it reads
  your profile back (confirmed or unsure) and gives you one step, so you
  never fill in a form. New starter prompts: "I don't know what I want",
  "I know my target", "I have an interview coming up".
  **Try it:** new chat, say "get started". After the ground rules it
  should ask whether you'd like to tell it or be asked. Pick "ask me
  questions": you should get one question at a time, and after three
  answers, a short read-back and one step.
- life_compass now remembers your answers (B-003), one question at a
  time, and can save one as something you want or a hard no.
  **Try it:** say "I don't know what I want". Answer the first
  question, then start a new chat and say it again: it should move on to
  question 2.
- Ground rules at the start: a short privacy summary, terms of use and
  "how Career Copilot talks", which the person agrees to once per
  version. If they say no, it still helps but saves nothing.
  **Try it:** in a new chat, say "get started". Before any questions, it
  should show three short lines about privacy, advice and who sends
  things, and ask if that's OK.
- A response check that every draft goes through before you see it. It
  flags insults, profanity, promised outcomes ("guaranteed job"),
  biased wording ("young", "salesman", "culture fit"), personal traits
  in things you send, money or visa talk without the
  education-not-advice note, and resume numbers you never confirmed.
  **Try it:** say "check this resume line: Grew revenue 300% and
  guaranteed results for 50 clients". It should flag the promise and
  the numbers, ask for your real figures, and suggest a fixed line.
- Full privacy notice and terms of use in plain English.
  **Try it:** say "what do you store about me, and how do I delete it?"
  It should answer from the privacy notice and mention `data_export` and
  `data_delete`.

### Changed
- Old resumes and the work you describe now feed the fact record
  automatically (B-022). Each resume bullet is saved as "unsure" until
  you confirm it; the same bullet in two versions is kept once; and when
  two versions give different numbers for the same thing, you're asked
  which is right. Facts you settle show up in your resume draft.
  **Try it:** paste two versions of one resume line, say "v1: Cut
  onboarding time by 30%" and "v2: Cut onboarding time by 45%", as two
  resumes. Career Copilot should ask which number is right.
- An owner's runbook: what's live, which settings do what, how to invite
  or remove people, and how to work on it with Claude.
  **Try it:** open `docs/OWNER.md` and follow "Invite a friend".
- The project page now starts with how to use it: connect in two minutes
  (hosted with GitHub sign-in, on your own computer, or your own free
  copy), then what your first chat looks like and what to ask. Technical
  details moved to a developer section at the end. A new blueprint page
  explains where Career Copilot goes next.
  **Try it:** open the GitHub repo page. The first section should be
  "Start in two minutes", with the plain connector address.
- Message and resume drafts now check themselves (B-007). A draft that
  promises an outcome, uses an unconfirmed number or has biased wording
  comes back marked, so it gets fixed before you see it.
  **Try it:** say "draft a thank-you note to Acme saying I'm a
  guaranteed hire and cut costs by 85%". It should refuse those parts
  and ask for your real figure instead.
- Your profile builds a piece at a time (B-002). Nothing is required,
  not even a target role. New answers add to it instead of wiping it,
  and it can hold what you want, hard no's, places, companies to target
  or avoid, and things you can't truthfully claim yet. Anything you're
  unsure about is labelled unsure, and "skip" is never asked again.
  **Try it:** say "I'm not sure what role I want, but I want remote
  work". It should save "remote" as a want without asking for a role,
  and read it back.
- Shorter, simpler replies (B-013). Career Copilot now answers in 2 to 4
  short sentences, gives one step at a time and ends with one question.
  It keeps its own voice even inside another assistant (like a custom
  persona), and explains more only when you ask. The response check now
  flags chat replies that are too long, ask several questions, list more
  than 3 items or use headings. You'll be asked to OK the ground rules
  once more, since they now include this.
  **Try it:** in a new chat, say "What's up next for me, Career
  Copilot?". You should get one step and one question, not a list.
- How Career Copilot talks, for every assistant: it stays on career,
  work, money and planning, steers back politely when asked about other
  things, stays neutral, never comments on personal traits unless you
  raise them, says where facts come from, and says "I don't know"
  instead of guessing.
  **Try it:** ask "what do you think about my religion?". It should
  politely say that's outside what it does and offer a career step.

### Fixed
- (nothing yet)

### Removed
- (nothing yet)

### Security
- Sign in with GitHub (B-006). The connector address is now plain, with
  no key in it, so it's safe to share. The first time someone connects,
  they sign in with GitHub and get their own private space. Career
  Copilot never sees passwords and asks GitHub only for the public
  profile. The owner can keep it invite-only with a list of GitHub
  usernames. Once it's on, old links with a key in them stop working.
  **Try it:** in claude.ai, add a connector with just
  `https://career-copilot-cg2k.onrender.com/mcp`. It should open a GitHub
  sign-in page, then work as before.
- Text sent to the response check is never written to logs.
- The built-in knowledge is now tested against the same insult, bias and
  promise checks, so a bad automated edit can't ship.

### Knowledge
- (weekly bot updates go here)

## [0.3.0] - 2026-11-03 baseline

Confirmed against the code on 2026-11-03.

### Added
- 60 tools, 7 resources and 13 starter prompts covering orientation,
  resume, applications, interview prep, layoffs and money basics.
- Daily one-step coaching with an energy check and a "never skip twice"
  streak.
- One private data file per user, with export and delete.
- HTML dashboard: Today, Pipeline, Prep, Money, Direction.
- Weekly bot that updates the knowledge folder, gated by tests.
- One-line local install for Claude Code, and hosted access for claude.ai
  and ChatGPT through a connector URL.
- Free one-click demo hosting on Render, with a keep-awake ping.
