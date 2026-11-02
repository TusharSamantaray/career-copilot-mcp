# Designing with Figma

Career Copilot has no app of its own; it lives inside the user's AI
assistant. Figma is still where we design three things:
1. the **marketing site**;
2. the **companion web view**, a lightweight dashboard (daily step,
   pipeline, money) for people who want to see everything at a glance;
3. the **cards** assistants can render.

The Figma MCP server lets Claude read a Figma file straight from a link
and turn frames into code.

## Connect

```
claude mcp add --transport http figma https://mcp.figma.com/mcp
```

Then `/mcp` → **figma** → Authenticate, and start a new session.

## Frames to design

| Frame | What it shows | Backed by |
|---|---|---|
| Daily step card | Energy picker, the one step, a momentum ring, a "done" button | `daily_step`, `step_done` |
| Onboarding | 5 questions, one per screen | `get_started`, `profile_save` |
| Direction | Role-fit bars, career-move path, city options map | `role_match`, `career_move`, `where_to_move` |
| Pipeline board | Applied → assessment → interviewing → offer columns, with due chips | `application_log`, `nudges_due` |
| Interview prep | Story bank with theme coverage, question bank | `story_add`, `story_match` |
| Money | Runway gauge, accessible vs locked bars, goal progress | `finance_dashboard`, `goals_review` |
| Landing page | Hero, "one small step a day", how it works, pricing | Marketing |

**Design principles:**
- Calm colours and lots of white space.
- One primary action per screen.
- Progress shown as momentum, never as debt.
- Never a red "overdue" wall: overdue items get a soft accent and a
  smaller step.

## Example prompts once Figma is connected

- "Here's my Figma frame for the daily step card: `<link>`. Build it as a
  React component wired to the daily_step response shape."
- "Compare the pipeline board frame `<link>` with what `nudges_due`
  returns, and list any fields the design is missing."
- "Pull the colours and type scale from `<link>` into CSS variables for
  the landing page."
- "Generate the onboarding screens from these 5 frames `<link>`, one
  question per screen, calling profile_save at the end."

## Design tokens (starting point)

| Token | Value | Use |
|---|---|---|
| `--calm` | `#1F6F5C` | Primary, momentum |
| `--warm` | `#E8A23B` | Encouragement, highlights |
| `--ink` | `#14161A` | Text |
| `--paper` | `#F7F6F2` | Background |
| `--soft-alert` | `#C2593F` | Overdue, used sparingly |
| Type | Inter / IBM Plex Sans | Friendly and legible |
