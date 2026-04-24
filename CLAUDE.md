# CLAUDE.md — Master Agent Rules
# Read this ENTIRE file before starting ANY task.
# Last updated: 2026-04-23

---

## 🔴 STOP — READ BEFORE DOING ANYTHING

1. **Check PROJECTS.md first.** Find the relevant project, read its status, continue from where it left off.
2. **Never start a new project if an existing one is incomplete.**
3. **Never mark a project done unless it has a working, testable output.**
4. **A login screen is not optional. Auth is not optional. Tests are not optional.**
5. **If you hit a blocker, STOP and report it. Do not skip it and continue.**

---

## MODEL RULES

- **Default:** `claude-sonnet-4-6` for ALL work
- **Never auto-escalate to Opus** — only use if Will explicitly says "use Opus"
- **For scripts calling Claude API:** always specify model explicitly, never use default
- **OpenRouter routing:** use existing tier config in `AI_Agent_Skills/agents/claude/global-mcps.template.json`

---

## REPO OWNERSHIP MAP

Every file created must go in the correct repo. No exceptions.

| Work Type | Repo | Path |
|-----------|------|------|
| Cloudflare Workers, willbracken.com, n8n.willbracken.com | `Cloudflare` | `/workers/`, `/domain/` |
| Azure resources, Azure OpenAI, Azure VMs | `Azure_GitHub` (rename to Azure_Domain) | `/resources/`, `/ai/` |
| CockroachDB, Neon, Supabase, DuckDB, Neo4j | `CloudDatabases` | `/cockroach/`, `/neon/`, `/supabase/` |
| n8n workflows, WSL, Docker, local LLM | `WSL_Docker` | `/n8n/`, `/docker/`, `/llm/` |
| Agent skills, MCP configs, shared prompts | `AI_Agent_Skills` | `/agents/`, `/mcp/`, `/skills/` |
| Atlassian, family tools | `Atlassian` | `/jira/`, `/confluence/` |
| General scripts, workspace config | `VSCodespace` | as appropriate |
| HuggingFace experiments | `HuggingFace` | local only unless specified |

### ❌ FORBIDDEN REPO ACTIONS
- Do NOT put cloud/database work in `AI_Agent_Skills`
- Do NOT put Cloudflare workers in `VSCodespace`
- Do NOT put Azure work in `Cloudflare`
- Do NOT create new repos without explicit instruction
- Do NOT push to GitHub without explicit instruction
- Do NOT move files between repos without explicit instruction

---

## MACHINE CONFIGURATION

### i9 Desktop (Windows 11) — PRIMARY DEV MACHINE
- Node: `C:\nvm4w\nodejs` or `C:\Program Files\nodejs`
- Python: `C:\Users\User\AppData\Local\Programs\Python\Python314`
- Claude Desktop config: `%APPDATA%\Claude\claude_desktop_config.json`
- Known issues: iCloudDrive memory leak (do not index iCloudDrive), GoogleDriveFS leak

### i7 Laptop (Windows 11)
- Same structure as i9
- Claude Desktop config not yet created — use template from AI_Agent_Skills

### MacBook Pro M3 Pro
- Claude config: `~/Library/Application Support/Claude/claude_desktop_config.json`
- WARNING: config may be symlinked to SD card — always use absolute paths
- NVM/Node: use absolute paths in all MCP configs, do not rely on PATH

---

## MCP SERVER RULES

- **Canonical MCP config** lives in `AI_Agent_Skills/mcp/profiles/`
- Deploy to each machine using `AI_Agent_Skills/scripts/sync.ps1` or `sync.sh`
- **Never run `auto-configure-mcp.ps1` without `-DryRun` first**
- **Never run `laptop-full-setup.ps1`** without reviewing what it will do
- Maximum MCP servers in Claude Desktop: ~16 (6 currently, rebuilding)
- `bypassPermissionsModeEnabled` must be `false` unless explicitly testing

---

## CLOUD RESOURCE RULES

### Azure (expires ~2026-05-03, $180 credits remaining)
- Use for: embeddings (text-embedding-3-small), heavy compute, vector indexing
- Do NOT run vector pipelines locally on i9 — offload to Azure VMs
- Endpoint: `https://willbracken-aoai-ihe42a.openai.azure.com/`

### CockroachDB ($400 credits)
- Primary database for production data
- All schema work goes in `CloudDatabases/cockroach/`

### Supabase (pgvector)
- URL: `https://smttdhtpwkowcyatoztb.supabase.co`
- Use for: vector search, embeddings storage
- All work goes in `CloudDatabases/supabase/`

### Neon
- Use for: serverless Postgres
- All work goes in `CloudDatabases/neon/`

### Cloudflare
- D1 for edge database, R2 for storage, Workers for compute
- DB ID: `cebbc6b3-8462-45a5-8588-94d5b3d5e910`
- Account ID: `a429049d531ba955ef37fbd55ce5f865`

### Railway
- Use for: Neo4j (mostly done), n8n cloud instance
- Do not spin up new Railway services without checking existing ones

### OpenRouter
- Use for: non-Claude AI routing (Gemini, GPT-4, Mistral, etc.)
- Tier config exists in `AI_Agent_Skills` — use it, don't rebuild it

---

## STORAGE RULES

- **iCloudDrive:** Do NOT index or scan — causes memory leak on Windows
- **Google Drive:** Max 1-2TB personal, rest for DuckDB/analytics
- **OneDrive:** Sync only, do not use as code storage
- **iDrive (10TB):** Pool important docs only, no program files or system files
- **Nord Cloud (2TB):** Available but low priority
- **Local i9 HDD:** 5TB available, use for working data and local LLM models

---

## DEFINITION OF DONE

A project is ONLY done when ALL of these are true:
1. ✅ Core feature works end-to-end
2. ✅ Authentication/login works (if applicable)
3. ✅ Can be run by Will without agent assistance
4. ✅ README exists with setup and run instructions
5. ✅ No hardcoded credentials (use .env)
6. ✅ PROJECTS.md updated with completion status

---

## FORBIDDEN ACTIONS (never do without explicit permission)

- Modify registry keys
- Delete files or directories
- Move files between repos
- Create new cloud resources (VMs, databases, buckets)
- Push to GitHub
- Run any `*-full-setup.ps1` or `auto-configure-*` scripts
- Modify `claude_desktop_config.json` preferences section
- Index or scan iCloudDrive folder
- Commit .env files or files containing API keys

---

## CLOUDFLARE SPECIFIC RULES

- **NordVPN conflict:** Always use cloudflared tunnels for external access. Docker bypasses NordVPN automatically — no action needed when in Docker context.
- **mTLS:** Currently active, causing cert picker on login. Do NOT re-enable without explicit instruction. Scope to members only if needed.
- **Zero Trust:** Custom login was configured — check before modifying. Dashboard: https://one.dash.cloudflare.com
- **iCloud email passthrough:** `will.i.bracken@icloud.com` routes through willbracken.com Cloudflare. DO NOT touch these email routing settings under any circumstances.
- **willbracken.com** was originally serving `brackenw3.github.io` — multiple projects, not just one monorepo.
- **Landing page:** BACK UP TO GIT before any change. Gemini has destroyed it multiple times. No exceptions.
- **SSO:** Azure Entra SSO for private sections (members). PIN or GitHub for general visitors.

## AZURE / ENTRA RULES

- Primary login: `will.bracken.icloud@outlook.com` (the only one currently working)
- Goal: SSO via Azure Entra for willbracken.com private sections
- entra-auth app: `Cloudflare/apps/entra-auth/` — ChatGPT started this, review before rebuilding
- Azure credits expire ~2026-05-03, $180 remaining — prioritize container apps + batch processing + LLM fine-tuning

## OPENROUTER

- Bots completed today (2026-04-24) — find at https://openrouter.ai/settings
- Integrate with existing ai-router 4-tier system in `Cloudflare/workers/ai-router/`
- Tier config already exists in `AI_Agent_Skills/agents/claude/global-mcps.template.json`

## UBUNTU / WSL

- Ubuntu was deleted from i9 — needs reinstall (`wsl --install -d Ubuntu`)
- Had custom SSH config and n8n-specific setup — restore from any backup found
- cloudflared must be configured in WSL for NordVPN compatibility

## EMAIL — HARD RULES

- `will.i.bracken@icloud.com` — passthrough only, DO NOT touch email settings
- `william.i.bracken@outlook.com` — primary, most important
- Family email work: dev environment ONLY until verified. NEVER delete, archive only.
- Family must not notice any changes during email migration/archiving
