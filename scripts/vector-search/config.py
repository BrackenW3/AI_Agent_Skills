#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Configuration module for vector search indexing pipeline.

Handles environment variables, defaults, and runtime configuration.
Supports both .env files and environment variable overrides.

Classes:
    AzureOpenAIConfig: Azure OpenAI API configuration
    SupabaseConfig: Supabase database configuration
    IndexingConfig: Document indexing pipeline configuration
    PipelineConfig: Complete pipeline configuration
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv


def _safe_int(env_var: str, default: int) -> int:
    """Safely parse an int from env var, returning default on failure.
    
    Args:
        env_var: Environment variable name
        default: Default value if parsing fails
        
    Returns:
        Parsed integer or default value
    """
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
    """Azure OpenAI API configuration.
    
    Attributes:
        api_key: Azure OpenAI API authentication key (required)
        api_version: API version for compatibility (default: 2024-02-15-preview)
        endpoint: Azure OpenAI endpoint URL (default: https://api.openai.com/v1)
        embedding_model: Model name for embedding generation (default: text-embedding-3-small)
        embedding_dimensions: Vector dimension size (default: 1536)
    """
    
    api_key: str
    api_version: str = "2024-02-15-preview"
    endpoint: str = "https://api.openai.com/v1"
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536
    
    @classmethod
    def from_env(cls) -> "AzureOpenAIConfig":
        """Load configuration from environment variables.
        
        Reads AZURE_OPENAI_API_KEY, AZURE_OPENAI_API_VERSION, AZURE_OPENAI_ENDPOINT,
        EMBEDDING_MODEL, and EMBEDDING_DIMENSIONS from environment.
        
        Returns:
            AzureOpenAIConfig instance with loaded values
            
        Raises:
            ValueError: If api_key is not set or api_version is not supported
        """
        api_key = os.getenv("AZURE_OPENAI_API_KEY", "")
        api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "https://api.openai.com/v1")
        embedding_model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
        embedding_dimensions = _safe_int("EMBEDDING_DIMENSIONS", 1536)
        
        # Check required environment variables
        if not api_key:
            raise ValueError("AZURE_OPENAI_API_KEY environment variable is not set")
        
        # Validate api_version format (YYYY-MM-DD or YYYY-MM-DD-preview)
        import re
        if not re.match(r"^\d{4}-\d{2}-\d{2}(-preview)?$", api_version):
            raise ValueError(
                f"AZURE_OPENAI_API_VERSION '{api_version}' has invalid format. "
                f"Expected YYYY-MM-DD or YYYY-MM-DD-preview"
            )
        
        return cls(
            api_key=api_key,
            api_version=api_version,
            endpoint=endpoint,
            embedding_model=embedding_model,
            embedding_dimensions=embedding_dimensions,
        )


@dataclass
class SupabaseConfig:
    """Supabase database configuration.
    
    Attributes:
        url: Supabase project URL (required)
        api_key: Supabase API key for authentication (required)
    """
    
    url: str
    api_key: str
    
    @classmethod
    def from_env(cls) -> "SupabaseConfig":
        """Load configuration from environment variables.
        
        Reads SUPABASE_URL and SUPABASE_API_KEY from environment.
        
        Returns:
            SupabaseConfig instance with loaded values
            
        Raises:
            ValueError: If url or api_key are not set
        """
        url = os.getenv("SUPABASE_URL", "")
        api_key = os.getenv("SUPABASE_API_KEY", "")
        
        # Check required environment variables
        if not url:
            raise ValueError("SUPABASE_URL environment variable is not set")
        if not api_key:
            raise ValueError("SUPABASE_API_KEY environment variable is not set")
        
        return cls(
            url=url,
            api_key=api_key,
        )


@dataclass
class IndexingConfig:
    """Indexing pipeline configuration.
    
    Attributes:
        chunk_size_bytes: Size of text chunks in bytes (default: 2048)
        chunk_overlap_ratio: Overlap ratio between chunks (default: 0.5)
        max_requests_per_minute: Rate limit for API requests (default: 200)
        max_tokens_per_minute: Token rate limit (default: 150000)
        onedrive_path: Path to OneDrive folder for indexing (optional)
        google_drive_path: Path to Google Drive folder for indexing (optional)
        local_paths: List of local file paths to index
        supported_extensions: File extensions to process for indexing
        sqlite_db_path: Path to SQLite metadata database (default: index_metadata.db)
        log_level: Logging level (default: INFO)
    """
    
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
        """Load configuration from environment variables.
        
        Reads CHUNK_SIZE_BYTES, CHUNK_OVERLAP_RATIO, MAX_REQUESTS_PER_MINUTE,
        MAX_TOKENS_PER_MINUTE, ONEDRIVE_PATH, GOOGLE_DRIVE_PATH, LOCAL_PATHS,
        SQLITE_DB_PATH, and LOG_LEVEL from environment.
        
        Returns:
            IndexingConfig instance with loaded values
        """
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
    """Complete pipeline configuration.
    
    Aggregates all component configurations (Azure OpenAI, Supabase, indexing)
    and provides validation to ensure system readiness.
    
    Attributes:
        azure_openai: Azure OpenAI configuration
        supabase: Supabase database configuration
        indexing: Indexing pipeline configuration
    """
    
    azure_openai: AzureOpenAIConfig
    supabase: SupabaseConfig
    indexing: IndexingConfig
    
    @classmethod
    def from_env(cls) -> "PipelineConfig":
        """Load complete configuration from environment variables.
        
        Creates AzureOpenAIConfig, SupabaseConfig, and IndexingConfig from
        environment variables and combines them into a single PipelineConfig.
        
        Returns:
            PipelineConfig instance with all component configurations
            
        Raises:
            ValueError: If any required environment variables are missing
        """
        return cls(
            azure_openai=AzureOpenAIConfig.from_env(),
            supabase=SupabaseConfig.from_env(),
            indexing=IndexingConfig.from_env(),
        )
    
    def validate(self) -> bool:
        """Validate all required configuration is present.
        
        Checks that all required environment variables are set for Azure OpenAI
        and Supabase integrations. Raises detailed errors for missing config.
        
        Returns:
            True if valid
            
        Raises:
            ValueError: If any required configuration is missing or invalid
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
    """Get or create the global configuration instance.
    
    Returns:
        Singleton PipelineConfig instance
    """
    global _config
    if _config is None:
        _config = PipelineConfig.from_env()
        _config.validate()
    return _config
