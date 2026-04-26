#!/usr/bin/env python3
"""
Cloud-Native Vector Indexer — Runs directly on Azure VM
No i9 middleman. Pull from cloud → embed via Azure OpenAI → push to Supabase.

Setup on VM:
  pip install httpx supabase python-dotenv google-auth google-auth-httplib2 google-api-python-client

Run:
  python3 cloud_indexer_vm.py --source gdrive
  python3 cloud_indexer_vm.py --source onedrive  
  python3 cloud_indexer_vm.py --source all
"""

import os, sys, json, hashlib, time, argparse, logging
from pathlib import Path
from typing import Optional
import httpx
from dotenv import load_dotenv

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────
AZURE_OPENAI_ENDPOINT = os.environ["AZURE_OPENAI_ENDPOINT"]
AZURE_OPENAI_KEY      = os.environ.get("AZURE_OPENAI_KEY") or os.environ["AZURE_OPENAI_API_KEY"]
AZURE_API_VERSION     = os.environ.get("AZURE_OPENAI_API_VERSION", "2025-01-01-preview")
EMBEDDING_MODEL       = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")
SUPABASE_URL          = os.environ["SUPABASE_URL"]
SUPABASE_KEY          = os.environ.get("SUPABASE_ANON_KEY") or os.environ["SUPABASE_API_KEY"]

CHUNK_SIZE     = int(os.environ.get("CHUNK_SIZE_BYTES", 2048))
MAX_RPM        = int(os.environ.get("MAX_REQUESTS_PER_MINUTE", 200))
LOG_LEVEL      = os.environ.get("LOG_LEVEL", "INFO")

SUPPORTED_EXTS = {'.txt','.md','.py','.ts','.js','.json','.csv','.html','.yaml','.yml','.sh','.ps1','.sql','.docx','.pdf'}
EXCLUDED_DIRS  = {'node_modules','.git','__pycache__','.venv','dist','build','.next','vendor'}

logging.basicConfig(level=getattr(logging, LOG_LEVEL), format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger(__name__)

# ── Embedding ─────────────────────────────────────────────────────────────────
def get_embedding(text: str) -> Optional[list[float]]:
    url = f"{AZURE_OPENAI_ENDPOINT}openai/deployments/{EMBEDDING_MODEL}/embeddings?api-version={AZURE_API_VERSION}"
    try:
        r = httpx.post(url, headers={"api-key": AZURE_OPENAI_KEY}, 
                       json={"input": text[:8000]}, timeout=30)
        r.raise_for_status()
        return r.json()["data"][0]["embedding"]
    except Exception as e:
        log.error(f"Embedding failed: {e}")
        return None

# ── Supabase ──────────────────────────────────────────────────────────────────
def upsert_document(file_path: str, content: str, embedding: list, source: str, metadata: dict):
    doc_id = hashlib.sha256(f"{source}:{file_path}".encode()).hexdigest()
    payload = {
        "id": doc_id,
        "content": content[:4000],
        "embedding": embedding,
        "file_path": file_path,
        "file_source": source,
        "metadata": json.dumps(metadata),
    }
    try:
        r = httpx.post(
            f"{SUPABASE_URL}/rest/v1/documents",
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json",
                "Prefer": "resolution=merge-duplicates",
            },
            json=payload,
            timeout=20
        )
        r.raise_for_status()
        return True
    except Exception as e:
        log.error(f"Supabase upsert failed for {file_path}: {e}")
        return False

# ── Google Drive ──────────────────────────────────────────────────────────────
def index_gdrive():
    """Index Google Drive files via Google Drive API — no local mount needed"""
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaIoBaseDownload
        import io
    except ImportError:
        log.error("Install: pip install google-auth google-auth-httplib2 google-api-python-client")
        return

    # Use service account or OAuth token from env
    creds_json = os.environ.get("GDRIVE_SERVICE_ACCOUNT_JSON")
    if not creds_json:
        log.error("Set GDRIVE_SERVICE_ACCOUNT_JSON env var with service account JSON")
        return

    from google.oauth2.service_account import Credentials as SACredentials
    creds = SACredentials.from_service_account_info(
        json.loads(creds_json),
        scopes=["https://www.googleapis.com/auth/drive.readonly"]
    )
    service = build("drive", "v3", credentials=creds)

    # List all text files
    page_token = None
    indexed = 0
    while True:
        query = "mimeType!='application/vnd.google-apps.folder' and trashed=false"
        results = service.files().list(
            q=query, pageSize=100, pageToken=page_token,
            fields="nextPageToken, files(id, name, mimeType, size, modifiedTime, parents)"
        ).execute()

        for f in results.get("files", []):
            name = f["name"]
            ext = Path(name).suffix.lower()
            if ext not in SUPPORTED_EXTS:
                continue
            
            try:
                request = service.files().get_media(fileId=f["id"])
                buf = io.BytesIO()
                downloader = MediaIoBaseDownload(buf, request)
                done = False
                while not done:
                    _, done = downloader.next_chunk()
                content = buf.getvalue().decode("utf-8", errors="ignore")
            except Exception as e:
                log.warning(f"Could not download {name}: {e}")
                continue

            if len(content.strip()) < 50:
                continue

            chunks = [content[i:i+CHUNK_SIZE] for i in range(0, len(content), CHUNK_SIZE)]
            for i, chunk in enumerate(chunks[:10]):  # max 10 chunks per file
                embedding = get_embedding(chunk)
                if embedding:
                    upsert_document(
                        file_path=f"gdrive://{f['id']}/{name}",
                        content=chunk,
                        embedding=embedding,
                        source="google_drive",
                        metadata={"name": name, "chunk": i, "gdrive_id": f["id"], "modified": f.get("modifiedTime")}
                    )
                    indexed += 1
                    time.sleep(60 / MAX_RPM)

        page_token = results.get("nextPageToken")
        if not page_token:
            break

    log.info(f"Google Drive indexing complete: {indexed} chunks indexed")

# ── OneDrive (Microsoft Graph) ────────────────────────────────────────────────
def index_onedrive():
    """Index OneDrive via Microsoft Graph API — no local mount needed"""
    tenant_id  = os.environ.get("AZURE_TENANT_ID")
    client_id  = os.environ.get("AZURE_CLIENT_ID")
    client_secret = os.environ.get("AZURE_CLIENT_SECRET")

    if not all([tenant_id, client_id, client_secret]):
        log.error("Set AZURE_TENANT_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET for OneDrive indexing")
        return

    # Get access token
    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    r = httpx.post(token_url, data={
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": "https://graph.microsoft.com/.default"
    })
    token = r.json().get("access_token")
    if not token:
        log.error(f"Could not get Graph token: {r.text}")
        return

    headers = {"Authorization": f"Bearer {token}"}
    
    # Get user's OneDrive files
    indexed = 0
    next_url = "https://graph.microsoft.com/v1.0/me/drive/root/children?$top=100"
    
    while next_url:
        r = httpx.get(next_url, headers=headers, timeout=30)
        if not r.is_success:
            log.error(f"Graph API error: {r.text}")
            break
        
        data = r.json()
        for item in data.get("value", []):
            if "folder" in item:
                continue
            name = item.get("name", "")
            ext = Path(name).suffix.lower()
            if ext not in SUPPORTED_EXTS:
                continue

            # Download content
            download_url = item.get("@microsoft.graph.downloadUrl")
            if not download_url:
                continue

            try:
                content_resp = httpx.get(download_url, timeout=30)
                content = content_resp.text
            except Exception as e:
                log.warning(f"Could not download {name}: {e}")
                continue

            if len(content.strip()) < 50:
                continue

            chunks = [content[i:i+CHUNK_SIZE] for i in range(0, len(content), CHUNK_SIZE)]
            for i, chunk in enumerate(chunks[:10]):
                embedding = get_embedding(chunk)
                if embedding:
                    upsert_document(
                        file_path=f"onedrive://{item['id']}/{name}",
                        content=chunk,
                        embedding=embedding,
                        source="onedrive",
                        metadata={"name": name, "chunk": i, "item_id": item["id"], "modified": item.get("lastModifiedDateTime")}
                    )
                    indexed += 1
                    time.sleep(60 / MAX_RPM)

        next_url = data.get("@odata.nextLink")

    log.info(f"OneDrive indexing complete: {indexed} chunks indexed")

# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cloud-native vector indexer for Azure VM")
    parser.add_argument("--source", choices=["gdrive", "onedrive", "all"], default="all")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    log.info(f"Starting cloud indexer — source={args.source}")

    if args.source in ("gdrive", "all"):
        log.info("Indexing Google Drive...")
        index_gdrive()

    if args.source in ("onedrive", "all"):
        log.info("Indexing OneDrive...")
        index_onedrive()

    log.info("Done.")
