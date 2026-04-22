#!/usr/bin/env python3
"""
Cloud Storage Diagnostic and Remediation Script for Windows

Diagnostics for:
- OneDrive (multiple accounts)
- Google Drive for Desktop
- File organization and optimization

Requirements: Python 3.10+, Windows OS
"""

import sys
import json
import hashlib
import logging
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import subprocess
import re
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Set, Tuple

# Windows-specific imports
import winreg
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class OneDriveAccount:
    """Represents a configured OneDrive account"""
    email: str
    display_name: str
    sync_path: Optional[str] = None
    is_configured: bool = False
    is_syncing: bool = False
    storage_used_gb: float = 0.0
    storage_quota_gb: float = 0.0
    errors: List[str] = field(default_factory=list)
    last_sync_time: Optional[str] = None
    files_on_demand_enabled: bool = False


@dataclass
class GoogleDriveAccount:
    """Represents a configured Google Drive account"""
    email: str
    is_configured: bool = False
    sync_path: Optional[str] = None
    is_syncing: bool = False
    errors: List[str] = field(default_factory=list)
    last_sync_time: Optional[str] = None


@dataclass
class DuplicateFile:
    """Represents a potential duplicate file"""
    name: str
    paths: List[str]
    size_bytes: int
    hash: Optional[str] = None


@dataclass
class FileOrganizationAnalysis:
    """Analysis of file organization in cloud storage"""
    total_files: int = 0
    total_size_gb: float = 0.0
    files_by_extension: Dict[str, int] = field(default_factory=dict)
    potential_duplicates: List[DuplicateFile] = field(default_factory=list)
    problematic_files: List[str] = field(default_factory=list)
    max_folder_depth: int = 0
    average_folder_depth: float = 0.0
    recommendations: List[str] = field(default_factory=list)


@dataclass
class DiagnosticReport:
    """Complete diagnostic report"""
    timestamp: str
    system_info: Dict
    onedrive_status: Dict
    onedrive_accounts: List[Dict]
    google_drive_status: Dict
    google_drive_accounts: List[Dict]
    file_analysis: Dict
    recommendations: List[str]


class CloudStorageDiagnostic:
    """Main diagnostic class"""

    # System file extensions that shouldn't be in cloud storage
    PROBLEMATIC_EXTENSIONS = {
        '.sqlite', '.db', '.plist', '.gitignore', '.git',
        '.swp', '.swo', '.tmp', '~', '.bak', '.cache',
        '.lock', '.lnk', '.sys', '.ini', '.log'
    }

    # Accounts to look for
    TARGET_ONEDRIVE_ACCOUNTS = [
        'will.i.bracken@outlook.com',
        'will.bracken.3@outlook.com'
    ]
    TARGET_GOOGLE_ACCOUNTS = [
        'william3bracken@gmail.com',
        'willbracken33@gmail.com'
    ]

    def __init__(self):
        """Initialize diagnostic tool"""
        self.username = os.getenv('USERNAME', 'User')
        self.localappdata = Path(os.getenv('LOCALAPPDATA', ''))
        self.userprofile = Path(os.getenv('USERPROFILE', ''))
        self.onedrive_base = self.userprofile / 'OneDrive'
        self.onedrive_logs = self.localappdata / 'Microsoft' / 'OneDrive' / 'logs'

    def run_full_diagnostic(self) -> DiagnosticReport:
        """Run complete diagnostic suite"""
        logger.info("Starting cloud storage diagnostic...")

        report = DiagnosticReport(
            timestamp=datetime.now().isoformat(),
            system_info=self._get_system_info(),
            onedrive_status=self._check_onedrive_process(),
            onedrive_accounts=self._diagnose_onedrive(),
            google_drive_status=self._check_google_drive_process(),
            google_drive_accounts=self._diagnose_google_drive(),
            file_analysis=asdict(self._analyze_file_organization()),
            recommendations=[]
        )

        # Generate recommendations
        report.recommendations = self._generate_recommendations(report)

        logger.info("Diagnostic complete")
        return report

    def _get_system_info(self) -> Dict:
        """Get system information"""
        return {
            'username': self.username,
            'platform': sys.platform,
            'python_version': f"{sys.version_info.major}.{sys.version_info.minor}",
            'timestamp': datetime.now().isoformat(),
            'userprofile': str(self.userprofile),
            'localappdata': str(self.localappdata)
        }

    def _check_onedrive_process(self) -> Dict:
        """Check if OneDrive process is running"""
        logger.info("Checking OneDrive process...")
        try:
            result = subprocess.run(
                ['tasklist', '/FI', 'IMAGENAME eq OneDrive.exe'],
                capture_output=True,
                text=True,
                timeout=5
            )
            is_running = 'OneDrive.exe' in result.stdout

            return {
                'running': is_running,
                'version': self._get_onedrive_version(),
                'check_time': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to check OneDrive process: {e}")
            return {'running': None, 'error': str(e)}

    def _get_onedrive_version(self) -> Optional[str]:
        """Get OneDrive version from file"""
        try:
            onedrive_path = Path('C:\\Program Files\\Microsoft OneDrive\\OneDrive.exe')
            if onedrive_path.exists():
                # Get file version info
                result = subprocess.run(
                    ['powershell', '-Command',
                     f'[System.Diagnostics.FileVersionInfo]::GetVersionInfo("{onedrive_path}").FileVersion'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                return result.stdout.strip() if result.returncode == 0 else None
        except Exception:
            pass
        return None

    def _diagnose_onedrive(self) -> List[Dict]:
        """Diagnose OneDrive accounts"""
        logger.info("Diagnosing OneDrive accounts...")
        accounts = []

        try:
            registry_path = r'Software\Microsoft\OneDrive\Accounts'
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, registry_path) as reg_key:
                account_count = winreg.QueryInfoKey(reg_key)[0]

                for i in range(account_count):
                    account_sid = winreg.EnumKeyEx(reg_key, i)
                    try:
                        with winreg.OpenKey(reg_key, account_sid) as account_key:
                            account = self._read_account_registry(account_key, account_sid)
                            if account:
                                accounts.append(account)
                                self._check_account_sync_status(account)
                    except Exception as e:
                        logger.warning(f"Failed to read account {account_sid}: {e}")

        except FileNotFoundError:
            logger.info("OneDrive registry key not found")
        except Exception as e:
            logger.error(f"Failed to diagnose OneDrive: {e}")

        return [asdict(acc) for acc in accounts]

    def _read_account_registry(self, account_key, account_sid: str) -> Optional[OneDriveAccount]:
        """Read OneDrive account from registry"""
        try:
            values = {}
            index = 0
            while True:
                try:
                    name, value, _ = winreg.EnumValue(account_key, index)
                    values[name] = value
                    index += 1
                except OSError:
                    break

            account = OneDriveAccount(
                email=values.get('UserEmail', values.get('DisplayName', 'Unknown')),
                display_name=values.get('DisplayName', 'Unknown'),
                sync_path=values.get('UserFolder'),
                is_configured=True
            )

            # Check for Files On Demand
            business_path = r'Software\Microsoft\OneDrive\Tenants'
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, business_path) as tenant_key:
                    index = 0
                    while True:
                        try:
                            tenant_id = winreg.EnumKeyEx(tenant_key, index)
                            with winreg.OpenKey(tenant_key, tenant_id) as tenant_subkey:
                                try:
                                    files_on_demand, _ = winreg.QueryValueEx(
                                        tenant_subkey, 'DehydrationPolicy'
                                    )
                                    account.files_on_demand_enabled = (files_on_demand == 3)
                                except OSError:
                                    pass
                            index += 1
                        except OSError:
                            break
            except OSError:
                pass

            return account

        except Exception as e:
            logger.warning(f"Error reading account registry: {e}")
            return None

    def _check_account_sync_status(self, account: OneDriveAccount) -> None:
        """Check sync status and errors for an account"""
        if not account.sync_path:
            return

        try:
            sync_path = Path(account.sync_path)
            if sync_path.exists():
                account.is_syncing = True

                # Check for sync errors
                errors = self._find_sync_errors(sync_path)
                if errors:
                    account.errors.extend(errors)

                # Get folder size
                try:
                    total_size = sum(
                        f.stat().st_size for f in sync_path.rglob('*')
                        if f.is_file()
                    )
                    account.storage_used_gb = total_size / (1024 ** 3)
                except Exception:
                    pass

        except Exception as e:
            logger.warning(f"Failed to check sync status: {e}")

    def _find_sync_errors(self, sync_path: Path) -> List[str]:
        """Find sync error indicators in folder"""
        errors = []

        # Check for conflict files
        for item in sync_path.rglob('*'):
            if ' (conflicted copy)' in item.name:
                errors.append(f"Sync conflict detected: {item.name}")

        # Check OneDrive logs for recent errors
        if self.onedrive_logs.exists():
            try:
                log_files = sorted(
                    self.onedrive_logs.glob('Sync*.log'),
                    key=lambda x: x.stat().st_mtime,
                    reverse=True
                )

                for log_file in log_files[:3]:  # Check last 3 logs
                    try:
                        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            if 'error' in content.lower():
                                # Extract error lines
                                for line in content.split('\n'):
                                    if 'error' in line.lower():
                                        errors.append(f"Log error: {line[:100]}")
                                        if len(errors) >= 5:
                                            break
                    except Exception:
                        pass

            except Exception as e:
                logger.debug(f"Failed to read OneDrive logs: {e}")

        return errors[:10]  # Limit to 10 errors

    def _check_google_drive_process(self) -> Dict:
        """Check if Google Drive for Desktop is running"""
        logger.info("Checking Google Drive process...")
        try:
            result = subprocess.run(
                ['tasklist', '/FI', 'IMAGENAME eq GoogleDriveFS.exe'],
                capture_output=True,
                text=True,
                timeout=5
            )
            is_running = 'GoogleDriveFS.exe' in result.stdout

            return {
                'installed': self._is_google_drive_installed(),
                'running': is_running,
                'check_time': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to check Google Drive: {e}")
            return {'installed': False, 'running': False, 'error': str(e)}

    def _is_google_drive_installed(self) -> bool:
        """Check if Google Drive for Desktop is installed"""
        try:
            result = subprocess.run(
                ['reg', 'query', 'HKLM\\SOFTWARE\\Google\\Drive',
                 '/v', 'InstallLocation'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False

    def _diagnose_google_drive(self) -> List[Dict]:
        """Diagnose Google Drive accounts"""
        logger.info("Diagnosing Google Drive...")
        accounts = []

        if not self._is_google_drive_installed():
            logger.info("Google Drive for Desktop not installed")
            return [{
                'email': 'N/A',
                'is_configured': False,
                'status': 'Google Drive for Desktop is not installed'
            }]

        # Try to find configured accounts
        try:
            # Check for Google Drive sync folders
            google_drive_root = self.userprofile / 'Google Drive'

            if google_drive_root.exists():
                for target_email in self.TARGET_GOOGLE_ACCOUNTS:
                    account = GoogleDriveAccount(
                        email=target_email,
                        is_configured=True,
                        sync_path=str(google_drive_root)
                    )
                    accounts.append(account)

        except Exception as e:
            logger.error(f"Failed to diagnose Google Drive: {e}")

        return [asdict(acc) for acc in accounts]

    def _analyze_file_organization(self) -> FileOrganizationAnalysis:
        """Analyze file organization in OneDrive directories"""
        logger.info("Analyzing file organization...")
        analysis = FileOrganizationAnalysis()

        if not self.onedrive_base.exists():
            logger.info("OneDrive base directory not found")
            return analysis

        try:
            all_files = list(self.onedrive_base.rglob('*'))
            files_only = [f for f in all_files if f.is_file()]
            analysis.total_files = len(files_only)

            # Calculate size and extensions
            for file_path in files_only:
                try:
                    size = file_path.stat().st_size
                    analysis.total_size_gb += size / (1024 ** 3)

                    ext = file_path.suffix.lower()
                    if ext:
                        analysis.files_by_extension[ext] = \
                            analysis.files_by_extension.get(ext, 0) + 1
                    else:
                        analysis.files_by_extension['[no extension]'] = \
                            analysis.files_by_extension.get('[no extension]', 0) + 1

                    # Check for problematic files
                    if ext in self.PROBLEMATIC_EXTENSIONS:
                        analysis.problematic_files.append(str(file_path))

                except Exception:
                    pass

            # Find duplicates
            analysis.potential_duplicates = self._find_duplicates(files_only)

            # Analyze folder depth
            analysis.max_folder_depth = self._calculate_max_depth(self.onedrive_base)
            analysis.average_folder_depth = self._calculate_avg_depth(self.onedrive_base)

            # Generate recommendations
            analysis.recommendations = self._generate_file_recommendations(analysis)

        except Exception as e:
            logger.error(f"Failed to analyze file organization: {e}")

        return analysis

    def _find_duplicates(self, files: List[Path]) -> List[DuplicateFile]:
        """Find potential duplicate files"""
        logger.info("Scanning for duplicates (this may take a while)...")
        duplicates = []
        seen_by_name_size = defaultdict(list)

        # First pass: group by name and size
        for file_path in files:
            try:
                size = file_path.stat().st_size
                key = (file_path.name, size)
                seen_by_name_size[key].append(file_path)
            except Exception:
                pass

        # Second pass: check hashes for files with same name/size
        for (name, size), paths in seen_by_name_size.items():
            if len(paths) > 1:
                # Calculate hashes to confirm duplicates
                hashes = {}
                for path in paths:
                    try:
                        file_hash = self._calculate_file_hash(path)
                        if file_hash not in hashes:
                            hashes[file_hash] = []
                        hashes[file_hash].append(path)
                    except Exception:
                        pass

                # Add to duplicates if confirmed
                for hash_val, dup_paths in hashes.items():
                    if len(dup_paths) > 1:
                        duplicates.append(DuplicateFile(
                            name=name,
                            paths=[str(p) for p in dup_paths],
                            size_bytes=size,
                            hash=hash_val
                        ))

        return duplicates[:50]  # Limit to 50 duplicates

    def _calculate_file_hash(self, file_path: Path, algorithm: str = 'md5') -> str:
        """Calculate file hash (limited to first 10MB for speed)"""
        hash_obj = hashlib.md5()

        try:
            with open(file_path, 'rb') as f:
                # Read in chunks, limit to 10MB
                for chunk in iter(lambda: f.read(8192), b''):
                    if hash_obj.digest_size * len(hash_obj.digest()) > 10 * 1024 * 1024:
                        break
                    hash_obj.update(chunk)
        except Exception:
            return ''

        return hash_obj.hexdigest()

    def _calculate_max_depth(self, root: Path) -> int:
        """Calculate maximum folder depth"""
        try:
            max_depth = 0
            for item in root.rglob('*'):
                depth = len(item.relative_to(root).parts)
                max_depth = max(max_depth, depth)
            return max_depth
        except Exception:
            return 0

    def _calculate_avg_depth(self, root: Path) -> float:
        """Calculate average folder depth"""
        try:
            depths = []
            for item in root.rglob('*'):
                if item.is_dir():
                    depth = len(item.relative_to(root).parts)
                    depths.append(depth)

            return sum(depths) / len(depths) if depths else 0.0
        except Exception:
            return 0.0

    def _generate_file_recommendations(self, analysis: FileOrganizationAnalysis) -> List[str]:
        """Generate file organization recommendations"""
        recommendations = []

        # Storage size recommendations
        if analysis.total_size_gb > 100:
            recommendations.append(
                f"Large storage usage ({analysis.total_size_gb:.1f}GB). Consider archiving old files."
            )

        # Duplicate recommendations
        if analysis.potential_duplicates:
            total_dup_size = sum(d.size_bytes for d in analysis.potential_duplicates)
            recommendations.append(
                f"Found {len(analysis.potential_duplicates)} potential duplicates "
                f"({total_dup_size / (1024**3):.1f}GB). Review and remove redundant files."
            )

        # Problematic files
        if analysis.problematic_files:
            recommendations.append(
                f"Found {len(analysis.problematic_files)} system/temporary files in cloud storage. "
                "Move these to local storage only."
            )

        # Folder depth
        if analysis.max_folder_depth > 8:
            recommendations.append(
                f"Folder nesting is very deep ({analysis.max_folder_depth} levels). "
                "Flatten structure for better organization."
            )

        # File extension diversity
        if len(analysis.files_by_extension) > 20:
            recommendations.append(
                "Many file types detected. Create a clearer folder taxonomy "
                "to improve organization."
            )

        return recommendations

    def _generate_recommendations(self, report: DiagnosticReport) -> List[str]:
        """Generate overall recommendations"""
        recommendations = []

        # OneDrive recommendations
        onedrive_accs = report.onedrive_accounts
        if onedrive_accs:
            for acc in onedrive_accs:
                if acc.get('errors'):
                    recommendations.append(
                        f"OneDrive account {acc['email']}: {len(acc['errors'])} issues detected. "
                        "Check sync settings and authentication."
                    )
                if not acc.get('files_on_demand_enabled'):
                    recommendations.append(
                        f"Enable Files On Demand for {acc['email']} to save local storage."
                    )

        # Google Drive recommendations
        if report.google_drive_status and not report.google_drive_status.get('installed'):
            recommendations.append(
                "Google Drive for Desktop is not installed. Install it to sync your Google Drive."
            )

        # General recommendations
        if report.file_analysis.get('recommendations'):
            recommendations.extend(report.file_analysis['recommendations'][:3])

        return recommendations

    def save_report(self, report: DiagnosticReport, output_path: Path) -> None:
        """Save report to JSON file"""
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(
                    asdict(report),
                    f,
                    indent=2,
                    default=str
                )

            logger.info(f"Report saved to {output_path}")
        except Exception as e:
            logger.error(f"Failed to save report: {e}")

    def print_summary(self, report: DiagnosticReport) -> None:
        """Print human-readable summary"""
        print("\n" + "=" * 80)
        print("CLOUD STORAGE DIAGNOSTIC REPORT")
        print("=" * 80)
        print(f"Generated: {report.timestamp}\n")

        # OneDrive Status
        print("OneDrive Status")
        print("-" * 40)
        print(f"Process Running: {report.onedrive_status.get('running', 'Unknown')}")
        print(f"Version: {report.onedrive_status.get('version', 'Unknown')}\n")

        if report.onedrive_accounts:
            print("Configured Accounts:")
            for acc in report.onedrive_accounts:
                print(f"  Email: {acc['email']}")
                print(f"    Display Name: {acc['display_name']}")
                print(f"    Storage Used: {acc['storage_used_gb']:.2f}GB")
                print(f"    Files On Demand: {acc['files_on_demand_enabled']}")
                if acc['errors']:
                    print(f"    Errors ({len(acc['errors'])}):")
                    for error in acc['errors'][:3]:
                        print(f"      - {error}")
                print()

        # Google Drive Status
        print("\nGoogle Drive Status")
        print("-" * 40)
        print(f"Installed: {report.google_drive_status.get('installed', False)}")
        print(f"Running: {report.google_drive_status.get('running', False)}\n")

        # File Organization
        print("\nFile Organization Analysis")
        print("-" * 40)
        file_info = report.file_analysis
        print(f"Total Files: {file_info.get('total_files', 0)}")
        print(f"Total Size: {file_info.get('total_size_gb', 0):.2f}GB")
        print(f"Max Folder Depth: {file_info.get('max_folder_depth', 0)}")

        if file_info.get('potential_duplicates'):
            print(f"Potential Duplicates: {len(file_info['potential_duplicates'])}")

        if file_info.get('problematic_files'):
            print(f"System Files in Cloud: {len(file_info['problematic_files'])}")

        # Recommendations
        print("\n\nRecommendations")
        print("-" * 40)
        if report.recommendations:
            for i, rec in enumerate(report.recommendations, 1):
                print(f"{i}. {rec}")
        else:
            print("No specific recommendations at this time.")

        print("\n" + "=" * 80 + "\n")


def main():
    """Main entry point"""
    try:
        # Run diagnostic
        diagnostic = CloudStorageDiagnostic()
        report = diagnostic.run_full_diagnostic()

        # Save JSON report
        output_dir = Path(__file__).parent.parent / 'reports'
        json_path = output_dir / f"cloud_storage_diagnostic_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        diagnostic.save_report(report, json_path)

        # Print summary
        diagnostic.print_summary(report)

        print(f"\nDetailed report saved to: {json_path}")
        return 0

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
