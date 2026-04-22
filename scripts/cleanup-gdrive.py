#!/usr/bin/env python3
"""
Google Drive Cleanup Script
Identifies and manages duplicate files, system junk, and organizes folder structure.

OAuth2 Setup Instructions:
========================
1. Go to https://console.cloud.google.com/
2. Create a new project (e.g., "GDrive Cleanup")
3. Enable Google Drive API:
   - Search for "Google Drive API"
   - Click "Enable"
4. Create OAuth2 credentials:
   - Go to "Credentials" in left sidebar
   - Click "Create Credentials" > "OAuth client ID"
   - Choose "Desktop application"
   - Download JSON and save as ~/.google_credentials.json
5. Run script normally - it will prompt you to authorize in browser on first run
"""

import os
import sys
import json
import argparse
import hashlib
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime

from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
from google.oauth2.credentials import Credentials as UserCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.exceptions import DefaultCredentialsError
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


# Configuration
SCOPES = ["https://www.googleapis.com/auth/drive"]
CREDENTIALS_FILE = os.path.expanduser("~/.google_credentials.json")
TOKEN_FILE = os.path.expanduser("~/.google_token.json")

# System junk file patterns to identify
JUNK_PATTERNS = {
    ".sqlite",
    ".sqlite-wal",
    ".sqlite-shm",
    ".plist",
    ".gitstatus",
    "FETCH_HEAD",
    ".kgdb-shm",
    ".cloudphotodb-wal",
    ".cloudphotodb-shm",
    ".DS_Store",
    "Thumbs.db",
    ".git",
    ".vscode",
}

# File size constants
KB = 1024
MB = KB * 1024
GB = MB * 1024


@dataclass
class FileInfo:
    """Represents a Google Drive file"""
    id: str
    name: str
    size: int  # in bytes
    parent_id: str
    mime_type: str
    modified_time: str

    def is_junk(self) -> bool:
        """Check if file matches junk patterns"""
        for pattern in JUNK_PATTERNS:
            if pattern in self.name or self.name.startswith(pattern):
                return True
        return False

    def format_size(self) -> str:
        """Human-readable file size"""
        if self.size >= GB:
            return f"{self.size / GB:.2f} GB"
        elif self.size >= MB:
            return f"{self.size / MB:.2f} MB"
        elif self.size >= KB:
            return f"{self.size / KB:.2f} KB"
        return f"{self.size} B"


@dataclass
class CleanupReport:
    """Cleanup analysis report"""
    total_files: int = 0
    total_size: int = 0
    duplicate_count: int = 0
    duplicate_space_waste: int = 0
    junk_file_count: int = 0
    junk_space_waste: int = 0
    duplicates: Dict[str, List[FileInfo]] = field(default_factory=dict)
    junk_files: List[FileInfo] = field(default_factory=list)
    folder_structure: Dict[str, int] = field(default_factory=dict)

    def format_report(self) -> str:
        """Generate formatted report text"""
        lines = [
            "\n" + "=" * 70,
            "GOOGLE DRIVE CLEANUP REPORT",
            "=" * 70,
            f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"\nTotal Files: {self.total_files}",
            f"Total Size: {self._format_bytes(self.total_size)}",
            f"\n--- DUPLICATES ---",
            f"Duplicate Files: {self.duplicate_count}",
            f"Space Wasted: {self._format_bytes(self.duplicate_space_waste)}",
        ]

        if self.duplicates:
            lines.append("\nDuplicate Details:")
            for key, files in sorted(self.duplicates.items()):
                if len(files) > 1:
                    lines.append(f"  {key} ({files[0].format_size()})")
                    for f in files:
                        lines.append(f"    - {f.name} (id: {f.id[:8]}...)")

        lines.extend([
            f"\n--- JUNK FILES ---",
            f"Junk Files Found: {self.junk_file_count}",
            f"Space Wasted: {self._format_bytes(self.junk_space_waste)}",
        ])

        if self.junk_files:
            lines.append("\nJunk Files:")
            for f in sorted(self.junk_files, key=lambda x: x.size, reverse=True)[:20]:
                lines.append(f"  - {f.name} ({f.format_size()})")
            if len(self.junk_files) > 20:
                lines.append(f"  ... and {len(self.junk_files) - 20} more")

        lines.extend([
            f"\n--- RECOMMENDED FOLDER STRUCTURE ---",
            "Personal/",
            "  ├── Email/",
            "  ├── Images/",
            "  └── Backups/",
            "Tools/",
            "  ├── DuckDB/",
            "  ├── API_Storage/",
            "  └── Configs/",
            "Projects/",
            "  ├── Development/",
            "  └── Archive/",
            "Cleanup/",
            "  ├── Junk/",
            "  └── Duplicates/",
            "\n" + "=" * 70,
        ])

        return "\n".join(lines)

    @staticmethod
    def _format_bytes(size: int) -> str:
        """Format bytes to human-readable"""
        if size >= GB:
            return f"{size / GB:.2f} GB"
        elif size >= MB:
            return f"{size / MB:.2f} MB"
        elif size >= KB:
            return f"{size / KB:.2f} KB"
        return f"{size} B"


class GDriveCleanup:
    """Main Google Drive cleanup handler"""

    def __init__(self):
        self.service = None
        self.report = CleanupReport()
        self._auth()

    def _auth(self):
        """Authenticate with Google Drive API"""
        try:
            # Try to load existing token
            if os.path.exists(TOKEN_FILE):
                with open(TOKEN_FILE, "r") as f:
                    creds_data = json.load(f)
                    self.service = build("drive", "v3", credentials=UserCredentials.from_authorized_user_info(creds_data))
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

        # Save token for future use
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())

        self.service = build("drive", "v3", credentials=creds)
        print("Successfully authenticated with Google Drive!")

    def list_all_files(self) -> Dict[str, FileInfo]:
        """List all files in Google Drive"""
        files = {}
        page_token = None
        query = "trashed = false"  # Exclude deleted files

        print("Listing all files in Google Drive...")
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
                    if item.get("size"):  # Only process files with size
                        file_info = FileInfo(
                            id=item["id"],
                            name=item["name"],
                            size=int(item.get("size", 0)),
                            parent_id=item["parents"][0] if item.get("parents") else "root",
                            mime_type=item.get("mimeType", ""),
                            modified_time=item.get("modifiedTime", ""),
                        )
                        files[item["id"]] = file_info

                page_token = results.get("nextPageToken")
                if not page_token:
                    break

            except HttpError as error:
                print(f"An error occurred: {error}")
                break

        print(f"Found {len(files)} files with size information")
        return files

    def analyze(self, files: Dict[str, FileInfo]) -> CleanupReport:
        """Analyze files for duplicates and junk"""
        report = CleanupReport()
        report.total_files = len(files)

        # Analyze each file
        duplicates_by_key: Dict[str, List[FileInfo]] = defaultdict()
        junk_files = []

        for file_id, file_info in files.items():
            report.total_size += file_info.size

            # Check if junk
            if file_info.is_junk():
                junk_files.append(file_info)
                report.junk_file_count += 1
                report.junk_space_waste += file_info.size
            else:
                # Track duplicates by name+size
                dup_key = f"{file_info.name}:{file_info.size}"
                if dup_key not in duplicates_by_key:
                    duplicates_by_key[dup_key] = []
                duplicates_by_key[dup_key].append(file_info)

        # Count duplicates (extras beyond the first)
        for key, file_list in duplicates_by_key.items():
            if len(file_list) > 1:
                report.duplicates[key] = file_list
                # Count extra copies as waste
                for extra_file in file_list[1:]:
                    report.duplicate_count += 1
                    report.duplicate_space_waste += extra_file.size

        report.junk_files = sorted(junk_files, key=lambda x: x.size, reverse=True)
        self.report = report
        return report

    def move_files(self, file_ids: List[str], destination_folder: str, dry_run: bool = False):
        """Move files to a destination folder"""
        # Ensure destination folder exists
        folder_id = self._ensure_folder(destination_folder)

        if dry_run:
            print(f"\n[DRY RUN] Would move {len(file_ids)} files to '{destination_folder}'")
            return

        moved = 0
        for file_id in file_ids:
            try:
                previous_parents = ",".join(self.service.files().get(
                    fileId=file_id, fields="parents").execute().get("parents", []))

                self.service.files().update(
                    fileId=file_id,
                    addParents=folder_id,
                    removeParents=previous_parents,
                    fields="id, parents",
                ).execute()
                moved += 1
            except HttpError as error:
                print(f"Error moving file {file_id}: {error}")

        print(f"Moved {moved}/{len(file_ids)} files to {destination_folder}")

    def _ensure_folder(self, folder_path: str) -> str:
        """Ensure folder exists in Google Drive, creating if needed"""
        parts = folder_path.strip("/").split("/")
        parent_id = "root"

        for part in parts:
            # Check if folder exists
            query = f"name = '{part}' and mimeType = 'application/vnd.google-apps.folder' and parents = '{parent_id}' and trashed = false"
            results = self.service.files().list(q=query, fields="files(id)").execute()

            if results["files"]:
                parent_id = results["files"][0]["id"]
            else:
                # Create folder
                file_metadata = {
                    "name": part,
                    "mimeType": "application/vnd.google-apps.folder",
                    "parents": [parent_id],
                }
                folder = self.service.files().create(body=file_metadata, fields="id").execute()
                parent_id = folder.get("id")

        return parent_id

    def cleanup_junk(self, dry_run: bool = False):
        """Move junk files to Cleanup/Junk"""
        if not self.report.junk_files:
            print("No junk files found")
            return

        file_ids = [f.id for f in self.report.junk_files]
        print(f"\nMoving {len(file_ids)} junk files to Cleanup/Junk...")
        self.move_files(file_ids, "Cleanup/Junk", dry_run=dry_run)

    def cleanup_duplicates(self, dry_run: bool = False):
        """Move duplicate files to Cleanup/Duplicates"""
        if not self.report.duplicates:
            print("No duplicates found")
            return

        dup_file_ids = []
        for key, file_list in self.report.duplicates.items():
            if len(file_list) > 1:
                # Keep first, move rest
                for extra_file in file_list[1:]:
                    dup_file_ids.append(extra_file.id)

        print(f"\nMoving {len(dup_file_ids)} duplicate files to Cleanup/Duplicates...")
        self.move_files(dup_file_ids, "Cleanup/Duplicates", dry_run=dry_run)

    def organize_folders(self, dry_run: bool = False):
        """Create recommended folder structure"""
        folders = [
            "Personal/Email",
            "Personal/Images",
            "Personal/Backups",
            "Tools/DuckDB",
            "Tools/API_Storage",
            "Tools/Configs",
            "Projects/Development",
            "Projects/Archive",
        ]

        if dry_run:
            print(f"\n[DRY RUN] Would create {len(folders)} folders:")
            for folder in folders:
                print(f"  - {folder}")
            return

        for folder in folders:
            try:
                self._ensure_folder(folder)
                print(f"Ensured folder: {folder}")
            except Exception as e:
                print(f"Error creating {folder}: {e}")


def main():
    parser = argparse.ArgumentParser(description="Google Drive Cleanup Script")
    parser.add_argument(
        "--mode",
        choices=["report", "move-junk", "dedup", "organize", "full"],
        default="report",
        help="Cleanup mode (default: report)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would happen without making changes",
    )

    args = parser.parse_args()

    # Initialize cleanup handler
    cleanup = GDriveCleanup()

    # List and analyze files
    files = cleanup.list_all_files()
    report = cleanup.analyze(files)
    print(report.format_report())

    # Execute mode
    if args.mode == "report":
        print("\nMode: REPORT (no changes made)")
    elif args.mode == "move-junk":
        cleanup.cleanup_junk(dry_run=args.dry_run)
    elif args.mode == "dedup":
        cleanup.cleanup_duplicates(dry_run=args.dry_run)
    elif args.mode == "organize":
        cleanup.organize_folders(dry_run=args.dry_run)
    elif args.mode == "full":
        print("Running FULL cleanup...")
        cleanup.cleanup_junk(dry_run=args.dry_run)
        cleanup.cleanup_duplicates(dry_run=args.dry_run)
        cleanup.organize_folders(dry_run=args.dry_run)

    if args.dry_run:
        print("\n[DRY RUN] No changes were made to Google Drive")


if __name__ == "__main__":
    main()
