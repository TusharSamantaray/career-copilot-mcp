# Privacy notice

Version 2026-11-08.14. This is a plain-English draft. Have a lawyer review it
before Career Copilot takes paying users.

Career Copilot is run by Tushar Samantaray ("we"). It's a connector that
your AI assistant uses to help with your career, money and plans.

## What we keep

Only what you or your assistant give it:

| Kind | Examples |
|---|---|
| Profile | Target role, level, location, goals |
| Work history | Jobs, achievements, stories, resume text you paste |
| Job search | Applications, statuses, reminders, interview dates, deadlines you set, roles already shown to you (so you only see new ones), and for postings you analyze: title, company and the skills asked (never the full text), watches you set with what they found, and lessons you note |
| Money | Account names, types and balances you enter or import |
| Coaching | Daily check-ins, energy level, steps done |
| Persona | Only if you publish it: the anonymous view described below |
| Hiring searches | If you search for candidates: how many questions you asked each persona and when (never the questions or the postings you paste) |
| Agreement | The date you agreed to these terms |

Each person's data is in **its own private file**, linked to their
sign-in (hosted) or kept on their own computer (local). Nobody else can
see it. On the hosted version the file can also be encrypted with a key of
its own; when it is, deleting your data destroys that key, so even an old
backup of the file can't be read.

The same list, as data a program can check (what, where, how long, who
can read it), is at `/data-handling` on the hosted server and in the
`copilot://data-handling` resource. Career Copilot shows it with the
ground rules before saving anything.

## Your anonymous persona (only if you publish it)

Off by default. If you choose to, Career Copilot builds an anonymous
view of your work so people hiring can find you without seeing who you
are. You see the exact view first, can leave out any line, and it is
published only after you say yes to that view.

- **In it:** your target role, level, an experience range (like "6-9
  years"), the locations you chose, and your confirmed work facts with
  the skills they prove. A skill appears only when a confirmed fact
  proves it.
- **Never in it:** your name, contact details, photo, age, gender,
  salary, work authorization, or the employer names you gave. Emails,
  links and phone numbers are removed from facts, and a line that
  mentions a personal trait (like religion) is left out.
- **Who sees it:** other signed-in people on this invite-only server
  who search for candidates. Nobody sees it before you publish.
- **Take it down:** `persona_unpublish` removes it from search at once;
  deleting your data deletes it too. It is a snapshot: it changes only
  when you publish again.
- **Searches:** a person searching sees the persona's role, level,
  experience range, locations, skills and proof lines, and can ask it
  questions answered only from those lines. Questions about who you are,
  where you work, how to reach you or salary are refused.
- **Be aware:** someone who already knows your work well might
  recognise it from the facts themselves. Leave out any line that feels
  too specific.

## Signing in with GitHub

On the hosted version you sign in with GitHub. GitHub checks your
password; Career Copilot never sees it. Career Copilot asks GitHub only
for your public profile (`read:user`): no repositories, no private email.
It uses your GitHub user number to find your file, and stores it only as a
scrambled code (a salted hash), never your username or name. Remove
Career Copilot's access any time in GitHub under Settings, Applications.

## What we never keep

- Passwords, one-time codes or bank logins. Career Copilot never asks
  for them and never logs in anywhere for you.
- Email text. When your assistant shares job emails for sorting, only the
  resulting application update is saved. Interview titles from your
  calendar are kept as reminder text.
- Account numbers or bank ids. They're dropped when you import balances.
- Messages you approve to send (emails, calendar changes, LinkedIn posts).
  Career Copilot checks the text and seals your approval, but keeps no
  copy, and never sends anything itself: your own connected app does.

## Logs

The server logs which tool ran, when, and how long it took. Your words,
emails, money figures, notes and keys are hidden before anything is
written. Logs on the host roll over and are deleted over time.

## Anonymous usage counts

To improve the product, the server counts things like "this tool failed"
or "this role wasn't in the catalogue". User ids are replaced with salted
hashes, text is cleaned of names, emails and numbers, and nothing is
reported until at least 5 different people share it. You can ask the
operator to turn this off (`CAREER_COPILOT_INSIGHTS=0`).

## Who else is involved

| Party | What they see |
|---|---|
| Your AI assistant (Claude, ChatGPT and so on) | Your conversation, under its own privacy policy |
| GitHub | That you signed in to Career Copilot |
| The host (Render now; later MCPHosting or another) | Runs the hosted version and keeps its logs |
| The database host (Neon) | Stores the hosted version's records, encrypted when the operator turns encryption on |
| The marketplace (MCPize, when listed) | Your subscription and billing details |
| World Bank API | Only which country's public data is requested; nothing about you |
| Public job boards (Greenhouse, Lever, Ashby) | Only which company's public job list the server read; nothing about you |

We don't sell your data, and we don't use it for ads.

## Your choices

- **See everything:** ask your assistant to run `data_export`.
- **Delete everything:** ask it to run `data_delete`. This also removes
  your anonymous usage counts.
- **Stay fully local:** run the local version, and nothing leaves your
  computer except what your assistant itself sends.
- **Say no:** if you don't agree to the terms, Career Copilot still
  helps, but saves nothing about you.

## The demo server

The hosted demo keeps your data in a managed Postgres database (Neon),
encrypted, so restarts and updates don't erase it. It is still a free
service that can change or pause, so keep your own copy with
`data_export` now and then.

## Age

Career Copilot is for people aged 16 and over.

## Changes and contact

When this notice changes, its version date changes, and Career Copilot
asks you to agree again. For questions or deletion requests, use
[GitHub](https://github.com/TusharSamantaray/career-copilot-mcp/issues).
For security problems, see [SECURITY.md](../SECURITY.md).
