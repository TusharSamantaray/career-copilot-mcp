# Guided tour

There are two ways to take the tour:
- ask your assistant to run the **`tour`** prompt, and it walks you
  through these five stops interactively;
- or read the example conversation below.

## Stop 1: The one small step

> **You:** hey
> **Copilot:** Morning! How's your energy today: low, medium or high?
> **You:** low honestly
> **Copilot:** Totally fine. Today's one thing: *save one job posting that
> looks interesting.* Five minutes, then you're done for the day.
> **You:** done
> **Copilot:** That counts. You moved today. That's 3 days of momentum.

Tools: `daily_step`, `step_done`. Rest days don't break your momentum;
two in a row do.

## Stop 2: Finding your direction

> **You:** I'm in sales but I think I want product management.
> **Copilot** *(`career_move`)*: It's a career change, but a reachable one.
> - **Carries over:** communication and stakeholder work.
> - **To build:** roadmapping, user research and analytics.
> - **Stepping stone:** marketing is a common bridge.
>
> Want me to check where PM roles are growing near you?
> **Copilot** *(`where_to_move`)*:
> - If you'd stay in India: Bengaluru first. It's the biggest product
>   market.
> - Remote roles let you keep your costs.
> - Always check visa and cost of living before moving.

Tools: `role_match`, `skills_gap`, `career_move`, `where_to_move`,
`life_compass` (for when you don't know what you want yet).

## Stop 3: The autopilot

> **You:** Here are this week's job emails.
> **Copilot** *(`inbox_triage`)*: I found 1 interview invite, 1
> rejection, and 1 assessment that expires Thursday. Shall I update your
> pipeline?
> **You:** yes
> **Copilot:** Done. I've also set reminders:
> - finish the assessment by Tuesday;
> - prep the day before the interview;
> - send a thank-you after it;
> - follow up 3 business days later if you hear nothing.

Tools: `inbox_triage`, `calendar_interviews`, `application_log`,
`nudges_due`, `calendar_export`.

## Stop 4: Interview prep

> **You:** I have a hiring manager screen Friday.
> **Copilot:** Let's line up three stories. Tell me about a time something
> went wrong at work... *(saves it with `story_add`)*
> For "tell me about a failure", use your launch story. Your bank still
> has no conflict story, so let's do that one next.

Tools: `story_add`, `story_match`, `interview_questions`,
`message_draft`, `coding_pattern`, `system_design`, `prep_checklist`.

## Stop 5: Money and the future

> **You:** How long can I last?
> **Copilot** *(`finance_dashboard`)*:
> - **Cash alone:** 10 months.
> - **All accessible money:** 26 months.
> - **Watch out:** one stock is 60% of your investments.
>
> Want to set an emergency-fund goal?

Tools: `finance_dashboard`, `layoff_fund_plan`, `goal_set`,
`future_projection`, `invest_guide`, `economy_indicators`.

All money, tax, visa and relocation answers are education, not advice.
