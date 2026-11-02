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
that supports MCP. Below, replace `URL` with your server's endpoint (it ends
in `/mcp`) and `KEY` with your API key.

**Two kinds of client:**

- **Desktop and IDE clients** (Claude Code, Claude Desktop, Cursor, VS
  Code, Gemini CLI, Windsurf) can send your key in an `Authorization`
  header. Use the configs below.
- **Web chat apps** (Claude.ai, ChatGPT) can't send custom headers. Connect
  them through the marketplace listing (MCPize), which gives you a URL tied
  to your subscription. OAuth support for direct web connections is on the
  roadmap.

## Claude Code

```
claude mcp add --transport http career-copilot URL --header "Authorization: Bearer KEY"
```

On Windows PowerShell, wrap commands containing `--` in `cmd /c "..."`.

## Claude Desktop

Settings → Developer → Edit Config, then add:

```json
{
  "mcpServers": {
    "career-copilot": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "URL", "--header", "Authorization: Bearer KEY"]
    }
  }
}
```

Needs Node.js. Restart Claude Desktop afterwards.

## Claude.ai (web and mobile)

Settings → Connectors → **Add custom connector** → paste your MCPize URL.
Then enable it in a chat from the tools menu.

## ChatGPT

Settings → Apps & Connectors → Advanced → turn on **Developer mode**. Then
**Create** a connector and paste your MCPize URL. Developer mode is
available on paid plans.

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
