# System Optimization Design — 2026-04-21

## Problem Statement

Claude App crashes/slowdowns, Claude Code sluggishness, 50+ Node.js processes, constant MCP disconnects, missing SSH config, and fragmented AI agent configs across machines. Root causes are now identified.

## Sub-Projects (Priority Order)

### P1 — Claude Code Performance (GitKraken hooks)

**Root cause:** `~/.claude/settings.json` registers `gk.exe ai hook run --host claude-code` on all 19 Claude Code event types. Every tool call fires Pre + Post hooks, spawning gk.exe (which uses Node internally) dozens of times per session.

**Fix:** Remove the entire `hooks` section from `~/.claude/settings.json`. GitKraken can be re-enabled with `gk ai hook install` when explicitly needed.

### P2 — VSCode MCP cleanup (disconnects + Node proliferation)

**Root cause:** `~/.vscode/User/mcp.json` contains:
- `jetbrains` → `http://localhost:64342/sse` (only valid when JetBrains is open; always reconnecting otherwise)
- `gemini/gemini-mcp-server` → `https://geminiapi.google.com/v1/mcp/` (non-existent endpoint)
- Duplicate GitHub MCP entry (two keys pointing to same URL)
- Duplicate HuggingFace MCP entry
- 4 `npx` stdio MCPs keeping Node alive: context7, perplexity, playwright, postman

**Fix:** Remove broken entries. Deduplicate. Convert `npx` stdio MCPs to `http` remote variants where available (context7, perplexity already have remote URLs).

### P3 — Claude Desktop MCP config

**Root cause:** `claude_desktop_config.json` has `"mcpServers": {}` — empty. No tools, no agents, no skills available.

**Fix:** Mirror working Claude Code MCPs (github, filesystem, context7, perplexity, grok) into Desktop config. Use env var references for auth tokens.

### P4 — SSH config + cross-machine keys

**Missing:** No `~/.ssh/config` file — Docker and VSCode instance connections aren't aliased.

**Fix:**
- Create `~/.ssh/config` with entries for: Docker container access (`docker-local`), WSL (`wsl`), and local VSCode-to-VSCode (`vscode-local`)
- Generate new `id_ed25519_vscode` key for inter-VSCode connections (separate from GitHub key)
- Verify Docker still uses `id_ed25519`

### P5 — VSCode profile + keybindings + layout

**Fix:**
- Add `settings.json` to unnamed profiles (`3003a964`, `-eef08c8`) — inherit from user settings with profile-specific overrides
- Add AI agent panel shortcuts and GitHub panel as right sidebar primary to `keybindings.json`
- GitLens: disable Worktrees (team feature), Drafts (team), Contributors (team) — keep blame, history, graph, PR views

### P6 — AI_Agent_Skills cross-machine sync

**Goal:** Skills, MCPs, and agent configs available on any machine regardless of API vs subscription access.

**Approach:**
- `AI_Agent_Skills/` repo is the single source of truth
- `sync.ps1` / `sync.sh` writes configs to: `~/.claude/settings.json` (MCP section only), `~/AppData/Roaming/Claude/claude_desktop_config.json`, VSCode `mcp.json`
- Credentials never in repo — all `${VAR}` placeholders resolved from local `~/VSCodespace/.env`
- On new machine: `git clone` + `sync` + populate `.env` = fully configured

### P7 — iCloud memory leak

**Approach:** Capture `iCloud.exe` memory growth via live process snapshot, check VSCode file watcher overlap with `~/iCloudDrive`, add `~/iCloudDrive` to VSCode `files.watcherExclude`.

## Non-Goals

- Git login prompts — user reports resolved; verify SSH auth config only
- Team features in GitKraken — reduce, not remove; GitKraken remains primary Git UI

## Success Criteria

- Claude Code responds without gk.exe lag
- Node.js process count stays under 10 at idle
- No MCP reconnect loops in VSCode Output panel
- Claude Desktop shows tools/MCPs
- `ssh docker-local` works
- On a fresh machine: clone + sync = working AI config
