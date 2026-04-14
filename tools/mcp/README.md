# Model Context Protocol (MCP) Configurations

[MCP (Model Context Protocol)](https://modelcontextprotocol.io/) is an open standard that lets AI models connect to external tools, APIs, and data sources consistently.

## What is MCP?

MCP servers expose **resources** (data) and **tools** (actions) to AI clients. Supported AI platforms include:

| Platform | MCP Support |
|----------|-------------|
| Claude (Anthropic) | ✅ Native |
| GitHub Copilot | ✅ VS Code extension |
| OpenAI | ✅ Via assistants API |
| Gemini | 🔄 In progress |
| Ollama | 🔄 Community support |
| Mistral | 🔄 In progress |
| ZAI | 🔄 In progress |

## MCP Server Registry

Add MCP server configurations below. Each entry represents a server that can be used by AI agents in this repository.

```json
{
  "mcpServers": {
    "example-server": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-example"],
      "env": {
        "EXAMPLE_API_KEY": "${EXAMPLE_API_KEY}"
      }
    }
  }
}
```

## Configuration File Locations

| Platform | MCP Config Location |
|----------|---------------------|
| VS Code (Claude Dev / Cline) | `.vscode/mcp.json` or settings |
| Claude Desktop | `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) |
| Claude Desktop (Windows) | `%APPDATA%\Claude\claude_desktop_config.json` |
| Cursor | `.cursor/mcp.json` |

## Available MCP Servers

| Server | Purpose | Package |
|--------|---------|---------|
| *(add MCP servers here)* | | |

## Adding a New MCP Server

1. Add a subdirectory under `tools/mcp/<server-name>/`
2. Include a `README.md` with setup instructions
3. Include a `config.template.json` with placeholder values (no real credentials)
4. Document which AI platforms support this server

## Security

- **Never** commit MCP config files containing real API keys
- Use environment variable substitution (e.g. `${MY_API_KEY}`) in config files
- Real credentials go in `.env` files that are gitignored
