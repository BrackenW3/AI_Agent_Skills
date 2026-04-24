# AI Agent Deployment Packages

Self-contained prompts for Will Bracken's infrastructure project. Each package is fully independent with zero external context required. Paste the entire prompt block into your target AI agent (ChatGPT, Gemini, OpenRouter, etc.) to deploy that component in parallel.

---

## Package 1: Azure Infrastructure Agent

**Target Agent:** OpenAI ChatGPT (GPT-4o) or Google Gemini  
**Estimated Time:** 4-5 days of agent work (with human validation)  
**Prerequisites:**
- Azure subscription with ~$180 credits remaining
- Azure CLI installed locally (for testing commands)
- Ability to execute Python scripts locally

**Key Deliverables:**
- Azure Functions deployment (code + ARM/Bicep)
- Blob Storage container setup
- Azure OpenAI embedding endpoint test with sample documents
- Azure Static Web App dashboard showing credit usage
- Cost tracking spreadsheet

```
TASK: Deploy Azure infrastructure for a multi-cloud file indexing system.

CONTEXT:
You are an Azure infrastructure agent responsible for maximizing $180 in Azure credits over 2 weeks to build serverless file indexing infrastructure. The goal is to index files from Google Drive, OneDrive, and iDrive, then store embeddings in Supabase pgvector.

AZURE CREDENTIALS (do not expose publicly):
- Subscription: Azure Portal (user has credits available)
- Existing Azure OpenAI Service: https://willbracken-aoai-ihe42a.openai.azure.com/
- API Key: 0003c1bb09a24edd9672dfcbb3c7f3fb
- API Version: 2025-01-01-preview
- Model: text-embedding-3-small

TARGET INFRASTRUCTURE:
1. Azure Functions (serverless): Trigger on file metadata changes → call Azure OpenAI embedding API → send to Supabase
2. Azure Blob Storage: Staging area for large file transfers (Google Drive exports, OneDrive syncs)
3. Azure OpenAI Integration: Test embedding pipeline with sample PDFs, Docs, and spreadsheets
4. Azure Static Web App: Real-time dashboard showing:
   - Total credit usage this month
   - Cost per component (Functions execution, storage, API calls)
   - Document count indexed
   - Average embedding latency

YOUR TASKS:

1. DESIGN AZURE INFRASTRUCTURE
   - Create an ARM template or Bicep file that deploys:
     * Azure Functions (Consumption plan, Python runtime)
     * Azure Blob Storage (Hot tier for staging, standard replication)
     * Azure Static Web App
     * Application Insights for monitoring
   - Estimate monthly cost for each component given $180/2 weeks budget
   - Output: Complete IaC file ready to deploy via `az deployment group create`

2. DEPLOY AZURE FUNCTIONS
   - Language: Python 3.11
   - Function 1: `IndexFileMetadata` (HTTP trigger)
     * Input: JSON with {file_name, file_size, file_type, source_system}
     * Call Azure OpenAI embedding API with file metadata as context
     * Output: embedding vector (1536 dimensions)
   - Function 2: `BulkIndexing` (Timer trigger, runs daily)
     * Query list of unindexed files from input blob storage
     * Batch process (10 at a time) to stay within rate limits
     * Store results in output blob
   - Include: requirements.txt, async HTTP handling, error handling with retries

3. BLOB STORAGE CONFIGURATION
   - Create 3 containers: "staging", "processed", "metadata"
   - Set up lifecycle rules: move staging files to archive after 7 days
   - Output: Container access keys and SAS URLs for secure access

4. AZURE OPENAI EMBEDDING TEST
   - Create a Python script `test_embeddings.py` that:
     * Reads sample documents from local /samples directory (provide sample generator)
     * Calls embedding endpoint with each document's text
     * Measures latency and token usage
     * Logs results to Application Insights
   - Test against: PDF (abstract + title), Google Doc (first 500 chars), Excel (sheet names + summary)
   - Output: Test report with latency stats and cost per embedding call

5. AZURE STATIC WEB APP DASHBOARD
   - Create HTML + vanilla JS (no frameworks for simplicity)
   - Real-time data source: Azure Table Storage (upsert usage metrics every hour via Functions)
   - Display:
     * Monthly spend vs. budget ($180 limit) — pie chart
     * Daily spend trend — line chart
     * Cost breakdown by resource type — bar chart
     * Document indexed count, average latency
   - Deployable directly via `az staticwebapp create`

6. COST TRACKING & OPTIMIZATION
   - Create a spreadsheet that logs:
     * Date, component, resource used (GB storage, function invocations, API calls), cost
     * Running total and % of $180 budget used
     * Alerts: warn if projected monthly spend exceeds $180
   - Identify 3 cost-saving opportunities (e.g., reduce function frequency, move cold data to archive)

OUTPUT FORMAT:
- iac.bicep or iac.json (ARM template)
- Azure Functions code (Function1, Function2 as separate .py files + function_app.py wrapper)
- requirements.txt for Functions
- test_embeddings.py (standalone Python script)
- Azure Static Web App HTML (dashboard.html, styles.css, app.js)
- cost_tracking.csv template
- DEPLOYMENT_GUIDE.md with step-by-step Azure CLI commands

CONSTRAINTS:
- Keep Functions cold startup under 5 seconds (use lightweight Python packages)
- Use Managed Identity for authentication (no connection strings in code)
- Ensure all costs are tracked and exportable
- Test everything locally before deploying to Azure

START NOW and provide complete, deployment-ready code.
```

---

## Package 2: DuckDB Analytics Agent

**Target Agent:** OpenAI ChatGPT (GPT-4) or OpenRouter (Claude 3)  
**Estimated Time:** 3-4 days of agent work  
**Prerequisites:**
- Python 3.10+, pip, venv
- Google Drive service account JSON (or OAuth 2.0 credentials)
- Supabase credentials (provided below)
- Cloudflare R2 access (optional, for Parquet export)

**Key Deliverables:**
- Full Python DuckDB + Google Drive + Supabase bridge
- CLI query tool: `python duckdb-cli.py query "find all PDFs about project management"`
- Analytics dashboard (HTML or Jupyter)
- Parquet exports to Cloudflare R2

```
TASK: Build a DuckDB analytics layer that bridges Google Drive, Supabase pgvector, and Cloudflare R2.

CONTEXT:
You are building an analytics engine for Will Bracken's multi-cloud file system. The system needs to:
1. Mount Google Drive files as DuckDB virtual tables (no local copy needed)
2. Query Supabase pgvector for semantic similarity search results
3. Join DuckDB queries with vector search results
4. Export analytics as Parquet to Cloudflare R2
5. Provide a CLI for ad-hoc queries like: "find all PDFs about project management"

CREDENTIALS (do not expose publicly):
Supabase:
  - URL: https://smttdhtpwkowcyatoztb.supabase.co
  - Anon Key: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNtdHRkaHRwd2tvd2N5YXRvenRiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQxNzIwMzgsImV4cCI6MjA4OTc0ODAzOH0.3JIWil_3aYG5PHn1NHhx4ltHr5YU_kQCW0MuAOrpW1M
  - pgvector table: documents(id UUID, file_id TEXT, path TEXT, embedding vector(1536), metadata JSONB)

Google Drive: (User will provide service account JSON or OAuth credentials)
  - Requires: Google Drive API v3 enabled
  - Scopes: https://www.googleapis.com/auth/drive.readonly

Cloudflare R2 (optional):
  - Account ID: a429049d531ba955ef37fbd55ce5f865
  - Bucket: duckdb-exports (user will create; provide R2 token via secure channel)

TECHNICAL STACK:
- duckdb==1.1.3
- httpx==0.27.0 (for Supabase REST API)
- google-auth==2.28.2
- google-auth-oauthlib==1.2.1
- pyarrow==15.0.0
- python-dotenv==1.0.0

YOUR TASKS:

1. DESIGN DUCKDB + GOOGLE DRIVE INTEGRATION
   - Create a Python class GoogleDriveMount that:
     * Authenticates to Google Drive via service account or OAuth
     * Lists all files in Will's Google Drive (folders, documents, spreadsheets, PDFs)
     * Creates DuckDB virtual table definitions (don't download files; use lazy metadata)
     * Example virtual table: files_metadata(id TEXT, name TEXT, size INT, type TEXT, modified_date DATE)
   - Implement caching: store file listings in local SQLite (expires daily)
   - Output: google_drive_mount.py class

2. BUILD SUPABASE PGVECTOR BRIDGE
   - Create a SupabaseVectorSearch class that:
     * Queries Supabase pgvector for semantic similarity
     * Input: query_text (string) or query_embedding (list[float])
     * Returns: JSON results with scores
     * Uses REST API (httpx), not PostgREST SDKs (simpler)
   - Method: search(query, top_k=10, threshold=0.7) -> list[dict]
   - Output: supabase_vector_search.py class

3. CREATE DuckDB ANALYTICS ENGINE
   - Build DuckDBAnalytics class with methods:
     * mount_google_drive() → creates virtual table from GoogleDriveMount
     * enrich_with_vectors(table_name, search_query) → joins DuckDB results with Supabase embeddings
     * query(sql_string) → executes arbitrary SQL, returns results as list[dict]
     * export_to_parquet(table_name, output_path) → exports results to Parquet
   - Example query:
     SELECT f.name, f.size, s.similarity_score
     FROM google_drive_files f
     JOIN vector_results s ON f.id = s.file_id
     WHERE s.query = 'project management' AND s.similarity_score > 0.8
   - Output: duckdb_analytics.py class

4. IMPLEMENT CLI QUERY TOOL
   - Create duckdb-cli.py with argparse that accepts:
     * `python duckdb-cli.py query "find all PDFs about project management"`
     * `python duckdb-cli.py export <table_name> --format parquet --output results.parquet`
     * `python duckdb-cli.py cache-refresh` (refresh Google Drive file list)
   - Query parsing: take natural language, convert to semantic search in Supabase, then join with DuckDB results
   - Output: duckdb-cli.py (executable)

5. BUILD CLOUDFLARE R2 EXPORT
   - Create R2Exporter class that:
     * Authenticates to Cloudflare R2 using S3-compatible API
     * Takes DuckDB Parquet results and uploads to R2 bucket
     * Generates public URLs (if bucket is public) or signed URLs (if private)
   - Method: upload_parquet(file_path, target_name) -> url
   - Output: r2_exporter.py class

6. CREATE ANALYTICS DASHBOARD (OPTIONAL)
   - Jupyter notebook (analytics_dashboard.ipynb) that:
     * Queries DuckDB for file statistics (size distribution, file type counts, dates)
     * Queries Supabase for vector search performance (avg similarity scores, latency)
     * Plots: file type pie chart, size histogram, search latency trend
   - Or simple HTML dashboard (dashboard.html) with embedded Python execution

7. CONFIGURATION & SECURITY
   - Create .env.template with all required credentials
   - Implement proper credential handling:
     * Load from .env or environment variables, never hardcode
     * Use Supabase anon key for read-only queries, enforce RLS policies
   - Output: .env.template and credentials_manager.py

8. DOCUMENTATION
   - README.md with:
     * Setup instructions (install dependencies, create .env)
     * Examples of CLI usage
     * Example SQL queries
     * Troubleshooting

OUTPUT FORMAT:
- google_drive_mount.py (class)
- supabase_vector_search.py (class)
- duckdb_analytics.py (class)
- r2_exporter.py (class)
- duckdb-cli.py (executable script)
- requirements.txt
- .env.template
- analytics_dashboard.ipynb or dashboard.html
- README.md

CONSTRAINTS:
- Do NOT download Google Drive files; use metadata only
- Use DuckDB's arrow-based integration where possible (faster)
- Implement proper error handling and retry logic for API calls
- Cache Google Drive results to minimize API quota usage
- All code must be testable without real Google Drive/Supabase (provide mock fixtures)

START NOW and provide complete, production-ready code.
```

---

## Package 3: Neon + CockroachDB Setup Agent

**Target Agent:** Any (Claude 3 Opus, ChatGPT-4, OpenRouter)  
**Estimated Time:** 2-3 days of agent work  
**Prerequisites:**
- Neon account (free tier available at neon.tech)
- CockroachDB serverless cluster (existing; Will has credentials)
- Python 3.10+, psycopg2-binary

**Key Deliverables:**
- Neon Postgres setup with tables and pgvector
- CockroachDB distributed schema
- Unified Python connection module
- Bi-directional sync script (Supabase ↔ Neon ↔ CockroachDB)

```
TASK: Set up Neon Postgres and CockroachDB as additional database backends with sync logic.

CONTEXT:
Will is building a multi-database architecture for file indexing:
- Supabase (primary, pgvector semantic search)
- Neon Postgres (secondary, query latency testing)
- CockroachDB (distributed, global deduplication logic)

Your job is to:
1. Create Neon Postgres account, enable pgvector, create tables
2. Connect to existing CockroachDB serverless cluster, create distributed tables
3. Build Python module that abstracts all three behind a unified interface
4. Write sync script that keeps document_catalog in sync across all three databases

NEON SETUP:
- Sign up at neon.tech (free project available)
- Region: US East (closest to Will's infrastructure)
- Enable pgvector extension

COCKROACHDB SETUP:
- Will has existing serverless cluster
- Connection string provided via secure channel
- Use CockroachDB SQL (PostgreSQL-compatible dialect)

Supabase (reference, already set up):
- URL: https://smttdhtpwkowcyatoztb.supabase.co
- Anon Key: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNtdHRkaHRwd2tvd2N5YXRvenRiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQxNzIwMzgsImV4cCI6MjA4OTc0ODAzOH0.3JIWil_3aYG5PHn1NHhx4ltHr5YU_kQCW0MuAOrpW1M

YOUR TASKS:

1. NEON POSTGRES SETUP
   Create SQL migration files:

   01_init_tables.sql:
   ```sql
   -- Enable pgvector
   CREATE EXTENSION IF NOT EXISTS vector;

   -- Document catalog (canonical file metadata)
   CREATE TABLE IF NOT EXISTS document_catalog (
     id BIGSERIAL PRIMARY KEY,
     file_id TEXT UNIQUE NOT NULL,
     path TEXT NOT NULL,
     device_id TEXT NOT NULL,
     file_hash TEXT UNIQUE NOT NULL,
     is_canonical BOOLEAN DEFAULT true,
     duplicate_of BIGINT REFERENCES document_catalog(id),
     file_size BIGINT,
     file_type TEXT,
     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
     updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
     INDEX idx_device_id (device_id),
     INDEX idx_file_hash (file_hash)
   );

   -- Search history (query + semantic embeddings)
   CREATE TABLE IF NOT EXISTS search_history (
     id BIGSERIAL PRIMARY KEY,
     user_id TEXT NOT NULL,
     query TEXT NOT NULL,
     embedding vector(1536),
     results JSONB,
     latency_ms INT,
     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   );

   -- File metadata index (denormalized for speed)
   CREATE TABLE IF NOT EXISTS file_index (
     id BIGSERIAL PRIMARY KEY,
     document_id BIGINT REFERENCES document_catalog(id),
     extracted_text TEXT,
     metadata JSONB,
     last_indexed TIMESTAMP
   );
   ```

   02_indexes.sql:
   ```sql
   CREATE INDEX idx_embedding ON search_history USING ivfflat (embedding vector_cosine_ops);
   CREATE INDEX idx_search_created ON search_history (created_at DESC);
   CREATE INDEX idx_catalog_hash ON document_catalog (file_hash);
   ```

   Output: SQL migration files in /neon/migrations/

2. COCKROACHDB SETUP
   Create CockroachDB schema (PostgreSQL-compatible):

   01_distributed_tables.sql:
   ```sql
   -- Device registry (distributed across zones)
   CREATE TABLE IF NOT EXISTS device_registry (
     device_id UUID PRIMARY KEY,
     device_name TEXT NOT NULL,
     device_type TEXT, -- laptop, server, nas, etc.
     last_sync TIMESTAMP,
     total_files INT DEFAULT 0,
     UNIQUE (device_name)
   );

   -- Sync log (audit trail)
   CREATE TABLE IF NOT EXISTS sync_log (
     id UUID PRIMARY KEY DEFAULT gen_uuid(),
     device_id UUID REFERENCES device_registry(device_id),
     operation TEXT, -- INSERT, UPDATE, DELETE, DEDUPLICATE
     file_hash TEXT NOT NULL,
     row_count INT,
     status TEXT, -- SUCCESS, FAILED
     error_msg TEXT,
     sync_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
     INDEX idx_device_sync (device_id, sync_time DESC)
   );

   -- File deduplication (distributed dedup logic)
   CREATE TABLE IF NOT EXISTS file_index_distributed (
     file_hash TEXT PRIMARY KEY,
     canonical_device_id UUID NOT NULL,
     canonical_path TEXT NOT NULL,
     replica_count INT DEFAULT 1,
     total_storage_bytes BIGINT,
     first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
     last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
     FOREIGN KEY (canonical_device_id) REFERENCES device_registry(device_id)
   );

   -- Dedup candidates (files to consolidate)
   CREATE TABLE IF NOT EXISTS dedup_candidates (
     id UUID PRIMARY KEY DEFAULT gen_uuid(),
     master_hash TEXT NOT NULL,
     replica_hash TEXT NOT NULL,
     replica_device_id UUID,
     similarity_score DECIMAL(3, 2),
     action_taken TEXT, -- CONSOLIDATED, IGNORED, PENDING
     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
     UNIQUE (master_hash, replica_hash)
   );
   ```

   Output: SQL migration files in /cockroachdb/migrations/

3. UNIFIED DATABASE ABSTRACTION
   Create database.py that provides a single interface:

   ```python
   # Pseudo-code structure
   class MultiDatabaseClient:
       def __init__(self, supabase_url, supabase_key, neon_conn_str, cockroach_conn_str):
           self.supabase = SupabaseClient(...)
           self.neon = PostgresConnection(...)
           self.cockroach = PostgresConnection(...)

       def insert_document(self, doc_data, sync_targets=['all']):
           """Insert document to one or more databases"""
           # Insert to Supabase
           if 'supabase' in sync_targets or 'all' in sync_targets:
               self.supabase.insert(...)
           # Insert to Neon
           if 'neon' in sync_targets or 'all' in sync_targets:
               self.neon.execute(...)
           # Insert to CockroachDB with replication
           if 'cockroach' in sync_targets or 'all' in sync_targets:
               self.cockroach.execute(...)

       def query_document(self, file_id, source='primary'):
           """Query from specified database"""
           if source == 'primary':
               return self.supabase.query(...)
           elif source == 'neon':
               return self.neon.query(...)
           elif source == 'cockroach':
               return self.cockroach.query(...)

       def deduplicate(self):
           """Run distributed dedup logic across CockroachDB"""
           # Query CockroachDB for files with same hash across devices
           # Mark replicas, consolidate metadata
           pass
   ```

   Output: database.py with full implementation

4. BI-DIRECTIONAL SYNC SCRIPT
   Create sync_manager.py:

   ```python
   # Pseudo-code
   class SyncManager:
       def __init__(self, db_client):
           self.db = db_client

       def sync_supabase_to_neon(self):
           """Replicate Supabase document_catalog to Neon"""
           # 1. Get all docs from Supabase modified since last sync
           # 2. Upsert to Neon
           # 3. Log sync_log entry

       def sync_neon_to_cockroach(self):
           """Replicate Neon to CockroachDB for distributed dedup"""
           # 1. Get all docs from Neon
           # 2. Group by file_hash
           # 3. Insert deduplicated view into CockroachDB

       def sync_cockroach_dedup_results_back(self):
           """Take CockroachDB dedup insights and update primary DBs"""
           # 1. Query CockroachDB for dedup candidates
           # 2. Mark duplicates in Supabase and Neon
           # 3. Log actions in sync_log

       def full_sync_cycle(self):
           """Run all syncs in order"""
           self.sync_supabase_to_neon()
           self.sync_neon_to_cockroach()
           self.sync_cockroach_dedup_results_back()
           # Log completion
   ```

   Output: sync_manager.py with full implementation

5. TESTING & VALIDATION
   Create test_databases.py:
   ```python
   # Tests for:
   # - Neon connection and table creation
   # - CockroachDB connection and distributed writes
   # - Sync consistency (data matches across all three DBs)
   # - Dedup logic correctness
   # - Latency comparison (Supabase vs Neon vs CockroachDB)
   ```

   Output: test_databases.py with pytest fixtures

6. DOCUMENTATION
   - SETUP_GUIDE.md: Step-by-step Neon + CockroachDB setup
   - DATABASE_ARCHITECTURE.md: Schema diagrams, sync flow, dedup logic
   - CONNECTION_GUIDE.md: How to get connection strings for Neon and CockroachDB

OUTPUT FORMAT:
- /neon/migrations/01_init_tables.sql
- /neon/migrations/02_indexes.sql
- /cockroachdb/migrations/01_distributed_tables.sql
- database.py (unified abstraction)
- sync_manager.py (bi-directional sync)
- test_databases.py
- SETUP_GUIDE.md
- requirements.txt (psycopg2-binary, etc.)

CONSTRAINTS:
- Neon tables must schema-match Supabase (for sync consistency)
- CockroachDB must use distributed-friendly syntax (no foreign key constraints across nodes)
- Sync script must be idempotent (safe to run multiple times)
- Include transaction handling and rollback logic for partial failures

START NOW and provide complete SQL migration files and Python code.
```

---

## Package 4: iDrive Data Viewer Agent

**Target Agent:** Claude (Claude 3 Opus) or any agent with strong front-end skills  
**Estimated Time:** 2-3 days of agent work  
**Prerequisites:**
- Ability to manually export iDrive data (or use CLI scraping if available)
- Node.js for development (if running a build step) OR plain React in single HTML file (no build required)

**Key Deliverables:**
- Single HTML file with React + Tailwind (fully self-contained, no external JS dependencies except React CDN)
- Device inventory grid with filtering
- Duplicate detection algorithm
- "Junk file" classifier
- Space savings calculator
- Sample JSON schema for iDrive data

```
TASK: Build a single-file React web app for browsing iDrive backup inventory with duplicate detection and junk file classification.

CONTEXT:
iDrive's native UI is slow and doesn't provide good visibility into:
- Which devices are backed up
- Duplicate files across devices
- Junk files taking up space (Windows, Program Files, node_modules, .git, temp files)
- Potential storage savings from cleanup

You are building a single HTML file (index.html) with React that:
1. Loads iDrive device inventory as JSON (user pastes it in)
2. Displays devices in a clean grid
3. Filters by device, file type, date range, size
4. Detects potential duplicates (same name + size across devices)
5. Flags "junk" file types
6. Calculates space savings

REQUIREMENTS:
- Single HTML file (no build, no npm install, just open in browser)
- React 18 via CDN
- Tailwind CSS via CDN
- No external state management library
- LocalStorage for saving filter preferences and imported data
- Works offline (no API calls)

DATA SCHEMA:
The app will accept JSON in this format (user manually pastes from iDrive export):

```json
{
  "devices": [
    {
      "device_id": "device_uuid_1",
      "device_name": "Laptop-Will",
      "device_type": "laptop",
      "os": "windows",
      "last_backup": "2026-04-22T10:30:00Z",
      "total_size_bytes": 500000000000,
      "file_count": 125000,
      "folders": [
        {
          "path": "C:/Users/Will/Documents",
          "size_bytes": 5000000,
          "file_count": 150,
          "files": [
            {
              "name": "project_plan.pdf",
              "size_bytes": 2000000,
              "ext": "pdf",
              "modified_date": "2026-03-15",
              "hash": null  // optional; iDrive may not provide
            }
          ]
        }
      ]
    },
    {
      "device_id": "device_uuid_2",
      "device_name": "Server-NAS",
      "device_type": "nas",
      "os": "linux",
      "last_backup": "2026-04-20T22:00:00Z",
      "total_size_bytes": 5000000000000,
      "file_count": 500000,
      "folders": []
    }
  ]
}
```

YOUR TASKS:

1. DESIGN DATA IMPORT & VALIDATION
   - Create a "Paste JSON" text area with error handling
   - Validate JSON schema before import
   - Show import summary: X devices, Y files, Z GB total
   - Save to localStorage so data persists across page reloads
   - Show timestamp of last import

2. BUILD DEVICE INVENTORY GRID
   - Grid view showing:
     * Device name (clickable to expand)
     * Backup status (checkmark, last backup date)
     * OS icon (Windows, macOS, Linux)
     * Total size (human readable: GB/TB)
     * File count
     * Color coded: green (recent backup), yellow (> 7 days), red (> 30 days)
   - Click device to show folder tree and file list
   - Show warning if device hasn't backed up in > 30 days

3. IMPLEMENT FILTERING & SEARCH
   - Filters:
     * Device selector (checkbox list)
     * File type selector (pdf, doc, xls, img, video, code, other)
     * Date range picker (last modified: last week, last month, last year, any)
     * Size range slider (0 - 10 GB)
   - Search box: filter by filename (partial match, case-insensitive)
   - Applied filters shown as chips (clickable to remove)
   - Results updated in real-time

4. DUPLICATE DETECTION ALGORITHM
   - Algorithm: Group files by (name, size_bytes)
   - Display duplicates in a table:
     * Filename
     * Size (human readable)
     * Devices where duplicate found (comma-separated)
     * # of copies across all devices
   - Total space savings if one copy is deleted
   - Filter view: "Show Only Duplicates" toggle
   - Indicate which copy is the "master" (oldest modification date)

5. JUNK FILE CLASSIFIER
   - Define junk patterns:
     * File paths containing: Windows, Program Files, AppData, node_modules, .git, .venv, __pycache__, dist, build, .cache, Temp, Logs
     * File types: .tmp, .log, .bak, .cache, .old
     * Folder patterns: $Recycle.bin, .Trash, SystemVolume, .thumbnails
   - Mark files/folders as "junk" in the display (red background, warning icon)
   - "Junk Summary" card showing:
     * Total junk files (count)
     * Total junk size (human readable)
     * % of total backup size
     * "Show Only Junk" toggle

6. SPACE SAVINGS CALCULATOR
   - Card showing:
     * "Current backup size: X TB"
     * "Junk to clean: X GB (Y%)"
     * "Duplicates to remove: X GB (Z%)"
     * "Conservative estimate after cleanup: X TB (A% reduction)"
   - Clickable "View Cleanup Plan" to show which specific files would be deleted

7. EXPORT & SHARING
   - Button to export current filtered results as CSV
   - Button to generate a summary report (HTML) showing:
     * Device inventory
     * Top 10 largest files
     * Duplicate summary
     * Junk summary
     * Space savings estimate

8. UI/UX DESIGN
   - Responsive layout (desktop + mobile)
   - Dark mode toggle (saved to localStorage)
   - Device icons (Windows, Mac, Linux, NAS, Cloud, Unknown)
   - File type icons (PDF, Doc, Image, Video, Code, Other)
   - Loading state while JSON is being processed
   - Clear, large fonts for readability
   - Color scheme: green (safe), yellow (warning), red (action needed)

OUTPUT FORMAT (SINGLE HTML FILE):
```html
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>iDrive Inventory Viewer</title>
    <script crossorigin src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
    <script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
    <style>
      /* Custom CSS here */
    </style>
  </head>
  <body>
    <div id="root"></div>
    <script type="text/babel">
      // Full React app here
      const App = () => {
        // State, handlers, JSX
      };
      const root = ReactDOM.createRoot(document.getElementById('root'));
      root.render(<App />);
    </script>
  </body>
</html>
```

9. SAMPLE DATA GENERATOR
   - Include a "Load Sample Data" button that populates the app with mock iDrive data
   - Sample includes: 3 devices, various file types, duplicates, junk files
   - Useful for testing and demos

10. INSTRUCTIONS FOR DATA EXTRACTION
    - Include a section (in HTML) with instructions for getting data out of iDrive:
      * Option A: Manual export from iDrive web UI (if available)
      * Option B: CLI scraping (if Will has iDrive CLI tool)
      * Option C: Screenshot + manual entry (fallback)
    - Generate template JSON for user to fill in manually

CONSTRAINTS:
- Single HTML file (no separate .js, .css, .html files)
- No npm, no build tools, no external libraries except React + Tailwind (via CDN)
- Works offline after initial load
- All data stored in browser (localStorage)
- No server-side processing
- Responsive design (works on mobile + desktop)
- Fast performance even with 100,000+ files

START NOW and provide the complete HTML file with all React components, styling, and logic.
```

---

## Deployment Strategy

### Parallel Execution Timeline
- **Week 1-2:** Deploy Packages 1 (Azure) and 2 (DuckDB) in parallel
- **Week 2:** Package 3 (Neon/CockroachDB) can start once Supabase is indexed
- **Week 2:** Package 4 (iDrive Viewer) is independent, can run anytime

### Hand-off Process for Will
1. Copy entire prompt block from target package
2. Paste into your chosen AI agent's chat
3. Agent will produce code + deployment instructions
4. Review outputs, validate on staging
5. Deploy to production with agent's guidance

### Success Criteria
- **Package 1:** $180 credits tracked, Functions deployed, dashboard live
- **Package 2:** CLI query tool working, Parquet exports flowing to R2
- **Package 3:** All three databases in sync, dedup logic proven
- **Package 4:** iDrive data loaded, duplicates/junk identified, savings calculated

---

**Created:** 2026-04-22  
**Target User:** Will Bracken (william.i.bracken@outlook.com)  
**Project:** Azure Vectorization + Multi-Cloud File Indexing Sprint
