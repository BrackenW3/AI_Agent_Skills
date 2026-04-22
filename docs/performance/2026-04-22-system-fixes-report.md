# System Fixes Report — 2026-04-22

## Summary
Full system diagnosis and repair session. Computer was severely degraded (99 Node.js processes, 32GB iCloud memory leak, broken SSH). All automated fixes applied; manual steps listed below.

---

## Fixes Applied (Done — No Action Needed)

### 1. zai-mcp-server Crash Loop — PERMANENTLY FIXED
- **Root cause:** `google.geminicodeassist` VSCode extension had `zai-mcp-server` hardcoded inside its **SQLite state database** (`state.vscdb`) — not in any text config file. Every time VSCode opened, it spawned 99+ Node.js processes in a crash-restart loop.
- **Fix:** Surgically removed z-ai entries from `C:\Users\User\AppData\Roaming\Code\User\globalStorage\state.vscdb`.
- **Backup:** `state.vscdb.pre-zai-fix.bak` in same directory.
- **Why previous sessions missed it:** Previous fixes cleaned text configs (`.gemini/settings.json`, `.claude.json`) but not the binary SQLite DB.

### 2. GitHub SSH in Git Bash — FIXED
- **Root cause:** Git Bash was using its own bundled SSH binary, which doesn't connect to the Windows OpenSSH Agent. Keys weren't being offered to GitHub.
- **Fix:** `git config --global core.sshCommand "C:/Windows/System32/OpenSSH/ssh.exe"`
- **Confirmed working:** `Hi BrackenW3!` response from GitHub.

### 3. MCP Config Trimmed — 14 → 11 MCPs
- **Removed from `~/.claude.json`:**
  - `serena` — background AI code-indexer, runs constantly, high memory
  - `grok` — redundant with Perplexity and Claude's own reasoning
  - `azure-cosmosdb` — not a primary project tool
- **Kept:** filesystem, azure, jira, github, perplexity, context7, supabase, cloudflare, azure-postgres, Neon (HTTP), cockroachdb-cloud (HTTP)
- **Backup:** `.claude.json.pre-mcp-trim.bak`

### 4. VSCode Settings Optimized
- **Fixed:** Removed deprecated `python.linting.enabled` setting
- **Added:** More aggressive `files.watcherExclude` (npm-cache, Anaconda3)
- **Added:** GitLens solo-dev settings (disabled code lens, telemetry, release notes, welcome screens)
- **Added:** Performance settings (GPU acceleration on, experiments off, telemetry error-only)
- **Added:** `terminal.integrated.enablePersistentSessions: false` (prevents ghost terminal processes)
- **Added:** `git.autoRepositoryDetection: "openEditors"` (prevents scanning all of `~/`)

### 5. CLAUDE.md MCP Table Updated
- Removed z-ai from the table
- Added all actual active MCPs

---

## You Must Do Manually

### A. iCloud Drive Memory Leak (32 GB!) — MOST IMPORTANT
`iCloudDrive.exe` is consuming **32+ GB RAM**. This is your #1 slowdown cause.

**Fix (30 seconds):**
1. Right-click iCloud icon in system tray
2. Click "Quit iCloud"
3. Reopen iCloud from Start menu

**If it happens again (recurring):**
- Open iCloud Settings → iCloud Drive → Options
- Uncheck any folders with > 10,000 files (e.g., Desktop, Documents)
- The leak is triggered by syncing too many small files

### B. Google Drive for Desktop Won't Install
**Root cause:** Bitdefender blocks `UpdaterSetup.exe /needsadmin=true` (times out at 60s, error 1603).

**Fix:**
1. Open **Bitdefender** → Protection → Advanced Threat Defense → **Exceptions**
2. Add exception: `C:\Users\User\AppData\Local\Temp\` (temporarily)
3. Run Google Drive installer again: https://dl.google.com/drive-file-stream/GoogleDriveSetup.exe
4. Remove the Bitdefender exception after install completes

### C. GitHub Right Panel (30 seconds)
VSCode secondary sidebar is already enabled. To pin GitHub there:
1. Right-click the **GitHub** icon in the left Activity Bar
2. Select **"Move to Secondary Side Bar"**
3. Done — GitHub Pull Requests will be on the right permanently

### D. Quick AI Agents Access
Your 39 GitHub Copilot agents are at `~/VSCodespace/VSCode_Folders/.github/agents/`.
To get quick access in VSCode:
- Open Command Palette → `Preferences: Open Keyboard Shortcuts`
- Bind `workbench.view.extension.github-copilot-chat` to a key you like

---

## WSL / Docker SSH — Status
- Your Windows SSH key IS registered with GitHub (`Hi BrackenW3!` confirmed)
- `npiperelay.exe` is installed and bridges Windows SSH Agent → WSL
- WSL should work. If not: in WSL, run `ssh-add -l` to verify agent forwarding
- Docker uses same key via `docker-local` host config in `~/.ssh/config`

---

## Node.js Process Monitoring
Run this to check if the crash loop returns:
```powershell
# PowerShell - count node processes
(Get-Process node -ErrorAction SilentlyContinue).Count

# If > 20, check what's spawning them:
Get-WmiObject Win32_Process -Filter "name='node.exe'" | Select-Object ProcessId, CommandLine | Format-Table
```

**Safe limit:** 5-15 node processes (one per active MCP server).
**Problem threshold:** > 20 processes with the same command = crash loop.

---

## Files Modified
| File | Change |
|------|--------|
| `state.vscdb` | Removed z-ai MCP from Gemini extension state |
| `~/.claude.json` | Removed serena, grok, azure-cosmosdb MCPs |
| `~/AppData/Roaming/Code/User/settings.json` | Performance + GitLens + watcher optimizations |
| `~/CLAUDE.md` | Updated MCP table |
| `~/.gitconfig` (global) | `core.sshCommand = C:/Windows/System32/OpenSSH/ssh.exe` |
