"""Vector search indexing pipeline.

Supports:
- OneDrive and Google Drive directory scanning
- Multiple file types (.txt, .md, .pdf, .docx, .py, .json, .csv, .html)
- Incremental indexing with SHA-256 deduplication
- Async concurrent API calls with rate limiting
- Azure OpenAI text-embedding-3-small embeddings
- Supabase pgvector storage
- EXCLUDED_PATHS support
- --dry-run flag
"""

import asyncio
import hashlib
import logging
import sqlite3
import time
import os
import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, AsyncGenerator
import json

try:
    import httpx
except ImportError:
    httpx = None

try:
    import tiktoken
except ImportError:
    tiktoken = None

try:
    from docx import Document
except ImportError:
    Document = None

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

from config import get_config


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024


class DocumentChunker:
    def __init__(self, chunk_size_bytes: int = 2048, overlap_ratio: float = 0.15):
        self.chunk_size_bytes = chunk_size_bytes
        self.overlap_ratio = overlap_ratio
        self.overlap_bytes = int(chunk_size_bytes * overlap_ratio)

    def chunk_text(self, text: str) -> list[str]:
        if not text:
            return []
        text_bytes = text.encode("utf-8")
        chunks = []
        start = 0
        while start < len(text_bytes):
            end = min(start + self.chunk_size_bytes, len(text_bytes))
            while end < len(text_bytes):
                try:
                    text_bytes[start:end].decode("utf-8")
                    break
                except UnicodeDecodeError:
                    end -= 1
            if end <= start:
                end = min(start + 1, len(text_bytes))
            chunk = text_bytes[start:end].decode("utf-8", errors="ignore").strip()
            if chunk:
                chunks.append(chunk)
            start = end - self.overlap_bytes if end < len(text_bytes) else len(text_bytes)
        return chunks


class FileProcessor:
    @staticmethod
    def extract_text_from_file(file_path: Path) -> Optional[str]:
        try:
            file_size = file_path.stat().st_size
            if file_size > MAX_FILE_SIZE_BYTES:
                logger.warning(f"File exceeds size limit: {file_path}")
                return None
            suffix = file_path.suffix.lower()
            if suffix in (".txt", ".md", ".py", ".csv", ".html"):
                return file_path.read_text(encoding="utf-8", errors="ignore")
            elif suffix == ".json":
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return json.dumps(data, indent=2)
            elif suffix == ".pdf":
                if PdfReader is None:
                    return None
                try:
                    reader = PdfReader(file_path)
                    return "\n".join(page.extract_text() for page in reader.pages)
                except Exception as e:
                    logger.warning(f"Failed to read PDF {file_path}: {e}")
                    return None
            elif suffix == ".docx":
                if Document is None:
                    return None
                try:
                    doc = Document(file_path)
                    return "\n".join(p.text for p in doc.paragraphs)
                except Exception as e:
                    logger.warning(f"Failed to read DOCX {file_path}: {e}")
                    return None
            else:
                return None
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            return None


class EmbeddingGenerator:
    def __init__(self, api_key: str, endpoint: str, model: str):
        if httpx is None:
            raise ImportError("httpx library required. Install with: pip install httpx")
        if tiktoken is None:
            raise ImportError("tiktoken library required. Install with: pip install tiktoken")
        self.api_key = api_key
        self.endpoint = endpoint.rstrip("/")
        self.model = model
        self.request_times = []
        self.token_count = 0
        try:
            self.encoding = tiktoken.encoding_for_model("text-embedding-3-small")
        except Exception:
            self.encoding = tiktoken.get_encoding("cl100k_base")

    async def generate_embedding(self, text: str, client: httpx.AsyncClient, max_retries: int = 3) -> Optional[list[float]]:
        await self._apply_rate_limit()
        self.token_count += len(self.encoding.encode(text))

        headers = {"api-key": self.api_key, "Content-Type": "application/json"}
        payload = {"input": text, "model": self.model}
        url = f"{self.endpoint}/openai/deployments/{self.model}/embeddings?api-version=2025-01-01-preview"

        for attempt in range(max_retries):
            try:
                resp = await client.post(url, json=payload, headers=headers, timeout=30)
                if resp.status_code == 200:
                    data = resp.json()
                    return data["data"][0]["embedding"]
                elif resp.status_code == 429:
                    wait_time = 2 ** attempt
                    logger.warning(f"Rate limited, waiting {wait_time}s (attempt {attempt+1}/{max_retries})")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"API error {resp.status_code}: {resp.text}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2 ** attempt)
            except Exception as e:
                logger.error(f"Embedding error (attempt {attempt+1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
        return None

    async def _apply_rate_limit(self):
        config = get_config()
        max_rpm = config.indexing.max_requests_per_minute
        now = time.time()
        self.request_times = [t for t in self.request_times if now - t < 60]
        if len(self.request_times) >= max_rpm:
            sleep_time = 60 - (now - self.request_times[0])
            if sleep_time > 0:
                logger.info(f"Rate limit reached, sleeping {sleep_time:.1f}s")
                await asyncio.sleep(sleep_time)
            self.request_times = []
        self.request_times.append(now)


class MetadataStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS file_index (
                    id INTEGER PRIMARY KEY,
                    file_hash TEXT UNIQUE NOT NULL,
                    file_path TEXT NOT NULL,
                    file_source TEXT NOT NULL,
                    file_size_bytes INTEGER NOT NULL,
                    chunk_count INTEGER NOT NULL,
                    last_modified_at TEXT NOT NULL,
                    indexed_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'active'
                )
            """)
            conn.commit()

    def get_file_hash(self, file_path: Path) -> str:
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def file_needs_reindexing(self, file_path: Path, file_source: str) -> bool:
        file_hash = self.get_file_hash(file_path)
        mtime = datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT last_modified_at FROM file_index WHERE file_hash = ?", (file_hash,))
            row = cursor.fetchone()
            if row is None:
                return True
            return mtime != row[0]

    def mark_file_indexed(self, file_path: Path, file_source: str, chunk_count: int):
        file_hash = self.get_file_hash(file_path)
        file_size = file_path.stat().st_size
        mtime = datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO file_index
                (file_hash, file_path, file_source, file_size_bytes, chunk_count, last_modified_at, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (file_hash, str(file_path), file_source, file_size, chunk_count, mtime, "active"))
            conn.commit()


class IndexingPipeline:
    def __init__(self, dry_run: bool = False):
        self.config = get_config()
        self.dry_run = dry_run
        self.chunker = DocumentChunker(
            self.config.indexing.chunk_size_bytes,
            self.config.indexing.chunk_overlap_ratio
        )
        self.embedder = EmbeddingGenerator(
            self.config.azure_openai.api_key,
            self.config.azure_openai.endpoint,
            self.config.azure_openai.embedding_model
        )
        self.metadata = MetadataStore(self.config.indexing.sqlite_db_path)
        self.supabase_client = None

        # Build excluded paths list from env
        excluded_raw = os.getenv("EXCLUDED_PATHS", "")
        self.excluded_paths = [
            Path(p.strip()).resolve()
            for p in excluded_raw.split(",")
            if p.strip()
        ]
        if self.excluded_paths:
            logger.info(f"Excluding {len(self.excluded_paths)} paths from indexing")

        if dry_run:
            logger.info("DRY RUN MODE — no data will be written to Supabase")

    def _is_excluded(self, file_path: Path) -> bool:
        resolved = file_path.resolve()
        return any(
            str(resolved).startswith(str(excl))
            for excl in self.excluded_paths
        )

    def _init_supabase(self):
        try:
            from supabase import create_client
            self.supabase_client = create_client(
                self.config.supabase.url,
                self.config.supabase.api_key
            )
            logger.info("Supabase client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase: {e}")
            raise

    async def _get_files_to_index(self) -> AsyncGenerator[tuple[Path, str], None]:
        paths_to_scan = []
        if self.config.indexing.onedrive_path:
            paths_to_scan.append((self.config.indexing.onedrive_path, "onedrive"))
        if self.config.indexing.google_drive_path:
            paths_to_scan.append((self.config.indexing.google_drive_path, "google_drive"))
        for local_path in self.config.indexing.local_paths:
            paths_to_scan.append((local_path, "local"))

        for path_str, source in paths_to_scan:
            path = Path(path_str)
            if not path.exists():
                logger.warning(f"Path does not exist: {path}")
                continue

            # Handle single file
            if path.is_file():
                if path.suffix.lower() in self.config.indexing.supported_extensions:
                    yield path, source
                continue

            # Handle directory
            for file_path in path.rglob("*"):
                if not file_path.is_file():
                    continue
                if file_path.suffix.lower() not in self.config.indexing.supported_extensions:
                    continue
                if self._is_excluded(file_path):
                    logger.debug(f"Excluded: {file_path}")
                    continue
                # Skip common junk directories
                parts = set(file_path.parts)
                if any(p in parts for p in ("node_modules", ".git", "__pycache__", ".venv", "dist", ".wrangler")):
                    continue
                yield file_path, source

    async def index_documents(self):
        if not self.dry_run:
            self._init_supabase()

        logger.info("Starting document indexing pipeline")
        indexed_count = 0
        skipped_count = 0
        error_count = 0
        total_count = 0

        async with httpx.AsyncClient() as client:
            async for file_path, file_source in self._get_files_to_index():
                total_count += 1
                try:
                    if not self.metadata.file_needs_reindexing(file_path, file_source):
                        logger.debug(f"Skipping unchanged: {file_path}")
                        skipped_count += 1
                        continue

                    logger.info(f"[{total_count}] Processing: {file_path}")

                    text = FileProcessor.extract_text_from_file(file_path)
                    if not text:
                        error_count += 1
                        continue

                    chunks = self.chunker.chunk_text(text)
                    if not chunks:
                        error_count += 1
                        continue

                    if self.dry_run:
                        logger.info(f"[DRY RUN] Would index {len(chunks)} chunks from {file_path}")
                        indexed_count += 1
                        continue

                    file_hash = self.metadata.get_file_hash(file_path)
                    successful_chunks = 0
                    for chunk_idx, chunk_text in enumerate(chunks):
                        embedding = await self.embedder.generate_embedding(chunk_text, client)
                        if embedding:
                            try:
                                self.supabase_client.table("documents").insert({
                                    "file_hash": file_hash,
                                    "file_source": file_source,
                                    "file_path": str(file_path),
                                    "chunk_index": chunk_idx,
                                    "chunk_text": chunk_text,
                                    "content": chunk_text,
                                    "embedding": embedding,
                                    "metadata": {
                                        "source": file_source,
                                        "path": str(file_path),
                                        "chunk": chunk_idx
                                    }
                                }).execute()
                                successful_chunks += 1
                            except Exception as e:
                                logger.error(f"Failed to store chunk {chunk_idx} for {file_path}: {type(e).__name__}: {e}")

                    if successful_chunks > 0:
                        self.metadata.mark_file_indexed(file_path, file_source, len(chunks))
                        indexed_count += 1
                    else:
                        error_count += 1

                except Exception as e:
                    logger.error(f"Error processing {file_path}: {e}")
                    error_count += 1

        logger.info(
            f"\n{'='*60}\n"
            f"INDEXING {'(DRY RUN) ' if self.dry_run else ''}COMPLETE\n"
            f"{'='*60}\n"
            f"  Indexed:  {indexed_count}\n"
            f"  Skipped:  {skipped_count} (unchanged)\n"
            f"  Errors:   {error_count}\n"
            f"  Total:    {total_count}\n"
            f"  Tokens:   {self.embedder.token_count:,}\n"
            f"  Est cost: ${self.embedder.token_count / 1_000_000 * 0.02:.4f}\n"
            f"{'='*60}"
        )


async def main():
    parser = argparse.ArgumentParser(description="Vector search indexing pipeline")
    parser.add_argument("--dry-run", action="store_true", help="Scan and chunk files without writing to Supabase")
    parser.add_argument("--path", type=str, help="Index a single file or directory (overrides .env paths)")
    args = parser.parse_args()

    if args.path:
        # Override paths with single target
        os.environ["LOCAL_PATHS"] = args.path
        os.environ["ONEDRIVE_PATH"] = ""

    pipeline = IndexingPipeline(dry_run=args.dry_run)
    await pipeline.index_documents()


if __name__ == "__main__":
    asyncio.run(main())
