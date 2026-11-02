"""How to connect each AI client. URL and KEY are placeholders."""

CLIENTS = {
    "claude_code": {
        "name": "Claude Code",
        "how": 'claude mcp add --transport http career-copilot URL '
               '--header "Authorization: Bearer KEY"'},
    "claude_desktop": {
        "name": "Claude Desktop",
        "how": 'In claude_desktop_config.json: {"mcpServers": '
               '{"career-copilot": {"command": "npx", "args": ["-y", '
               '"mcp-remote", "URL", "--header", '
               '"Authorization: Bearer KEY"]}}}'},
    "claude_web": {
        "name": "Claude.ai (web and mobile)",
        "how": "Settings > Connectors > Add custom connector > paste the "
               "marketplace URL. Web connectors can't send custom headers, "
               "so use a URL from the marketplace gateway that carries "
               "your subscription."},
    "chatgpt": {
        "name": "ChatGPT",
        "how": "Settings > Apps & Connectors > Advanced > Developer mode, "
               "then Create > paste the marketplace URL. Same header "
               "limitation as Claude.ai."},
    "muse": {
        "name": "Muse (Meta)",
        "how": "Add a connector in Muse and paste the marketplace URL. To "
               "let Muse hand tasks to a Claude Code session on your "
               "computer, also add the Reason Network connector."},
    "cursor": {
        "name": "Cursor",
        "how": '~/.cursor/mcp.json: {"mcpServers": {"career-copilot": '
               '{"url": "URL", "headers": {"Authorization": '
               '"Bearer KEY"}}}}'},
    "vscode": {
        "name": "VS Code (GitHub Copilot agent mode)",
        "how": '.vscode/mcp.json: {"servers": {"career-copilot": '
               '{"type": "http", "url": "URL", "headers": '
               '{"Authorization": "Bearer KEY"}}}}'},
    "gemini_cli": {
        "name": "Gemini CLI",
        "how": '~/.gemini/settings.json: {"mcpServers": {"career-copilot": '
               '{"httpUrl": "URL", "headers": {"Authorization": '
               '"Bearer KEY"}}}}'},
    "windsurf": {
        "name": "Windsurf",
        "how": '~/.codeium/windsurf/mcp_config.json: {"mcpServers": '
               '{"career-copilot": {"serverUrl": "URL", "headers": '
               '{"Authorization": "Bearer KEY"}}}}'},
}
