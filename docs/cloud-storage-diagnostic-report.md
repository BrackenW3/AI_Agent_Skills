# Cloud Storage Diagnostic Report

**Date:** 2026-04-21  
**Machine:** Main Windows Workstation (LG QHD, NVIDIA GPU)  
**Analyst:** Claude (Cowork session)

---

## Executive Summary

Diagnostic analysis of 4 cloud storage accounts across 2 services reveals significant issues with connectivity, organization, and data quality. Two of four accounts are not properly connected. The connected accounts contain disorganized file structures with system backup files, duplicates, and no logical taxonomy. A remediation plan and tooling have been created.

---

## OneDrive Findings

### Account: will.i.bracken@outlook.com ("Will - Personal")

**Status:** Connected and syncing  
**Location:** OneDrive > Will - Personal > Documents  
**Items:** 52 folders in Documents  
**Sync Mode:** Files On Demand (Available when online)

**Issues identified:**

The folder structure mixes completely unrelated content categories with no consistent taxonomy. The Documents folder contains gaming files (Baldur's Gate II, Mount and Blade II Bannerlord, Game Mods, My Games), development files (AI Agents, Cline, Cloudflare, Development Work, Git, Programming), personal files (Current Resumes, Pictures, Music), office files (Excel Documents, Custom Office Templates, Microsoft Office), and system/app config files (AdGuard, CCleaner Registry, Corsair iCUE Profiles, Desktop, Icon Files, My Shapes).

**Recommended folder taxonomy:**

```
OneDrive/
├── Work/
│   ├── Development/
│   ├── Cloud-Infrastructure/
│   └── AI-Agents/
├── Personal/
│   ├── Resumes/
│   ├── Finance/
│   └── Media/
├── Projects/
│   ├── [project-name]/
│   └── ...
├── Archive/
│   ├── Gaming/
│   └── Legacy/
└── System-Backups/
    ├── App-Configs/
    └── Browser/
```

### Account: will.bracken.3@outlook

**Status:** NOT CONNECTED  
**Evidence:** Does not appear in File Explorer navigation pane. No OneDrive sync icon for this account in system tray area.

**Remediation:** Sign into OneDrive with this account via Settings > Accounts > Add account, or via the OneDrive system tray icon > Settings > Account > Add an account.

---

## Google Drive Findings

### Account: william3bracken@gmail.com (main)

**Status:** API accessible via MCP connector  
**Storage Plan:** Google One / 5TB+ Pro  
**Local Sync:** "Drive - Cloud Drive" desktop shortcut exists but may not be properly configured for this Windows machine

**Critical Issues:**

The drive is being used primarily as a raw Mac device backup. Recent files analysis shows: Apple Photos database files (.sqlite, .sqlite-wal, .sqlite-shm, .plist) actively syncing, git repository internals (.gitstatus, FETCH_HEAD), VS Code extensions and settings (extensions.json, argv.json, claude-code-settings.schema.json), and hash-named cache files (44cf5ca2*.txt).

No Google Docs, Sheets, or Slides documents were found. The only PDFs are matplotlib example files (subplots.pdf, matplotlib.pdf, filesave.pdf, etc.) duplicated across at least 2 parent folder hierarchies, and theme-showcase.pdf duplicated across 3 folders.

**Storage waste estimate:** The Apple Photos databases alone (.sqlite files + WAL journals) are consuming significant storage with constant sync churn. The Photos.sqlite-wal file alone is 2MB and updates frequently.

### Account: willbracken33@gmail.com (second)

**Status:** NOT CONNECTED to any MCP connector or local sync client  
**Remediation:** Add to Google Drive MCP connector or install/configure Google Drive for Desktop.

### Google Drive for Desktop

The desktop shortcut "Drive - Cloud Drive" suggests Google Drive for Desktop may be installed but possibly misconfigured or not signed into the correct accounts on this Windows machine. The Mac system files being synced via API suggest another device (Mac) is doing the syncing.

---

## Duplicate Analysis

### Confirmed Duplicates in Google Drive

| File | Size | Locations |
|------|------|-----------|
| subplots.pdf | 1,714 B | 2 parent folders |
| matplotlib.pdf | 22,852 B | 2 parent folders |
| filesave.pdf | 1,734 B | 2 parent folders |
| zoom_to_rect.pdf | 1,609 B | 2 parent folders |
| forward.pdf | 1,630 B | 2 parent folders |
| back.pdf | 1,623 B | 2 parent folders |
| move.pdf | 1,867 B | 2 parent folders |
| home.pdf | 1,737 B | 2 parent folders |
| hand.pdf | 4,172 B | 2 parent folders |
| help.pdf | 1,813 B | 2 parent folders |
| qt4_editor_options.pdf | 1,568 B | 2 parent folders |
| theme-showcase.pdf | 124,310 B | 3 parent folders |

### Files That Should NOT Be in Cloud Storage

System/app files detected that create sync churn and waste storage: .sqlite databases (Photos.sqlite, MediaAnalysis.sqlite, VUIndex.sqlite, CLSLocationCache.sqlite), .plist files (PhotoAnalysisServicePreferences.plist, syncstatus.plist, appPrivateData.plist), .sqlite-wal and .sqlite-shm journal files (constant write churn), git internals (.gitstatus, FETCH_HEAD), and application cache files (hash-named .txt files).

---

## Generalized Error Patterns (Multi-Machine)

These issues commonly affect multi-account cloud storage setups across OS's:

1. **Account confusion:** When multiple OneDrive or Google Drive accounts are on one machine, sync clients often default to only one account. The second account silently disconnects after Windows updates or credential refreshes.

2. **Mac-to-Windows sync pollution:** Google Drive for Desktop on Mac syncs application support directories (Photos, iCloud, VS Code) by default. These files are useless on Windows and create constant sync traffic.

3. **Files On Demand conflicts:** OneDrive's "Available when online" mode can make files appear present but fail to open when offline. This makes the drive feel "barely usable" even though sync is technically working.

4. **Duplicate sync paths:** When the same Google account is signed into Drive for Desktop on multiple machines, each machine may create its own "Computer Backup" folder, leading to duplicated directory trees.

5. **SQLite + cloud sync = corruption risk:** SQLite databases (.sqlite) use WAL journaling that requires atomic file operations. Cloud sync services can't guarantee atomicity, leading to database corruption, constant re-syncs, and "file in use" errors.

---

## Remediation Actions

### Immediate (Today)

1. Run `python scripts/cloud-storage-diagnostic.py` to get detailed local diagnostics
2. Sign into OneDrive with will.bracken.3@outlook account
3. Check Google Drive for Desktop settings — ensure both Gmail accounts are connected
4. Exclude system directories from Google Drive sync (Photos library, .git folders, VS Code extensions)

### Short-term (This Week)

5. Reorganize OneDrive Documents folder using the recommended taxonomy above
6. Delete confirmed duplicate files in Google Drive
7. Set up Google Drive API access for both accounts
8. Configure `.env` file with Azure OpenAI and Supabase credentials
9. Run `setup_supabase.sql` to create the pgvector schema
10. Run the vector search indexer on cleaned-up storage

### Medium-term (2-Week Sprint)

11. Complete vector search indexing across all cloud sources
12. Partition Google storage (~1/3 personal, rest for DuckDB/tools)
13. Set up SSH connectivity for i7 laptop
14. Migrate vector search from Azure to local embeddings before credits expire
15. Document final architecture for other machines

---

## Tools Created

| File | Lines | Purpose |
|------|-------|---------|
| `scripts/cloud-storage-diagnostic.py` | 707 | Windows cloud storage diagnostic tool |
| `scripts/vector-search/indexer.py` | 522 | Vector search indexing pipeline |
| `scripts/vector-search/search.py` | 335 | Semantic search interface |
| `scripts/vector-search/config.py` | 168 | Configuration management |
| `scripts/vector-search/setup_supabase.sql` | 81 | pgvector database schema |
| `scripts/vector-search/requirements.txt` | 8 | Python dependencies |
| `scripts/vector-search/USAGE.txt` | 206 | Setup and usage guide |
