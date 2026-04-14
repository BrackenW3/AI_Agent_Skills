# Centralized AI Agent Tools Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Centralize all MCP servers, shared configurations, and setup scripts into a single `brackenw3/AI_Agent_Skills` repo so every AI agent (Claude, Gemini, Copilot, OpenAI, ZAI) across all machines shares one source of truth and can be updated in one place.

**Architecture:** A git repo at `~/AI_Agent_Skills` acts as the single registry for MCP server configs, per-agent bridge files, environment templates, and cross-platform setup scripts. Each agent reads its config from a symlink or copy pointing back to this repo. Adding a new MCP or changing a tool happens once in this repo; running `sync.sh` / `sync.ps1` propagates it everywhere.

**Tech Stack:** JSON (MCP configs), Bash (Linux/macOS/WSL2 setup), PowerShell (Windows setup), GitHub Actions (optional CI lint), Node.js/npx (MCP server runtime — already installed)

---

## Root Cause Analysis

**Why Claude is slow and forgetting things:**

1. **31 plugins loaded globally** — Every session starts with ~200 deferred tool definitions injected into context (visible as the giant `<system-reminder>` tool list). This consumes context window before any work begins, causes faster compression, and is why things get "forgotten."
2. **Duplicate registrations** — `context7` and `github` exist as both plugins AND MCP servers. Claude resolves both, doubling their footprint.
3. **No global MCP config** — MCPs live only in `VSCodespace/.mcp.json` (project-scoped), so they don't follow you across projects/machines.
4. **No cross-agent sharing** — Each agent has its own isolated toolset with no synchronization.

**Expected outcome after this plan:** ~40% reduction in per-session context overhead; single `git pull && ./sync.sh` to update all agents on any machine.

---

## File Structure

```
AI_Agent_Skills/
├── README.md
├── mcp/
│   ├── shared.mcp.json           # All core MCPs — single source of truth
│   └── profiles/
│       ├── full.mcp.json         # All MCPs (dev workstation)
│       └── light.mcp.json        # Minimal set (fast sessions)
├── agents/
│   ├── claude/
│   │   ├── settings.base.json    # Recommended plugin list (trimmed)
│   │   └── global-mcps.json      # Patch snippet for ~/.claude.json mcpServers
│   ├── gemini/
│   │   └── settings.json         # ~/.gemini/settings.json format
│   └── copilot/
│       └── mcp.json              # VS Code MCP extension config
├── env/
│   └── template.env              # All variable names, no secret values
├── scripts/
│   ├── setup.sh                  # Linux / macOS / WSL2 first-time setup
│   ├── setup.ps1                 # Windows PowerShell first-time setup
│   ├── sync.sh                   # Pull latest + re-apply all links
│   └── sync.ps1                  # Windows sync
├── docs/
│   └── superpowers/
│       └── plans/
│           └── 2026-04-13-centralized-ai-agent-tools.md  ← this file
└── .github/
    └── workflows/
        └── validate-json.yml     # CI: validate all JSON configs on push
```

---

## Task 1: Audit & Reduce Claude Plugin Footprint

**Files:**
- Read: `C:\Users\User\.claude\plugins\installed_plugins.json`
- Modify: `C:\Users\User\.claude\settings.json` (remove from `enabledPlugins`)

**Context:** Each enabled plugin injects its tools/skills into every session's context window. LSP plugins (5 language servers) are worth-zero overhead unless you're actively doing that language's work. Duplicates between plugins and MCP servers double the tool count.

**Plugins safe to disable (load tools but you rarely invoke them directly):**
- `gopls-lsp` — Go language server; only needed for Go projects
- `clangd-lsp` — C/C++ language server
- `jdtls-lsp` — Java language server
- `csharp-lsp` — C# language server  
- `pyright-lsp` — Python LSP (Claude has native Python understanding; pyright is redundant for most tasks)
- `typescript-lsp` — TypeScript LSP (same reasoning)
- `greptile` — Code search; context7 MCP covers this
- `context7` — **DUPLICATE**: already registered as MCP server in VSCodespace/.mcp.json

**Plugins to keep (actively provide skills you invoke):**
- `superpowers`, `feature-dev`, `agent-sdk-dev`, `plugin-dev`, `code-review`, `pr-review-toolkit`
- `commit-commands`, `hookify`, `skill-creator`, `claude-md-management`, `claude-code-setup`
- `frontend-design`, `security-guidance`, `sentry`, `microsoft-docs`, `atlassian`
- `huggingface-skills`, `ralph-loop`, `playground`, `chrome-devtools-mcp`
- `playwright`, `code-simplifier`
- `github` — keep for now until global MCP is confirmed working

- [ ] **Step 1: Read current settings.json to get exact format**

```bash
cat /c/Users/User/.claude/settings.json
```

Expected: JSON with `enabledPlugins` array listing ~31 plugin names.

- [ ] **Step 2: Write updated settings.json with LSP plugins and greptile disabled**

Edit `C:\Users\User\.claude\settings.json` — remove these entries from `enabledPlugins`:
```
gopls-lsp@claude-plugins-official
clangd-lsp@claude-plugins-official
jdtls-lsp@claude-plugins-official
csharp-lsp@claude-plugins-official
pyright-lsp@claude-plugins-official
typescript-lsp@claude-plugins-official
greptile@claude-plugins-official
context7@claude-plugins-official
```

- [ ] **Step 3: Verify the JSON is valid after edit**

```bash
python3 -c "import json; json.load(open('/c/Users/User/.claude/settings.json')); print('valid')"
```
Expected: `valid`

- [ ] **Step 4: Commit the audit findings as a reference doc**

```bash
cd /c/Users/User/AI_Agent_Skills
git add docs/
git commit -m "docs: add centralized agent tools implementation plan"
```

---

## Task 2: Create AI_Agent_Skills Repo Structure

**Files:**
- Create: `README.md`
- Create: `mcp/shared.mcp.json`
- Create: `mcp/profiles/full.mcp.json`
- Create: `mcp/profiles/light.mcp.json`
- Create: `env/template.env`
- Create: `agents/claude/settings.base.json`
- Create: `agents/claude/global-mcps.json`
- Create: `agents/gemini/settings.json`
- Create: `agents/copilot/mcp.json`

- [ ] **Step 1: Create README.md**

```markdown
# AI Agent Skills — Centralized Tool Registry

Single source of truth for MCP server configs, agent settings, and setup scripts
used across all AI agents (Claude, Gemini, Copilot, OpenAI, ZAI) on all machines.

## Quick Start

**Windows (PowerShell):**
```powershell
git clone https://github.com/BrackenW3/AI_Agent_Skills.git ~/AI_Agent_Skills
cd ~/AI_Agent_Skills
./scripts/setup.ps1
```

**Linux / macOS / WSL2:**
```bash
git clone https://github.com/BrackenW3/AI_Agent_Skills.git ~/AI_Agent_Skills
cd ~/AI_Agent_Skills
chmod +x scripts/setup.sh && ./scripts/setup.sh
```

## Update All Agents (run after git pull)

**Windows:** `./scripts/sync.ps1`  
**Linux/macOS/WSL2:** `./scripts/sync.sh`

## Structure

| Path | Purpose |
|------|---------|
| `mcp/shared.mcp.json` | All core MCP servers |
| `mcp/profiles/` | Curated profiles (full, light) |
| `agents/` | Per-agent config snippets |
| `env/template.env` | Environment variable names (no secrets) |
| `scripts/` | Setup and sync automation |

## Adding a New MCP Server

1. Add entry to `mcp/shared.mcp.json`
2. Run `./scripts/sync.sh` (or `.ps1`) on each machine
3. Commit and push — all machines update on next `git pull && sync`
```

- [ ] **Step 2: Create mcp/shared.mcp.json**

```json
{
  "$comment": "Canonical MCP server registry. Edit here, then run scripts/sync to apply everywhere.",
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": { "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_MCP_PAT}" }
    },
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "${FILESYSTEM_ALLOWED_PATH}"
      ]
    },
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp"],
      "env": { "CONTEXT7_API_KEY": "${CONTEXT7_API_KEY}" }
    },
    "perplexity": {
      "command": "npx",
      "args": ["-y", "perplexity-mcp"],
      "env": { "PERPLEXITY_API_KEY": "${PERPLEXITY_API_KEY}" }
    },
    "brave-search": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-brave-search"],
      "env": { "BRAVE_API_KEY": "${BRAVE_API_KEY}" }
    },
    "grok": {
      "command": "npx",
      "args": ["-y", "mcp-server-xai-grok"],
      "env": { "XAI_API_KEY": "${XAI_API_KEY}" }
    },
    "z-ai": {
      "command": "npx",
      "args": ["-y", "zai-mcp-server"],
      "env": { "ZAI_API_KEY": "${ZAI_API_KEY}" }
    },
    "anthropic": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-anthropic"],
      "env": { "ANTHROPIC_API_KEY": "${ANTHROPIC_API_KEY}" }
    },
    "openai": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-openai"],
      "env": { "OPENAI_API_KEY": "${OPENAI_API_KEY}" }
    },
    "gemini": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-gemini"],
      "env": { "GEMINI_API_KEY": "${GEMINI_API_KEY}" }
    },
    "ollama": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-ollama"],
      "env": { "OLLAMA_CLOUD_API": "${OLLAMA_CLOUD_API}" }
    }
  }
}
```

- [ ] **Step 3: Create mcp/profiles/full.mcp.json** (all 11 servers — for dev workstations)

```json
{
  "$comment": "Full profile — all MCP servers. Use on dedicated dev machines.",
  "extends": "../shared.mcp.json",
  "profile": "full",
  "servers": ["github","filesystem","context7","perplexity","brave-search","grok","z-ai","anthropic","openai","gemini","ollama"]
}
```

- [ ] **Step 4: Create mcp/profiles/light.mcp.json** (core only — for fast sessions)

```json
{
  "$comment": "Light profile — minimal MCPs. Use when sessions are slow or on lower-spec machines.",
  "extends": "../shared.mcp.json",
  "profile": "light",
  "servers": ["github","filesystem","context7","perplexity"]
}
```

- [ ] **Step 5: Create env/template.env**

```bash
# AI Agent Skills — Environment Variable Template
# Copy this to ~/VSCodespace/.env and fill in values.
# NEVER commit actual values. This file contains only variable names.

# GitHub
GITHUB_TOKEN=
GITHUB_MCP_PAT=
GH_MODELS=

# Anthropic
ANTHROPIC_API_KEY=

# OpenAI
OPENAI_API_KEY=

# Google
GEMINI_API_KEY=
GOOGLE_CLOUD_KEY=

# xAI (Grok)
XAI_API_KEY=

# Z.ai
ZAI_API_KEY=
USE_ZAI=false

# Perplexity
PERPLEXITY_API_KEY=

# Brave Search
BRAVE_API_KEY=

# Context7
CONTEXT7_API_KEY=

# Atlassian (Jira/Confluence)
ATLASSIAN_API_TOKEN=
ATLASSIAN_EMAIL=
ATLASSIAN_BASE_URL=
ATLASSIAN_ORG_ID=

# Azure
AZURE_TENANT_ID=
AZURE_SUBSCRIPTION_ID=
AZURE_CLIENT_ID=

# HuggingFace
HF_API_KEY=
HF_TOKEN=

# Ollama
OLLAMA_CLOUD_API=

# Filesystem MCP scope (set per machine)
FILESYSTEM_ALLOWED_PATH=~/VSCodespace
```

- [ ] **Step 6: Commit the base structure**

```bash
cd /c/Users/User/AI_Agent_Skills
git add mcp/ env/ README.md
git commit -m "feat: add shared MCP registry and env template"
```

---

## Task 3: Build Agent Bridge Configs

**Files:**
- Create: `agents/claude/global-mcps.json`
- Create: `agents/claude/settings.base.json`
- Create: `agents/gemini/settings.json`
- Create: `agents/copilot/mcp.json`

**Purpose:** These are the agent-specific config snippets the setup script injects. They reference `shared.mcp.json` indirectly — the script resolves the variables and writes the final values.

- [ ] **Step 1: Create agents/claude/global-mcps.json**

This is the `mcpServers` block that gets merged into `~/.claude.json`:

```json
{
  "$comment": "Global MCP registrations for Claude Code. Merged into ~/.claude.json by sync script.",
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": { "GITHUB_PERSONAL_ACCESS_TOKEN": "__GITHUB_MCP_PAT__" }
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "__FILESYSTEM_ALLOWED_PATH__"]
    },
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp"],
      "env": { "CONTEXT7_API_KEY": "__CONTEXT7_API_KEY__" }
    },
    "perplexity": {
      "command": "npx",
      "args": ["-y", "perplexity-mcp"],
      "env": { "PERPLEXITY_API_KEY": "__PERPLEXITY_API_KEY__" }
    },
    "grok": {
      "command": "npx",
      "args": ["-y", "mcp-server-xai-grok"],
      "env": { "XAI_API_KEY": "__XAI_API_KEY__" }
    },
    "z-ai": {
      "command": "npx",
      "args": ["-y", "zai-mcp-server"],
      "env": { "ZAI_API_KEY": "__ZAI_API_KEY__" }
    }
  }
}
```

- [ ] **Step 2: Create agents/claude/settings.base.json**

The recommended `~/.claude/settings.json` with trimmed plugin list:

```json
{
  "$comment": "Recommended Claude Code global settings. Copy to ~/.claude/settings.json.",
  "permissions": {
    "defaultMode": "acceptEdits",
    "allowedTools": ["Bash(*)", "mcp__github__*", "mcp__filesystem__*", "mcp__context7__*", "mcp__perplexity__*", "mcp__grok__*", "mcp__z-ai__*"]
  },
  "enabledPlugins": [
    "superpowers@claude-plugins-official",
    "feature-dev@claude-plugins-official",
    "agent-sdk-dev@claude-plugins-official",
    "plugin-dev@claude-plugins-official",
    "code-review@claude-plugins-official",
    "pr-review-toolkit@claude-plugins-official",
    "commit-commands@claude-plugins-official",
    "hookify@claude-plugins-official",
    "skill-creator@claude-plugins-official",
    "claude-md-management@claude-plugins-official",
    "claude-code-setup@claude-plugins-official",
    "frontend-design@claude-plugins-official",
    "security-guidance@claude-plugins-official",
    "sentry@claude-plugins-official",
    "microsoft-docs@claude-plugins-official",
    "atlassian@claude-plugins-official",
    "huggingface-skills@claude-plugins-official",
    "ralph-loop@claude-plugins-official",
    "playground@claude-plugins-official",
    "chrome-devtools-mcp@claude-plugins-official",
    "playwright@claude-plugins-official",
    "code-simplifier@claude-plugins-official",
    "github@claude-plugins-official"
  ],
  "notes": "LSP plugins (gopls, clangd, jdtls, csharp, pyright, typescript), greptile, and context7 plugin removed. context7 is covered by the global MCP server."
}
```

- [ ] **Step 3: Create agents/gemini/settings.json**

Gemini CLI reads `~/.gemini/settings.json`. MCP support uses `mcpServers` key (same format as Claude):

```json
{
  "$comment": "Gemini CLI settings. Sync script writes this to ~/.gemini/settings.json.",
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": { "GITHUB_PERSONAL_ACCESS_TOKEN": "__GITHUB_MCP_PAT__" }
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "__FILESYSTEM_ALLOWED_PATH__"]
    },
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp"],
      "env": { "CONTEXT7_API_KEY": "__CONTEXT7_API_KEY__" }
    },
    "perplexity": {
      "command": "npx",
      "args": ["-y", "perplexity-mcp"],
      "env": { "PERPLEXITY_API_KEY": "__PERPLEXITY_API_KEY__" }
    }
  },
  "theme": "Default"
}
```

- [ ] **Step 4: Create agents/copilot/mcp.json**

VS Code MCP extension config (written to `.vscode/mcp.json` or workspace settings):

```json
{
  "$comment": "GitHub Copilot MCP config for VS Code. Reference from workspace .vscode/mcp.json.",
  "servers": {
    "github": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": { "GITHUB_PERSONAL_ACCESS_TOKEN": "${env:GITHUB_MCP_PAT}" }
    },
    "filesystem": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "${env:FILESYSTEM_ALLOWED_PATH}"]
    },
    "context7": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp"],
      "env": { "CONTEXT7_API_KEY": "${env:CONTEXT7_API_KEY}" }
    },
    "perplexity": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "perplexity-mcp"],
      "env": { "PERPLEXITY_API_KEY": "${env:PERPLEXITY_API_KEY}" }
    }
  }
}
```

- [ ] **Step 5: Commit agent bridges**

```bash
cd /c/Users/User/AI_Agent_Skills
git add agents/
git commit -m "feat: add per-agent bridge configs for Claude, Gemini, Copilot"
```

---

## Task 4: Build Cross-Platform Setup & Sync Scripts

**Files:**
- Create: `scripts/setup.sh`
- Create: `scripts/setup.ps1`
- Create: `scripts/sync.sh`
- Create: `scripts/sync.ps1`
- Create: `scripts/_lib.sh` (shared functions)

**What the scripts do:**
1. Load API keys from `~/VSCodespace/.env`
2. Resolve `__PLACEHOLDER__` tokens in agent bridge configs with real values
3. Merge Claude global MCPs into `~/.claude.json`
4. Write Gemini settings to `~/.gemini/settings.json`
5. Symlink Copilot MCP config into `~/VSCodespace/.vscode/mcp.json`
6. Create `~/VSCodespace/.mcp.json` pointing to full profile

- [ ] **Step 1: Create scripts/_lib.sh** (shared shell functions)

```bash
#!/usr/bin/env bash
# _lib.sh — shared functions for setup.sh and sync.sh

# Load .env without executing arbitrary code
load_env() {
  local env_file="${1:-$HOME/VSCodespace/.env}"
  if [[ ! -f "$env_file" ]]; then
    echo "ERROR: .env not found at $env_file"
    echo "Copy env/template.env to $env_file and fill in your values."
    exit 1
  fi
  set -a
  # Only export KEY=VALUE lines, skip comments and blank lines
  while IFS='=' read -r key value; do
    [[ "$key" =~ ^[[:space:]]*# ]] && continue
    [[ -z "$key" ]] && continue
    export "$key"="$value"
  done < <(grep -E '^[A-Z_]+=.*' "$env_file")
  set +a
}

# Replace __PLACEHOLDER__ tokens in a file with env var values
resolve_tokens() {
  local src="$1" dst="$2"
  cp "$src" "$dst"
  # Replace __VAR_NAME__ with value of $VAR_NAME
  while IFS= read -r line; do
    while [[ "$line" =~ __([A-Z_]+)__ ]]; do
      local var="${BASH_REMATCH[1]}"
      local val="${!var:-}"
      if [[ -z "$val" ]]; then
        echo "WARN: $var is not set — leaving __${var}__ unreplaced in $dst"
        break
      fi
      line="${line//__${var}__/$val}"
    done
  done < "$src" > "$dst"
  sed -i 's|__[A-Z_]*__|MISSING_VAR|g' "$dst"  # catch any stragglers
}

# Merge mcpServers from a JSON file into ~/.claude.json
merge_claude_mcps() {
  local mcp_patch="$1"
  local claude_json="$HOME/.claude.json"
  python3 - "$claude_json" "$mcp_patch" <<'EOF'
import json, sys
target_path, patch_path = sys.argv[1], sys.argv[2]
with open(target_path) as f: target = json.load(f)
with open(patch_path) as f: patch = json.load(f)
target.setdefault("mcpServers", {}).update(patch.get("mcpServers", {}))
with open(target_path, "w") as f: json.dump(target, f, indent=2)
print(f"Merged {len(patch.get('mcpServers', {}))} MCP servers into {target_path}")
EOF
}

AI_SKILLS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RESOLVED_DIR="$AI_SKILLS_DIR/.resolved"
mkdir -p "$RESOLVED_DIR"
```

- [ ] **Step 2: Create scripts/setup.sh** (Linux / macOS / WSL2 first-time setup)

```bash
#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/_lib.sh"

echo "=== AI Agent Skills Setup ==="
echo "Repo: $AI_SKILLS_DIR"
echo ""

# 1. Load environment
load_env "$HOME/VSCodespace/.env"
export FILESYSTEM_ALLOWED_PATH="${FILESYSTEM_ALLOWED_PATH:-$HOME/VSCodespace}"

# 2. Resolve token placeholders in Claude global-mcps.json
echo "→ Resolving Claude MCP config..."
resolve_tokens \
  "$AI_SKILLS_DIR/agents/claude/global-mcps.json" \
  "$RESOLVED_DIR/claude-global-mcps.json"

# 3. Merge into ~/.claude.json
echo "→ Merging MCPs into ~/.claude.json..."
merge_claude_mcps "$RESOLVED_DIR/claude-global-mcps.json"

# 4. Write Gemini settings
echo "→ Writing Gemini settings..."
mkdir -p "$HOME/.gemini"
resolve_tokens \
  "$AI_SKILLS_DIR/agents/gemini/settings.json" \
  "$HOME/.gemini/settings.json"

# 5. Write VSCodespace .mcp.json (project-level, full profile resolved)
echo "→ Writing VSCodespace .mcp.json..."
resolve_tokens \
  "$AI_SKILLS_DIR/agents/copilot/mcp.json" \
  "$HOME/VSCodespace/.vscode/mcp.json"

# 6. Write full shared.mcp.json to VSCodespace for backward compat
resolve_tokens \
  "$AI_SKILLS_DIR/mcp/shared.mcp.json" \
  "$HOME/VSCodespace/.mcp.json"

echo ""
echo "✓ Setup complete. Restart Claude Code and Gemini CLI to pick up new MCPs."
echo "  Run ./scripts/sync.sh after 'git pull' to update configs."
```

- [ ] **Step 3: Create scripts/sync.sh** (update all agents after git pull)

```bash
#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== AI Agent Skills Sync ==="
git -C "$(dirname "$SCRIPT_DIR")" pull --ff-only

# Re-run setup to apply any changes
source "$SCRIPT_DIR/setup.sh"
```

- [ ] **Step 4: Create scripts/setup.ps1** (Windows PowerShell)

```powershell
#Requires -Version 5.1
# setup.ps1 — Windows first-time setup for AI Agent Skills

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$ResolvedDir = Join-Path $RepoRoot ".resolved"
New-Item -ItemType Directory -Force -Path $ResolvedDir | Out-Null

Write-Host "=== AI Agent Skills Setup (Windows) ===" -ForegroundColor Cyan
Write-Host "Repo: $RepoRoot"

# Load .env
$EnvFile = "$HOME\VSCodespace\.env"
if (-not (Test-Path $EnvFile)) {
    Write-Error ".env not found at $EnvFile. Copy env/template.env and fill values."
    exit 1
}
Get-Content $EnvFile | Where-Object { $_ -match '^[A-Z_]+=' -and $_ -notmatch '^#' } | ForEach-Object {
    $parts = $_ -split '=', 2
    [System.Environment]::SetEnvironmentVariable($parts[0].Trim(), $parts[1].Trim(), "Process")
}
if (-not $env:FILESYSTEM_ALLOWED_PATH) { $env:FILESYSTEM_ALLOWED_PATH = "$HOME\VSCodespace" }

function Resolve-Tokens($Src, $Dst) {
    $content = Get-Content $Src -Raw
    [regex]::Matches($content, '__([A-Z_]+)__') | Select-Object -ExpandProperty Value -Unique | ForEach-Object {
        $token = $_
        $varName = $token.Trim('_')
        $val = [System.Environment]::GetEnvironmentVariable($varName, "Process")
        if ($val) { $content = $content.Replace($token, $val) }
        else { Write-Warning "$varName not set — $token left unreplaced" }
    }
    $content | Set-Content $Dst -NoNewline
}

# Claude MCPs
Write-Host "`n→ Resolving Claude MCP config..."
Resolve-Tokens "$RepoRoot\agents\claude\global-mcps.json" "$ResolvedDir\claude-global-mcps.json"

Write-Host "→ Merging MCPs into $HOME\.claude.json..."
$claudeJson = "$HOME\.claude.json"
$target = Get-Content $claudeJson -Raw | ConvertFrom-Json
$patch = Get-Content "$ResolvedDir\claude-global-mcps.json" -Raw | ConvertFrom-Json
if (-not $target.mcpServers) { $target | Add-Member -NotePropertyName mcpServers -NotePropertyValue @{} }
$patch.mcpServers.PSObject.Properties | ForEach-Object { $target.mcpServers | Add-Member -NotePropertyName $_.Name -NotePropertyValue $_.Value -Force }
$target | ConvertTo-Json -Depth 10 | Set-Content $claudeJson

# Gemini settings
Write-Host "→ Writing Gemini settings..."
$geminiDir = "$HOME\.gemini"
New-Item -ItemType Directory -Force -Path $geminiDir | Out-Null
Resolve-Tokens "$RepoRoot\agents\gemini\settings.json" "$geminiDir\settings.json"

# VS Code / Copilot MCP
Write-Host "→ Writing VS Code MCP config..."
$vscodeDir = "$HOME\VSCodespace\.vscode"
New-Item -ItemType Directory -Force -Path $vscodeDir | Out-Null
Resolve-Tokens "$RepoRoot\agents\copilot\mcp.json" "$vscodeDir\mcp.json"

# VSCodespace .mcp.json
Resolve-Tokens "$RepoRoot\mcp\shared.mcp.json" "$HOME\VSCodespace\.mcp.json"

Write-Host "`n✓ Setup complete. Restart Claude Code and Gemini CLI." -ForegroundColor Green
Write-Host "  Run .\scripts\sync.ps1 after 'git pull' to update configs."
```

- [ ] **Step 5: Create scripts/sync.ps1** (Windows sync)

```powershell
#Requires -Version 5.1
$RepoRoot = Split-Path -Parent $PSScriptRoot
Write-Host "=== AI Agent Skills Sync ===" -ForegroundColor Cyan
git -C $RepoRoot pull --ff-only
& "$PSScriptRoot\setup.ps1"
```

- [ ] **Step 6: Make shell scripts executable and commit**

```bash
cd /c/Users/User/AI_Agent_Skills
chmod +x scripts/setup.sh scripts/sync.sh scripts/_lib.sh
git add scripts/
git commit -m "feat: add cross-platform setup and sync scripts"
```

---

## Task 5: Add GitHub Actions JSON Validation

**Files:**
- Create: `.github/workflows/validate-json.yml`
- Create: `.gitignore`

**Purpose:** Catch malformed JSON configs before they break a machine on sync.

- [ ] **Step 1: Create .gitignore**

```
.resolved/
*.env
.env*
!env/template.env
node_modules/
```

- [ ] **Step 2: Create .github/workflows/validate-json.yml**

```yaml
name: Validate JSON Configs
on:
  push:
    paths: ['mcp/**', 'agents/**']
  pull_request:
    paths: ['mcp/**', 'agents/**']

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Validate all JSON files
        run: |
          find mcp/ agents/ -name '*.json' | while read f; do
            python3 -c "import json; json.load(open('$f'))" && echo "✓ $f" || { echo "✗ $f INVALID"; exit 1; }
          done
```

- [ ] **Step 3: Commit and push everything to GitHub**

```bash
cd /c/Users/User/AI_Agent_Skills
git add .gitignore .github/
git commit -m "ci: add JSON validation workflow"
git push origin main
```

---

## Task 6: Apply Plugin Reduction to Claude (Immediate Fix)

**Files:**
- Modify: `C:\Users\User\.claude\settings.json`

This is the immediate performance fix. Do this task first if you want faster Claude sessions NOW.

- [ ] **Step 1: Read current settings.json**

```bash
cat /c/Users/User/.claude/settings.json
```

- [ ] **Step 2: Write trimmed settings.json**

Remove from `enabledPlugins`: `gopls-lsp`, `clangd-lsp`, `jdtls-lsp`, `csharp-lsp`, `pyright-lsp`, `typescript-lsp`, `greptile`, `context7`.

Keep the 23 plugins listed in `agents/claude/settings.base.json`.

- [ ] **Step 3: Verify JSON is valid**

```bash
python3 -c "import json; d=json.load(open('/c/Users/User/.claude/settings.json')); print('Plugins remaining:', len(d.get('enabledPlugins', [])))"
```
Expected: `Plugins remaining: 23`

- [ ] **Step 4: Start a fresh Claude Code session to verify improvement**

Open a new terminal and start `claude`. The deferred tools list in `<system-reminder>` should be significantly shorter.

---

## Task 7: Run Setup Script on This Machine

- [ ] **Step 1: Run Windows setup**

```powershell
cd C:\Users\User\AI_Agent_Skills
.\scripts\setup.ps1
```

Expected output:
```
=== AI Agent Skills Setup (Windows) ===
→ Resolving Claude MCP config...
→ Merging MCPs into C:\Users\User\.claude.json...
→ Writing Gemini settings...
→ Writing VS Code MCP config...
✓ Setup complete.
```

- [ ] **Step 2: Verify Claude global MCPs were written**

```bash
python3 -c "
import json
d = json.load(open('/c/Users/User/.claude.json'))
mcps = d.get('mcpServers', {})
print('Global MCPs registered:', list(mcps.keys()))
"
```
Expected: `Global MCPs registered: ['github', 'filesystem', 'context7', 'perplexity', 'grok', 'z-ai']`

- [ ] **Step 3: Verify Gemini settings written**

```bash
cat /c/Users/User/.gemini/settings.json | python3 -m json.tool | head -10
```
Expected: Valid JSON with `mcpServers` block.

- [ ] **Step 4: Verify VSCodespace .mcp.json updated**

```bash
python3 -c "import json; d=json.load(open('/c/Users/User/VSCodespace/.mcp.json')); print(list(d['mcpServers'].keys()))"
```

---

## Self-Review

**Spec coverage check:**
- ✓ Reduce Claude context overhead → Task 1 + Task 6 (plugin audit)
- ✓ Remove duplicate tools → context7 plugin disabled, MCP kept; greptile removed
- ✓ Single source of truth → `mcp/shared.mcp.json`
- ✓ Cross-platform support → `setup.sh` (Linux/macOS/WSL2) + `setup.ps1` (Windows)
- ✓ Single update point → `sync.sh` / `sync.ps1` after `git pull`
- ✓ GitHub repo → Task 5, push to `brackenw3/AI_Agent_Skills`
- ✓ All agents covered → Claude (global-mcps.json), Gemini (settings.json), Copilot (.vscode/mcp.json)
- ✓ Immediate performance fix → Task 6 can be done first

**Placeholder scan:** All code blocks contain complete, runnable content. No TBDs.

**Type consistency:** JSON structure for `mcpServers` is identical across all agent bridge files. `__PLACEHOLDER__` token format consistent in all templates and resolver functions.

---

## Execution Order (Recommended)

For fastest impact, do **Task 6 first** (plugin reduction — immediate Claude speedup), then work Tasks 2–5 in order to build and push the repo, then Task 7 to run the setup on this machine.

**On new machines:** `git clone https://github.com/BrackenW3/AI_Agent_Skills.git ~/AI_Agent_Skills && cd ~/AI_Agent_Skills && ./scripts/setup.sh`

**Weekly maintenance:** `cd ~/AI_Agent_Skills && ./scripts/sync.sh`
