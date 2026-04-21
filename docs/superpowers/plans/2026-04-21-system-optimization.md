# System Optimization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix Claude Code slowdowns, MCP disconnects, missing Claude Desktop tools, disorganized SSH, cluttered VSCode, and enable cross-machine AI config sync via AI_Agent_Skills repo.

**Architecture:** Config-only changes — no new application code. Each task modifies one file and verifies the result. The AI_Agent_Skills repo becomes the single source of truth synced to all agents on any machine.

**Tech Stack:** PowerShell, Bash, JSON/JSONC config files, OpenSSH, VSCode settings API

---

## File Map

| File | Action | Purpose |
|------|--------|---------|
| `C:/Users/User/.claude/settings.json` | Modify | Remove 19 GitKraken hooks → immediate Claude Code speedup |
| `C:/Users/User/AppData/Roaming/Code/User/mcp.json` | Modify | Remove dead MCPs, deduplicate, fix disconnects |
| `C:/Users/User/AppData/Roaming/Claude/claude_desktop_config.json` | Modify | Populate empty mcpServers for Claude App |
| `C:/Users/User/.ssh/config` | Create | Named host aliases for Docker, WSL, local VSCode |
| `C:/Users/User/.ssh/id_ed25519_vscode` | Create | Key for VSCode-to-VSCode local connections |
| `C:/Users/User/AppData/Roaming/Code/User/keybindings.json` | Modify | Add AI agent panel + GitHub right-sidebar shortcuts |
| `C:/Users/User/AppData/Roaming/Code/User/settings.json` | Modify | Add iCloudDrive to watcherExclude, GitLens solo tweaks |
| `C:/Users/User/AppData/Roaming/Code/User/profiles/3003a964/settings.json` | Create | Named profile settings |
| `C:/Users/User/AppData/Roaming/Code/User/profiles/-eef08c8/settings.json` | Create | Named profile settings |
| `C:/Users/User/AI_Agent_Skills/scripts/sync.ps1` | Modify | Add Claude Desktop config as sync output target |
| `C:/Users/User/AI_Agent_Skills/agents/claude-desktop/` | Create | Claude Desktop MCP template |

---

## Task 1: Remove GitKraken Hooks — Immediate Claude Code Speedup

**Files:**
- Modify: `C:/Users/User/.claude/settings.json` (hooks section, lines 44–286)

**Why this is critical:** The `hooks` section registers `gk.exe ai hook run --host claude-code` on all 19 event types. Every tool call fires PreToolUse + PostToolUse = 2 gk.exe spawns. At high effort with subagents, that's 30–60+ process spawns per minute. gk.exe uses Node.js/Electron internally, explaining the 50+ Node processes.

- [ ] **Step 1: Back up current settings**

```bash
cp "C:/Users/User/.claude/settings.json" "C:/Users/User/.claude/settings.json.bak-$(date +%Y%m%d)"
```

- [ ] **Step 2: Remove the entire hooks section from settings.json**

Open `C:/Users/User/.claude/settings.json` and delete the entire `"hooks": { ... }` block (lines 44–286). The resulting file keeps `env`, `permissions`, `enabledPlugins`, `extraKnownMarketplaces`, `forceLoginMethod`, `effortLevel`, `autoUpdatesChannel` — nothing else changes.

- [ ] **Step 3: Verify hooks are gone**

```bash
python3 -c "
import json
with open('C:/Users/User/.claude/settings.json') as f:
    d = json.load(f)
print('hooks present:', 'hooks' in d)
print('keys:', list(d.keys()))
"
```

Expected output:
```
hooks present: False
keys: ['env', 'permissions', 'enabledPlugins', 'extraKnownMarketplaces', 'forceLoginMethod', 'effortLevel', 'autoUpdatesChannel']
```

- [ ] **Step 4: Verify settings.json is valid JSON**

```bash
python3 -m json.tool "C:/Users/User/.claude/settings.json" > /dev/null && echo "VALID" || echo "INVALID"
```

Expected: `VALID`

- [ ] **Step 5: Commit**

```bash
cd "C:/Users/User/AI_Agent_Skills"
git add -A
git commit -m "fix: document hooks removal from claude settings — primary perf fix"
```

**To re-enable GitKraken hooks later:** Run `gk ai hook install --host claude-code` and select only the events you actually need (recommend: SessionStart only).

---

## Task 2: Clean VSCode Global MCP Config

**Files:**
- Modify: `C:/Users/User/AppData/Roaming/Code/User/mcp.json`

**Problems to fix:**
- `jetbrains` → `http://localhost:64342/sse` — only valid when JetBrains is open; causes constant reconnect errors
- `gemini/gemini-mcp-server` → `https://geminiapi.google.com/v1/mcp/` — endpoint does not exist
- `github/github-mcp-server` + `io.github.github/github-mcp-server` — same `https://api.githubcopilot.com/mcp/` URL, duplicate
- `huggingface/hf-mcp-server` + `hf-mcp-server` — same `https://huggingface.co/mcp?login` URL, duplicate
- `anthropic/claude-mcp-server` → `https://api.anthropic.com/v1/mcp/` — not a real MCP endpoint

- [ ] **Step 1: Back up mcp.json**

```bash
cp "C:/Users/User/AppData/Roaming/Code/User/mcp.json" \
   "C:/Users/User/AppData/Roaming/Code/User/mcp.json.bak-$(date +%Y%m%d)"
```

- [ ] **Step 2: Write the cleaned mcp.json**

Write the following to `C:/Users/User/AppData/Roaming/Code/User/mcp.json` — keeping all valid working entries, removing dead/duplicate ones:

```jsonc
{
  "servers": {
    "github/github-mcp-server": {
      "type": "http",
      "url": "https://api.githubcopilot.com/mcp/",
      "gallery": "https://api.mcp.github.com/2025-09-15/v0/servers/123e4567-e89b-12d3-a456-426614174000",
      "version": "2.0.1"
    },
    "microsoftdocs/mcp": {
      "type": "http",
      "url": "https://learn.microsoft.com/api/mcp",
      "gallery": "https://api.mcp.github.com/2025-09-15/v0/servers/e0455530-d34a-4795-8dc6-b2888ae76c27",
      "version": "1.0.0"
    },
    "huggingface/hf-mcp-server": {
      "url": "https://huggingface.co/mcp?login",
      "type": "http"
    },
    "microsoft/markitdown": {
      "type": "stdio",
      "command": "uvx",
      "args": ["markitdown-mcp==0.0.1a4"],
      "gallery": "https://api.mcp.github.com",
      "version": "1.0.0"
    },
    "com.postman/postman-mcp-server": {
      "type": "stdio",
      "command": "npx",
      "args": ["@postman/postman-mcp-server@2.4.9"],
      "env": {
        "POSTMAN_API_KEY": "${input:POSTMAN_API_KEY}"
      },
      "gallery": "https://api.mcp.github.com",
      "version": "2.4.9"
    },
    "com.microsoft/azure": {
      "type": "stdio",
      "command": "dnx",
      "args": ["Azure.Mcp@2.0.0-beta.5", "--yes", "--", "server", "start"],
      "gallery": "https://api.mcp.github.com",
      "version": "2.0.0-beta.5"
    },
    "perplexity": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@perplexity-ai/mcp-server"]
    },
    "io.github.upstash/context7": {
      "type": "stdio",
      "command": "npx",
      "args": ["@upstash/context7-mcp@1.0.31"],
      "env": {
        "CONTEXT7_API_KEY": "${input:CONTEXT7_API_KEY}"
      },
      "gallery": "https://api.mcp.github.com",
      "version": "1.0.31"
    },
    "microsoft/playwright-mcp": {
      "type": "stdio",
      "command": "npx",
      "args": ["@playwright/mcp@latest"],
      "gallery": "https://api.mcp.github.com",
      "version": "0.0.1-seed"
    },
    "azure-ai-foundry/mcp-foundry": {
      "type": "stdio",
      "command": "uvx",
      "args": [
        "--prerelease=allow",
        "--from", "git+https://github.com/azure-ai-foundry/mcp-foundry.git",
        "run-azure-ai-foundry-mcp",
        "--envFile", "${input:env_file_path}"
      ],
      "env": {
        "GITHUB_TOKEN": "${input:github_token}",
        "AZURE_AI_SEARCH_ENDPOINT": "${input:ai_search_endpoint}",
        "AZURE_AI_SEARCH_API_VERSION": "${input:ai_search_api_version}",
        "SEARCH_AUTHENTICATION_METHOD": "${input:search_auth_method}",
        "AZURE_TENANT_ID": "${input:azure_tenant_id}",
        "AZURE_CLIENT_ID": "${input:azure_client_id}",
        "AZURE_CLIENT_SECRET": "${input:azure_client_secret}",
        "AZURE_AI_SEARCH_API_KEY": "${input:ai_search_api_key}",
        "EVAL_DATA_DIR": "${input:eval_data_dir}",
        "AZURE_OPENAI_ENDPOINT": "${input:az_openai_endpoint}",
        "AZURE_OPENAI_API_KEY": "${input:az_openai_api_key}",
        "AZURE_OPENAI_DEPLOYMENT": "${input:az_openai_deployment}",
        "AZURE_OPENAI_API_VERSION": "${input:az_openai_api_version}",
        "AZURE_AI_PROJECT_ENDPOINT": "${input:ai_project_endpoint}"
      },
      "gallery": "https://api.mcp.github.com",
      "version": "1.0.0"
    },
    "GitKraken": {
      "command": "c:\\Users\\User\\AppData\\Roaming\\Code\\User\\globalStorage\\eamodio.gitlens\\gk.exe",
      "type": "stdio",
      "args": ["mcp", "--host=vscode", "--source=gitlens", "--scheme=vscode"]
    },
    "oraios/serena": {
      "type": "stdio",
      "command": "uvx",
      "args": [
        "--from", "git+https://github.com/oraios/serena",
        "serena", "start-mcp-server", "serena@latest",
        "--context", "ide-assistant"
      ],
      "gallery": "https://api.mcp.github.com",
      "version": "1.0.0"
    },
    "com.supabase/mcp": {
      "type": "http",
      "url": "https://mcp.supabase.com/mcp",
      "gallery": "https://api.mcp.github.com",
      "version": "0.7.0"
    },
    "Neon": {
      "type": "http",
      "url": "https://mcp.neon.tech/mcp",
      "headers": {
        "Authorization": "Bearer napi_vfn2yqt3el9a44j5or8mxlyul30cj6ppbzw6o6atteyui9p1rp6a2k1scg0tn51f"
      }
    },
    "cockroachdb-cloud": {
      "type": "http",
      "url": "https://cockroachlabs.cloud/mcp",
      "headers": {
        "mcp-cluster-id": "0fcabf5e-1e74-4206-8e4c-a8def83f6bdf"
      }
    },
    "supabase": {
      "type": "http",
      "url": "https://mcp.supabase.com/mcp?project_ref=smttdhtpwkowcyatoztb&features=docs,database,development,debugging,account,functions,branching"
    }
  },
  "inputs": [
    {
      "id": "CONTEXT7_API_KEY",
      "type": "promptString",
      "description": "API key for authentication",
      "password": true
    },
    {
      "id": "github_token",
      "type": "promptString",
      "description": "Optional: GitHub token for testing models for free with rate limits.",
      "password": true
    },
    {
      "id": "ai_search_endpoint",
      "type": "promptString",
      "description": "Your Azure AI Search endpoint (https://<service>.search.windows.net/).",
      "password": false
    },
    {
      "id": "ai_search_api_version",
      "type": "promptString",
      "description": "API version (defaults to 2025-03-01-preview).",
      "password": false
    },
    {
      "id": "search_auth_method",
      "type": "promptString",
      "description": "Authentication method: 'service-principal' or 'api-search-key'.",
      "password": false
    },
    {
      "id": "azure_tenant_id",
      "type": "promptString",
      "description": "Required if using service-principal auth.",
      "password": false
    },
    {
      "id": "azure_client_id",
      "type": "promptString",
      "description": "Required if using service-principal auth.",
      "password": false
    },
    {
      "id": "azure_client_secret",
      "type": "promptString",
      "description": "Required if using service-principal auth.",
      "password": true
    },
    {
      "id": "ai_search_api_key",
      "type": "promptString",
      "description": "Required if using api-search-key auth.",
      "password": true
    },
    {
      "id": "eval_data_dir",
      "type": "promptString",
      "description": "Path to JSONL datasets for evaluation tools.",
      "password": false
    },
    {
      "id": "az_openai_endpoint",
      "type": "promptString",
      "description": "Endpoint for text-quality evaluators (optional).",
      "password": false
    },
    {
      "id": "az_openai_api_key",
      "type": "promptString",
      "description": "API key for the above endpoint (optional).",
      "password": true
    },
    {
      "id": "az_openai_deployment",
      "type": "promptString",
      "description": "Deployment name (e.g., gpt-4o) used by evaluators (optional).",
      "password": false
    },
    {
      "id": "az_openai_api_version",
      "type": "promptString",
      "description": "API version for Azure OpenAI (optional).",
      "password": false
    },
    {
      "id": "ai_project_endpoint",
      "type": "promptString",
      "description": "Azure AI Project endpoint for agent tools (optional).",
      "password": false
    },
    {
      "id": "env_file_path",
      "type": "promptString",
      "description": "Path to a .env file to load (e.g., ${workspaceFolder}/.env).",
      "password": false
    },
    {
      "id": "POSTMAN_API_KEY",
      "type": "promptString",
      "description": "Postman API key.",
      "password": true
    }
  ]
}
```

- [ ] **Step 3: Verify JSON is valid**

```bash
python3 -m json.tool "C:/Users/User/AppData/Roaming/Code/User/mcp.json" > /dev/null && echo "VALID" || echo "INVALID"
```

Expected: `VALID`

- [ ] **Step 4: Verify removed entries are gone, kept entries present**

```bash
python3 -c "
import json
with open('C:/Users/User/AppData/Roaming/Code/User/mcp.json') as f:
    d = json.load(f)
servers = list(d['servers'].keys())
removed = [k for k in ['jetbrains','gemini/gemini-mcp-server','io.github.github/github-mcp-server','hf-mcp-server','anthropic/claude-mcp-server'] if k in servers]
kept = [k for k in ['github/github-mcp-server','Neon','GitKraken','supabase'] if k in servers]
print('REMOVED (should be empty):', removed)
print('KEPT (should have 4):', kept)
"
```

Expected:
```
REMOVED (should be empty): []
KEPT (should have 4): ['github/github-mcp-server', 'Neon', 'GitKraken', 'supabase']
```

- [ ] **Step 5: Reload VSCode MCP servers**

In VSCode: `Ctrl+Shift+P` → `MCP: List Servers` — verify no red/error indicators on previously broken entries.

---

## Task 3: Populate Claude Desktop MCP Config

**Files:**
- Modify: `C:/Users/User/AppData/Roaming/Claude/claude_desktop_config.json`
- Create: `C:/Users/User/AI_Agent_Skills/agents/claude-desktop/mcp.template.json`

**Why:** Claude Desktop currently has `"mcpServers": {}` — no tools, no agents. We populate it from `~/VSCodespace/.env` using the same vars the sync script already reads.

- [ ] **Step 1: Create the Claude Desktop MCP template in AI_Agent_Skills**

```bash
mkdir -p "C:/Users/User/AI_Agent_Skills/agents/claude-desktop"
```

Write to `C:/Users/User/AI_Agent_Skills/agents/claude-desktop/mcp.template.json`:

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_MCP_PAT}",
        "GITHUB_TOKEN": "${GITHUB_MCP_PAT}"
      }
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "C:/Users/User/VSCodespace"],
      "env": {}
    },
    "perplexity": {
      "command": "npx",
      "args": ["-y", "perplexity-mcp"],
      "env": {
        "PERPLEXITY_API_KEY": "${PERPLEXITY_API_KEY}"
      }
    },
    "grok": {
      "command": "npx",
      "args": ["-y", "mcp-server-xai-grok"],
      "env": {
        "XAI_API_KEY": "${XAI_API_KEY}"
      }
    },
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp"],
      "env": {
        "CONTEXT7_API_KEY": "${CONTEXT7_API_KEY}"
      }
    }
  }
}
```

- [ ] **Step 2: Resolve template and write live Claude Desktop config**

Run in PowerShell — reads from `.env`, resolves `${VAR}` placeholders, writes live config:

```powershell
$envPath = "C:/Users/User/VSCodespace/.env"
$templatePath = "C:/Users/User/AI_Agent_Skills/agents/claude-desktop/mcp.template.json"
$outputPath = "C:/Users/User/AppData/Roaming/Claude/claude_desktop_config.json"

# Load env vars
$envMap = @{}
foreach ($line in Get-Content $envPath) {
    if ($line -match '^([^=]+)=(.+)$' -and $line -notmatch '^\s*#') {
        $envMap[$matches[1].Trim()] = $matches[2].Trim()
    }
}

# Resolve template
$template = Get-Content -Raw $templatePath
$resolved = [regex]::Replace($template, '\$\{([A-Z0-9_]+)\}', {
    param($m)
    $key = $m.Groups[1].Value
    if ($envMap.ContainsKey($key)) { return $envMap[$key] }
    Write-Warning "Missing env var: $key"
    return ""
})

# Read existing config (keep preferences section)
$existing = Get-Content -Raw $outputPath | ConvertFrom-Json
$resolvedObj = $resolved | ConvertFrom-Json

$existing.mcpServers = $resolvedObj.mcpServers
$existing | ConvertTo-Json -Depth 10 | Set-Content -Path $outputPath -Encoding UTF8

Write-Host "Claude Desktop config updated with $(($existing.mcpServers | Get-Member -MemberType NoteProperty).Count) MCP servers."
```

Expected output: `Claude Desktop config updated with 5 MCP servers.`

- [ ] **Step 3: Verify the output**

```bash
python3 -c "
import json
with open('C:/Users/User/AppData/Roaming/Claude/claude_desktop_config.json') as f:
    d = json.load(f)
servers = list(d.get('mcpServers', {}).keys())
print('MCP servers:', servers)
for name, cfg in d['mcpServers'].items():
    has_empty_token = any(v == '' for v in cfg.get('env', {}).values())
    print(f'  {name}: empty tokens = {has_empty_token}')
"
```

If any token is empty, that env var is missing from `~/VSCodespace/.env` — add it there and re-run Step 2.

- [ ] **Step 4: Restart Claude Desktop**

Close and reopen Claude App. Verify tools/MCPs appear in the chat interface (look for the tool count in the compose area).

---

## Task 4: Create SSH Config + VSCode Local Key

**Files:**
- Create: `C:/Users/User/.ssh/config`
- Create: `C:/Users/User/.ssh/id_ed25519_vscode` (key pair)

- [ ] **Step 1: Generate the VSCode-to-VSCode key**

```bash
ssh-keygen -t ed25519 -C "vscode-local@DESKTOP-PHMUM56" \
  -f "C:/Users/User/.ssh/id_ed25519_vscode" \
  -N ""
```

Expected: Creates `id_ed25519_vscode` and `id_ed25519_vscode.pub` in `~/.ssh/`.

- [ ] **Step 2: Verify Docker still works with existing key**

```bash
# Check Docker Desktop SSH agent integration
docker info --format "{{.ServerVersion}}" 2>/dev/null && echo "Docker accessible" || echo "Docker not running"
ssh-add -l 2>/dev/null || echo "No ssh-agent or no loaded keys"
```

If Docker containers need SSH: add `id_ed25519` to any containers' `authorized_keys`.

- [ ] **Step 3: Create ~/.ssh/config**

Write to `C:/Users/User/.ssh/config`:

```ssh-config
# ── GitHub (main identity) ────────────────────────────────────────────────────
Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519
    AddKeysToAgent yes

# ── WSL local instance ───────────────────────────────────────────────────────
Host wsl-local
    HostName localhost
    User wbracken
    IdentityFile ~/.ssh/id_ed25519_wsl
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null

# ── Docker containers (mapped to localhost ports) ────────────────────────────
# Usage: ssh docker-local -p <container-port>
Host docker-local
    HostName localhost
    User root
    IdentityFile ~/.ssh/id_ed25519
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null

# ── Local VSCode remote instance (second machine or WSL remote) ─────────────
# Usage: ssh vscode-remote
# Add id_ed25519_vscode.pub to target machine's ~/.ssh/authorized_keys
Host vscode-remote
    HostName localhost
    Port 2222
    User User
    IdentityFile ~/.ssh/id_ed25519_vscode
    StrictHostKeyChecking no

# ── Remote development machines ─────────────────────────────────────────────
# Uncomment and fill in when connecting to real remote machines:
# Host i9-desktop
#     HostName <IP-ADDRESS>
#     User User
#     IdentityFile ~/.ssh/id_ed25519
#     AddKeysToAgent yes
#
# Host macbook-m3
#     HostName <IP-ADDRESS>
#     User wbracken
#     IdentityFile ~/.ssh/id_ed25519

# ── Global defaults ──────────────────────────────────────────────────────────
Host *
    ServerAliveInterval 60
    ServerAliveCountMax 3
    ConnectTimeout 10
```

- [ ] **Step 4: Verify GitHub SSH still works**

```bash
ssh -T git@github.com 2>&1 | grep -E "successfully authenticated|permission denied"
```

Expected: `Hi WillBracken! You've successfully authenticated...`

- [ ] **Step 5: Print the new VSCode key public key**

```bash
cat "C:/Users/User/.ssh/id_ed25519_vscode.pub"
```

Copy this output — add it to `~/.ssh/authorized_keys` on any machine you want to connect to via `ssh vscode-remote`.

---

## Task 5: VSCode Profiles + Keybindings + GitLens Solo Mode

**Files:**
- Modify: `C:/Users/User/AppData/Roaming/Code/User/settings.json`
- Modify: `C:/Users/User/AppData/Roaming/Code/User/keybindings.json`
- Create: `C:/Users/User/AppData/Roaming/Code/User/profiles/3003a964/settings.json`
- Create: `C:/Users/User/AppData/Roaming/Code/User/profiles/-eef08c8/settings.json`

### 5a — User settings: iCloud watcher + GitLens solo

- [ ] **Step 1: Add iCloudDrive to watcherExclude and GitLens solo settings**

Add to `C:/Users/User/AppData/Roaming/Code/User/settings.json` (merge into existing JSON — add these keys):

```jsonc
// iCloud — prevent VSCode file watcher from tracking iCloudDrive
// (reduces memory pressure and eliminates language server noise for non-code files)
"files.watcherExclude": {
  "**/.git/objects/**": true,
  "**/.git/subtree-cache/**": true,
  "**/node_modules/**": true,
  "**/.venv/**": true,
  "**/__pycache__/**": true,
  "**/dist/**": true,
  "**/build/**": true,
  "C:/Users/User/iCloudDrive/**": true,
  "C:/Users/User/OneDrive/**": true
},

// GitLens — disable team/pro features for solo developer
"gitlens.plusFeatures.enabled": false,
"gitlens.views.drafts.enabled": false,
"gitlens.views.worktrees.enabled": false,
"gitlens.launchpad.indicator.enabled": false,
"gitlens.views.contributors.enabled": false,

// GitHub panel — make Source Control the right sidebar primary
"workbench.secondarySideBar.defaultVisibility": "visible",
```

- [ ] **Step 2: Verify settings.json remains valid**

```bash
python3 -m json.tool "C:/Users/User/AppData/Roaming/Code/User/settings.json" > /dev/null && echo "VALID" || echo "INVALID — check for trailing comma or comment syntax"
```

Note: VSCode settings.json is JSONC (allows `//` comments) but python's json.tool will fail on comments. Use this instead:

```bash
node -e "
const fs = require('fs');
const content = fs.readFileSync('C:/Users/User/AppData/Roaming/Code/User/settings.json','utf8');
const stripped = content.replace(/\/\/[^\n]*/g,'').replace(/\/\*[\s\S]*?\*\//g,'');
JSON.parse(stripped);
console.log('VALID');
"
```

Expected: `VALID`

### 5b — Keybindings: add AI agent + GitHub panel shortcuts

- [ ] **Step 3: Add AI agent panel and GitHub right-sidebar shortcuts**

Append the following entries to `C:/Users/User/AppData/Roaming/Code/User/keybindings.json` (inside the existing `[...]` array, before the final `]`):

```jsonc
  // ───────────────────────────────────────────────────────────────────────────
  // AI AGENTS — Quick Access
  // ───────────────────────────────────────────────────────────────────────────

  // Open GitHub Copilot chat (right secondary sidebar)
  { "key": "ctrl+shift+i", "command": "workbench.panel.chat.view.copilot.focus" },

  // Focus secondary sidebar (where GitHub panel lives)
  { "key": "ctrl+alt+g", "command": "workbench.action.focusAuxiliaryBar" },

  // Toggle secondary sidebar (right panel)
  { "key": "ctrl+alt+b", "command": "workbench.action.toggleAuxiliaryBar" },

  // Open GitHub Pull Requests view
  { "key": "ctrl+alt+h", "command": "workbench.view.extension.github-pull-requests" },

  // GitLens — Open Git Graph
  { "key": "ctrl+alt+g ctrl+alt+g", "command": "gitlens.showGraph" },

  // GitLens — File history
  { "key": "ctrl+alt+g ctrl+alt+f", "command": "gitlens.showFileHistoryView" },

  // GitLens — Line blame toggle
  { "key": "ctrl+alt+g ctrl+alt+b", "command": "gitlens.toggleLineBlame" }
```

- [ ] **Step 4: Verify keybindings.json valid (JSONC)**

```bash
node -e "
const fs = require('fs');
const content = fs.readFileSync('C:/Users/User/AppData/Roaming/Code/User/keybindings.json','utf8');
const stripped = content.replace(/\/\/[^\n]*/g,'').replace(/\/\*[\s\S]*?\*\//g,'');
JSON.parse(stripped);
console.log('VALID');
"
```

Expected: `VALID`

### 5c — Named profile settings

- [ ] **Step 5: Create settings for profile 3003a964 (Python/Data profile)**

Write to `C:/Users/User/AppData/Roaming/Code/User/profiles/3003a964/settings.json`:

```jsonc
{
  // Python / Data Science profile
  // Inherits user settings.json; overrides specific to Python/notebook work
  "workbench.colorTheme": "Ayu Light Bordered",
  "editor.fontSize": 13,
  "python.defaultInterpreterPath": "C:/Users/User/AppData/Local/Programs/Python/Python314/python.exe",
  "notebook.output.scrolling": true,
  "notebook.lineNumbers": "on",
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff"
  }
}
```

- [ ] **Step 6: Create settings for profile -eef08c8 (Node/Web profile)**

Write to `C:/Users/User/AppData/Roaming/Code/User/profiles/-eef08c8/settings.json`:

```jsonc
{
  // Node.js / Web profile
  // Inherits user settings.json; overrides specific to JS/TS work
  "workbench.colorTheme": "Ayu Dark Bordered",
  "editor.fontSize": 13,
  "editor.tabSize": 2,
  "[javascript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "eslint.validate": ["javascript", "typescript", "javascriptreact", "typescriptreact"]
}
```

---

## Task 6: Add Claude Desktop to AI_Agent_Skills Sync Script

**Files:**
- Modify: `C:/Users/User/AI_Agent_Skills/scripts/sync.ps1`
- Create: `C:/Users/User/AI_Agent_Skills/agents/claude-desktop/mcp.template.json` (done in Task 3)

This makes `sync.ps1` the single command to update ALL agents: Claude Code CLI, Claude Desktop, VSCode/Copilot, Gemini, JetBrains.

- [ ] **Step 1: Add Claude Desktop sync block to sync.ps1**

Add the following block to `sync.ps1` just before the final `Write-Host 'MCP templates synced...'` line:

```powershell
# ── Claude Desktop ──────────────────────────────────────────────────────────
$claudeDesktopTemplatePath = Join-Path $registryRoot 'agents\claude-desktop\mcp.template.json'
$claudeDesktopOutputPath = Join-Path $Root 'AppData\Roaming\Claude\claude_desktop_config.json'

if (Test-Path $claudeDesktopTemplatePath) {
    $cdTemplate = Get-Content -Raw $claudeDesktopTemplatePath | ConvertFrom-Json | ConvertTo-Hashtable
    $cdResolved = Resolve-TemplateValue -Value $cdTemplate -EnvMap $envMap

    if (Test-Path $claudeDesktopOutputPath) {
        $cdCurrent = Get-Content -Raw $claudeDesktopOutputPath | ConvertFrom-Json | ConvertTo-Hashtable
    } else {
        $cdCurrent = @{ preferences = @{} }
    }
    $cdCurrent['mcpServers'] = $cdResolved['mcpServers']
    Write-JsonFile -Path $claudeDesktopOutputPath -Object $cdCurrent
    Write-Host "-> Claude Desktop: $claudeDesktopOutputPath"
} else {
    Write-Warning "Claude Desktop template not found at $claudeDesktopTemplatePath"
}
```

- [ ] **Step 2: Test the sync script end-to-end**

```powershell
cd "C:/Users/User/AI_Agent_Skills"
.\scripts\sync.ps1 -Profile windows-full
```

Expected output includes:
```
-> Using MCP profile: ...\mcp\profiles\windows-full.mcp.json
-> Claude Desktop: C:\Users\User\AppData\Roaming\Claude\claude_desktop_config.json
MCP templates synced to local configs.
```

- [ ] **Step 3: Verify Claude Desktop config was updated by sync**

```bash
python3 -c "
import json
with open('C:/Users/User/AppData/Roaming/Claude/claude_desktop_config.json') as f:
    d = json.load(f)
print('servers:', list(d.get('mcpServers',{}).keys()))
"
```

- [ ] **Step 4: Commit AI_Agent_Skills changes**

```bash
cd "C:/Users/User/AI_Agent_Skills"
git add agents/claude-desktop/ scripts/sync.ps1 docs/
git commit -m "feat: add Claude Desktop to sync pipeline; add cross-machine MCP template"
git push
```

---

## Task 7: Fix iCloud Memory Pressure (File Watcher)

**Files:**
- Modify: `C:/Users/User/AppData/Roaming/Code/User/settings.json` (done in Task 5a — watcherExclude already added)

This task captures the baseline and verifies the fix.

- [ ] **Step 1: Capture iCloud process memory before fix**

Run in PowerShell:

```powershell
Get-Process -Name "iCloud*","iCloudDrive*" -ErrorAction SilentlyContinue |
  Select-Object Name, Id, @{n='MemMB';e={[math]::Round($_.WorkingSet64/1MB,1)}} |
  Format-Table
```

Note the `MemMB` value — this is your baseline.

- [ ] **Step 2: Verify watcherExclude was applied (from Task 5a)**

```bash
python3 -c "
import re, json
content = open('C:/Users/User/AppData/Roaming/Code/User/settings.json').read()
stripped = re.sub(r'//[^\n]*','',content)
d = json.loads(stripped)
watcher = d.get('files.watcherExclude', {})
print('iCloudDrive excluded:', 'C:/Users/User/iCloudDrive/**' in watcher)
print('OneDrive excluded:', 'C:/Users/User/OneDrive/**' in watcher)
"
```

Expected:
```
iCloudDrive excluded: True
OneDrive excluded: True
```

- [ ] **Step 3: Reload VSCode window**

In VSCode: `Ctrl+Shift+P` → `Developer: Reload Window`

- [ ] **Step 4: Monitor iCloud memory after reload**

Wait 2–3 minutes after reload, then:

```powershell
Get-Process -Name "iCloud*","iCloudDrive*" -ErrorAction SilentlyContinue |
  Select-Object Name, Id, @{n='MemMB';e={[math]::Round($_.WorkingSet64/1MB,1)}} |
  Format-Table
```

If memory is still climbing, the leak is in iCloud.exe itself (Windows iCloud app bug, not VSCode). In that case:

```powershell
# Check if iCloud is watching too many paths
Get-Process iCloud | Select-Object -ExpandProperty Handles
```

If handles > 5000: Go to **iCloud for Windows Settings → iCloud Drive → Manage** and disable "Sync this PC" for large non-code folders (Downloads, Photos, Documents subfolders). The code folders you work in should stay synced.

---

## Cross-Machine Setup (New Machine Quickstart)

After completing all tasks above, this is the full setup for a new machine:

```bash
# 1. Clone AI_Agent_Skills
git clone https://github.com/WillBracken/AI_Agent_Skills.git ~/AI_Agent_Skills

# 2. Create ~/VSCodespace/.env with your API keys
#    (copy from another machine or 1Password)

# 3. Run sync
cd ~/AI_Agent_Skills
./scripts/sync.ps1 -Profile windows-full     # Windows
# bash scripts/sync.sh --profile linux        # Linux/macOS/WSL

# 4. Generate SSH keys if needed
ssh-keygen -t ed25519 -C "user@newmachine" -f ~/.ssh/id_ed25519 -N ""
ssh-keygen -t ed25519 -C "vscode-local@newmachine" -f ~/.ssh/id_ed25519_vscode -N ""
cp ~/.ssh/config ~/.ssh/config   # from AI_Agent_Skills/config/ssh.config template
```

Skills are downloaded by Claude Code on first use — they come from the plugin marketplace, not the AI_Agent_Skills repo. The repo manages MCP configs and environment variables only.
