"""Configuration module for vector search indexing pipeline.

Handles environment variables, defaults, and runtime configuration.
Supports both .env files and environment variable overrides.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv


def _safe_int(env_var: str, default: int) -> int:
    """Safely parse an int from env var, returning default on failure."""
    try:
        return int(os.getenv(env_var, str(default)))
    except (ValueError, TypeError):
        return default


# Load environment variables from .env file if it exists
_env_path = Path(__file__).parent / ".env"
if _env_path.exists():
    load_dotenv(_env_path)


@dataclass
class AzureOpenAIConfig:
    """Azure OpenAI API configuration."""
    
    api_key: str
    api_version: str = "2024-02-15-preview"
    endpoint: str = "https://api.openai.com/v1"
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536
    
    @classmethod
    def from_env(cls) -> "AzureOpenAIConfig":
        """Load configuration from environment variables."""
        return cls(
            api_key=os.getenv("AZURE_OPENAI_API_KEY", ""),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
            endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", "https://api.openai.com/v1"),
            embedding_model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"),
            embedding_dimensions=_safe_int("EMBEDDING_DIMENSIONS", 1536),
        )


@dataclass
class SupabaseConfig:
    """Supabase database configuration."""
    
    url: str
    api_key: str
    
    @classmethod
    def from_env(cls) -> "SupabaseConfig":
        """Load configuration from environment variables."""
        return cls(
            url=os.getenv("SUPABASE_URL", ""),
            api_key=os.getenv("SUPABASE_API_KEY", ""),
        )


@dataclass
class IndexingConfig:
    """Indexing pipeline configuration."""
    
    # Chunking parameters
    chunk_size_bytes: int = 2048
    chunk_overlap_ratio: float = 0.5
    
    # Rate limiting (Azure quota)
    max_requests_per_minute: int = 200
    max_tokens_per_minute: int = 150000
    
    # Directory scanning
    onedrive_path: Optional[str] = None
    google_drive_path: Optional[str] = None
    local_paths: list[str] = None
    
    # File types to index
    supported_extensions: tuple[str, ...] = (
        ".txt", ".md", ".pdf", ".docx", ".py", ".json", ".csv", ".html"
    )
    
    # Database
    sqlite_db_path: str = "index_metadata.db"
    
    # Logging
    log_level: str = "INFO"
    
    def __post_init__(self):
        """Initialize default values for mutable fields."""
        if self.local_paths is None:
            self.local_paths = []
    
    @classmethod
    def from_env(cls) -> "IndexingConfig":
        """Load configuration from environment variables."""
        local_paths = os.getenv("LOCAL_PATHS", "").split(",")
        local_paths = [p.strip() for p in local_paths if p.strip()]
        
        return cls(
            chunk_size_bytes=_safe_int("CHUNK_SIZE_BYTES", 2048),
            chunk_overlap_ratio=float(os.getenv("CHUNK_OVERLAP_RATIO", "0.5")),
            max_requests_per_minute=_safe_int("MAX_REQUESTS_PER_MINUTE", 200),
            max_tokens_per_minute=_safe_int("MAX_TOKENS_PER_MINUTE", 150000),
            onedrive_path=os.getenv("ONEDRIVE_PATH"),
            google_drive_path=os.getenv("GOOGLE_DRIVE_PATH"),
            local_paths=local_paths,
            sqlite_db_path=os.getenv("SQLITE_DB_PATH", "index_metadata.db"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        )


@dataclass
class PipelineConfig:
    """Complete pipeline configuration."""
    
    azure_openai: AzureOpenAIConfig
    supabase: SupabaseConfig
    indexing: IndexingConfig
    
    @classmethod
    def from_env(cls) -> "PipelineConfig":
        """Load complete configuration from environment variables."""
        return cls(
            azure_openai=AzureOpenAIConfig.from_env(),
            supabase=SupabaseConfig.from_env(),
            indexing=IndexingConfig.from_env(),
        )
    
    def validate(self) -> bool:
        """Validate all required configuration is present.
        
        Returns:
            True if valid, raises ValueError otherwise.
        """
        errors = []
        
        if not self.azure_openai.api_key:
            errors.append("AZURE_OPENAI_API_KEY is not set")
        
        if not self.supabase.url:
            errors.append("SUPABASE_URL is not set")
        
        if not self.supabase.api_key:
            errors.append("SUPABASE_API_KEY is not set")
        
        if errors:
            raise ValueError(f"Configuration validation failed:\n" + "\n".join(errors))
        
        return True


# Global configuration instance
_config: Optional[PipelineConfig] = None


def get_config() -> PipelineConfig:
    """Get or create the global configuration instance."""
    global _config
    if _config is None:
        _config = PipelineConfig.from_env()
        _config.validate()
 