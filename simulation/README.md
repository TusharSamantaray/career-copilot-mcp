# Simulation

Five made-up job seekers and two made-up recruiters use a real Career
Copilot server on your computer, end to end. Nothing here is real, and
nothing leaves your machine.

| Who | Comes in with | Decides |
|---|---|---|
| Maya | Senior data engineer, owns Spark and Airflow work | Publishes; says yes to an intro |
| Jon | Backend engineer between jobs, led a Kafka move | Publishes; says no to an intro |
| Priya | Frontend engineer | Publishes, but hides one line first |
| Alex | Analyst switching to data engineering | Publishes; builds a pathway |
| Sam | ML engineer, interviewing | Keeps the persona private |
| Northwind Logistics recruiter | A Senior Data Engineer posting, must have Spark | Answers the survey, searches, asks questions, asks to meet the top match |
| Contoso Pay recruiter | A Backend Engineer posting, must have Kafka | The same |

Each person has their own sign-in (an API key), so their data stays
separate exactly as it does for real users. Every step is a real tool
call over the same connection Claude uses.

Then it checks the rules held:

- no name, employer or contact reached a recruiter before both sides
  said yes (the facts have an employer, an email and a phone number
  planted in them);
- no salary was shown, although a posting had one;
- Sam, who kept the persona private, never appeared;
- the top match is the person who owns the work, and a must-have
  filters;
- identity and salary questions were refused;
- the recruiter saw a contact only after both said yes, and nothing
  after a no;
- every pathway step has a reason.

## Run it

    uv run simulation/run.py

It prints the whole story and writes [REPORT.md](REPORT.md): every
check, then what each person said and what Career Copilot answered.
`--check` runs it without writing the report (used before each commit
and in CI).

## Try it yourself, as any of them

    uv run simulation/run.py --serve

This runs the simulation, then keeps the server running with everyone's
data. In a second terminal, add yourself as one of them in Claude Code
(the VS Code extension uses the same list):

    claude mcp add --transport http cc-northwind http://127.0.0.1:8790/mcp --header "Authorization: Bearer sim-northwind"

Start a new chat and try:

- "I'm hiring a data engineer. Here's the posting: ..." then "Ask the
  top one what they built with dbt", then "What's their email?"
- "Any introduction requests?" (add `sim-jon` or `sim-maya` instead)
- "What are recruiters asking for in data engineering?" and "Build my
  pathway to data engineer" (as `sim-alex`)
- "Show me what my anonymous persona would look like" (as `sim-sam`)

Every key is listed when the server starts: `sim-maya`, `sim-jon`,
`sim-priya`, `sim-alex`, `sim-sam`, `sim-northwind`, `sim-contoso`.
When you're done, press Ctrl+C and remove the connector:

    claude mcp remove cc-northwind

These keys only work on this local test server. The data is in
`simulation/.data/` (never committed) and is reset each time.

## Change the story

The people, postings and questions are plain lists at the top of
`run.py` (`SEEKERS`, `RECRUITERS`). Add a person or change a posting and
run it again. Keep everyone made up.
