# PROJECTS.md — Will Bracken
# Last updated: 2026-04-27
# Active projects tracked across all machines

---

## STATUS LEGEND
- ✅ Complete
- 🔄 In Progress  
- ⏳ Pending/Blocked
- ❌ Failed/Abandoned

---

## OVERNIGHT JOBS RUNNING (2026-04-27)

### Batch Enrichment (82K docs)
- **Status:** 🔄 Running in GitHub Actions
- **Progress:** ~300/82,054 documents enriched
- **ETA:** ~8-10 hours at current rate
- **Workflow:** AI_Agent_Skills/.github/workflows/batch-enrichment.yml

### Deploy All Services
- **Status:** 🔄 Running in GitHub Actions
- **Jobs:** Neo4j, PDF enrichment, LoRA fine-tune, Container Apps (LiteLLM/LangFuse/Metabase)
- **Workflow:** AI_Agent_Skills/.github/workflows/deploy-all.yml
- **Blocker:** AZURE_CLIENT_ID, AZURE_SUBSCRIPTION_ID needed for Container Apps

---

## PROJECT LIST

### 1. n8n Automation Engine
**Status:** ✅ Running
**URL:** https://n8n.willbracken.com
**Host:** Railway (Docker)
**Integrations:** Microsoft Graph, Jira, GitHub, Supabase, Neo4j

### 2. willbracken.com / Portfolio
**Status:** 🔄 SSO broken
**URL:** https://willbracken.com
**Host:** Cloudflare Pages
**Blocker:** Zero Trust bypasses auth.willbracken.com

### 3. Vector Search Pipeline
**Status:** ✅ 82,054 docs indexed
**Storage:** Supabase pgvector
**Enrichment:** Running overnight (GPT-4o-mini summaries)
**Schema:** documents table with summary, entities, doc_type, enriched_at columns

### 4. Azure SSO / Entra
**Status:** 🔄 Partial
**Working:** will.bracken.icloud@outlook.com
**Broken:** william.i.bracken@outlook.com (directory corruption)
**App:** b07e9b3b-01b2-4fcf-b643-586ccea97bbc

### 5. AI Router (Cloudflare Worker)
**Status:** ⏳ Stub deployed, full version not deployed
**Repo:** BrackenW3/Cloudflare/apps/ai-router
**Design:** 5 tiers, 11 agents, 22 models
**Blocker:** npm install broken in Desktop Commander

### 6. LiteLLM Proxy
**Status:** 🔄 Deploying to Azure Container Apps
**Port:** 4000
**Config:** All 5 providers configured (Anthropic, OpenAI, Azure, OpenRouter, Grok)

### 7. LangFuse (LLM Observability)
**Status:** 🔄 Deploying to Azure Container Apps
**URL (pending):** https://langfuse.willbracken.com
**Login:** will@willbracken.com / WillBracken2026!

### 8. Metabase (Analytics)
**Status:** 🔄 Deploying to Azure Container Apps
**Config:** Connected to CockroachDB

### 9. Neo4j (Graph DB)
**Status:** 🔄 Schema applying via GitHub Actions
**Host:** Railway
**URI:** bolt://neo4j-production-dafa.up.railway.app:7687
**Schema:** User, Content, Tag, Project nodes + constraints

### 10. CockroachDB
**Status:** ✅ Schema applied
**Host:** CockroachDB Cloud
**Tables:** device_registry, ai_usage_log, user_sessions

### 11. Neon PostgreSQL
**Status:** ⏳ Needs NEON_API_KEY

### 12. Supabase
**Status:** ✅ Primary DB working
**URL:** https://smttdhtpwkowcyatoztb.supabase.co
**Tables:** documents (82K rows), + app schema

### 13. LoRA Fine-tuning
**Status:** 🔄 Training data prepared, job submitting
**Model:** gpt-4o-mini -> gpt-4o-mini.ft-wb-assistant
**Data:** AI_Agent_Skills + VSCodespace + Cloudflare repos + CLAUDE.md

### 14. iDrive Backup
**Status:** ⏳ 90% full - needs cleanup
**Plan:** Remove node_modules/AppData from backup set
**Target:** 1-2GB of actual important docs

### 15. GitHub Actions CI/CD
**Status:** ✅ Multi-bot PR review working
**Bots:** Claude, Copilot, Gemini, Jules

### 16. Mac Setup
**Status:** 🔄 In progress
**Done:** Node 24, Ollama on APFS_1TB, 25 models
**Pending:** Claude CLI interactive mode, SSH config

### 17. i7 Setup
**Status:** 🔄 Minimal setup done
**Done:** Node 24, env vars
**Pending:** Repos cloned, Claude CLI

### 18. i9 Desktop
**Status:** 🔄 Primary machine, most things working
**Issues:** PS7 profile strips PATH, Claude CLI interactive broken

### 19. OpenRouter AI Router
**Status:** ✅ Model tiers designed, presets documented
**Tiers:** Free, Budget, Standard, Premium, Elite
**Agents:** 11 specialized agents with system prompts

### 20. Cloudflare Zero Trust
**Status:** 🔄 4 apps configured with Azure AD + Microsoft OIDC
**Issue:** SSO SAML app needs UI config, auth.willbracken.com bypass needed

### 21. Secrets Management
**Status:** ✅ Master .env synced to 5 repos
**Missing:** AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_SUBSCRIPTION_ID, NEO4J_PASSWORD, NEON_API_KEY, RAILWAY_TOKEN

### 22. entra-auth Worker
**Status:** 🔄 Deployed at https://auth.willbracken.com
**Issue:** Zero Trust intercepts it

### 23. Azure Container Apps Environment
**Status:** 🔄 Deploying LiteLLM, LangFuse, Metabase
**RG:** willbracken-free-rg
**Env:** willbracken-env
**Budget:** ~$150 remaining, expires ~May 3 2026

---

## PRIORITY TODO (next session)
1. Get AZURE_CLIENT_ID + AZURE_SUBSCRIPTION_ID from Azure Portal
2. Set NEO4J_PASSWORD, NEON_API_KEY, RAILWAY_TOKEN
3. Check Container Apps deployment results
4. Mac SSH config fix (run in Terminal)
5. Claude CLI interactive mode (trace complete, gh.exe fix applied)
6. iDrive cleanup
7. Check LoRA fine-tune status
