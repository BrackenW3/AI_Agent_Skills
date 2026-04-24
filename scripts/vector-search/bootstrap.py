#!/usr/bin/env python3
"""Bootstrap script for vector search indexing pipeline.

Validates and tests all components before indexing:
  - Python dependencies (pip requirements)
  - Environment configuration (.env file)
  - Azure OpenAI connectivity
  - Supabase connectivity
  - Database schema setup
  - Cost estimation for indexing

Usage:
  python bootstrap.py
  python bootstrap.py --verbose
  python bootstrap.py --skip-tests

Classes:
  BootstrapStatus: Status tracking for bootstrap checks
  DependencyChecker: Check and install Python dependencies
  EnvConfigChecker: Check .env file configuration
  AzureOpenAITester: Test Azure OpenAI connectivity and embeddings
  SupabaseTester: Test Supabase connectivity and schema
  DirectoryScanner: Scan configured directories for files to index
"""

import os
import sys
import subprocess
import logging
import hashlib
import json
from pathlib import Path
from typing import Dict, Tuple
import sqlite3

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class BootstrapStatus:
    """Status tracking for bootstrap checks.
    
    Attributes:
        checks (dict): Dictionary mapping component names to status results
        ready (bool): Overall readiness status
    """
    
    def __init__(self):
        """Initialize BootstrapStatus with empty checks and ready=True."""
        self.checks = {}
        self.ready = True
    
    def record(self, component: str, status: bool, message: str = ""):
        """Record a check result.
        
        Args:
            component (str): Name of the component being checked
            status (bool): True if check passed, False if failed
            message (str): Optional message describing the result
        """
        self.checks[component] = {
            "status": "✓ OK" if status else "✗ FAIL",
            "message": message
        }
        if not status:
            self.ready = False
    
    def print_summary(self):
        """Print formatted status summary.
        
        Returns:
            bool: True if overall status is READY, False otherwise
        """
        print("\n" + "=" * 70)
        print("BOOTSTRAP STATUS REPORT")
        print("=" * 70)
        
        for component, result in self.checks.items():
            status_str = result["status"]
            msg = f" - {result['message']}" if result["message"] else ""
            print(f"{component:.<50} {status_str}{msg}")
        
        print("=" * 70)
        overall = "READY" if self.ready else "NOT READY"
        print(f"Overall Status: {overall}")
        print("=" * 70 + "\n")
        
        return self.ready


class DependencyChecker:
    """Check and install Python dependencies.
    
    Attributes:
        None (static methods only)
    """
    
    @staticmethod
    def check_pip():
        """Verify pip is available.
        
        Returns:
            bool: True if pip is available and functional, False otherwise
        """
        try:
            subprocess.run(
                ["pip", "--version"],
                capture_output=True,
                check=True,
                timeout=5
            )
            return True
        except Exception as e:
            logger.error(f"pip not found: {e}")
            return False
    
    @staticmethod
    def install_requirements(requirements_file: str = "requirements.txt"):
        """Install requirements from requirements.txt.
        
        Uses sys.executable to ensure pip commands run in the current Python environment.
        
        Args:
            requirements_file (str): Path to requirements.txt file
            
        Returns:
            bool: True if installation successful, False otherwise
        """
        try:
            if not Path(requirements_file).exists():
                logger.error(f"requirements.txt not found: {requirements_file}")
                return False
            
            logger.info(f"Installing dependencies from {requirements_file}...")
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-q", "-r", requirements_file],
                check=True,
                timeout=120
            )
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install dependencies: {e}")
            return False
        except Exception as e:
            logger.error(f"Error during pip install: {e}")
            return False
    
    @staticmethod
    def check_imports():
        """Verify all required packages can be imported.
        
        Returns:
            tuple: (bool indicating success, list of missing packages)
        """
        required_packages = [
            ("openai", "OpenAI"),
            ("supabase", "Supabase"),
            ("tiktoken", "tiktoken"),
            ("docx", "python-docx"),
            ("pypdf", "pypdf"),
            ("aiohttp", "aiohttp"),
            ("dotenv", "python-dotenv"),
            ("pydantic", "pydantic"),
        ]
        
        missing = []
        for import_name, package_name in required_packages:
            try:
                __import__(import_name)
            except ImportError:
                missing.append(package_name)
        
        return len(missing) == 0, missing


class EnvConfigChecker:
    """Check .env file configuration.
    
    Attributes:
        None (static methods only)
    """
    
    @staticmethod
    def check_env_exists():
        """Check if .env file exists.
        
        Returns:
            bool: True if .env file exists, False otherwise
        """
        return Path(".env").exists()
    
    @staticmethod
    def load_env():
        """Load environment variables from .env.
        
        Returns:
            bool: True if load was successful, False otherwise
        """
        try:
            from dotenv import load_dotenv
            return load_dotenv(".env")
        except ImportError:
            logger.error("python-dotenv not installed")
            return False
    
    @staticmethod
    def check_required_vars():
        """Check all required environment variables are set.
        
        Returns:
            tuple: (bool indicating all vars set, list of missing variables)
        """
        required_vars = [
            "AZURE_OPENAI_API_KEY",
            "AZURE_OPENAI_ENDPOINT",
            "EMBEDDING_MODEL",
            "SUPABASE_URL",
            "SUPABASE_API_KEY",
        ]
        
        missing = []
        for var in required_vars:
            if not os.getenv(var):
                missing.append(var)
        
        return len(missing) == 0, missing
    
    @staticmethod
    def validate_env_format():
        """Validate environment variable values.
        
        Returns:
            tuple: (bool indicating all formats valid, list of validation errors)
        """
        errors = []
        
        # Check Azure OpenAI endpoint format
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "")
        if endpoint and not endpoint.startswith("https://"):
            errors.append(f"AZURE_OPENAI_ENDPOINT should be HTTPS URL, got: {endpoint}")
        
        # Check Supabase URL format
        supabase_url = os.getenv("SUPABASE_URL", "")
        if supabase_url and ".supabase.co" not in supabase_url:
            errors.append(f"SUPABASE_URL should contain .supabase.co, got: {supabase_url}")
        
        # Check API key format (non-empty)
        api_key = os.getenv("AZURE_OPENAI_API_KEY", "")
        if api_key and len(api_key) < 10:
            errors.append("AZURE_OPENAI_API_KEY appears too short")
        
        return len(errors) == 0, errors


class AzureOpenAITester:
    """Test Azure OpenAI connectivity and embeddings.
    
    Attributes:
        None (static methods only)
    """
    
    @staticmethod
    def test_connection():
        """Test basic Azure OpenAI API connectivity.
        
        Returns:
            tuple: (bool indicating success, str message describing result)
        """
        try:
            from openai import AzureOpenAI
            
            api_key = os.getenv("AZURE_OPENAI_API_KEY")
            endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
            api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
            
            if not api_key or not endpoint:
                return False, "Missing AZURE_OPENAI_API_KEY or AZURE_OPENAI_ENDPOINT"
            
            client = AzureOpenAI(
                api_key=api_key,
                api_version=api_version,
                azure_endpoint=endpoint
            )
            
            logger.info("Testing Azure OpenAI embedding generation...")
            test_text = "This is a test string for embeddings"
            response = client.embeddings.create(
                input=test_text,
                model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
            )
            
            embedding = response.data[0].embedding
            embedding_size = len(embedding)
            
            return True, f"Generated {embedding_size}-dim embedding"
        
        except ImportError:
            return False, "openai package not installed"
        except Exception as e:
            return False, f"Failed to generate embedding: {str(e)[:100]}"
    
    @staticmethod
    def estimate_embedding_cost(file_count: int, avg_tokens_per_file: int = 500):
        """Estimate Azure OpenAI embedding costs.
        
        Args:
            file_count (int): Number of files to index
            avg_tokens_per_file (int): Average tokens per file (default 500)
            
        Returns:
            tuple: (int total tokens, float estimated cost in USD)
        """
        # OpenAI text-embedding-3-small pricing (as of April 2026)
        # $0.02 per 1M tokens
        cost_per_million_tokens = 0.02
        
        total_tokens = file_count * avg_tokens_per_file
        estimated_cost = (total_tokens / 1_000_000) * cost_per_million_tokens
        
        return total_tokens, estimated_cost


class SupabaseTester:
    """Test Supabase connectivity and schema.
    
    Attributes:
        None (static methods only)
    """
    
    @staticmethod
    def test_connection():
        """Test basic Supabase connectivity.
        
        Returns:
            tuple: (bool indicating success, str message describing result)
        """
        try:
            from supabase import create_client
            
            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_API_KEY")
            
            if not url or not key:
                return False, "Missing SUPABASE_URL or SUPABASE_API_KEY"
            
            supabase = create_client(url, key)
            
            logger.info("Testing Supabase connectivity...")
            # Test with a simple query
            response = supabase.table("documents").select("count", count="exact").limit(1).execute()
            
            return True, "Connected successfully"
        
        except ImportError:
            return False, "supabase package not installed"
        except Exception as e:
            return False, f"Connection failed: {str(e)[:100]}"
    
    @staticmethod
    def check_schema():
        """Check if required Supabase tables exist.
        
        Returns:
            tuple: (bool indicating all tables exist, str message describing result)
        """
        try:
            from supabase import create_client
            
            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_API_KEY")
            
            if not url or not key:
                return False, "Missing SUPABASE_URL or SUPABASE_API_KEY"
            
            supabase = create_client(url, key)
            
            # Try to query each table
            tables_exist = True
            missing_tables = []
            
            for table_name in ["documents", "file_metadata"]:
                try:
                    supabase.table(table_name).select("count", count="exact").limit(1).execute()
                except Exception:
                    tables_exist = False
                    missing_tables.append(table_name)
            
            if tables_exist:
                return True, "All tables exist"
            else:
                return False, f"Missing tables: {', '.join(missing_tables)}"
        
        except Exception as e:
            return False, f"Failed to check schema: {str(e)[:100]}"


class DirectoryScanner:
    """Scan configured directories for files to index.
    
    Attributes:
        None (static methods only)
    """
    
    @staticmethod
    def scan_directories():
        """Count files in configured directories.
        
        Returns:
            tuple: (int total files, dict file counts by source)
        """
        try:
            from config import IndexingConfig
            config = IndexingConfig.from_env()
        except:
            return 0, {}
        
        file_counts = {}
        total_files = 0
        
        paths_to_scan = [
            ("OneDrive", config.onedrive_path),
            ("Google Drive", config.google_drive_path),
        ]
        
        for source_name, path_str in paths_to_scan:
            if path_str and Path(path_str).exists():
                file_count = len(list(Path(path_str).rglob("*")))
                file_counts[source_name] = file_count
                total_files += file_count
        
        for local_path in config.local_paths:
            if Path(local_path).exists():
                file_count = len(list(Path(local_path).rglob("*")))
                file_counts[f"Local: {local_path}"] = file_count
                total_files += file_count
        
        return total_files, file_counts
    
    @staticmethod
    def estimate_indexing_time(file_count: int, avg_seconds_per_file: float = 0.5):
        """Estimate total indexing time.
        
        Args:
            file_count (int): Number of files to index
            avg_seconds_per_file (float): Average time per file in seconds
            
        Returns:
            tuple: (float hours, float minutes)
        """
        total_seconds = file_count * avg_seconds_per_file
        hours = total_seconds / 3600
        minutes = (total_seconds % 3600) / 60
        
        return hours, minutes


def run_bootstrap(verbose: bool = False, skip_tests: bool = False):
    """Run complete bootstrap sequence.
    
    Performs all validation checks and reports readiness status.
    
    Args:
        verbose (bool): Enable verbose output (default False)
        skip_tests (bool): Skip API connectivity tests (default False)
        
    Returns:
        bool: True if all checks pass, False otherwise
    """
    status = BootstrapStatus()
    
    print("\n" + "=" * 70)
    print("VECTOR SEARCH PIPELINE BOOTSTRAP")
    print("=" * 70 + "\n")
    
    # Step 1: Check pip
    print("Step 1: Checking Python package manager...")
    pip_ok = DependencyChecker.check_pip()
    status.record("pip", pip_ok)
    
    if not pip_ok:
        status.print_summary()
        return False
    
    # Step 2: Install dependencies
    print("Step 2: Installing dependencies...")
    install_ok = DependencyChecker.install_requirements()
    status.record("Dependencies", install_ok)
    
    if not install_ok:
        status.print_summary()
        return False
    
    # Step 3: Verify imports
    print("Step 3: Verifying package imports...")
    imports_ok, missing = DependencyChecker.check_imports()
    msg = "" if imports_ok else f"Missing: {', '.join(missing)}"
    status.record("Imports", imports_ok, msg)
    
    # Step 4: Check .env file
    print("Step 4: Checking environment configuration...")
    env_exists = EnvConfigChecker.check_env_exists()
    if env_exists:
        EnvConfigChecker.load_env()
    status.record(".env file", env_exists, "Create from .env.example if missing")
    
    # Step 5: Check environment variables
    print("Step 5: Validating environment variables...")
    vars_ok, missing_vars = EnvConfigChecker.check_required_vars()
    msg = "" if vars_ok else f"Missing: {', '.join(missing_vars[:3])}"
    status.record("Required variables", vars_ok, msg)
    
    # Step 6: Validate variable formats
    print("Step 6: Validating variable formats...")
    format_ok, format_errors = EnvConfigChecker.validate_env_format()
    msg = "" if format_ok else f"Issues: {format_errors[0][:50]}"
    status.record("Variable formats", format_ok, msg)
    
    if not skip_tests and vars_ok and format_ok:
        # Step 7: Test Azure OpenAI
        print("Step 7: Testing Azure OpenAI connectivity...")
        azure_ok, azure_msg = AzureOpenAITester.test_connection()
        status.record("Azure OpenAI API", azure_ok, azure_msg)
        
        # Step 8: Test Supabase
        print("Step 8: Testing Supabase connectivity...")
        sb_ok, sb_msg = SupabaseTester.test_connection()
        status.record("Supabase API", sb_ok, sb_msg)
        
        # Step 9: Check Supabase schema
        print("Step 9: Checking Supabase schema...")
        schema_ok, schema_msg = SupabaseTester.check_schema()
        status.record("Supabase schema", schema_ok, schema_msg)
    else:
        status.record("Azure OpenAI API", False, "Skipped (missing config)")
        status.record("Supabase API", False, "Skipped (missing config)")
        status.record("Supabase schema", False, "Skipped (missing config)")
    
    # Step 10: Scan directories
    print("Step 10: Scanning configured directories...")
    file_count, file_breakdown = DirectoryScanner.scan_directories()
    if file_count > 0:
        breakdown_str = "; ".join([f"{src}: {cnt}" for src, cnt in file_breakdown.items()])
        status.record(f"Directory scan", True, f"{file_count} files found")
    else:
        status.record("Directory scan", False, "No paths configured or accessible")
    
    # Step 11: Cost estimation
    print("Step 11: Estimating indexing costs...")
    if file_count > 0:
        tokens, cost = AzureOpenAITester.estimate_embedding_cost(file_count)
        hours, minutes = DirectoryScanner.estimate_indexing_time(file_count)
        cost_msg = f"~${cost:.2f} for {tokens:,} tokens; ~{int(hours)}h {int(minutes)}m to index"
        status.record("Cost estimate", True, cost_msg)
    else:
        status.record("Cost estimate", False, "Cannot estimate (no files found)")
    
    # Print final status
    ready = status.print_summary()
    
    if ready:
        print("\n✓ System is ready to begin indexing!")
        print("  Next step: python indexer.py")
    else:
        print("\n✗ System is NOT ready. Fix the issues above before proceeding.")
        print("  Review the messages above and update your .env configuration.")
    
    return ready


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Bootstrap vector search pipeline")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--skip-tests", action="store_true", help="Skip API tests")
    
    args = parser.parse_args()
    
    ready = run_bootstrap(verbose=args.verbose, skip_tests=args.skip_tests)
    sys.exit(0 if ready else 1)
