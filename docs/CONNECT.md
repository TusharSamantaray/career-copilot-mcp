# Connect Career Copilot to your AI assistant

## It's just a connector: no logins, no passwords

**Career Copilot never logs in to anything for you.** It has no access
to your email, calendar, bank or Zoom, and it will never ask for a
password.

If you want those in the picture, connect them in your own chat. Your
assistant then reads from them and hands Career Copilot only the few facts
it needs:

| You connect (in your assistant) | Your assistant hands over | Career Copilot does |
|---|---|---|
| Gmail or Outlook | Job emails: sender, subject, date, snippet | `inbox_triage`: pipeline updates and reminders |
| Google or Outlook calendar, Zoom | Upcoming events | `calendar_interviews`: prep, thank-you and follow-up |
| A bank-data connector, or typing it in | Account names, types and balances | `finance_import`: dashboard and runway |
| Drive, OneDrive, Notion, or pasting | Old resume text | `resume_import` then `resume_merge` |

No connector? Just paste or type the facts. Ask your assistant to call
`companions` for the full list.

## Connect Career Copilot itself

Career Copilot is a standard MCP server, so it works with any assistant
that supports MCP. There are two ways to run it:

| Way | Best for | What you need |
|---|---|---|
| **Local** (runs on your computer) | Claude Code, Claude Desktop, Cursor, VS Code | [uv](https://docs.astral.sh/uv/) installed |
| **Hosted** (runs on a server) | claude.ai, ChatGPT, phones, Muse | A server URL and a key |

## The one-liners

**Claude Code, local:**

```
claude mcp add --scope user career-copilot -- uvx --from git+https://github.com/TusharSamantaray/career-copilot-mcp career-copilot --stdio
```

**Claude Code, hosted:**

```
claude mcp add --scope user --transport http career-copilot "https://<server>/mcp?key=<key>"
```

On Windows PowerShell, wrap commands containing `--` in `cmd /c "..."`.

**claude.ai and ChatGPT, hosted:** paste this URL into the connector
settings (steps below):

```
https://<server>/mcp?key=<key>
```

Below, `URL` means `https://<server>/mcp` and `KEY` means your key. A key
in the URL works everywhere. Clients that can send headers can use
`Authorization: Bearer KEY` instead, which keeps the key out of the URL.
Treat a URL that contains a key like a password: anyone who has it can use
your copy of Career Copilot.

## Claude Desktop

Settings → Developer → Edit Config, then add (local):

```json
{
  "mcpServers": {
    "career-copilot": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/TusharSamantaray/career-copilot-mcp",
               "career-copilot", "--stdio"]
    }
  }
}
```

Restart Claude Desktop afterwards. To use the hosted server instead, add it
as a connector the same way as claude.ai.

## Claude.ai (web and mobile)

Settings → Connectors → **Add custom connector**. Give it the name
`Career Copilot` and the URL `https://<server>/mcp?key=<key>`. Then turn it
on in a chat from the tools menu. It also appears in the Claude mobile app.

## ChatGPT

Settings → Apps & Connectors → Advanced → turn on **Developer mode**. Then
**Create**: name `Career Copilot`, URL `https://<server>/mcp?key=<key>`,
authentication **No authentication** (the key is in the URL). In a chat,
pick it from the **+** menu → Developer mode. Developer mode needs a paid
plan.

## Muse (Meta)

Muse is a hosted assistant, so it connects like Claude.ai: add a connector
in Muse and paste your MCPize URL.

**Bonus: reach your own computer from Muse.** Add the Reason connector
(`https://mcp.reasonmachines.com/mcp`) in Muse, and join Claude Code to
the same Reason Network. Muse can then hand longer tasks to your Claude
Code session, which uses Career Copilot too. For example: "ask my Claude
Code session to turn my merged resume bullets into a PDF".

## Cursor

`~/.cursor/mcp.json`:

```json
{ "mcpServers": { "career-copilot": {
    "url": "URL",
    "headers": { "Authorization": "Bearer KEY" } } } }
```

## VS Code (GitHub Copilot agent mode)

`.vscode/mcp.json` in your workspace:

```json
{ "servers": { "career-copilot": {
    "type": "http",
    "url": "URL",
    "headers": { "Authorization": "Bearer KEY" } } } }
```

## Gemini CLI

`~/.gemini/settings.json`:

```json
{ "mcpServers": { "career-copilot": {
    "httpUrl": "URL",
    "headers": { "Authorization": "Bearer KEY" } } } }
```

## Windsurf

`~/.codeium/windsurf/mcp_config.json`:

```json
{ "mcpServers": { "career-copilot": {
    "serverUrl": "URL",
    "headers": { "Authorization": "Bearer KEY" } } } }
```

## First things to try

- "What's due today?" (`nudges_due`)
- "Which roles am I suited for? My skills are Python, AWS, Kafka, SQL."
- "Here are my old resumes. Merge the best bullets."
- "Plan my prep. My interview is on the 20th, and I have 3 hours a day."
- "Show my finance dashboard and how long my runway is."

Client settings move around between releases. If a path above has changed,
search the client's docs for "MCP server".
