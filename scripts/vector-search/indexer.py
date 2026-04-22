"""Vector search indexing pipeline.

Main module for scanning directories, chunking documents, generating embeddings,
and storing vectors in Supabase with metadata tracking for deduplication.

Supports:
- OneDrive and Google Drive directory scanning
- Multiple file types (.txt, .md, .pdf, .docx, .py, .json, .csv, .html)
- Incremental indexing with SHA-256 deduplication
- Async concurrent API calls with rate limiting
- Azure OpenAI text-embedding-3-small embeddings
- Supabase pgvector storage
"""

import asyncio
import hashlib
import logging
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, AsyncGenerator
import json

import aiohttp
import tiktoken
from docx import Document
from pypdf import PdfReader

from config import get_config


# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DocumentChunker:
    """Chunks documents into overlapping segments for embedding."""
    
    def __init__(self, chunk_size_bytes: int = 2048, overlap_ratio: float = 0.5):
        """Initialize chunker.
        
        Args:
            chunk_size_bytes: Target chunk size in bytes
            overlap_ratio: Overlap between chunks (0.0 to 1.0)
        """
        self.chunk_size_bytes = chunk_size_bytes
        self.overlap_ratio = overlap_ratio
        self.overlap_bytes = int(chunk_size_bytes * overlap_ratio)
    
    def chunk_text(self, text: str) -> list[str]:
        """Chunk text into overlapping segments.
        
        Args:
            text: Text to chunk
            
        Returns:
            List of text chunks
        """
        if not text:
            return []
        
        # Encode to bytes for accurate size calculation
        text_bytes = text.encode("utf-8")
        chunks = []
        start = 0
        
        while start < len(text_bytes):
            # Find chunk end position
            end = min(start + self.chunk_size_bytes, len(text_bytes))
            
            # Try to avoid cutting off mid-character
            while end < len(text_bytes):
                try:
                    text_bytes[start:end].decode("utf-8")
                    break
                except UnicodeDecodeError:
                    end -= 1
            
            if end <= start:
                # Safety fallback
                end = min(start + 1, len(text_bytes))
            
            chunk = text_bytes[start:end].decode("utf-8", errors="ignore").strip()
            if chunk:
                chunks.append(chunk)
            
            # Move start position for next chunk with overlap
            start = end - self.overlap_bytes if end < len(text_bytes) else len(text_bytes)
        
        return chunks


class FileProcessor:
    """Processes various file formats and extracts text."""
    
    @staticmethod
    def extract_text_from_file(file_path: Path) -> Optional[str]:
        """Extract text from supported file formats.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Extracted text or None if processing fails
        """
        try:
            suffix = file_path.suffix.lower()
            
            if suffix == ".txt":
                return file_path.read_text(encoding="utf-8", errors="ignore")
            
            elif suffix == ".md":
                return file_path.read_text(encoding="utf-8", errors="ignore")
            
            elif suffix == ".json":
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return json.dumps(data, indent=2)
            
            elif suffix == ".pdf":
                try:
                    reader = PdfReader(file_path)
                    text = ""
                    for page in reader.pages:
                        text += page.extract_text() + "\n"
                    return text
                except Exception as e:
                    logger.warning(f"Failed to read PDF {file_path}: {e}")
                    return None
            
            elif suffix == ".docx":
                try:
                    doc = Document(file_path)
                    text = "\n".join(paragraph.text for paragraph in doc.paragraphs)
                    return text
                except Exception as e:
                    logger.warning(f"Failed to read DOCX {file_path}: {e}")
                    return None
            
            elif suffix in (".py", ".csv", ".html"):
                return file_path.read_text(encoding="utf-8", errors="ignore")
            
            else:
                logger.debug(f"Unsupported file type: {suffix}")
                return None
                
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            return None


class EmbeddingGenerator:
    """Generates embeddings using Azure OpenAI API with rate limiting."""
    
    def __init__(self, api_key: str, endpoint: str, model: str):
        """Initialize embedding generator.
        
        Args:
            api_key: Azure OpenAI API key
            endpoint: API endpoint
            model: Model name (e.g., text-embedding-3-small)
        """
        self.api_key = api_key
        self.endpoint = endpoint
        self.model = model
        self.request_times = []
        self.token_count = 0
        self.encoding = tiktoken.encoding_for_model(model)
    
    async def generate_embedding(
        self,
        text: str,
        session: aiohttp.ClientSession,
        max_retries: int = 3
    ) -> Optional[list[float]]:
        """Generate embedding for text with retry logic.
        
        Args:
            text: Text to embed
            session: aiohttp session
            max_retries: Maximum retry attempts
            
        Returns:
            Embedding vector or None if generation fails
        """
        # Apply rate limiting
        await self._apply_rate_limit()
        
        # Count tokens
        token_count = len(self.encoding.encode(text))
        self.token_count += token_count
        
        headers = {
            "api-key": self.api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "input": text,
            "model": self.model
        }
        
        for attempt in range(max_retries):
            try:
                async with session.post(
                    f"{self.endpoint}/embeddings",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        embedding = data["data"][0]["embedding"]
                        logger.debug(f"Generated embedding for {len(text)} chars")
                        return embedding
                    
                    elif resp.status == 429:  # Rate limited
                        wait_time = 2 ** attempt
                        logger.warning(f"Rate limited, waiting {wait_time}s")
                        await asyncio.sleep(wait_time)
                    
                    else:
                        error_text = await resp.text()
                        logger.error(f"API error {resp.status}: {error_text}")
                        if attempt < max_retries - 1:
                            await asyncio.sleep(2 ** attempt)
                        else:
                            return None
            
            except asyncio.TimeoutError:
                logger.error(f"Timeout generating embedding (attempt {attempt + 1})")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
            
            except Exception as e:
                logger.error(f"Error generating embedding: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    return None
        
        return None
    
    async def _apply_rate_limit(self):
        """Apply rate limiting based on request frequency."""
        config = get_config()
        max_rpm = config.indexing.max_requests_per_minute
        
        now = time.time()
        # Remove requests older than 1 minute
        self.request_times = [t for t in self.request_times if now - t < 60]
        
        if len(self.request_times) >= max_rpm:
            sleep_time = 60 - (now - self.request_times[0])
            if sleep_time > 0:
                logger.info(f"Rate limit reached, sleeping {sleep_time:.1f}s")
                await asyncio.sleep(sleep_time)
            self.request_times = []
        
        self.request_times.append(now)


class MetadataStore:
    """SQLite database for tracking file metadata and deduplication."""
    
    def __init__(self, db_path: str):
        """Initialize metadata store.
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema."""
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
        """Calculate SHA-256 hash of file.
        
        Args:
            file_path: Path to file
            
        Returns:
            Hex digest of SHA-256 hash
        """
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    def file_needs_reindexing(self, file_path: Path, file_source: str) -> bool:
        """Check if file needs reindexing based on hash and modification time.
        
        Args:
            file_path: Path to file
            file_source: Source identifier (onedrive, google_drive, local)
            
        Returns:
            True if file needs reindexing
        """
        file_hash = self.get_file_hash(file_path)
        mtime = datetime.fromtimestamp(
            file_path.stat().st_mtime,
            tz=timezone.utc
        ).isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT last_modified_at FROM file_index WHERE file_hash = ?",
                (file_hash,)
            )
            row = cursor.fetchone()
            
            if row is None:
                return True
            
            stored_mtime = row[0]
            return mtime != stored_mtime
    
    def mark_file_indexed(
        self,
        file_path: Path,
        file_source: str,
        chunk_count: int
    ):
        """Mark file as indexed in metadata store.
        
        Args:
            file_path: Path to file
            file_source: Source identifier
            chunk_count: Number of chunks created
        """
        file_hash = self.get_file_hash(file_path)
        file_size = file_path.stat().st_size
        mtime = datetime.fromtimestamp(
            file_path.stat().st_mtime,
            tz=timezone.utc
        ).isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO file_index
                (file_hash, file_path, file_source, file_size_bytes, chunk_count, last_modified_at, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (file_hash, str(file_path), file_source, file_size, chunk_count, mtime, "active"))
            conn.commit()


class IndexingPipeline:
    """Main indexing pipeline orchestrator."""
    
    def __init__(self):
        """Initialize the indexing pipeline."""
        self.config = get_config()
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
        logger.info("Indexing pipeline initialized")
    
    def _init_supabase(self):
        """Initialize Supabase client."""
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
    
    def _get_files_to_index(self) -> AsyncGenerator[tuple[Path, str], None]:
        """Scan configured directories for files to index.
        
        Yields:
            Tuples of (file_path, file_source)
        """
        async def _scan():
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
                
                for file_path in path.rglob("*"):
                    if file_path.is_file() and file_path.suffix.lower() in self.config.indexing.supported_extensions:
                        yield file_path, source
        
        return _scan()
    
    async def index_documents(self):
        """Run the complete indexing pipeline."""
        self._init_supabase()
        
        logger.info("Starting document indexing pipeline")
        indexed_count = 0
        skipped_count = 0
        error_count = 0
        
        try:
            async with aiohttp.ClientSession() as session:
                async for file_path, file_source in self._get_files_to_index():
                    try:
                        # Check if file needs reindexing
                        if not self.metadata.file_needs_reindexing(file_path, file_source):
                            logger.debug(f"Skipping unchanged file: {file_path}")
                            skipped_count += 1
                            continue
                        
                        logger.info(f"Processing: {file_path}")
                        
                        # Extract text from file
                        text = FileProcessor.extract_text_from_file(file_path)
                        if not text:
                            logger.warning(f"Failed to extract text: {file_path}")
                            error_count += 1
                            continue
                        
                        # Chunk the text
                        chunks = self.chunker.chunk_text(text)
                        if not chunks:
                            logger.warning(f"No chunks generated: {file_path}")
                            error_count += 1
                            continue
                        
                        logger.info(f"Generated {len(chunks)} chunks for {file_path}")
                        
                        # Generate embeddings and store
                        file_hash = self.metadata.get_file_hash(file_path)
                        for chunk_idx, chunk_text in enumerate(chunks):
                            embedding = await self.embedder.generate_embedding(
                                chunk_text,
                                session
                            )
                            
                            if embedding:
                                # Store in Supabase
                                self.supabase_client.table("documents").insert({
                                    "file_hash": file_hash,
                                    "file_source": file_source,
                                    "file_path": str(file_path),
                                    "chunk_index": chunk_idx,
                                    "chunk_text": chunk_text,
                                    "embedding": embedding
                                }).execute()
                        
                        # Mark file as indexed
                        self.metadata.mark_file_indexed(file_path, file_source, len(chunks))
                        indexed_count += 1
                        
                        logger.info(f"Successfully indexed: {file_path}")
                    
                    except Exception as e:
                        logger.error(f"Error processing {file_path}: {e}")
                        error_count += 1
                        continue
        
        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            raise
        
        finally:
            # Log statistics
            logger.info(
                f"Indexing complete - "
                f"Indexed: {indexed_count}, "
                f"Skipped: {skipped_count}, "
                f"Errors: {error_count}, "
                f"Total tokens: {self.embedder.token_count}"
            )


async def main():
    """Main entry point."""
    pipeline = IndexingPipeline()
    await pipeline.index_documents()


if __name__ == "__main__":
    asyncio.run(main())
