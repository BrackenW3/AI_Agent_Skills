# BrackenW3 Next Phase Action Plan
**Generated:** 2026-04-22 | **Sprint:** Infrastructure Build Week 1

---

## 1. Scripts to Run — Step by Step (Next Phase)

Run these IN ORDER. Each step assumes the previous completed successfully.

### Step A: Desktop Recovery (CLX-DESKTOP — do this FIRST)
```
1. Double-click: AI_Agent_Skills\scripts\kill-nodes.bat
   → Kills all zombie node.exe processes. Takes 3-5 seconds.
   → Verify: open Task Manager, search "node" — should be 0

2. Right-click → Run as Administrator: AI_Agent_Skills\scripts\fix-startup-admin.bat
   → Cleans startup items, disables unnecessary services
   → If UAC prompt fails: skip to Step 3, come back after reboot

3. Right-click → Run as Administrator: AI_Agent_Skills\scripts\fix-windows-search.bat
   → Restricts Windows Search indexing scope (remove G:, H:, iCloudDrive)

4. Reboot Desktop. After reboot, verify:
   → Task Manager: <10 node.exe processes
   → Typing lag: <1 second
   → RAM: <70% usage at idle
```

### Step B: Environment Setup (Any machine — Desktop preferred)
```
5. Open PowerShell, navigate to AI_Agent_Skills\scripts\vector-search\
   → Edit .env file with your actual keys:
     AZURE_OPENAI_API_KEY=<your key>
     AZURE_OPENAI_ENDPOINT=https://willbracken-aoai-ihe42a.openai.azure.com
     SUPABASE_URL=https://smttdhtpwkowcyatoztb.supabase.co
     SUPABASE_API_KEY=<your anon key>

6. pip install -r requirements.txt --break-system-packages
   → Installs: supabase, openai, pypdf, python-docx, aiohttp, python-dotenv

7. python bootstrap.py
   → Validates all connections (Azure OpenAI, Supabase)
   → Creates tables if missing, tests embedding generation
   → Expected output: "All checks passed" with green indicators
```

### Step C: First Vectorization Run (Desktop)
```
8. python indexer.py --path "C:\Users\User\AI_Agent_Skills" --device desktop-clx
   → Indexes all files in AI_Agent_Skills as a test run
   → Creates embeddings via Azure OpenAI, stores in Supabase
   → Watch for: progress bar, files processed count
   → Expected: ~50-100 files, 2-5 minutes

9. python search.py "vector search configuration" --limit 5
   → Tests semantic search against indexed documents
   → Should return relevant config files ranked by similarity
```

### Step D: Full Indexing (Desktop — run overnight if needed)
```
10. python indexer.py --path "C:\Users\User\Documents" --device desktop-clx
11. python indexer.py --path "C:\Users\User\VSCodespace" --device desktop-clx
12. python indexer.py --path "C:\Users\User\OneDrive\Documents" --device desktop-clx
    → These will take longer (30min-2hrs depending on file count)
    → Azure rate limit: 200 req/min — indexer handles backoff automatically
```

### Step E: Cloud Storage Cleanup (After indexing)
```
13. python partition-gdrive.py --dry-run
    → Shows what WOULD be organized without making changes
    → Review output, then run without --dry-run to execute

14. python cleanup-gdrive.py --dry-run
    → Identifies duplicates via SHA256 hash comparison
    → Review, then run without --dry-run

15. python cloud-storage-diagnostic.py
    → Full diagnostic: all cloud storage providers, sync status, issues
```

### Step F: Laptop + MacBook (After Desktop is stable)
```
16. On Laptop: git pull in AI_Agent_Skills, repeat Steps B-D with --device laptop-i7
17. On MacBook: git pull, repeat Steps B-D with --device macbook
18. Run SSH setup scripts (AI_Agent_Skills\ssh-keys\setup-*.ps1 / .sh)
```

---

## 2. Items Requiring More Work (Prioritized)

### P0 — Critical Path (blocks everything)
| Item | Effort | Details |
|------|--------|---------|
| Desktop node.exe + UAC fix | 10 min manual | Must be done before any scripting. Kill nodes → test UAC → run admin scripts |
| .env credential setup | 5 min | Need actual Supabase anon key and Azure OpenAI key in .env file |
| Delete .git/index.lock | 1 min | In AI_Agent_Skills folder. OneDrive contention — just delete the file |

### P1 — High Priority (enables next features)
| Item | Effort | Details |
|------|--------|---------|
| Bitdefender exclusions | 10 min | Add: node_modules, .git, .vscode, AppData\Local\AnthropicClaude, VSCodespace. Massive perf impact |
| GitHub MCP reconnect | 5 min | Reconnect the GitHub connector in Claude with fresh token |
| Google Drive cleanup | 30 min | Run partition + cleanup scripts. Hundreds of MB of node_modules syncing |
| Install Dispatch on Laptop | 5 min | Enables cross-device Claude sessions |
| NordLocker install | 5 min per machine | 3TB free encrypted storage — install on all 3 machines |

### P2 — Medium Priority (enhances capability)
| Item | Effort | Details |
|------|--------|---------|
| Neon Postgres account | 15 min | Create free tier account at neon.tech, deploy document catalog schema |
| CockroachDB schema expansion | 30 min | Connect to existing cluster, add dedup tracking tables |
| Metabase dashboard creation | 1-2 hrs | Already deployed on Supabase — needs dashboard configuration |
| SSH mesh activation | 20 min per machine | Run setup scripts, enable sshd (admin required on Windows) |

### P3 — Nice to Have
| Item | Effort | Details |
|------|--------|---------|
| iDrive device cleanup | 1-2 hrs | Use viewer to identify valuable files, consolidate, delete old devices |
| MacBook SSD optimization | 30 min | Move large files to SD card or NordCloud |
| Neo4j knowledge graph setup | 2-3 hrs | Build document relationship graph from indexed data |

---

## 3. AI Agent Tiers & Cost Estimates (via OpenRouter)

### Tier 1: Premium Reasoning ($15-75/M output tokens)
Best for: Architecture decisions, complex debugging, code review, security analysis

| Model | Input $/M | Output $/M | Context | Best For |
|-------|-----------|------------|---------|----------|
| anthropic/claude-opus-4 | $15.00 | $75.00 | 200K | Complex architecture, critical decisions |
| openai/o3 | $10.00 | $40.00 | 200K | Deep reasoning, math-heavy analysis |
| x-ai/grok-3 | $3.00 | $15.00 | 131K | Research, alternative perspectives |
| google/gemini-2.5-pro | $1.25 | $10.00 | 1M | Massive context analysis, full-repo review |

**Monthly estimate:** $20-80/mo at moderate use (50-100 queries/day)

**Preset prompt — Premium Orchestrator:**
```
You are a senior infrastructure architect working on a multi-machine, multi-cloud 
project. You have access to: Azure OpenAI, Supabase (pgvector), Cloudflare 
(D1/R2/KV), CockroachDB, Neon Postgres, DuckDB, Neo4j. 3 machines: Windows 11 
Desktop (CLX-DESKTOP), Windows 11 Laptop, MacBook. GitHub: BrackenW3 org.
Make architectural decisions, review code for security/performance, and design 
system integrations. Always consider cost optimization and use free tiers where 
possible. Budget: ~$180 Azure credits remaining.
```

### Tier 2: Workhorse ($1-15/M output tokens)
Best for: Daily coding, script writing, API integration, documentation

| Model | Input $/M | Output $/M | Context | Best For |
|-------|-----------|------------|---------|----------|
| anthropic/claude-sonnet-4 | $3.00 | $15.00 | 200K | Coding, analysis, tool use |
| openai/gpt-4o | $2.50 | $10.00 | 128K | General coding, API work |
| google/gemini-2.5-flash | $0.15 | $0.60 | 1M | High-volume analysis, huge context |
| deepseek/deepseek-r1 | $0.55 | $2.19 | 64K | Reasoning tasks at budget price |
| openai/gpt-4.1 | $2.00 | $8.00 | 1M | Coding with massive context |

**Monthly estimate:** $10-40/mo at heavy use (200+ queries/day)

**Preset prompt — Coding Workhorse:**
```
You are a Python/TypeScript developer working on cloud storage and vector search 
pipelines. Key stack: Python (asyncio, aiohttp, supabase-py), Azure OpenAI 
(text-embedding-3-small, 1536 dims), Supabase (pgvector, RLS), Cloudflare Workers.
Write clean, tested code. Include error handling, retry logic with exponential 
backoff, and environment variable configuration. Target Python 3.10+.
GitHub repo: BrackenW3/AI_Agent_Skills. Follow existing patterns in scripts/.
```

### Tier 3: Budget ($0.10-1/M output tokens)
Best for: Batch processing, file classification, log analysis, simple transforms

| Model | Input $/M | Output $/M | Context | Best For |
|-------|-----------|------------|---------|----------|
| anthropic/claude-haiku-4.5 | $0.80 | $4.00 | 200K | Fast classification, summaries |
| openai/gpt-4o-mini | $0.15 | $0.60 | 128K | Cheap general purpose |
| google/gemini-2.0-flash | $0.10 | $0.40 | 1M | Ultra-cheap with huge context |
| meta-llama/llama-3.3-70b | $0.10 | $0.30 | 128K | Open-source, self-hostable |
| qwen/qwen-2.5-72b | $0.15 | $0.40 | 128K | Strong multilingual, coding |

**Monthly estimate:** $2-15/mo even at very heavy use (500+ queries/day)

**Preset prompt — Batch Processor:**
```
You are a file classification and data processing agent. Your job:
1. Read file metadata (name, path, size, type, modified date)
2. Classify into categories: Document, Code, Media, Config, Junk, Duplicate
3. Recommend action: Keep, Archive, Delete, Consolidate
4. Output JSON with classification and confidence score
Be fast and concise. No explanations unless asked. Output valid JSON only.
```

### Tier 4: Ultra-Budget (Free or <$0.10/M)
Best for: Bulk data labeling, simple extraction, formatting, high-volume low-stakes

| Model | Input $/M | Output $/M | Context | Best For |
|-------|-----------|------------|---------|----------|
| google/gemini-2.5-flash-lite | $0.02 | $0.10 | 1M | Near-free with good quality |
| openai/gpt-4.1-nano | $0.10 | $0.40 | 1M | Tiny cost, decent capability |
| meta-llama/llama-3.1-8b | $0.02 | $0.05 | 128K | Self-hostable, nearly free |
| microsoft/phi-4 | $0.03 | $0.10 | 16K | Small but capable for structured tasks |

**Monthly estimate:** $0.50-5/mo even at massive volume (1000+ queries/day)

### Total Monthly Cost Estimates (All Tiers Combined)

| Usage Level | Low | Medium | High | Max |
|-------------|-----|--------|------|-----|
| Queries/day | 50 | 200 | 500 | 1000+ |
| Monthly cost | $5-15 | $15-50 | $40-120 | $80-200 |

**Recommended mix:** 70% Tier 2-3, 20% Tier 1, 10% Tier 4. Most work should run on Sonnet/Flash/Haiku with Opus reserved for architecture decisions.

---

## 4. Quick Wins You Can Do Right Now (Unblocks Me)

These take <5 minutes each and each one unblocks further automation:

1. **Delete `.git/index.lock`** in AI_Agent_Skills folder → unblocks local git operations
2. **Run `kill-nodes.bat`** → unblocks all Desktop scripting
3. **Give me your Supabase anon key** → I can deploy Edge Functions for automated indexing
4. **Reconnect GitHub MCP** in Claude settings → I can push code directly without API workarounds
5. **Open Azure Portal** → tell me your subscription ID → I can deploy Azure Functions for serverless indexing triggers
6. **Open iDrive web portal** → leave it logged in → I can audit device backups via Chrome MCP

Each of these lets me kick off a new development stream immediately.

---

## 5. Azure Build-Out — What to Do in the Next Hour

### Already deployed:
- Azure OpenAI: text-embedding-3-small on willbracken-aoai-ihe42a.openai.azure.com
- ~$180 credits, ~2 weeks remaining

### What you can do NOW (15 min total):

**A. Get your Subscription ID:**
```
Azure Portal → Subscriptions → copy the Subscription ID
```

**B. Fix the cert auth issue (use device code flow):**
```bash
az login --use-device-code
# Opens browser, enter code, authenticate with password (bypasses cert prompt)
```

**C. Once logged in, create resources:**
```bash
# Resource group
az group create --name brackenw3-infra --location eastus

# Storage account for blob staging
az storage account create --name brackenw3storage --resource-group brackenw3-infra --sku Standard_LRS

# Function app for serverless indexing
az functionapp create --name brackenw3-indexer --resource-group brackenw3-infra \
  --consumption-plan-location eastus --runtime python --runtime-version 3.10 \
  --storage-account brackenw3storage
```

**D. Or just give me the subscription ID** and I'll generate complete deployment scripts you can paste into Azure Cloud Shell (no local az cli needed).

### What I'll build once Azure is accessible:
- **Azure Functions:** File-change triggers → auto-embed new documents → push to Supabase
- **Azure Blob Storage:** Staging area for large file transfers between machines
- **Azure Static Web App:** Host the infrastructure dashboard and iDrive viewer publicly

### Cost estimate:
- Functions: ~$0 (consumption plan, free tier covers ~1M executions/month)
- Blob Storage: ~$0.02/GB/month (negligible for staging)
- Static Web App: Free tier available
- Total new Azure spend: ~$1-5/month on top of existing OpenAI credits

---

## 6. Immediate Actions for DuckDB, CockroachDB, etc.

### DuckDB (ready to go — no account needed)
```bash
pip install duckdb --break-system-packages
python scripts/gdrive-duckdb-bridge.py --scan
# Mounts Google Drive files as virtual SQL tables
# Query: SELECT * FROM read_csv('gdrive://path/to/file.csv')
```
DuckDB runs locally, zero cost. The bridge script connects to Google Drive API and lets you query files with SQL. Already fixed and pushed to GitHub.

### CockroachDB (need connection string)
- You have an existing serverless cluster. I need:
  - Connection string (postgresql://...@free-tier.gcp-...:26257/defaultdb?sslmode=verify-full)
  - Or: log into cockroachlabs.com → Clusters → Connect → copy the string
- Once I have it, I'll deploy: dedup tracking, cross-device metadata sync, distributed file catalog

### Neon Postgres (15 min setup)
1. Go to https://neon.tech → Sign up (free, no credit card)
2. Create project: "brackenw3-catalog" in us-east-1
3. Copy the connection string
4. I'll deploy: document_catalog + search_history schemas with pgvector

### Neo4j (already installed on Desktop)
- Neo4j Desktop is installed but needs a database created
- Once vectorization is running, I'll build a knowledge graph from document relationships
- This is Phase 4 work — not urgent yet

---

## 7. Timeline to Results

| Milestone | Time from Now | What You'll See |
|-----------|---------------|-----------------|
| Desktop responsive | 10-15 min | After kill-nodes + reboot, typing lag gone |
| First search results | 30-45 min | After bootstrap + indexer on AI_Agent_Skills folder |
| Full Desktop indexed | 2-4 hours | All Documents/VSCodespace/OneDrive searchable via semantic search |
| Google Drive cleaned | 1-2 hours | Duplicates identified, dev artifacts flagged for removal |
| Cross-device search | 1-2 days | After Laptop + MacBook run indexer with same Supabase target |
| iDrive consolidated | 2-3 days | After reviewing viewer, deleting old devices, consolidating |
| Full pipeline automated | 5-7 days | Nightly indexing, auto-archive, sync monitoring |
| Front-end dashboard live | 7-10 days | Metabase or custom dashboard with real-time metrics |

**Critical path:** Desktop fix → .env setup → bootstrap → indexer → first search result. Everything else can run in parallel.

The fastest path to "seeing something work" is 30-45 minutes from right now if you kill nodes and set up .env.

---

## 8. Process Flow & Advice Going Forward

### Recommended Daily Workflow
```
Morning:
  1. Check infrastructure dashboard (bookmark idrive-data-viewer.html and infrastructure-dashboard.html)
  2. Review any overnight indexing results
  3. Run search.py for any files you need to find

During work:
  4. Use Claude (Cowork) for orchestration and complex tasks
  5. Dispatch agents to OpenRouter for parallel batch work
  6. New files auto-indexed if Azure Functions are deployed

Evening:
  7. Kick off full re-index on any machine with new files
  8. Review dedup reports from cleanup-gdrive.py
  9. Archive stale files (>90 days untouched → move to COLD tier)
```

### Architecture Advice
- **Don't over-engineer storage tiers yet.** Get the indexer running first, then optimize.
- **Start with one machine** (Desktop), get it fully working, then replicate to Laptop/MacBook.
- **Use free tiers aggressively:** Supabase free (500MB), Neon free (512MB), CockroachDB free (10GB), Cloudflare free (D1 5GB, R2 10GB, KV unlimited reads).
- **Azure credits are a sprint resource** — burn them on OpenAI embeddings now while they last. After credits expire, switch to a cheaper embedding model (Gemini embedding or local).
- **Git lock issue is real** — move AI_Agent_Skills OUT of OneDrive to C:\Users\User\AI_Agent_Skills (outside OneDrive sync). Use git push/pull for sync instead.

### Multi-Agent Strategy
- **Claude Cowork (you're here):** Orchestration, infrastructure, MCP integrations
- **Claude Code (terminal):** Deep code fixes, test generation, refactoring
- **OpenRouter agents:** Batch file classification, data processing at scale
- **Gemini CLI:** Google Drive API work (native integration advantage)
- **GitHub Copilot:** Inline code completion while editing scripts

---

## 9. AV Exclusion Paths (Bitdefender + Windows Defender)

The performance degradation you're seeing is almost certainly AV scanning dev files. Every npm install, git operation, and Python script triggers thousands of file scans.

### Add these exclusions in Bitdefender Settings → Antivirus → Exclusions:

**Folders to exclude:**
```
C:\Users\User\node_modules
C:\Users\User\AppData\Local\AnthropicClaude
C:\Users\User\AppData\Roaming\Claude
C:\Users\User\.vscode
C:\Users\User\VSCodespace\node_modules
C:\Users\User\AI_Agent_Skills\.git
C:\Users\User\AI_Agent_Skills\node_modules
C:\Users\User\AppData\Local\Programs\cursor
C:\Users\User\AppData\Local\Google\Chrome\User Data\Default\Extensions
C:\Users\User\.npm
C:\Users\User\.cache
C:\ProgramData\chocolatey
```

**Processes to exclude:**
```
node.exe
python.exe
python3.exe
git.exe
code.exe (VS Code)
cursor.exe
claude.exe
```

### Windows Defender (also add these):
Settings → Virus & Threat Protection → Manage Settings → Exclusions → Add
Same paths as above.

### Why it gets worse over time:
- **npm installs** create thousands of tiny .js files → each one scanned
- **git operations** touch hundreds of files in .git → each one scanned
- **VS Code/Cursor** file watchers trigger re-scans on every save
- **OneDrive sync** ALSO triggers scans when it downloads/uploads
- **Compound effect:** AV scans trigger sync, sync triggers scans → feedback loop

After adding exclusions, you should see 30-50% RAM reduction and significantly faster file operations.

---

## 10. Cloudflare Traffic Capture & Bot Experiments

### What's Possible with Cloudflare (Already Available):

**A. Bot traffic analysis with Workers + D1 (essentially free):**
You already have `willbracken-observability` D1 database with request_logs and security_events tables. A Cloudflare Worker can:
- Log every request (IP, User-Agent, path, response time, country)
- Detect bot patterns (rate, known bot UA strings, automated behavior)
- Store in D1 for SQL analysis
- Cost: **$0** on Workers free plan (100K requests/day)

**B. Cloudflare Analytics (built-in, free):**
- Web Analytics: page views, unique visitors, countries, devices
- Security Analytics: threats blocked, bot score distribution
- Already available on your account, just needs a domain/zone configured

**C. Azure alternative (Blob + Functions):**

| Component | What it does | Monthly cost |
|-----------|-------------|-------------|
| Azure Blob Storage | Store raw request logs as JSON | ~$0.02/GB ($0.50 for 25GB) |
| Azure Functions | Process and aggregate logs | ~$0 (consumption plan) |
| Azure Log Analytics | Query and visualize | ~$2.76/GB ingested |
| Total for 1GB/month of logs | | ~$3-5/month |

**Cloudflare is clearly cheaper** for this use case — the data is already at the edge. Azure makes sense only if you need to correlate with Azure-hosted services.

### R2 vs Azure Blob for Log Storage:

| Feature | Cloudflare R2 | Azure Blob |
|---------|--------------|------------|
| Storage cost | $0.015/GB/month | $0.018/GB/month |
| Egress | **$0 (free!)** | $0.087/GB |
| Free tier | 10GB/month | 5GB (first 12 months) |
| Best for | Edge-generated logs | Azure-integrated pipelines |

**Recommendation:** Use R2 for log storage (you already have `willbracken-logs` bucket). Zero egress costs is a huge advantage. Only use Azure Blob for staging data that Azure Functions need to process.

### Quick Experiment — Deploy a Traffic Capture Worker:
I can deploy a Cloudflare Worker right now that logs all traffic to your D1 database. Takes about 5 minutes. It would give you:
- Real-time request logging with bot detection
- Geographic distribution of visitors
- Performance metrics (response times)
- Security event tracking

Say the word and I'll deploy it via the Cloudflare MCP.

---

*Generated 2026-04-22 | AI_Agent_Skills/docs/next-phase-action-plan.md*
