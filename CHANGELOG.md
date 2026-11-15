# Changelog

All notable changes to Career Copilot. Newest first.
Every Added or Changed line has a **Try it:** line.

## [Unreleased]

### Added
- The free trial now looks after itself so it never needs paying for
  (B-082). It runs on free hosting, so on a very busy day it first
  stops taking new people (those already in carry on), and if the
  whole day's budget is used it pauses until midnight UTC. Either way
  the person gets a short, plain note instead of an error, nothing
  is lost, and exporting or deleting data still works. The try-it
  page shows the trial status at the top.
  **Try it:** open `https://career-copilot-cg2k.onrender.com/`: under
  the address it should say "Trial status: Open". Open `/health`:
  the `trial` part shows today's counts, never who.

### Knowledge
- A message template for replying to a hiring post (GitHub #36).
  **Try it:** "Draft a reply to this hiring post" gives a short
  note that names the role and one thing you did.

### Security
- Fixed a published hole in dnspython, a library pulled in by FastMCP
  (GHSA-vvf4-9x63-8xvv; it could be made to use too much memory). You
  won't notice anything.
  **Try it:** Actions → Security → the "Known holes in libraries" step is
  green.

### Changed
- The server's own address is now a "Try Career Copilot" page you can
  share (B-076). It has the connector address with a copy button, setup
  steps for Claude, ChatGPT and code editors, six things to say first,
  what Career Copilot promises, and the fair-use limits. If sign-in is
  invite-only, it says so and tells people to send their GitHub
  username. The privacy notice and terms now open from the server at
  `/privacy` and `/terms`, so people without access to the private
  repository can read them.
  **Try it:** open `https://career-copilot-cg2k.onrender.com/` on your
  phone. Tap Copy and paste it somewhere: you should get the address
  ending in `/mcp`. Then tap Privacy and Terms at the bottom.
- Getting-started steps match what new people now see: the "Connect
  Career Copilot?" page, and that the first connect can take up to a
  minute while the free server wakes (B-075). The owner's runbook explains
  why the GitHub keep-awake ping isn't enough on its own (GitHub runs it
  hours late) and how to add a free pinger, plus the exact steps to open
  sign-in to everyone (GitHub #24, #25).
  **Try it:** read README section 1, option A, and follow it from a fresh
  assistant: every step should match what you see.

### Added
- From a hiring post to a sent message in one guided flow (GitHub #36,
  B-080). Paste a post and say "help me reach out". Career Copilot
  reads it, says how well it fits, looks up the company, drafts a
  reply that quotes one thing you confirmed you did, and lays out the
  steps: check it, your yes to the exact text, you send it (LinkedIn
  messages are pasted by you), then it's logged with a follow-up date.
  It never sends for you. Messages still never mention a visa
  deadline, urgency or a performance plan, unless you say you want it
  in that one message; then the choice is tied to that exact text.
  **Try it:** paste a hiring post and say "Help me reach out to
  this person." You should get a fit verdict, a short draft and one
  next step. Add "my visa deadline is in March": it should ask you
  to confirm you want that in, and only then let it through.
- Paste hiring posts and get them ranked for you (GitHub #33, B-079).
  Copy a few "we're hiring" posts from LinkedIn into the chat.
  Career Copilot reads who posted, the role, company, place, pay,
  how to reach them, the link and the date. Posts older than a week
  or that break a dealbreaker are set aside with the reason. The
  rest are ranked by fit, with one line on why and flags for
  stretch roles, pay below your floor and places outside your list.
  It never opens LinkedIn or contacts anyone.
  **Try it:** paste three hiring posts and say "Rank these for me."
  You should get the best one first, with role, company and one
  reason, and a line on any that were set aside and why.
- Company research and a one-page brief for outreach (GitHub #34, #35,
  B-078). Ask about a company and Career Copilot reads its home page
  (what they do, in their own words) and its public job board (how
  many roles are open, where, and the newest one). Anything else your
  assistant finds must come with a link, or it's set aside as
  unverified. Then it builds a one-page brief: The fit, How I plug
  into your system, What changes by line, Why this why now, The
  offer. Every line has to point at a source (the company's public
  facts or your own confirmed work), any number has to be in that
  source, and it has to fit on one page. Sources are listed at the
  bottom. Print it or save it as PDF from your browser.
  **Try it:** say "Research Northwind Talent, northwindtalent.com,
  and build me a one-pager for a data engineering role." You should
  get one line on what they do with its link, then a one-page brief
  to review. Ask it to add "you grew 300% this year" and it should
  refuse unless a source says so.
- Fair-use limits on the hosted server (GitHub #27, B-074): each person
  can make 60 requests a minute and 1,500 a day. An assistant stuck in a
  loop is told to wait a few seconds; nobody else slows down. `/health`
  shows the limits and how many people hit one today (never who), and
  the Keep awake check fails, so GitHub emails the owner, when use looks
  unusual.
  **Try it:** open `https://career-copilot-cg2k.onrender.com/health`. You
  should see `"limits": {"per_minute": 60, "per_day": 1500, ...}`.
- Free security checks on every change and every Monday (B-073):
  published holes in our libraries (pip-audit), risky code (bandit),
  plain bugs (ruff) and secrets anywhere in git history (gitleaks).
  Dependabot is on: GitHub alerts on new holes and opens a weekly pull
  request with fixes.
  **Try it:** on GitHub, Actions → Security → Run workflow. All three jobs
  should finish green. Security → Dependabot shows any open alerts.
- Connecting now shows a Career Copilot page first: "Connect Career
  Copilot?", naming the app and where the sign-in goes, with **Allow** and
  **Don't allow** (B-070). The sign-in only finishes in the browser that
  clicked Allow. Before this, someone could send a Career Copilot user a
  GitHub link that, with one click, gave the sender's app access to that
  user's data, because GitHub skips its own screen for people who approved
  it before. We found this through a published flaw (CVE-2026-27124) in
  the library's own GitHub sign-in, which we don't use but had copied the
  pattern of. Nobody needs to sign in again.
  **Try it:** remove Career Copilot from claude.ai and add it again. You
  should see "Connect Career Copilot?" naming Claude, then GitHub, then
  the tools work.

### Fixed
- Signing in for the first time no longer shows a scary "invalid_token"
  error that blames a token you never had (B-069, GitHub #17). If your
  assistant reaches Career Copilot before you've finished signing in, it
  now says "Not signed in yet" and what to do. A sign-in that really has
  expired says so and tells you to remove and re-add the connector. If
  you're not on the invite list, the page shows the GitHub username you
  signed in as, so you can send the owner the right name.
  **Try it:** in a browser, open
  `https://career-copilot-cg2k.onrender.com/mcp`. It should say "Not
  signed in yet", not "invalid, expired, or no longer recognized".
- The weekly "Improve knowledge" job no longer fails on GitHub while it
  isn't set up (B-068). Without its three secrets it now skips with a
  note saying which to add. Once set up, it waits for the sleeping server
  and runs every test, the validation cases and the simulation before
  merging anything.
  **Try it:** on GitHub, Actions → Improve knowledge → Run workflow. It
  should finish green, with a "Skipped" note naming the three secrets.

### Changed
- The guides now match what Career Copilot does today (B-065). The
  architecture page has a new diagram of what someone hiring can see and
  when anyone learns who you are, and no longer says nobody else can
  reach your data (a persona you publish can be searched). The README,
  spec, connect guide and tour cover personas, recruiters and
  introductions. They also say plainly that the local install and the
  Deploy button need read access while the repository is private.
  **Try it:** open `docs/ARCHITECTURE.md` on GitHub and find "Being
  found without being named"; the diagram should match what the
  simulation report shows.

### Added
- A simulation you can run on your own computer: 5 made-up job seekers
  build profiles and personas, and 2 made-up recruiters bring a job
  posting, search, ask questions and ask to meet someone (B-063). It
  uses a real local server with a separate sign-in for each person, then
  checks that no name, employer, contact or salary reached a recruiter
  before both sides said yes. It runs before every commit and in CI.
  With `--serve` it keeps the server running so you can chat as any of
  them from Claude Code.
  **Try it:** run `uv run simulation/run.py` and open
  `simulation/REPORT.md`. You should see 10 checks passed, then the whole
  story. Then run it with `--serve`, add the Northwind recruiter as
  `simulation/README.md` shows, and say "I'm hiring a data engineer".
- Meet a persona only when both sides agree (B-055, GitHub #16). Someone
  hiring asks to meet a persona with their company, role and a short
  message, which is checked first. The persona's owner sees the request
  and how many screening questions came first, then says yes (choosing
  what contact to share) or no. Nobody learns who the other is until
  both have confirmed; then each sees what the other shared. The persona
  notes each reveal and that it came after the screen.
  **Try it:** from a hiring account, find a persona and say "Ask to meet
  this one for our backend role at Globex". As the job seeker, say "Any
  introduction requests?", then "Yes, share my name and email". Neither
  side should see the other's contact until both said yes.
- Pathways built on what people hiring actually ask for (B-061, from
  GitHub #14). People hiring can answer a short survey (three questions,
  versioned so questions can change later), and their searches count
  too. The demand digest shows each skill asked for per role, with how
  many said it, who (a company name only if they gave one) and the
  source, never "the market wants". Pick a direction and your pathway
  gives a few small steps, one at a time, each with its reason: the
  direction and the demand behind it. "Immediate" mode lists roles
  asking for what you already prove, with nothing new to learn.
  **Try it:** from a hiring account say "I'd like to answer the hiring
  survey". Then, as a job seeker, say "What are recruiters asking for
  in backend roles?" and "Build my pathway to backend engineer". Each
  step should end with a reason like "2 recruiters named Kafka (survey
  v1)". Also try "What job could I start right now?".
- Find candidates by their verified work, with no new website (B-053,
  GitHub #13). Someone hiring connects the same Career Copilot in their
  own AI assistant (invite-only, like everyone), pastes a job posting
  and says what the role must have. They get up to 5 published
  anonymous personas, ranked by work that proves each skill (owned or
  led counts most), each with proof lines. They can ask a persona about
  its work; questions about who someone is, where they work, how to
  reach them or salary are refused. Nobody is contacted automatically.
  **Try it:** from a second GitHub account on the invite list, say "I'm
  hiring", paste a job posting, and add "it must have Python". You
  should get anonymous matches with proof lines and no names. Then ask
  "What's their email?"; it should refuse.
- An anonymous persona you can publish so people hiring find your work,
  not your name (B-052, GitHub #12). It shows your target role, level,
  an experience range and your confirmed work facts with the skills they
  prove. Employer names, emails, links and phone numbers are removed,
  and a line mentioning a personal trait is left out. You see the exact
  view first, can hide any line, and it's published only after your yes.
  Take it down any time. The privacy and terms version changed, so
  you'll be asked to agree once more.
  **Try it:** say "Show me what my anonymous persona would look like".
  You should see every line, with no name, employer or contact details,
  and "Publish this?". Say "hide the second line", then "yes, publish
  it", then "take my persona down".
- A data-handling statement any program can check before you connect
  (B-043, GitHub #4). It lists what is stored, where, for how long and
  who can read it, plus what is never stored. It is shown with the
  ground rules before anything is saved, and served without sign-in at
  `/data-handling` on the hosted server. The privacy and terms version
  changed, so you'll be asked to agree once more.
  **Try it:** open `<your server>/data-handling` in a browser, or say
  "What data do you keep about me, and where?". You should see each kind
  of data with where it lives, how long it's kept and who can read it.

- A `validation/` folder that proves each improvement with numbers
  (B-060). Each case replays one improvement with made-up people and
  measures it, like the before and after table in a resume proof.
  `RESULTS.md` shows the latest scoreboard; `HISTORY.md` gets a dated
  row whenever a score changes, so you can see when each improvement
  landed. It runs before every commit and on every push. First two
  cases: the resume rebuild and the send-with-your-yes flow.
  **Try it:** open `validation/RESULTS.md` on GitHub. You should see
  both cases with every measure marked pass, and `validation/HISTORY.md`
  with today's rows.
- Send emails, add or cancel calendar events, and post to LinkedIn, only
  with your yes (B-056). Your assistant drafts it, Career Copilot checks
  the exact text (no invented numbers, and nothing about a performance
  plan, urgency or a visa deadline), then shows it to you word for word.
  Only after you say yes to that message does your own connected app
  (like Gmail or Google Calendar) send it, and your assistant checks it
  arrived. Change a word and it asks again. Career Copilot keeps no copy
  and never sends anything itself. Calendar events get reminders 30
  minutes and 1 minute before.
  **Try it:** with Gmail connected, say "Draft a thank-you email to the
  recruiter and send it after I check it". You should see the exact
  email and "Send it?"; say yes, and it should confirm it found the
  email in your sent mail.
- See how your resume improved, version by version (B-051). Save a dated
  snapshot after each rebuild. Each one is checked for internal level
  tags (like L5), numbers none of your confirmed facts hold, and a
  summary written in first person or full of filler. The timeline shows
  what changed each time and flags a version that brought an old
  problem back. Nothing is ever overwritten. You can compare any two
  versions, or get a proof document: dated timeline, before and after
  table, and the final resume at the end.
  **Try it:** paste your resume and say "Snapshot my resume as September".
  Paste a newer one and say "Snapshot this as October", then "Show how
  my resume improved". You should get a dated table with word counts and
  checks before and after, and the October resume at the end.
- A weekly error report for the owner (B-046). Every Monday, GitHub
  turns the anonymous error counts into one "Error report" issue: which
  error codes people hit, on which tool, how many people, and the
  suggested fix. Quiet weeks stay quiet. It never changes code on its
  own.
  **Try it:** on GitHub, open Actions → Error report → Run workflow. With
  the insights secrets set, you get "Nothing to report" or an issue
  labelled `triage`.
- Your dashboard now shows which applications need you (B-034): up to
  five cards at the top of Today and Pipeline, most urgent first:
  overdue, due within two days, no next step yet, or (if you need visa
  sponsorship) still unknown. Each card says the one thing to do.
  Closed applications never appear.
  **Try it:** say "Show my dashboard". Under "Loops needing action" you
  should see your most urgent application first, with what to do next.
- Check what a company actually says about visa sponsorship (B-029).
  You get yes, no or "not stated", how sure that is, and the exact
  sentences it's based on, plus what you logged from recruiters. If the
  posting is silent, it suggests asking the recruiter once, plainly; it
  never assumes yes. Links to public H-1B filing data are included as
  background, not a promise.
  **Try it:** paste a posting and say "Does this company sponsor visas?".
  You should get yes, no or not stated, with the sentence quoted.
- Tailor your resume to a posting without stretching the truth (B-026).
  Your assistant suggests lines for the role, and each one must rest on
  facts you've confirmed. A line is held back, with the reason, if it has
  a number you never gave, says you led something you only took part in,
  mixes two jobs into one claim, names one of your honest gaps, or adds a
  posting keyword your facts don't back. Lines that pass can be saved as
  a named resume version, so you can see later which version got replies.
  **Try it:** paste a job posting and say "Tailor my resume for this and
  save it as Acme v1". You should get lines built from your confirmed
  facts, a short reason for anything held back, and "Acme v1" in your
  resume versions.
- Errors now explain themselves (B-045). Every error starts with a short
  code, like `[UNKNOWN_TOOL]`, and a new `report_issue` tool says what it
  means and what to do: reconnect, fix a value, or try again once. Only
  an anonymous count is kept. Calling an out-of-date tool or sending a
  wrong value no longer shows as "Internal error". The codes are listed
  in `docs/CONNECT.md`.
  **Try it:** say "Call the tool no_such_tool". You should see an
  `[UNKNOWN_TOOL]` error. Then say "What does that error mean?" and get
  "disconnect and reconnect, or start a new chat".
- Deadlines and fast-track mode (B-030). A hard date, like the end of a
  grace period, is saved with a best case and a safer, earlier date, and
  plans use the safer one. When it's under 60 days away, Career Copilot
  says fast-track is on: money runway first, shorter plans, and the
  freshest job postings first.
  **Try it:** say "I was laid off; my last day is in 10 days and I have
  a 60-day grace period after that". You should get the key dates, a
  safer date to plan on, "fast-track is on", and a first step under an
  hour.
- A readable copy of your data (B-036). Ask for it and you get one
  plain page with everything stored about you, with confirmed and unsure
  facts labelled. On your own computer it's also saved as
  `~/CareerCopilot/my-data.md`, so you can open it in any editor.
  **Try it:** say "Show me everything you know about me". You should get
  a short summary, and on your computer a file you can open.
- Cover letter drafts (B-028). A short letter made only from facts
  you've confirmed: the two that best match the posting, in your own
  words, in your chosen voice. It's checked for promises, bias and
  unconfirmed numbers before you see it.
  **Try it:** say "Draft a cover letter for the Data Analyst role at
  Acme" and paste the posting. Every point in it should be something
  you've confirmed.
- Find a recruiter (B-035). Get ready-made search links for a company's
  recruiters or hiring manager, then draft a short note to send
  yourself. Links only: it never searches LinkedIn for you or messages
  anyone.
  **Try it:** say "Who's the recruiter for data roles at Acme?". You
  should get three links and an offer to draft a note.
- Lessons (B-033). Note what you learned after an interview or a
  search week, in your own words. Prep for your next round shows your
  three latest lessons.
  **Try it:** say "Lesson from Acme: lead with the number, then the
  story". Next time you prep a round it should remind you.
- Keyword check (B-027). Compare a posting's skills with your resume:
  what's already there, what's missing but true (you've confirmed it,
  so it's safe to add inside a real bullet), and real gaps, which it
  never adds.
  **Try it:** paste a posting and say "which keywords am I missing?".
  You should get the safe-to-add ones and the real gaps, separately.
- Ownership check (B-025). Before a resume line uses a strong verb like
  "led", "owned", "architected" or "designed", Career Copilot checks it
  against your part in the work. If your fact says you contributed, it
  suggests a truer verb. If there's no fact yet, it asks: did you write
  it, lead it or fix it?
  **Try it:** say "Check this line: Architected our billing platform".
  It should ask what your part was before using "architected".
- Watches (B-020). Ask Career Copilot to keep an eye on companies' job
  boards, or on assessments, follow-ups and deadlines coming due. What it
  finds waits for you, and the next time you open a chat it mentions the
  most urgent thing in one line. Each item shows once, and it stays quiet
  when nothing is new. Watches only find things; they never apply or
  message anyone.
  **Try it:** say "Watch greenhouse:anthropic for new engineering roles,
  daily". Start a new chat tomorrow: it should mention anything new, or
  nothing.
- Skill gaps from real postings (B-016). Every posting you analyze leaves
  a short note (title, company, skills asked, never the full text). After
  five or more, Career Copilot shows how often each skill is asked for,
  whether your confirmed facts prove it, and which gap costs you most.
  When you log which resume version you sent, it also shows each
  version's reply rate once there are five applications for it.
  **Try it:** analyze five postings, then say "what skill gap is costing
  me most?". You should get one skill, how often it's asked, and one way
  to prove it this week.
- Round prep checks your calendar (B-024). When your calendar is
  connected, it confirms the next round is really booked before planning
  prep, and tells you to check with the recruiter if it isn't there.
  **Try it:** with your calendar connected, say "Prep me for my next
  Acme round". It should say whether the round is on your calendar.
- Story coverage (B-018). See your interview stories against each
  competency (ownership, conflict, failure, ambiguity, influence,
  leadership, impact, customer, speed), how strong each one is, where you
  have no good story yet, and the one story to write or fix next. It also
  flags story numbers you haven't confirmed.
  **Try it:** say "Which interview stories am I missing?". You should get
  one line: the next story to write or strengthen.
- Interview rounds that build on each other (B-017). Log what each round
  asked, which story you told, who was on the panel (by role, never by
  name) and any feedback. Prep for the next round then shows what's
  still uncovered, which story to bring for each gap, a warning if this
  panel may already have heard it, your weak spots, and one thing to do
  today. Loops are tracked by company and requisition number.
  **Try it:** say "Round 1 at Acme was behavioral; they asked about a
  disagreement and I told my migration story. The recruiter said go
  deeper on numbers. Prep me for round 2." It should log the round and
  give you one thing to rework today.
- A pre-apply check (B-019). Before you apply, it tells you which
  application system the company uses, what in your resume that system
  may scramble (tables, two columns, icons, mixed date styles, missing
  headings or email), which knock-out questions the posting implies
  (work authorization, location, years, degree, clearance) and whether
  you have an answer ready, then gives a verdict: ready, fix first, or
  knock-out risk.
  **Try it:** paste a posting and its link and say "anything to fix
  before I apply?". You should get the platform, the top fix and the
  verdict.
- Job search on official job boards (B-005). Give it companies'
  Greenhouse, Lever or Ashby boards and it finds fresh roles, each with
  the date it was posted (nothing older than a week by default, and
  nothing without a provable date). Hard no's and excluded companies are
  filtered out, your wants rank the rest, and it only shows roles you
  haven't seen, so "nothing new" is a normal answer. It never applies for
  you. For LinkedIn it gives you a link instead.
  **Try it:** say "Find new engineering roles at greenhouse:anthropic".
  You should get a few dated roles. Ask again: it should say nothing is
  new.
- Posting analysis (B-005). Paste a job posting and get the level, years
  asked, pay compared with your floor, what it says about sponsorship,
  where you fit, the gaps, and a verdict.
  **Try it:** paste any posting and say "is this worth applying to?".
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
- Resumes, messages and personas now also flag Catholic, Protestant,
  Mormon, Evangelical and church as personal traits, like other faiths
  (B-052).
  **Try it:** say "Check this line: Led the church fundraising
  committee". It should suggest leaving the faith detail out unless you
  chose to include it.
- The ground rules now read as a disclosure: plain statements of what
  Career Copilot does, with a three-line summary, instead of
  instructions to your assistant (B-043, GitHub #4). Cautious assistants
  treat server instructions as a risk, so the rules no longer give any.
  **Try it:** start a new chat and say "What are your ground rules?".
  You should get three short lines (your data, not advice, nothing sent
  without your yes) and a question whether that's OK.
- The resume timeline now checks what a real rebuild proof checks
  (B-059): a summary is flagged when it doesn't lead with a number, not
  for using "I"; education lines no longer count as roles; and you can
  list internal team names recruiters won't know, so each version is
  checked for them. The proof shows the role count and how much tighter
  the resume got.
  **Try it:** say "Snapshot my resume as October, and flag these internal
  names: <your team nickname>". The checks should list that name if it's
  still there, and "Show how my resume improved" should show roles and a
  percent change in words.
- The terms now say how sending works: nothing goes out without your yes
  to the exact text, and your own app does the sending (version
  2026-11-08.11). You'll be asked to agree once more.
  **Try it:** say "Show me the ground rules". The terms should include
  the new sending line, and it should ask if that's OK.
- The health check now says whether sign-in is invite-only (B-042), next
  to the sign-in method and tool count, so you or a tester's assistant
  can check the server before connecting. It never shows who is invited.
  A ready-to-send tester message that explains GitHub sign-in is in
  `docs/OWNER.md` (B-041).
  **Try it:** open https://career-copilot-cg2k.onrender.com/health. You
  should see `"auth_mode": "github-oauth"` and `"invite_only": true` or
  `false`.
- Diagrams are easier to read in light and dark mode. Boxes now have a
  coloured outline with a faint tint, and the text uses the page's own
  colour, so nothing is pale-on-white or dark-on-black. Safety checks
  are purple and "never does" items are red and dashed.
  **Try it:** open `docs/ARCHITECTURE.md` on GitHub, then switch GitHub
  between light and dark theme. The text in every box should stay sharp
  in both.
- Documentation brought up to date, with diagrams in one colour scheme
  (blue is you, green is Career Copilot, amber is stored data, grey is an
  outside service, purple is a safety check, red is something it never
  does). Each diagram answers one stated question. New page,
  `docs/ENGINEERING.md`: how it's tested, the acceptance tests, a
  timeline of every problem found during testing, and for each one the
  cause, the fix and the test that guards it. The architecture page is
  rewritten for today's system (sign-in, encryption, Neon storage, job
  search), and the guided tour covers the new features.
  **Try it:** open `docs/ENGINEERING.md` on GitHub and look at section 3:
  one picture of why the free host lost sign-ins and data, and what
  changed.
- Study plans fit the interview format (B-031). Tell it the kind of loop
  (coding-heavy, values-heavy, practical, enterprise, startup or
  non-technical) and the daily plan shifts to match: more story practice
  for values-heavy loops, applied builds for practical ones, work samples
  and case practice for non-technical roles.
  **Try it:** say "Plan my prep for a values-heavy loop on the 14th, 2
  hours a day". Story practice should show up every other day.
- Sponsorship in your pipeline (B-037). If needing visa sponsorship is
  one of your hard no's, the daily pipeline view lists applications where
  sponsorship is still unknown and flags any that said no, so you can ask
  once, early. You can record what each company said when logging it.
  **Try it:** with "no visa sponsorship" as a hard no, log an application
  and say "what's my pipeline today?". It should list where sponsorship
  is still unknown.
- Drafts in your voice (B-032). Messages can sound plain (the default),
  warm or formal. Only the greeting, opening and sign-off change, never
  the facts. Say which you like once and it's remembered.
  **Try it:** say "Write my thank-you notes in a formal voice from now
  on", then ask for a thank-you note. It should start "Dear" and end
  "Kind regards".
- The spec page is now Spec v2 (B-011): the journey-first design, with
  what's built and what's still open marked on every part, including
  the acceptance tests. The old v1 spec and cost model moved to
  `docs/archive/`.
  **Try it:** open `docs/SPEC.md` and read section 7: each build step
  says Done or Open, with a backlog id.
- Ready for a persistent disk (B-008). Sign-ins are now kept in the same
  place as your data, so adding one disk on Render keeps both through
  restarts. The steps are in the setup guide. On the free plan nothing
  changes, except that everyone signs in once more after this update.
  **Try it:** (owner) read "Keep data across restarts" in
  `docs/SETUP.md`.
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
- The demand digest counted one recruiter twice for the same skill when
  they both answered the survey and searched (B-064). Now each person
  counts once per skill, and every source is listed together, like
  "1 recruiter named Spark (persona searches, survey v1)".
- The anonymous usage counts that drive the weekly improvements were
  wiped every time the free server restarted (B-049). The owner can now
  keep them in the database instead (`CAREER_COPILOT_INSIGHTS_STORE=
  database`); nothing changes until that's switched on. The health check
  shows `"insights": "file"` or `"database"`.
- If something breaks inside a tool, you now see a short code and a
  reference (`[INTERNAL_ERROR] … (ref a1b2c3)`) instead of a technical
  error message (B-047).
- Reminders made from your emails and calendar now land on your dates,
  even when your assistant passes your local date (B-048).
- If GitHub is down or answers oddly while you sign in, you now get a
  clear "Couldn't reach GitHub, try again in a minute" page instead of a
  server error (B-044).
- The privacy notice and terms no longer say the demo is wiped on every
  restart: data now lives in a managed database. They still suggest
  keeping your own copy, since it's a free service. You'll be asked to
  OK the ground rules once more.
  **Try it:** in a new chat, say "get started". After you accept, ask
  "what happens to my data if the server restarts?". It should say the
  data stays, and suggest an export now and then.
- Neon's pooled connection works reliably: Career Copilot no longer uses
  prepared statements, which the pooler can't keep between requests. The
  health check now says which storage is in use (`"storage":
  "postgres"`), never the address.
  **Try it:** open `https://career-copilot-cg2k.onrender.com/health`
  after adding `DATABASE_URL` in Render. It should show
  `"storage": "postgres"`.
- Your data no longer disappears when the server restarts (B-008). The
  hosted version can now keep everything in a free hosted database
  (Neon) instead of the free server's disk, which is wiped on every
  restart. Data stays encrypted, each person with their own key.
  **Try it:** (owner) add `DATABASE_URL` in Render as described in
  `docs/SETUP.md`. Save a goal in a chat, wait until the next deploy or
  restart, and ask "what are my goals?". It should still be there.
- No more "Reconnect to use it again" (B-039). Sign-ins used to be
  remembered on the free server's disk, which is wiped whenever the
  server sleeps, restarts or updates, so you had to reconnect almost
  every chat. Now nothing about your sign-in is stored on the server:
  it's sealed inside your connection itself. Sign in once and stay
  connected through restarts and updates. GitHub's token is also no
  longer kept at all, only your GitHub id.
  **Try it:** after this update, reconnect once in claude.ai. Then open
  a new chat the next day: it should work without asking to reconnect.
- The "I don't know what I want" journey is now tested end to end on
  every change (B-038): within five questions you get 2 or 3 directions,
  pick one, and every line of your profile is labelled confirmed or
  unsure.
  **Try it:** in a new chat, say "I don't know what I want" and answer
  the questions. You should see directions before a sixth question.
- A rejection email no longer closes the wrong application (B-023). If
  you applied to two roles at one company, a rejection closes only the
  one whose role or job id it names. If it doesn't say, Career Copilot
  asks you which one. You can now save a job id when logging an
  application.
  **Try it:** log two roles at one company, then share a rejection email
  that doesn't name the role. It should ask which application it was.

### Removed
- (nothing yet)

### Security
- Lessons, resume lines, answers and posting text you share are now
  hidden from server logs, like the rest of your words.
- Encryption at rest (B-021). When the server owner adds a master key,
  everyone's saved data is encrypted, each person with their own key.
  Deleting your data destroys your key, so even an old backup of your
  file can't be read. Nothing changes in how you use it.
  **Try it:** (owner) add `CAREER_COPILOT_MASTER_KEY` in Render, then
  save something in a chat and say "export my data". Everything should
  come back as normal.
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
