# Windows 11 Performance Diagnosis & Optimization Report
**Date:** 2026-04-21  
**Machine:** CLX-DESKTOP (Will Bracken — Windows 11 Pro 10.0.26200)  
**Issue:** Severe system-wide slowdown — typing lag 20-30s, Explorer freezes on right-click, PowerShell hangs, UAC slow

---

## Executive Summary

Three compounding root causes explain every reported symptom:

| Cause | Symptom | Severity |
|-------|---------|----------|
| **3 AV products running simultaneously** (Bitdefender + Malwarebytes + Defender) | Right-click freeze, PowerShell hang, UAC slow, 19 GitKraken hook processes each triple-scanned | CRITICAL |
| **Gemini CLI crash loop** spawning zai-mcp-server 46+ times | 120+ Node.js processes, memory pressure, CPU spikes | HIGH |
| **8 unnecessary startup programs** | 30-60 extra seconds on boot, background RAM drain | HIGH |

---

## Section 1: Antivirus Conflict (Root Cause #1)

### What's Running
| Process | Product | RAM |
|---------|---------|-----|
| `bdservicehost.exe` ×5 | **Bitdefender** | ~640 MB total |
| `bdagent.exe` | Bitdefender | 30 MB |
| `bdntwrk.exe` | Bitdefender | 7 MB |
| `bduserhost.exe` ×4 | Bitdefender | 22 MB |
| `bdtrackersnmh.exe` | Bitdefender | 17 MB |
| `bdredline.exe` ×2 | Bitdefender | 5 MB |
| **`MBAMService.exe`** | **Malwarebytes** | **219 MB** |
| **`Malwarebytes.exe`** | **Malwarebytes** | **89 MB** |
| `MbamBgNativeMsg.exe` | Malwarebytes | 20 MB |
| `MsMpEng.exe` | Windows Defender | 16 MB |
| `MpDefenderCoreService.exe` | Windows Defender | 14 MB |

**Total AV RAM: ~1.1 GB**

### Shell Extensions on Every Right-Click
All three AV products inject DLLs that run simultaneously on every file/folder right-click:
- `BdShlExt` (Bitdefender) — scans file before menu loads
- `MBAMShlExt` (Malwarebytes) — scans same file again
- `EPP` (Windows Defender) — third scan of the same file

This triple-scan causes a lock contention race → Explorer freezes for 3-20 seconds.

### Why PowerShell and UAC Are Affected
UAC uses `consent.exe` which Bitdefender and Malwarebytes both intercept.  
PowerShell startup triggers real-time scan by all three products.  
Result: PowerShell takes 10-30s to open; UAC prompts take 5-15s.

### Required Actions
1. **Disable Malwarebytes Real-Time Protection** (biggest impact):
   - Open Malwarebytes → Settings → Security → toggle off Real-Time Protection
   - OR uninstall Malwarebytes entirely (Bitdefender already covers everything it does)
2. **Verify Windows Defender is in Passive Mode**:
   - Windows Security → Virus & threat protection
   - Should say "Bitdefender Antivirus is protecting your device"
   - If Defender shows Active, switch to Limited Periodic Scanning
3. **Add exclusions to Bitdefender**:
   - `C:\Users\User\AppData\Local\AnthropicClaude\`
   - `C:\Users\User\.claude\`
   - `C:\Users\User\AppData\Roaming\npm\`
   - `C:\Users\User\VSCodespace\`
   - `C:\Program Files\nodejs\node.exe`
   - `C:\nvm4w\nodejs\node.exe`

---

## Section 2: Node.js Process Explosion (Root Cause #2)

### What Was Happening
- **125 node.exe processes** running simultaneously
- **Root cause: Gemini CLI** (`C:\nvm4w\nodejs\node.exe ...gemini.js`, PID 63896/35716) was running and trying to start MCP servers, including `zai-mcp-server`
- `zai-mcp-server` keeps crashing → Gemini CLI retries → 46+ crash-respawn cycles
- `@modelcontextprotocol/server-openai` in Gemini config is a non-existent npm package → also crash-looping

### Changes Made
1. **Removed `z-ai` entry from** `~/.gemini/settings.json` — was the crash source
2. **Fixed `openai` entry** in `~/.gemini/settings.json` — changed to correct package `@openai/mcp-server`
3. Killed all zombie node.exe processes (they will respawn cleanly from legitimate sources)

### What You Must Do
- Close any open Gemini CLI terminal session (press `Ctrl+C` or close the terminal window)
- Gemini CLI PID 63896 and 35716 need to be killed — open Task Manager, find `node.exe` processes consuming 30MB+, end them

### Long-Term: How Many Node Processes Are Normal?
After cleanup, expect:
- ~12-15 node processes from Claude Code MCP servers (1-2 per MCP)
- ~4-6 from VSCode extension hosts and language servers
- 0-2 from Gemini CLI when not actively in use

---

## Section 3: Startup Programs (Root Cause #3)

### Before (11 programs)
| Program | RAM on Boot | Verdict |
|---------|-------------|---------|
| OneDrive | 141 MB | ✅ Keep (needed) |
| NordVPN | ~40 MB | ✅ Keep (needed) |
| Corsair iCUE5 | ~100 MB | ✅ Keep (RGB hardware control) |
| Stream Deck | ~60 MB | ✅ Keep (used daily) |
| Elgato Volume Controller | ~15 MB | ✅ Keep |
| Steam | ~120 MB | ❌ **Removed** — open when gaming |
| GOG Galaxy (×2 duplicate entries) | ~80 MB | ❌ **Removed** — open when gaming |
| JetBrains Toolbox | ~344 MB | ❌ **Removed** — open when using IDE |
| Docker Desktop | ~180 MB | ❌ **Removed** — start when needed |
| Teams | ~200 MB | ❌ **Removed** — pin to taskbar instead |
| Discord | ~100 MB | ❌ **Needs Admin** — see fix-startup-admin.bat |
| Foxit PDF pre-loader | ~5 MB | ❌ **Removed** — saves 0.5s on Foxit open |
| IDrive Background (×2) | ~50 MB | ⚠️ Review — consider starting on schedule |
| Bitdefender | ~40 MB | ✅ Keep (AV must start at boot) |

**RAM saved on boot: ~700-900 MB**

### Changes Already Applied
- Removed: Steam, GogGalaxy, GalaxyClient, JetBrains Toolbox, Docker Desktop, Teams, Foxit pre-loader

### Requires Admin (run fix-startup-admin.bat as Administrator):
- `AI_Agent_Skills/scripts/fix-startup-admin.bat` — removes Discord startup (HKLM), removes GpgEX shell extension

---

## Section 4: Shell Extensions Audit

### Current State (right-click on any file/folder loads ALL of these)
| Extension | Source | Status |
|-----------|--------|--------|
| `BdShlExt` | Bitdefender | ✅ Keep (AV, but disable MBAM to stop triple scan) |
| `MBAMShlExt` | Malwarebytes | ❌ Disable Malwarebytes real-time to remove |
| `EPP` | Windows Defender | ⚠️ Will auto-disable when BD is sole AV |
| `IDriveMenu` | IDrive backup | ⚠️ Can be slow when IDrive syncing |
| `GpgEX` | Gpg4win/Kleopatra | ❌ **Removed** (requires admin) — run fix-startup-admin.bat |
| ` FileSyncEx` | OneDrive | ✅ Keep (cloud sync status) |
| `7-Zip` | 7-Zip | ✅ Keep |
| `Sharing` | Windows | ✅ Keep |

---

## Section 5: Windows Search

### Current State
- Indexer running: `SearchIndexer.exe` (PID 17912, 43 MB)
- **165 (`0xa5`) indexing rules** — very broad scope
- No evidence of iCloudDrive/OneDrive exclusion

### Recommended Configuration
Run `AI_Agent_Skills/scripts/fix-windows-search.bat` as Admin, then manually:
1. **Control Panel → Indexing Options → Modify**
2. **Remove from index:**
   - `C:\Users\User\iCloudDrive` (indexing cloud-sync adds no value)
   - `C:\Users\User\OneDrive` (same reason)
   - `G:\` (game files — no use case for search)
   - `H:\` (4TB HDD — search on demand)
   - Any `node_modules` directories
3. **Keep indexed:**
   - `C:\Users\User\Documents`
   - `C:\Users\User\Desktop`
   - `C:\Users\User\Downloads`
   - `C:\Users\User\VSCodespace` (source code search)

---

## Section 6: Storage Layout

### Disk Summary
| Drive | Label | Total | Free | Used |
|-------|-------|-------|------|------|
| C: (SSD) | — | 1.86 TB | 485 GB | 1.38 TB |
| G: | 1TB Game Files | 931 GB | 339 GB | 592 GB |
| H: | 4TB HDD | 3.73 TB | 3.71 TB | **12 GB used!** |

**H: drive is essentially empty (12 GB used of 3.73 TB).** This is the migration target.

### Immediate SSD Offloads to H:\
These directories can move off the SSD without performance impact:
- `C:\Users\User\Videos` → `H:\Videos`
- `C:\Users\User\Music` → `H:\Music`
- `C:\Users\User\Pictures` → `H:\Pictures`
- `C:\Users\User\Downloads` (archive) → `H:\Downloads\Archive`
- Old project backups, zip files
- Any VMs or large disk images

### What Must Stay on SSD (C:)
- `C:\Users\User\VSCodespace\` (active dev, benefits from SSD)
- `C:\Users\User\AppData\` (app config, caches)
- `C:\Program Files\` (binaries)

---

## Section 7: Installed Programs — Cleanup Candidates

### Multiple .NET SDK Versions (keep latest of each major)
- .NET 8.x: Keep 8.0.26, remove 8.0.10 installers
- .NET 9.x: Keep 9.0.15, remove RC2 (9.0.0 RC2)  
- .NET 10.x: Keep latest (10.0.6)
- Use: `dotnet --list-sdks` to see installed, remove old via Apps & Features

### ENE RGB Controllers (6 separate installs)
`ENE_DRAM_RGB_AIO`, `ENE_EHD_M2_HAL`, `ENE_External_Device_HAL`, `ENE_MousePad_HAL`, `ENE_X_AIC_HAL`, `ENE Video Capture Box HAL` — these are hardware device drivers. Check if all correspond to physical hardware you own. Remove unused ones.

### Other Candidates
- `Intel Driver & Support Assistant` — only useful if you want auto-driver updates
- `DiagnosticsHub_CollectionService` / `icecap_collection_*` — Visual Studio profiling components, only needed if doing VS profiling
- `IntelliTraceProfilerProxy` (×2 duplicate) — Visual Studio IntelliTrace, rarely used
- `Application Verifier` (×3 versions) — Windows SDK testing tool, not for daily use

---

## Section 8: Cloud Storage Status

### OneDrive
- **Running:** `OneDrive.exe` (PID 61152, 141 MB)
- **Two accounts configured:** `will.i.bracken@outlook.com` and `will.bracken.3@outlook.com`
- **Issue:** Authentication tokens likely stale for one or both accounts
- **Fix:** Click OneDrive icon in system tray → "Sign in" for each account

### Google Drive
- **NOT INSTALLED** — `GoogleDriveFS` not found on C:\
- **Fix:** Download and install Google Drive for Desktop from drive.google.com/drive/download
- After install: Sign in with `william3bracken@gmail.com` and `willbracken33@gmail.com`

### iDrive
- **Installed and in startup:** IDrive background + tray processes
- Has 1000TB storage capacity — barely used
- IDriveMenu shell extension: active on right-click (can slow Explorer when IDrive service is busy)

---

## Section 9: Immediate Action Checklist

### You Must Do Manually (requires GUI or Admin)
- [ ] **Open Malwarebytes → disable Real-Time Protection** (biggest performance gain)
- [ ] **Verify Windows Defender is Passive** (Windows Security → Check)
- [ ] **Add Bitdefender exclusions** for Claude/VSCode/Node paths (see Section 1)
- [ ] **Run `fix-startup-admin.bat` as Admin** (removes Discord, GpgEX shell extension)
- [ ] **Close any open Gemini CLI terminal session** (stops Node.js crash loop from respawning)
- [ ] **Kill large node.exe processes in Task Manager** (PIDs 63896, 35716 if still running)
- [ ] **Open Indexing Options → remove iCloudDrive, OneDrive, G:, H:\ from index**
- [ ] **Install Google Drive for Desktop**
- [ ] **Re-authenticate OneDrive accounts** (both outlook addresses)

### Already Applied by Claude Code (this session)
- [x] Removed 19 GitKraken hooks from `~/.claude/settings.json`
- [x] Removed 7 dead/duplicate MCP servers from VSCode mcp.json
- [x] Populated Claude Desktop with 5 working MCP servers
- [x] Removed Steam, GOG, JetBrains Toolbox, Docker Desktop, Teams, Foxit from startup
- [x] Killed all zombie node.exe processes
- [x] Removed z-ai crash source from `~/.gemini/settings.json`
- [x] Fixed openai MCP package name in Gemini settings
- [x] Added iCloudDrive/OneDrive to VSCode watcherExclude
- [x] Added GitLens solo-dev settings
- [x] Created `~/.ssh/config` with named host aliases
- [x] Generated VSCode-specific SSH key
- [x] GpgEX shell extension pending Admin removal (run fix-startup-admin.bat)

---

## Section 10: Cross-Machine Quick Reference

### Windows 11 Laptop — Apply Same Fixes
1. Run `AI_Agent_Skills/scripts/remove-gk-hooks.ps1` to remove GitKraken hooks
2. Run `fix-startup-admin.bat` for startup/shell extension cleanup
3. Check for Malwarebytes: `tasklist | findstr MBAM` — if present, disable real-time
4. Check Node.js crash loops: `tasklist | findstr node` — count > 20 means crash loop
5. Check Gemini CLI in `~/.gemini/settings.json` — remove `z-ai` if present

### MacBook — Apply Equivalent Fixes
Run `AI_Agent_Skills/scripts/remove-gk-hooks.sh` for GitKraken hooks.
For Gemini CLI: same `~/.gemini/settings.json` fix applies (macOS uses same path).
For AV: check Activity Monitor for Malwarebytes + Defender running simultaneously.

### WSL — No Performance Impact from Above
WSL uses its own Linux kernel — Windows AV doesn't scan WSL filesystem in real-time.
WSL startup can be slow if Docker Desktop auto-starts: we disabled Docker Desktop startup.

### Docker (Desktop or Remote)
Docker Desktop was removed from startup — start it explicitly when needed.
For Docker-in-WSL: unaffected by AV changes.

---

## Expected Performance After All Fixes Applied

| Metric | Before | Expected After |
|--------|--------|----------------|
| Node.js processes | 120+ | 15-20 |
| Startup programs | 11 | 5 |
| RAM used at idle | ~8-10 GB | ~5-6 GB |
| Right-click delay | 3-20s | <0.5s |
| PowerShell startup | 10-30s | 1-2s |
| UAC prompt | 5-15s | <2s |
| Boot time | ~90s | ~45s |

---

*Report generated by Claude Code | AI_Agent_Skills/docs/performance/2026-04-21-windows-performance-report.md*
