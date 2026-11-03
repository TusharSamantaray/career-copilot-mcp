# Privacy notice

Version 2026-11-03.7. This is a plain-English draft. Have a lawyer review it
before Career Copilot takes paying users.

Career Copilot is run by Tushar Samantaray ("we"). It's a connector that
your AI assistant uses to help with your career, money and plans.

## What we keep

Only what you or your assistant give it:

| Kind | Examples |
|---|---|
| Profile | Target role, level, location, goals |
| Work history | Jobs, achievements, stories, resume text you paste |
| Job search | Applications, statuses, reminders, interview dates, roles already shown to you (so you only see new ones), and for postings you analyze: title, company and the skills asked (never the full text), watches you set with what they found, and lessons you note |
| Money | Account names, types and balances you enter or import |
| Coaching | Daily check-ins, energy level, steps done |
| Agreement | The date you agreed to these terms |

Each person's data is in **its own private file**, linked to their
sign-in (hosted) or kept on their own computer (local). Nobody else can
see it. On the hosted version the file can also be encrypted with a key of
its own; when it is, deleting your data destroys that key, so even an old
backup of the file can't be read.

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
| The host (Render now; later MCPHosting or another) | Stores the data files and logs for the hosted version |
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

The free demo server is wiped every time it restarts or updates. Keep your
own copy with `data_export`.

## Age

Career Copilot is for people aged 16 and over.

## Changes and contact

When this notice changes, its version date changes, and Career Copilot
asks you to agree again. For questions or deletion requests, use
[GitHub](https://github.com/TusharSamantaray/career-copilot-mcp/issues).
For security problems, see [SECURITY.md](../SECURITY.md).
