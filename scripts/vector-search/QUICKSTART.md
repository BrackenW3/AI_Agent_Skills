# Vector Search Pipeline - Quick Start Guide

Complete setup and validation scripts for the vector search indexing pipeline.

## What's New

Three new files have been created to simplify pipeline initialization:

1. **bootstrap.py** - Comprehensive system validation and readiness check
2. **quickstart.sh** - Automated setup script for Linux/macOS
3. **quickstart.ps1** - Automated setup script for Windows

## Quick Start (5 minutes)

### Option 1: Windows (PowerShell)
```powershell
.\quickstart.ps1
```

### Option 2: Linux / macOS (Bash)
```bash
chmod +x quickstart.sh
./quickstart.sh
```

### Option 3: Manual Setup
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Validate environment
python bootstrap.py

# 3. Start indexing
python indexer.py
```

## Bootstrap Validation

The `bootstrap.py` script checks:

✓ **Dependencies**
  - pip availability
  - All required Python packages installed
  - Package import verification

✓ **Configuration**
  - .env file exists and is readable
  - All required environment variables set
  - Variable values valid (URLs, API keys)

✓ **Azure OpenAI Connectivity**
  - API key and endpoint valid
  - Test embedding generation succeeds
  - Cost estimation for your file count

✓ **Supabase Connectivity**
  - Database connection successful
  - Required tables exist (documents, file_metadata)
  - pgvector extension enabled

✓ **Directory Scanning**
  - Configured directories accessible
  - File count estimation
  - Indexing time estimation

✓ **Cost & Time Estimates**
  - Estimated Azure embedding costs
  - Estimated indexing duration
  - Breakdown by source (OneDrive, Google Drive, Local)

### Running Bootstrap Only
```bash
python bootstrap.py
python bootstrap.py --verbose
python bootstrap.py --skip-tests  # Skip API connectivity tests
```

### Bootstrap Output Example
```
======================================================================
BOOTSTRAP STATUS REPORT
======================================================================
pip................................................ ✓ OK
Dependencies......................................... ✓ OK
Imports.............................................. ✓ OK
.env file............................................ ✓ OK
Required variables.................................. ✓ OK
Variable formats.................................... ✓ OK
Azure OpenAI API.................................... ✓ OK - Generated 1536-dim embedding
Supabase API......................................... ✓ OK - Connected successfully
Supabase schema...................................... ✓ OK - All tables exist
Directory scan....................................... ✓ OK - 1,247 files found
Cost estimate........................................ ✓ OK - ~$0.12 for 6,235 tokens; ~0h 10m to index
======================================================================
Overall Status: READY
======================================================================

✓ System is ready to begin indexing!
  Next step: python indexer.py
```

## Configuration Checklist

Before running, ensure:

- [ ] `.env` file exists (copy from `.env.example`)
- [ ] `AZURE_OPENAI_API_KEY` is set
- [ ] `AZURE_OPENAI_ENDPOINT` is set (e.g., https://your-resource.openai.azure.com)
- [ ] `SUPABASE_URL` is set (e.g., https://your-project.supabase.co)
- [ ] `SUPABASE_API_KEY` is set
- [ ] Directory paths configured (at least one of ONEDRIVE_PATH, GOOGLE_DRIVE_PATH, LOCAL_PATHS)
- [ ] Supabase tables created (run setup_supabase.sql in your Supabase SQL editor)

## Script Options

### quickstart.sh / quickstart.ps1

```bash
# Full pipeline (default)
./quickstart.sh

# Skip bootstrap validation
./quickstart.sh --skip-bootstrap

# Skip indexing (just setup)
./quickstart.sh --skip-index

# Skip both (manual control)
./quickstart.sh --skip-bootstrap --skip-index
```

## Troubleshooting

### "Python not found"
```bash
# Windows: Ensure Python is in PATH or use full path
python --version
# or
python3 --version
```

### "Missing required variables"
```bash
# Copy template and fill in your values
cp .env.example .env
# Then edit .env with your API keys
```

### "Azure OpenAI API: Connection failed"
- Verify AZURE_OPENAI_ENDPOINT is HTTPS (not HTTP)
- Check API key validity
- Ensure you have credits/quota on your Azure account

### "Supabase API: Connection failed"
- Verify SUPABASE_URL contains ".supabase.co"
- Verify SUPABASE_API_KEY is correct (use service_role or anon key)
- Check if tables exist: run setup_supabase.sql

### "Directory scan: No paths configured"
- Set at least one path:
  - `ONEDRIVE_PATH=/path/to/onedrive`
  - `GOOGLE_DRIVE_PATH=/path/to/gdrive`
  - `LOCAL_PATHS=/path/to/dir1,/path/to/dir2`

## What Happens During Quick Start

1. **Dependencies Installation**
   - Runs: `pip install -r requirements.txt`
   - Duration: 1-2 minutes
   - Result: All Python packages ready

2. **Bootstrap Validation**
   - Checks all components
   - Tests API connectivity
   - Estimates costs and time
   - Duration: 30-60 seconds
   - Result: Detailed readiness report

3. **Indexing Pipeline**
   - Scans directories for files
   - Chunks documents
   - Generates embeddings via Azure OpenAI
   - Stores in Supabase
   - Duration: Varies by file count
   - Result: Indexed documents ready for search

## Performance Tips

- **Reduce file count**: Test with LOCAL_PATHS set to a small directory first
- **Adjust chunk size**: Smaller chunks = more API calls but finer-grained search
- **Rate limiting**: Adjust MAX_REQUESTS_PER_MINUTE if hitting quota limits
- **Async concurrency**: Built-in; no configuration needed

## Cost Estimation

Azure OpenAI text-embedding-3-small: **$0.02 per 1M tokens**

Example costs (April 2026 pricing):
- 1,000 files × 500 tokens/file = 500K tokens = **$0.01**
- 10,000 files = 5M tokens = **$0.10**
- 100,000 files = 50M tokens = **$1.00**

Bootstrap estimates your actual cost based on file count.

## Next Steps After Quick Start

1. **Interactive Search**
   ```bash
   python search.py
   ```
   Enter queries and get similarity-ranked results

2. **Check Logs**
   ```bash
   # View indexing statistics
   cat index_metadata.db
   
   # Check configuration
   cat .env
   ```

3. **Monitor Index Status**
   - Query Supabase directly for document counts
   - Review vector similarity in search results
   - Adjust chunk size or API limits as needed

## Support

For detailed documentation see:
- **USAGE.txt** - Full feature overview
- **config.py** - Configuration options
- **indexer.py** - Indexing implementation
- **search.py** - Search interface
