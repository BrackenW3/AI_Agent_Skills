#!/usr/bin/env python3
"""
Google Drive Partition Manager
Organizes Google Drive storage into Personal (~1/3) and Data (~2/3) partitions.

OAuth2 Setup:
Same as cleanup-gdrive.py - credentials at ~/.google_credentials.json

Usage:
  python partition-gdrive.py --scan          # Analyze current structure
  python partition-gdrive.py --execute       # Move files to partitions
  python partition-gdrive.py --status        # Show partition usage
"""

import os
import sys
import json
import argparse
import time
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime

from google.oauth2.credentials import Credentials as UserCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


# Configuration
SCOPES = ["https://www.googleapis.com/auth/drive"]
CREDENTIALS_FILE = os.path.expanduser("~/.google_credentials.json")
TOKEN_FILE = os.path.expanduser("~/.google_token.json")

# Storage targets (in bytes)
TOTAL_QUOTA = 5 * 1024 * 1024 * 1024 * 1024  # 5TB
PERSONAL_TARGET = TOTAL_QUOTA // 3            # ~1.67TB
DATA_TARGET = TOTAL_QUOTA * 2 // 3            # ~3.33TB

# File size constants
KB = 1024
MB = KB * 1024
GB = MB * 1024
TB = GB * 1024


# MIME type categories
PERSONAL_MIMES = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    "image/bmp",
    "image/tiff",
    "image/x-canon-crw",
    "image/x-canon-raw",
    "video/mp4",
    "video/quicktime",
    "video/x-msvideo",
    "application/vnd.google-apps.document",
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}

DATA_MIMES = {
    "text/csv",
    "application/json",
    "application/x-parquet",
    "application/x-sqlite3",
    "application/gzip",
    "application/zip",
    "application/vnd.google-apps.spreadsheet",
}


@dataclass
class FileInfo:
    """Represents a Google Drive file"""
    id: str
    name: str
    size: int  # in bytes
    parent_id: str
    mime_type: str
    modified_time: str
    is_folder: bool = False

    def format_size(self) -> str:
        """Human-readable file size"""
        if self.size >= TB:
            return f"{self.size / TB:.2f} TB"
        elif self.size >= GB:
            return f"{self.size / GB:.2f} GB"
        elif self.size >= MB:
            return f"{self.size / MB:.2f} MB"
        elif self.size >= KB:
            return f"{self.size / KB:.2f} KB"
        return f"{self.size} B"

    def get_suggested_partition(self) -> str:
        """Suggest which partition this file should go to"""
        lower_name = self.name.lower()
        
        # Check by MIME type first
        if self.mime_type in PERSONAL_MIMES:
            return "Personal"
        if self.mime_type in DATA_MIMES:
            return "Data"
        
        # Check by filename patterns
        personal_patterns = {
            "photo", "image", "picture", "backup", "email", "contact",
            "document", "resume", "receipt", "bill", "invoice"
        }
        data_patterns = {
            "data", "export", "api", "output", "query", "result",
            "csv", "json", "parquet", "duckdb", "database", "index"
        }
        
        for pattern in personal_patterns:
            if pattern in lower_name:
                return "Personal"
        
        for pattern in data_patterns:
            if pattern in lower_name:
                return "Data"
        
        # Default: Data for unclassified
        return "Data"


@dataclass
class PartitionReport:
    """Partition analysis report"""
    total_files: int = 0
    personal_files: List[FileInfo] = field(default_factory=list)
    data_files: List[FileInfo] = field(default_factory=list)
    unclassified: List[FileInfo] = field(default_factory=list)
    personal_size: int = 0
    data_size: int = 0
    unclassified_size: int = 0
    personal_target_exceeded: bool = False

    def format_report(self) -> str:
        """Generate formatted report"""
        lines = [
            "\n" + "=" * 80,
            "GOOGLE DRIVE PARTITION ANALYSIS",
            "=" * 80,
            f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"\nTotal Files: {self.total_files}",
            f"Total Size: {self._format_bytes(self.personal_size + self.data_size + self.unclassified_size)}",
            
            f"\n--- PERSONAL PARTITION (~1/3, target {self._format_bytes(PERSONAL_TARGET)}) ---",
            f"Files: {len(self.personal_files)}",
            f"Size: {self._format_bytes(self.personal_size)}",
        ]
        
        if self.personal_target_exceeded:
            lines.append(f"⚠️  WARNING: Personal exceeds target by {self._format_bytes(self.personal_size - PERSONAL_TARGET)}")
        
        lines.extend([
            f"\n--- DATA PARTITION (~2/3, target {self._format_bytes(DATA_TARGET)}) ---",
            f"Files: {len(self.data_files)}",
            f"Size: {self._format_bytes(self.data_size)}",
            
            f"\n--- UNCLASSIFIED ({len(self.unclassified)} files) ---",
            f"Size: {self._format_bytes(self.unclassified_size)}",
        ])
        
        if self.unclassified and len(self.unclassified) <= 20:
            lines.append("\nUnclassified files:")
            for f in sorted(self.unclassified, key=lambda x: x.size, reverse=True):
                lines.append(f"  → {f.name} ({f.format_size()}) [{f.mime_type}]")
        elif self.unclassified:
            lines.append("\nTop 20 unclassified files:")
            for f in sorted(self.unclassified, key=lambda x: x.size, reverse=True)[:20]:
                lines.append(f"  → {f.name} ({f.format_size()}) [{f.mime_type}]")
            lines.append(f"  ... and {len(self.unclassified) - 20} more")
        
        lines.append("\n--- RECOMMENDED STRUCTURE ---")
        lines.extend([
            "Personal/",
            "  ├── Photos/        (image files)",
            "  ├── Documents/     (personal docs, PDFs)",
            "  ├── Backups/       (device backups, archives)",
            "  └── Email/         (email archives, mbox files)",
            "",
            "Data/",
            "  ├── DuckDB/        (parquet, CSV files)",
            "  ├── API-Storage/   (API exports, JSON responses)",
            "  ├── Indexes/       (indexed data, metadata)",
            "  └── Exports/       (query results, reports)",
            "",
            "Projects/",
            "  ├── Active/        (current projects)",
            "  └── Archive/       (completed projects)",
        ])
        
        lines.append("\n" + "=" * 80)
        return "\n".join(lines)

    @staticmethod
    def _format_bytes(size: int) -> str:
        """Format bytes to human readable"""
        if size >= TB:
            return f"{size / TB:.2f} TB"
        elif size >= GB:
            return f"{size / GB:.2f} GB"
        elif size >= MB:
            return f"{size / MB:.2f} MB"
        elif size >= KB:
            return f"{size / KB:.2f} KB"
        return f"{size} B"


class DrivePartitionManager:
    """Manages Google Drive partitioning"""
    
    def __init__(self):
        self.service = None
        self.folder_cache: Dict[str, str] = {}  # name -> id mapping
        self._auth()
    
    def _auth(self):
        """Authenticate with Google Drive API"""
        try:
            # Try to load existing token
            if os.path.exists(TOKEN_FILE):
                with open(TOKEN_FILE, "r") as f:
                    creds_data = json.load(f)
                    self.service = build("drive", "v3", credentials=UserCredentials.from_authorized_user_info(creds_data))
                print("✓ Loaded cached credentials")
                return
        except Exception as e:
            print(f"Token load failed: {e}")
        
        # Check for credentials file
        if not os.path.exists(CREDENTIALS_FILE):
            print(f"ERROR: Credentials file not found at {CREDENTIALS_FILE}")
            print("Please download OAuth2 credentials from Google Cloud Console:")
            print("1. Go to https://console.cloud.google.com/")
            print("2. Create a new project")
            print("3. Enable Google Drive API")
            print("4. Create OAuth2 credentials (Desktop application)")
            print("5. Download as JSON and save to ~/.google_credentials.json")
            sys.exit(1)
        
        # Create new auth flow
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
        creds = flow.run_local_server(port=0)
        
        # Save token
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
        
        self.service = build("drive", "v3", credentials=creds)
        print("✓ Successfully authenticated with Google Drive")
    
    def list_all_files(self) -> Dict[str, FileInfo]:
        """List all files in Google Drive"""
        files = {}
        page_token = None
        query = "trashed = false"
        
        print("📂 Listing files in Google Drive...")
        count = 0
        
        while True:
            try:
                results = self.service.files().list(
                    q=query,
                    spaces="drive",
                    pageSize=1000,
                    pageToken=page_token,
                    fields="nextPageToken, files(id, name, size, parents, mimeType, modifiedTime)",
                ).execute()
                
                for item in results.get("files", []):
                    is_folder = item.get("mimeType") == "application/vnd.google-apps.folder"
                    
                    file_info = FileInfo(
                        id=item["id"],
                        name=item["name"],
                        size=int(item.get("size", 0)),
                        parent_id=item["parents"][0] if item.get("parents") else "root",
                        mime_type=item.get("mimeType", ""),
                        modified_time=item.get("modifiedTime", ""),
                        is_folder=is_folder,
                    )
                    files[item["id"]] = file_info
                    count += 1
                    if count % 500 == 0:
                        print(f"  ... {count} files listed")
                
                page_token = results.get("nextPageToken")
                if not page_token:
                    break
            
            except HttpError as e:
                print(f"Error listing files: {e}")
                break
        
        print(f"✓ Listed {count} files total")
        return files
    
    def scan_files(self, files: Dict[str, FileInfo]) -> PartitionReport:
        """Analyze files and suggest partitions"""
        report = PartitionReport()
        report.total_files = len(files)
        
        for file_id, file_info in files.items():
            if file_info.is_folder:
                continue
            
            partition = file_info.get_suggested_partition()
            
            if partition == "Personal":
                report.personal_files.append(file_info)
                report.personal_size += file_info.size
            elif partition == "Data":
                report.data_files.append(file_info)
                report.data_size += file_info.size
            else:
                report.unclassified.append(file_info)
                report.unclassified_size += file_info.size
        
        report.personal_target_exceeded = report.personal_size > PERSONAL_TARGET
        
        return report
    
    def ensure_partition_folders(self) -> Dict[str, str]:
        """Create partition folder structure if it doesn't exist"""
        folder_ids = {}
        
        # Define structure: (parent_folder_name, folder_names_to_create)
        structure = {
            "Personal": ["Photos", "Documents", "Backups", "Email"],
            "Data": ["DuckDB", "API-Storage", "Indexes", "Exports"],
            "Projects": ["Active", "Archive"],
        }
        
        try:
            # Check existing folders
            results = self.service.files().list(
                q="mimeType='application/vnd.google-apps.folder' and trashed=false",
                spaces="drive",
                pageSize=1000,
                fields="files(id, name, parents)",
            ).execute()
            
            existing = {item["name"]: item["id"] for item in results.get("files", [])}
            
            # Create root partitions
            for partition_name in structure.keys():
                if partition_name not in existing:
                    file_metadata = {
                        "name": partition_name,
                        "mimeType": "application/vnd.google-apps.folder",
                    }
                    file = self.service.files().create(
                        body=file_metadata,
                        fields="id"
                    ).execute()
                    folder_ids[partition_name] = file.get("id")
                    print(f"✓ Created folder: {partition_name}")
                else:
                    folder_ids[partition_name] = existing[partition_name]
                    print(f"✓ Found existing folder: {partition_name}")
            
            # Create subfolders
            for partition_name, subfolders in structure.items():
                parent_id = folder_ids[partition_name]
                
                for subfolder_name in subfolders:
                    full_path = f"{partition_name}/{subfolder_name}"
                    
                    # Check if subfolder exists under this parent
                    results = self.service.files().list(
                        q=f"name='{subfolder_name}' and '{parent_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false",
                        spaces="drive",
                        fields="files(id)",
                    ).execute()
                    
                    if results.get("files"):
                        folder_ids[full_path] = results["files"][0]["id"]
                        print(f"✓ Found existing folder: {full_path}")
                    else:
                        file_metadata = {
                            "name": subfolder_name,
                            "parents": [parent_id],
                            "mimeType": "application/vnd.google-apps.folder",
                        }
                        file = self.service.files().create(
                            body=file_metadata,
                            fields="id"
                        ).execute()
                        folder_ids[full_path] = file.get("id")
                        print(f"✓ Created folder: {full_path}")
            
            return folder_ids
        
        except HttpError as e:
            print(f"Error creating folders: {e}")
            return {}
    
    def move_file_to_folder(self, file_id: str, destination_folder_id: str, file_name: str) -> bool:
        """Move a file to a destination folder"""
        try:
            # Get current parents
            file = self.service.files().get(
                fileId=file_id,
                fields="parents"
            ).execute()
            
            previous_parents = ",".join(file.get("parents", []))
            
            # Move file
            file = self.service.files().update(
                fileId=file_id,
                addParents=destination_folder_id,
                removeParents=previous_parents,
                fields="id, parents"
            ).execute()
            
            return True
        except HttpError as e:
            print(f"Error moving {file_name}: {e}")
            return False
    
    def execute_partitioning(self, files: Dict[str, FileInfo], report: PartitionReport):
        """Execute file moves to partition folders"""
        print("\n⚙️  Setting up partition structure...")
        folder_ids = self.ensure_partition_folders()
        
        if not folder_ids:
            print("ERROR: Could not set up partition folders")
            return
        
        total_files_to_move = len(report.personal_files) + len(report.data_files)
        moved_count = 0
        failed_count = 0
        
        print(f"\n📦 Moving {len(report.personal_files)} files to Personal/")
        for file_info in report.personal_files:
            # Determine specific subfolder
            lower_name = file_info.name.lower()
            if any(p in lower_name for p in ["photo", "image", "picture", "jpeg", "png"]):
                dest_folder = folder_ids.get("Personal/Photos")
            elif any(p in lower_name for p in ["backup", "bak"]):
                dest_folder = folder_ids.get("Personal/Backups")
            elif any(p in lower_name for p in ["email", "eml", "mbox"]):
                dest_folder = folder_ids.get("Personal/Email")
            else:
                dest_folder = folder_ids.get("Personal/Documents")
            
            if dest_folder:
                if self.move_file_to_folder(file_info.id, dest_folder, file_info.name):
                    moved_count += 1
                else:
                    failed_count += 1
            
            if moved_count % 50 == 0:
                print(f"  ... {moved_count} files moved")
        
        print(f"\n📦 Moving {len(report.data_files)} files to Data/")
        for file_info in report.data_files:
            # Determine specific subfolder
            lower_name = file_info.name.lower()
            if any(p in lower_name for p in ["parquet", "duckdb", "sqlite"]):
                dest_folder = folder_ids.get("Data/DuckDB")
            elif any(p in lower_name for p in ["api", "response", "export"]):
                dest_folder = folder_ids.get("Data/API-Storage")
            elif any(p in lower_name for p in ["index"]):
                dest_folder = folder_ids.get("Data/Indexes")
            else:
                dest_folder = folder_ids.get("Data/Exports")
            
            if dest_folder:
                if self.move_file_to_folder(file_info.id, dest_folder, file_info.name):
                    moved_count += 1
                else:
                    failed_count += 1
            
            if moved_count % 50 == 0:
                print(f"  ... {moved_count} files moved")
        
        print(f"\n✓ Partitioning complete: {moved_count} files moved, {failed_count} failed")
    
    def get_partition_status(self, files: Dict[str, FileInfo]) -> str:
        """Get current partition usage"""
        # Query folders in root
        try:
            results = self.service.files().list(
                q="mimeType='application/vnd.google-apps.folder' and trashed=false",
                spaces="drive",
                pageSize=1000,
                fields="files(id, name)",
            ).execute()
            
            partitions = {item["name"]: item["id"] for item in results.get("files", [])}
            
            status_lines = [
                "\n" + "=" * 80,
                "PARTITION USAGE STATUS",
                "=" * 80,
                f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            ]
            
            for partition_name in ["Personal", "Data", "Projects"]:
                if partition_name not in partitions:
                    status_lines.append(f"\n{partition_name}: NOT CREATED")
                    continue
                
                partition_id = partitions[partition_name]
                partition_size = 0
                partition_files = 0
                
                # Sum files in this partition (recursively)
                for file_info in files.values():
                    if self._is_in_folder(file_info, partition_id, files):
                        partition_size += file_info.size
                        partition_files += 1
                
                target = PERSONAL_TARGET if partition_name == "Personal" else (DATA_TARGET if partition_name == "Data" else None)
                
                if target:
                    pct = (partition_size / target) * 100
                    status_lines.append(
                        f"\n{partition_name}: {self._format_bytes(partition_size)} / {self._format_bytes(target)} ({pct:.1f}%)"
                    )
                else:
                    status_lines.append(f"\n{partition_name}: {self._format_bytes(partition_size)}")
                
                status_lines.append(f"  Files: {partition_files}")
            
            status_lines.append("\n" + "=" * 80)
            return "\n".join(status_lines)
        
        except HttpError as e:
            return f"Error getting status: {e}"
    
    @staticmethod
    def _format_bytes(size: int) -> str:
        """Format bytes"""
        if size >= TB:
            return f"{size / TB:.2f} TB"
        elif size >= GB:
            return f"{size / GB:.2f} GB"
        elif size >= MB:
            return f"{size / MB:.2f} MB"
        elif size >= KB:
            return f"{size / KB:.2f} KB"
        return f"{size} B"
    
    def _is_in_folder(self, file_info: FileInfo, folder_id: str, all_files: Dict[str, FileInfo]) -> bool:
        """Check if file is in a folder (recursively)"""
        current_parent = file_info.parent_id
        checked = set()
        
        while current_parent and current_parent not in checked:
            if current_parent == folder_id:
                return True
            checked.add(current_parent)
            
            if current_parent in all_files:
                current_parent = all_files[current_parent].parent_id
            else:
                break
        
        return False


def main():
    parser = argparse.ArgumentParser(description="Google Drive partition manager")
    parser.add_argument("--scan", action="store_true", help="Scan and analyze files")
    parser.add_argument("--execute", action="store_true", help="Execute partitioning")
    parser.add_argument("--status", action="store_true", help="Show partition usage")
    
    args = parser.parse_args()
    
    if not (args.scan or args.execute or args.status):
        parser.print_help()
        sys.exit(1)
    
    manager = DrivePartitionManager()
    files = manager.list_all_files()
    
    if args.scan:
        print("\n📊 Analyzing files...")
        report = manager.scan_files(files)
        print(report.format_report())
    
    elif args.execute:
        print("\n📊 Analyzing files...")
        report = manager.scan_files(files)
        print(report.format_report())
        
        response = input("\nProceed with partitioning? [y/N]: ")
        if response.lower() == "y":
            manager.execute_partitioning(files, report)
    
    elif args.status:
        print(manager.get_partition_status(files))


if __name__ == "__main__":
    main()
