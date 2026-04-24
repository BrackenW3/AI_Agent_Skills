# PROJECTS.md — Master Project Tracker
# Updated: 2026-04-23
# READ THIS before starting any session. UPDATE THIS before ending any session.

---

## 🔴 ACTIVE — IN PROGRESS (work on these, in priority order)

### 1. n8n Local Deployment + Cloud Integration
**Repo:** `WSL_Docker/n8n/`
**Priority:** HIGH — ties into almost everything else
**Status:** ~50% — local deployment partially works, NOT basic, full robust platform
**Actual scope:**
- All APIs pre-loaded for all agents (OpenRouter, Azure, Cloudflare, GitHub, etc.)
- Robust enough to handle any automation down the line
- Local LLM support (Ollama)
- Cloud resources on Railway for heavy tasks
- Shareable to father Bill for simple tasks (doc sorting, file conversion, AI features)
**Blocked on:** Unknown — agent stopped without reporting blocker
**Definition of done:**
- [ ] n8n running locally via Docker on all 3 machines (plug and play)
- [ ] n8n.willbracken.com routing via Cloudflare
- [ ] ALL API credentials pre-loaded (OpenRouter, Azure OpenAI, GitHub, Cloudflare, Perplexity, xAI, Supabase, CockroachDB, Neo4j, Atlassian)
- [ ] Local LLM connected (Ollama)
- [ ] OpenRouter tier routing integrated
- [ ] Railway cloud instance for heavy processing
- [ ] At least 5 working workflows end-to-end
- [ ] Simplified view for Bill (doc convert, sort, basic AI)
- [ ] README with setup instructions per machine
**Next step:** Check `WSL_Docker/n8n/` — find exactly where it stopped

---

### 2. Vector Search Pipeline (Azure Credits — DEADLINE ~2026-05-03)
**Repo:** `CloudDatabases/vector-search/` or `AI_Agent_Skills/scripts/vector-search/`
**Priority:** HIGH — Azure credits expiring
**Status:** Pipeline exists, was running locally on i9 (wrong), should run on Azure
**Blocked on:** Azure OpenAI login issues (may be fixed)
**Definition of done:**
- [ ] Pipeline runs on Azure VM, NOT locally on i9
- [ ] Indexes: willbracken.com, n8n.willbracken.com, Cloudflare data
- [ ] Embeddings stored in Supabase (pgvector)
- [ ] Search API working
- [ ] iCloudDrive explicitly EXCLUDED from indexing
**Next step:** Verify Azure OpenAI login, move pipeline config to Azure target

---

### 3. CockroachDB Schema + API
**Repo:** `CloudDatabases/cockroach/`
**Priority:** HIGH — $400 credits sitting unused
**Status:** Unknown — no confirmed progress seen
**Blocked on:** Unknown
**Definition of done:**
- [ ] Schema designed and deployed
- [ ] Basic CRUD API working
- [ ] Connected to at least one data source
- [ ] README with connection instructions
**Next step:** Check `CloudDatabases/cockroach/` for any existing work

---

### 4. Cloudflare Workers + willbracken.com
**Repo:** `Cloudflare/`
**Priority:** MEDIUM-HIGH
**Status:** ai-router built with 4-tier OpenRouter routing, 5 agent workers created, D1 schema initialized
**Blocked on:** mcp-bridge Dockerfile and n8n credential workflow JSON (pending from April 6 session)
**Definition of done:**
- [ ] ai-router deployed and routing correctly
- [ ] All 5 agent workers deployed
- [ ] D1 observability working
- [ ] mcp-bridge Dockerfile complete
- [ ] n8n credential workflow JSON complete
- [ ] willbracken.com resolving correctly
**Next step:** Complete mcp-bridge Dockerfile, then n8n credential JSON

---

### 5. Atlassian Family Site
**Repo:** `Atlassian/`
**Priority:** LOW-MEDIUM
**Status:** Basic setup done, needs useful workflows for non-technical family
**Blocked on:** Time/priority
**Definition of done:**
- [ ] PDF to Excel workflow working (wow factor for family)
- [ ] Project/appointment tracker visible
- [ ] Calendar integration (iCal)
- [ ] At least 3 AI agents useful for daily household tasks
- [ ] Cloudflare integration (if applicable)
**Next step:** Build PDF→Excel workflow first (highest impact, low effort)

---

### 6. Google Drive Cleanup + DuckDB Partition
**Repo:** `CloudDatabases/gdrive/`
**Priority:** MEDIUM
**Status:** Google Drive loaded with duplicates, only 5% used before, now cluttered
**Definition of done:**
- [ ] Duplicates removed
- [ ] Personal data: max 1-2TB partition
- [ ] Analytics partition: rest of 5TB for DuckDB
- [ ] DuckDB connected to analytics partition
**Next step:** Run cleanup script (review before executing), then partition

---

### 7. Storage Consolidation
**Repo:** `Cloud-Drive/`
**Priority:** MEDIUM
**NAMING — agents keep confusing these, never mix them up:**
- **iCloud Drive** = Apple cloud sync → should sync to i9, i7, Mac, Parallels (Win+Ubuntu) — currently BROKEN
- **iDrive** = separate 10TB backup service — unorganized, needs cleanup
- **DO NOT suggest buying more cloud storage** — Will has 80TB+ locally available

**Full hardware inventory:**
- i9 desktop: 5TB HDD (empty), RTX4080, 64GB RAM — primary
- i7 laptop: active
- MacBook M3 Pro: active
- Old PC (offline ~1yr): 4-5TB SSD + 60-80TB HDD, RTX2080, 64GB RAM — untapped resource
- iDrive: 10TB
- Nord Cloud: 2TB

**Storage tiers:**
- Hot: NVMe/SSD on active machines (working files)
- Warm: local HDD i9/old PC (recent archives)
- Cold: iDrive (long-term backup, not re-indexed)

**Definition of done:**
- [ ] iCloud Drive sync working on i9, i7, Mac, Parallels (Win+Ubuntu)
- [ ] iDrive cleaned — documents/important only, no program files, no duplicates
- [ ] Old PC spun up, added to local network as storage+compute node
- [ ] Cold/warm/hot tiers implemented — cold data excluded from vector re-indexing
- [ ] Nord Cloud assessed for useful role
**Next step:** Fix iCloud Drive sync, then spin up old PC and inventory it

---

### 8. AI_Agent_Skills Consolidation
**Repo:** `AI_Agent_Skills/`
**Priority:** MEDIUM — blocks efficiency of everything else
**Status:** Mixed — good structure exists but cloud work incorrectly placed here
**Definition of done:**
- [ ] Cloud/ETL work moved to correct repos
- [ ] MCP configs canonical and deployed to all 3 machines
- [ ] Single source of truth for agent skills
- [ ] All agents read CLAUDE.md before starting
**Next step:** Move misplaced files, then deploy MCP config to i7 and MacBook

---

---

### 5b. willbracken.com Landing Page (DESTROYED — rebuild needed)
**Repo:** `Cloudflare/`
**Priority:** HIGH — was professionally designed, Gemini destroyed it multiple times
**Status:** GONE — needs full rebuild
**Definition of done:**
- [ ] Professional design restored
- [ ] Live monitoring widgets
- [ ] Portfolio/projects section with interactive demos
- [ ] SSO via Azure AD for private sections
- [ ] PIN or GitHub login for general visitors
- [ ] Dynamic portfolio — shows how apps work interactively
- [ ] Low traffic optimized (Cloudflare Workers + D1)
- [ ] Public Neo4j graph visualization for visual appeal
**Note:** Do NOT let Gemini touch this. Claude only, with explicit backup before any change.
**Next step:** Check what exists in `Cloudflare/` right now, restore from git history if possible

---

### 5c. Email Management (Outlook + iCloud domain)
**Repo:** `Cloudflare/` or `WSL_Docker/n8n/`
**Priority:** MEDIUM — add to vector pipeline since we're indexing anyway
**Status:** Not started
**Emails:**
- `william.i.bracken@outlook.com` — PRIMARY, most important
- `will.i.bracken@icloud.com` — vanity domain via willbracken.com Cloudflare
**Definition of done:**
- [ ] Spam detection working on Outlook
- [ ] Unsubscribe automation (1-click via n8n workflow)
- [ ] Emails vectorized and searchable (same pipeline as docs)
- [ ] Email sorting/categorization
- [ ] Optional: share simplified version to father Bill (document sorting, conversion)
**Note:** iCloud email routes through willbracken.com Cloudflare domain — leverage this for filtering

---

## 🟡 PENDING — NOT STARTED

### 9. HuggingFace Local Playground → n8n Integration
**Repo:** `HuggingFace/`
**Priority:** LOW — after n8n is stable
**Status:** Not started
**Note:** Tie into n8n once n8n is complete

### 10. Outlook Email Sorting
**Priority:** LOW — nice to have
**Status:** Not started
**Note:** Can route through n8n once n8n is complete

### 11. VSCodespace + VSCode_Folders GitHub Unification
**Priority:** LOW
**Status:** Partial — Windows/WSL mirror exists
**Note:** Ensure Windows/Linux/Mac settings compatible

---

## ✅ COMPLETE

### Neo4j on Railway
**Status:** BROKEN — not done, minimal data ingested
**Note:** Two instances needed: (1) public-facing for willbracken.com visual appeal/visitors, (2) internal for all personal data/relationships

### Cloudflare D1 Schema
**Status:** Done — 4 tables created with indexes
**DB ID:** `cebbc6b3-8462-45a5-8588-94d5b3d5e910`

### OpenRouter 4-tier routing
**Status:** Done — in ai-router worker
**Tiers:** free/standard/premium/elite

---

## 📋 SESSION LOG
*Agents: append a line here at end of every session*

- 2026-04-23: i9 emergency triage — fixed LocalAppData, killed iCloudDrive/GoogleDriveFS leak, identified auto-configure-mcp.ps1 as source of 700+ MCP entries, confirmed 13 claude processes are normal Desktop+CLI, created CLAUDE.md + PROJECTS.md (Sonnet 4.6)

---

### 12. Local LLM Tuning (Ollama + LoRA)
**Repo:** `WSL_Docker/llm/`
**Priority:** MEDIUM — long-requested, ties into n8n and all local AI work
**Status:** Not started (Ollama installed, models running, no tuning done)
**Goal:** Improve local model quality for Will's specific domains (Cloudflare, n8n, coding, data)
**Approach:**
- LoRA fine-tuning on domain-specific data (not full retrain — fast and cheap)
- Use Azure credits for training runs before they expire
- Models: likely Mistral 7B or Llama 3 base — good tuning targets on RTX4080
- Training data: Will's own docs, code, Cloudflare configs, n8n workflows
**Definition of done:**
- [ ] Training dataset prepared from existing repos/docs
- [ ] LoRA adapter trained (Azure VM or local RTX4080)
- [ ] Fine-tuned model running in Ollama
- [ ] Noticeably better at Cloudflare Workers, n8n, Will's codebase
- [ ] Integrated into n8n as local AI option
**Note:** RTX4080 on i9 is excellent for local inference. Old PC RTX2080 also viable for training.
**Next step:** Prepare training dataset from `Cloudflare/` and `WSL_Docker/n8n/` repos

---

### 13. Azure Container Apps — Credit Utilization
**Repo:** `Azure_GitHub/containers/`
**Priority:** HIGH — use before credits expire ~2026-05-03
**Status:** Not started
**Best uses of remaining $180 Azure credits:**
- [ ] n8n on Container Apps (run during credit period, export workflows before expiry)
- [ ] Batch document processing — OCR + summarization on iDrive archive (one-time, results kept forever)
- [ ] Vector embedding fine-tuning run (LoRA training job)
- [ ] Pre-generate summaries of all important docs → store in CockroachDB
**Key rule:** Build outputs that persist after credits expire. Don't build things that stop working when Azure billing starts.
**Next step:** Spin up Container App for n8n first, then batch processing job

---

### 14. Atlassian Family Site — Fix Cross-Contamination
**Repo:** `Atlassian/`
**Priority:** LOW-MEDIUM (but quick fix available)
**Status:** Basic setup done, BROKEN — Will's tasks bleeding into family view
**Critical bug:** Family members seeing Will's work tasks ("pay this bill", "project work", "vacation plans") — completely unusable until fixed
**Fix needed:** Separate Jira projects with strict permission boundaries:
- Family project: chores, household, shared calendar, appointments
- Will's project: completely hidden from family view
**Definition of done:**
- [ ] Permission fix — zero cross-contamination
- [ ] Family sees ONLY: household tasks, chores, shared calendar
- [ ] Will's work tasks completely invisible to family
- [ ] iCal integration working for appointments
- [ ] PDF→Excel workflow (huge impact for low-tech family)
- [ ] Simple AI features accessible (doc convert, sort)
- [ ] Bill can use basic features without assistance
**Note:** Permission fix is ~30 min work. Do this first before any new features.
**Next step:** Fix Jira project permissions, then iCal integration


---

### 15. Family Email Management (Dev → Prod pipeline)
**Repo:** `WSL_Docker/n8n/email/` or `CloudDatabases/email/`
**Priority:** MEDIUM — high impact for family, must be done carefully
**Status:** Scripts written previously, location unknown — check `AI_Agent_Skills/scripts/` and `VSCodespace/`
**Accounts:**
- Family shared inbox — ~10 years of email, only need 2 years vectorized
- One Outlook (family member)
- One iCloud (barely used, low priority)
**Goals:**
- Spam detection + auto-unsubscribe (inbox is very cluttered)
- Vector search across family emails (last 2 years only)
- Emails 2+ years old → pipeline to archive storage (free up device space seamlessly)
- Family devices constantly running out of space — offload old emails transparently
- Missed emails in shared inbox → smart notifications or digest

**CRITICAL RULES:**
- Dev environment FIRST — never touch prod until verified working
- NEVER delete emails — archive only, always recoverable
- Family must not notice the transition (no confusion, no visible changes to their UI)
- No accidental deletions under any circumstances — read-only access during dev
- Test on a small sample (50-100 emails) before bulk processing

**Definition of done:**
- [ ] Dev environment set up with copy of email data (not live)
- [ ] Spam classification working (test on sample)
- [ ] Unsubscribe automation tested and verified
- [ ] 2+ year emails archived to accessible cold storage (not deleted)
- [ ] Device storage freed up transparently
- [ ] Vector search working on last 2 years
- [ ] Verified working in dev before any prod change
- [ ] Rollback plan documented

**Next step:** Find previously written scripts, then set up dev environment with email copy

---

### 16. Google Drive Partition + DuckDB Analytics Layer
**Repo:** `CloudDatabases/gdrive/`
**Priority:** MEDIUM
**Status:** Scripts written previously on all machines — location unknown, check `AI_Agent_Skills/scripts/`
**Current state:** 5TB Google Drive, was nearly empty, now cluttered with duplicates
**Plan:**
- Personal partition: 1-2TB max (documents, photos, important files)
- Development partition: scratch space, experiments, temp files
- Analytics partition: DuckDB target, Parquet files, data exports
- Archive partition: cold data, rarely accessed

**DuckDB use cases:**
- Query Parquet files stored in Google Drive directly (no database server needed)
- Analytics on personal data (spending, emails, documents metadata)
- Bridge between Google Drive and CockroachDB for enriched data
- Free alternative to BigQuery for personal analytics

**Definition of done:**
- [ ] Find and review existing partition scripts before re-running
- [ ] Duplicates removed first (before partitioning)
- [ ] Partition structure created and documented
- [ ] DuckDB connected to analytics partition
- [ ] Sample query working (e.g. "find all PDFs modified last 30 days")
- [ ] cleanup-gdrive.py script from AI_Agent_Skills reviewed and safely run

**Note:** `AI_Agent_Skills/scripts/cleanup-gdrive.py` and `partition-gdrive.py` already exist — review these before writing new ones. Also `gdrive-duckdb-bridge.py` exists.
**Next step:** Locate and review existing scripts, run cleanup in dry-run mode first

