# Cloud Storage Diagnosis & Vectorization Plan
**Date:** 2026-04-21  
**Priority:** High — ~2 weeks of Azure credits remaining

---

## Part 1: Cloud Storage Current State

### OneDrive (2 accounts)
| Account | Status | Capacity |
|---------|--------|----------|
| will.i.bracken@outlook.com | Running but auth issues | ~15 TB |
| will.bracken.3@outlook.com | Auth issues | ~15 TB |

**Problem:** OneDrive.exe is running but showing errors — likely stale OAuth tokens.  
**Fix now:**
1. Right-click OneDrive tray icon → Settings → Account
2. Sign out of both accounts, sign back in
3. After re-auth, verify sync folders in OneDrive Settings → Backup

### Google Drive (2 accounts)
| Account | Status |
|---------|--------|
| william3bracken@gmail.com | **NOT INSTALLED** |
| willbracken33@gmail.com | **NOT INSTALLED** |

**Google Drive for Desktop is not installed on this machine at all.**  
**Fix now:**
1. Download: https://www.google.com/drive/download/
2. Install "Google Drive for Desktop"
3. Sign in with primary `william3bracken@gmail.com`
4. Add second account `willbracken33@gmail.com` in Drive settings

### iDrive (1000 TB available, barely used)
- Installed and running in background
- Shell extension active on right-click
- Massive unused capacity — best use: cold backup of H:\ archive files

### Nord Vault (2 TB)
- Running via NordVPN startup
- Good for sensitive/encrypted files

---

## Part 2: Gmail Partition Strategy

### Current: two Gmail accounts, mostly unused for storage
**Proposed split for `william3bracken@gmail.com`:**
- **1/3 Personal** — email, calendar, personal docs in Drive
- **2/3 Data/Storage** — Google Drive as DuckDB data source, large dataset storage

**For `willbracken33@gmail.com`:**
- Dedicated data lake account — AI/ML datasets, exports, backups

### Google Drive as DuckDB Storage
Google Drive FUSE mount (Drive for Desktop) makes Drive appear as a local drive letter.  
DuckDB can query files directly from Drive without downloading them:

```sql
-- Query Parquet file stored in Google Drive
SELECT * FROM read_parquet('G:/My Drive/data/dataset.parquet');

-- Or via HTTP URL if sharing is enabled
SELECT * FROM read_parquet('https://drive.google.com/uc?id=FILE_ID');
```

**Implementation plan:**
1. Mount Drive as `D:\GoogleDrive\` (Drive for Desktop setting)
2. Store structured data as Parquet files in Drive
3. DuckDB queries Drive via the mounted path

---

## Part 3: Vectorization Project (Azure Credits — 2 Weeks)

### Objective
Build a semantic search system across all cloud storage locations so files are findable by meaning, not just filename.

### Architecture
```
Cloud Storage (OneDrive, Drive, iDrive)
         ↓
   [Extraction Pipeline]
         ↓
   Azure OpenAI Embeddings (text-embedding-3-small)
         ↓
   Azure AI Search (vector index)
         ↓
   Query Interface (web app / Claude MCP)
```

### Phase 1: Local Processing + Azure Embedding (Week 1)

Files stay LOCAL. Only text/metadata is sent to Azure for embedding.

**Step 1 — File catalog with DuckDB**
```python
# catalog.py — scan all cloud mounts and build file index
import duckdb
con = duckdb.connect('file_catalog.duckdb')
con.execute("""
    CREATE TABLE files AS 
    SELECT 
        file, size, last_modified,
        strftime(last_modified, '%Y-%m') as month
    FROM glob('C:/Users/User/iCloudDrive/**/*')
    UNION ALL
    SELECT file, size, last_modified, strftime(last_modified, '%Y-%m')
    FROM glob('C:/Users/User/OneDrive/**/*')
""")
```

**Step 2 — Text extraction**
```python
# Extract text from PDFs, DOCX, XLSX, code files
# Libraries: pypdf2, python-docx, openpyxl, ast
# Output: file_id → text chunks (512 token max)
```

**Step 3 — Embed with Azure OpenAI**
```python
from openai import AzureOpenAI
client = AzureOpenAI(
    azure_endpoint="https://your-resource.openai.azure.com/",
    api_version="2024-02-01"
)
# Cost: text-embedding-3-small = $0.02/1M tokens
# For 100K files, avg 500 tokens each = 50M tokens = ~$1
response = client.embeddings.create(
    model="text-embedding-3-small",
    input=text_chunk
)
```

**Step 4 — Store vectors in Azure AI Search**
```python
# Azure AI Search vector index
# Already have Azure infra (AZURE_SUBSCRIPTION_ID: 11301eb9-...)
# Use existing service or create in West US 2
# Free tier: 50MB vector storage (~100K documents)
# Basic tier: $73/month — covers millions of docs
```

### Phase 2: Query Interface (Week 2)

**MCP Server for Claude Code**
Build a custom MCP server that wraps the vector search:
```typescript
// File: AI_Agent_Skills/mcp_servers/file-search/index.ts
// Tool: search_files(query: string) → returns top 10 matching files
// Tool: get_file_summary(path: string) → returns AI summary of file
```

**DuckDB-backed deduplication**
```sql
-- Find duplicate files by content hash
SELECT md5_hash, COUNT(*) as copies, LIST(file_path) as locations
FROM file_hashes
GROUP BY md5_hash
HAVING COUNT(*) > 1
ORDER BY COUNT(*) DESC;
```

### Estimated Azure Credit Usage
| Service | Tier | Weekly Cost |
|---------|------|-------------|
| Azure OpenAI (embeddings) | Pay-per-use | ~$2-5 (one-time batch) |
| Azure AI Search | Basic | ~$36/week |
| Azure Storage (blob, for index backup) | LRS | ~$1/week |
| **Total/week** | | **~$40/week** |

With 2 weeks of credits, this is entirely feasible.

### Priority Order (by value)
1. **OneDrive documents** — most used, most searchable value
2. **iCloudDrive** — photos/docs from Apple ecosystem  
3. **Google Drive** — after installing Drive for Desktop
4. **H:\ archive** — large cold storage, index metadata only

---

## Part 4: File Organization Strategy

### OneDrive (15 TB each account) — Proposed Structure
```
OneDrive/
├── Active/              ← Current year projects
│   ├── Work/
│   ├── Personal/
│   └── AI_Projects/
├── Archive/             ← Previous years, organized by year
│   ├── 2024/
│   ├── 2023/
│   └── ...
├── Data/               ← Structured data files (Parquet, CSV, JSON)
└── Media/              ← Videos, photos (consider iDrive for this)
```

### H:\ Drive (3.7 TB free) — Migration Target
```
H:\
├── Archives/           ← Move from C: SSD
│   ├── Projects/       ← Old project backups
│   ├── Downloads/      ← Downloaded installers, ISOs
│   └── Media/
├── VMs/                ← Virtual machine disk images
├── Backups/            ← Local backup destination
└── Dev/                ← Large repositories that don't need SSD speed
```

### Deduplication Approach
1. Use `fdupes` (Linux/WSL) or `dupeGuru` (Windows) to scan H:\ + OneDrive mount
2. DuckDB file catalog (above) handles the cataloging
3. Keep one copy in cloud (OneDrive/iDrive), delete local duplicate

---

## Part 5: Implementation Timeline

### This Week (immediate, low Azure cost)
- [ ] Install Google Drive for Desktop
- [ ] Re-auth OneDrive accounts
- [ ] Set up DuckDB file catalog script
- [ ] Build file index for C:\ and cloud mounts
- [ ] Run deduplication scan on H:\

### Week 2 (Azure vectorization sprint)
- [ ] Deploy Azure AI Search (Basic tier)
- [ ] Batch embed all OneDrive text documents
- [ ] Build file search MCP server
- [ ] Set up Claude Code integration for file search
- [ ] Test query interface

### After 2-Week Sprint
- [ ] Switch Azure AI Search to Free tier if index fits (< 50MB)
- [ ] Schedule weekly incremental re-indexing
- [ ] Expand to Google Drive and iDrive

---

## Appendix: Azure Resources Already Available
From `~/.claude.json` MCP configuration:
- **Azure Subscription:** `11301eb9-a26b-4b41-badb-c1b10f446d99`
- **Azure Tenant:** `99150341-b2dc-4715-bab9-3b1cd11b5411`
- **CosmosDB:** `az-nosql-cosmosdb.documents.azure.com` (can store file metadata)
- **Azure PostgreSQL:** `willbracken-pg-wb0414.postgres.database.azure.com` (vector extension pgvector available)
- **Supabase:** Connected (also has pgvector — free tier)
- **CockroachDB:** Connected (`0fcabf5e-1e74-4206-8e4c-a8def83f6bdf`)

**Recommendation: Use Supabase pgvector first** — it's free tier and already connected, saving Azure credits for Azure OpenAI embeddings only.
