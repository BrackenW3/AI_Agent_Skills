# AI Agent Skills

Secret-free MCP templates and sync helpers — the single source of truth for MCP server configurations shared across Claude, Gemini, Copilot, JetBrains, and ZAI agents on Windows, Linux, macOS, and WSL2.

## Goals

- **Standardize** AI agent MCP configs so they work consistently across platforms and agents
- **Reduce duplication** — write once, use everywhere
- **Keep secrets out** — all templates use `${VAR}` placeholders resolved at sync time from your local `.env`
- **Centralize configuration** with agent-specific templates derived from a single shared registry

## Quick Start

```bash
git clone https://github.com/WillBracken/AI_Agent_Skills.git ~/AI_Agent_Skills
cp ~/AI_Agent_Skills/env/template.env ~/VSCodespace/.env

# Windows (PowerShell)
~/AI_Agent_Skills/scripts/sync.ps1

# Linux / macOS / WSL2 (Bash)
bash ~/AI_Agent_Skills/scripts/sync.sh
```

The sync scripts read `~/VSCodespace/.env`, resolve all `${VAR}` placeholders, and write live configs for every supported agent.

## Platform Profiles

Sync scripts auto-detect your platform and apply the right profile. You can override with `--profile`:

| Platform | MCP Profile | Plugin Profile | Auto-detected? |
|----------|-------------|----------------|----------------|
| Windows (full workstation) | `windows-full` | `settings.base.json` | ✓ via sync.ps1 |
| macOS | `macos` | `settings.macos.json` | ✓ |
| Linux / Ubuntu | `linux` | `settings.thin.json` | ✓ |
| WSL2 | `linux` | `settings.thin.json` | ✓ |
| Docker | `docker` | `settings.thin.json` | ✓ |

**Override profile:**
```bash
bash scripts/sync.sh --profile macos          # force macOS profile
.\scripts\sync.ps1 -Profile windows-full     # force Windows full profile
```

**MCP profiles** (in `mcp/profiles/`):
- `windows-full` — github, filesystem, context7, perplexity, grok, brave-search, azure, jira
- `macos` — github, filesystem, context7, perplexity, grok, brave-search
- `linux` — github, filesystem, context7, perplexity, grok
- `docker` — github, filesystem, context7 (minimal)
- `zai-optional` — add to project `.mcp.json` when you need Z.ai tools

**Plugin profiles** (in `agents/claude/`):
- `settings.base.json` — 23 plugins (full workstation)
- `settings.macos.json` — 15 plugins (macOS, no Windows-specific)
- `settings.thin.json` — 14 plugins (laptop/VM/Docker, minimal)

## Repository Structure

```
AI_Agent_Skills/
├── mcp/
│   └── shared.mcp.json          # Canonical MCP server registry (9 servers)
├── env/
│   └── template.env             # Required env variable names and aliases
│   └── repository-bootstrap.json # Repo secret/variable inventory + default repo list
├── agents/
│   ├── claude/
│   │   ├── global-mcps.template.json    # Claude ~/.claude.json mcpServers block
│   │   └── settings.base.json           # Recommended ~/.claude/settings.json
│   ├── copilot/
│   │   └── mcp.template.json            # Copilot / VS Code .mcp.json
│   ├── gemini/
│   │   └── settings.patch.template.json # Gemini ~/.gemini/settings.json patch
│   └── jetbrains/
│       └── llm.mcpServers.template.xml  # JetBrains llm.mcpServers.xml
├── scripts/
│   ├── sync.ps1                 # Windows PowerShell sync script
│   └── sync.sh                  # Linux / macOS / WSL2 Bash sync script
├── skills/                      # Agent-specific and shared skill definitions
├── tools/                       # Additional tool configurations
├── config/                      # Service-specific config templates
└── docs/                        # Setup guides and documentation
```

## Key Directories

| Path | Description |
|------|-------------|
| `mcp/shared.mcp.json` | Canonical registry — edit here first |
| `env/template.env` | Lists every required env variable |
| `env/repository-bootstrap.json` | Lists GitHub repo variables/secrets mirrored across repos |
| `agents/` | Per-agent templates (Claude, Copilot, Gemini, JetBrains) |
| `scripts/sync.ps1` | Windows sync — writes live configs from templates |
| `scripts/sync.sh` | Linux/macOS/WSL2 sync — same logic in Bash |
| `scripts/populate-repo-settings.py` | Pushes shared variables/secrets into one or more GitHub repos |

## Secrets & Environment Variables

All secret values are stored in `~/VSCodespace/.env` (gitignored). The templates reference them as `${VAR_NAME}` and are safe to commit. See `env/template.env` for the full list of required variables.

**Never commit `.env` files or secret literals to this repository.**

## Repository Bootstrap

Use the canonical inventory in `env/repository-bootstrap.json` to mirror shared GitHub Actions variables/secrets into every repo:

```bash
# Preview updates for all known repos
python3 scripts/populate-repo-settings.py --all-default-repos --dry-run

# Populate a single new repo
python3 scripts/populate-repo-settings.py --repo NewRepoName
```

The repository also includes a `Populate Repository Settings` workflow for manual runs or `repository_dispatch` automation when a new repo is created.

## Supported Agents

| Agent | Template | Live Config Written |
|-------|----------|---------------------|
| Claude Code | `agents/claude/global-mcps.template.json` | `~/.claude.json` |
| GitHub Copilot | `agents/copilot/mcp.template.json` | `~/VSCodespace/.mcp.json`, `.vscode/mcp.json` |
| Google Gemini | `agents/gemini/settings.patch.template.json` | `~/.gemini/settings.json` |
| JetBrains | `agents/jetbrains/llm.mcpServers.template.xml` | `~/.config/JetBrains/PyCharm*/options/llm.mcpServers.xml` |
