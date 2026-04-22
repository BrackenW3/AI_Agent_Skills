#!/usr/bin/env python3
"""
Google Drive to DuckDB Bridge
Download Parquet/CSV files from Google Drive Data/ folder, query them with DuckDB,
and export results back to Google Drive.

OAuth2 Setup:
Same as cleanup-gdrive.py - credentials at ~/.google_credentials.json

Usage:
  python gdrive-duckdb-bridge.py                      # Enter REPL
  python gdrive-duckdb-bridge.py --refresh            # Download latest files
  python gdrive-duckdb-bridge.py --query "SELECT ..." # Run single query
"""

import os
import sys
import json
import argparse
import tempfile
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass

try:
    import duckdb
except ImportError:
    print("ERROR: duckdb not installed. Install with: pip install duckdb")
    sys.exit(1)

from google.oauth2.credentials import Credentials as UserCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError
import io


# Configuration
SCOPES = ["https://www.googleapis.com/auth/drive"]
CREDENTIALS_FILE = os.path.expanduser("~/.google_credentials.json")
TOKEN_FILE = os.path.expanduser("~/.google_token.json")
LOCAL_CACHE_DIR = os.path.expanduser("~/.gdrive_duckdb_cache")


@dataclass
class DataFile:
    """Represents a downloadable data file"""
    id: str
    name: str
    size: int
    mime_type: str
    modified_time: str
    local_path: Optional[str] = None

    def format_size(self) -> str:
        """Human readable size"""
        KB = 1024
        MB = KB * 1024
        GB = MB * 1024
        
        if self.size >= GB:
            return f"{self.size / GB:.2f} GB"
        elif self.size >= MB:
            return f"{self.size / MB:.2f} MB"
        elif self.size >= KB:
            return f"{self.size / KB:.2f} KB"
        return f"{self.size} B"

    def table_name(self) -> str:
        """Valid DuckDB table name from filename"""
        name = Path(self.name).stem
        name = name.replace("-", "_").replace(" ", "_").lower()
        name = "".join(c for c in name if c.isalnum() or c == "_")
        return name


class GDriveDuckDBBridge:
    """Bridge between Google Drive and DuckDB"""
    
    def __init__(self):
        self.service = None
        self.db = None
        self.data_files: Dict[str, DataFile] = {}
        self.data_folder_id = None
        self._auth()
        self._init_db()
    
    def _auth(self):
        """Authenticate with Google Drive"""
        try:
            if os.path.exists(TOKEN_FILE):
                with open(TOKEN_FILE, "r") as f:
                    creds_data = json.load(f)
                    self.service = build("drive", "v3", credentials=UserCredentials.from_authorized_user_info(creds_data))
                print("✓ Loaded cached credentials")
                return
        except Exception as e:
            print(f"Token load failed: {e}")
        
        if not os.path.exists(CREDENTIALS_FILE):
            print(f"ERROR: Credentials file not found at {CREDENTIALS_FILE}")
            print("Setup instructions in partition-gdrive.py")
            sys.exit(1)
        
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
        creds = flow.run_local_server(port=0)
        
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
        
        self.service = build("drive", "v3", credentials=creds)
        print("✓ Authenticated with Google Drive")
    
    def _init_db(self):
        """Initialize DuckDB in memory"""
        self.db = duckdb.connect(":memory:")
        print("✓ Initialized DuckDB (in-memory)")
    
    def _find_data_folder(self) -> Optional[str]:
        """Find the Data/ folder in Google Drive"""
        try:
            results = self.service.files().list(
                q="name='Data' and mimeType='application/vnd.google-apps.folder' and trashed=false",
                spaces="drive",
                fields="files(id)",
                pageSize=1
            ).execute()
            
            files = results.get("files", [])
            if files:
                self.data_folder_id = files[0]["id"]
                return self.data_folder_id
            
            return None
        except HttpError as e:
            print(f"Error finding Data folder: {e}")
            return None
    
    def list_data_files(self) -> List[DataFile]:
        """List all Parquet and CSV files in Data/ folder"""
        if not self.data_folder_id:
            if not self._find_data_folder():
                print("WARNING: Data/ folder not found in Google Drive")
                return []
        
        try:
            mime_types = [
                "text/csv",
                "application/x-parquet",
                "application/octet-stream",
            ]
            
            query = f"'{self.data_folder_id}' in parents and trashed=false and ("
            query += " or ".join([f"mimeType='{mt}'" for mt in mime_types])
            query += " or name contains '.csv' or name contains '.parquet')"
            
            results = self.service.files().list(
                q=query,
                spaces="drive",
                pageSize=1000,
                fields="files(id, name, size, mimeType, modifiedTime)"
            ).execute()
            
            self.data_files = {}
            for item in results.get("files", []):
                data_file = DataFile(
                    id=item["id"],
                    name=item["name"],
                    size=int(item.get("size", 0)),
                    mime_type=item.get("mimeType", ""),
                    modified_time=item.get("modifiedTime", "")
                )
                self.data_files[data_file.table_name()] = data_file
            
            return list(self.data_files.values())
        
        except HttpError as e:
            print(f"Error listing data files: {e}")
            return []
    
    def download_files(self, force_refresh: bool = False) -> Dict[str, str]:
        """Download data files from Google Drive"""
        os.makedirs(LOCAL_CACHE_DIR, exist_ok=True)
        
        files = self.list_data_files()
        if not files:
            print("No data files found")
            return {}
        
        print(f"\n📥 Downloading {len(files)} files...")
        
        downloaded = {}
        for data_file in files:
            local_path = os.path.join(LOCAL_CACHE_DIR, data_file.name)
            
            if os.path.exists(local_path) and not force_refresh:
                file_mtime = os.path.getmtime(local_path)
                file_modified = datetime.fromisoformat(data_file.modified_time.replace("Z", "+00:00")).timestamp()
                
                if file_mtime >= file_modified:
                    print(f"  ✓ {data_file.name} (cached)")
                    data_file.local_path = local_path
                    downloaded[data_file.table_name()] = local_path
                    continue
            
            try:
                request = self.service.files().get_media(fileId=data_file.id)
                fh = io.FileIO(local_path, "wb")
                downloader = MediaIoBaseDownload(fh, request)
                
                done = False
                while not done:
                    status, done = downloader.next_chunk()
                
                fh.close()
                
                print(f"  ✓ {data_file.name} ({data_file.format_size()})")
                data_file.local_path = local_path
                downloaded[data_file.table_name()] = local_path
            
            except HttpError as e:
                print(f"  ✗ {data_file.name}: {e}")
        
        return downloaded
    
    def register_tables(self) -> Dict[str, str]:
        """Register downloaded files as DuckDB tables"""
        print("\n📋 Registering tables...")
        
        tables = {}
        for table_name, data_file in self.data_files.items():
            if not data_file.local_path or not os.path.exists(data_file.local_path):
                continue
            
            try:
                if data_file.name.endswith(".csv"):
                    self.db.execute(f"""
                        CREATE OR REPLACE TABLE {table_name} AS
                        SELECT * FROM read_csv('{data_file.local_path}')
                    """)
                    print(f"  ✓ {table_name} (CSV)")
                
                elif data_file.name.endswith(".parquet"):
                    self.db.execute(f"""
                        CREATE OR REPLACE TABLE {table_name} AS
                        SELECT * FROM read_parquet('{data_file.local_path}')
                    """)
                    print(f"  ✓ {table_name} (Parquet)")
                
                tables[table_name] = data_file.local_path
            
            except Exception as e:
                print(f"  ✗ {table_name}: {e}")
        
        return tables
    
    def show_schema(self):
        """Display schema of registered tables"""
        try:
            result = self.db.execute("SELECT table_name FROM duckdb_tables() WHERE database='memory'").fetchall()
            
            if not result:
                print("No tables registered")
                return
            
            print("\n📊 Available tables:")
            for (table_name,) in result:
                count = self.db.execute(f"SELECT count(*) FROM {table_name}").fetchone()[0]
                columns = self.db.execute(f"DESCRIBE {table_name}").fetchall()
                
                print(f"\n  {table_name} ({count} rows, {len(columns)} columns)")
                for col_name, col_type, *_ in columns:
                    print(f"    - {col_name}: {col_type}")
        
        except Exception as e:
            print(f"Error showing schema: {e}")
    
    def execute_query(self, query: str) -> Optional[list]:
        """Execute a DuckDB query"""
        try:
            result = self.db.execute(query).fetchall()
            return result
        except Exception as e:
            print(f"Query error: {e}")
            return None
    
    def export_query_result(self, query: str, export_name: str) -> bool:
        """Export query result as Parquet to Google Drive"""
        try:
            result = self.db.execute(query).fetchdf()
            
            temp_file = os.path.join(LOCAL_CACHE_DIR, f"{export_name}.parquet")
            result.to_parquet(temp_file)
            
            print(f"\n📤 Exporting query result to Google Drive...")
            
            if not self.data_folder_id:
                self._find_data_folder()
            
            try:
                results = self.service.files().list(
                    q=f"name='Exports' and '{self.data_folder_id}' in parents",
                    fields="files(id)",
                    pageSize=1
                ).execute()
                
                exports_folder_id = results.get("files", [{}])[0].get("id")
            except:
                exports_folder_id = self.data_folder_id
            
            file_metadata = {
                "name": f"{export_name}.parquet",
                "parents": [exports_folder_id or "root"]
            }
            
            with open(temp_file, "rb") as f:
                media = io.BytesIO(f.read())
            
            file = self.service.files().create(
                body=file_metadata,
                media_body=io.BytesIO(media.getvalue()),
                fields="id, webViewLink"
            ).execute()
            
            print(f"✓ Exported to: {file.get('webViewLink', '')}")
            return True
        
        except Exception as e:
            print(f"Export error: {e}")
            return False
    
    def interactive_repl(self):
        """Interactive REPL for querying"""
        print("\n" + "=" * 80)
        print("GDRIVE-DUCKDB REPL")
        print("=" * 80)
        print("\nType SQL queries. Special commands:")
        print("  .schema     - Show table schema")
        print("  .tables     - List tables")
        print("  .export <query> <name> - Export query to Parquet")
        print("  .quit       - Exit")
        print("=" * 80)
        
        self.show_schema()
        
        while True:
            try:
                query = input("\nSQL> ").strip()
                
                if not query:
                    continue
                
                if query == ".quit" or query == ".exit":
                    break
                
                elif query == ".schema":
                    self.show_schema()
                
                elif query == ".tables":
                    result = self.db.execute("SELECT table_name FROM duckdb_tables() WHERE database='memory'").fetchall()
                    for (name,) in result:
                        print(f"  - {name}")
                
                elif query.startswith(".export"):
                    parts = query.split(None, 1)
                    if len(parts) > 1:
                        sql_part = parts[1]
                        last_space = sql_part.rfind(" ")
                        if last_space > 0:
                            sql = sql_part[:last_space].strip()
                            name = sql_part[last_space:].strip()
                            self.export_query_result(sql, name)
                        else:
                            print("Usage: .export <query> <export_name>")
                    else:
                        print("Usage: .export <query> <export_name>")
                
                else:
                    result = self.execute_query(query)
                    
                    if result is not None:
                        if not result:
                            print("(No results)")
                        else:
                            for row in result[:100]:
                                print(row)
                            if len(result) > 100:
                                print(f"... and {len(result) - 100} more rows")
            
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")


def main():
    parser = argparse.ArgumentParser(description="Google Drive to DuckDB bridge")
    parser.add_argument("--refresh", action="store_true", help="Force refresh from Google Drive")
    parser.add_argument("--query", type=str, help="Execute single query and exit")
    
    args = parser.parse_args()
    
    bridge = GDriveDuckDBBridge()
    
    bridge.download_files(force_refresh=args.refresh)
    bridge.register_tables()
    
    if args.query:
        result = bridge.execute_query(args.query)
        if result:
            for row in result:
                print(row)
    else:
        bridge.interactive_repl()


if __name__ == "__main__":
    main()
