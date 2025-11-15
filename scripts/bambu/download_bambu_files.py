#!/usr/bin/env python3
"""
Bambu Lab File Download Integration Script

This script provides a high-level function to download files from all configured Bambu Lab
printers using the new direct FTP implementation. It can be used standalone or integrated
into the main Printernizer application.

Features:
- Discover and connect to all Bambu Lab printers
- List available files on each printer
- Download selected files with organized directory structure
- Progress tracking and error handling
- Summary reporting

Usage:
    # Download all 3D files from all printers
    python scripts/download_bambu_files.py --all

    # Download specific file from specific printer
    python scripts/download_bambu_files.py --ip 192.168.1.100 --code 12345678 --file model.3mf

    # Interactive mode - select files to download
    python scripts/download_bambu_files.py --interactive
"""

import asyncio
import argparse
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, Optional, Any
import json

# Add source directory to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))
sys.path.insert(0, str(project_root))

try:
    from services.bambu_ftp_service import BambuFTPService, BambuFTPFile
    from printers.bambu_lab import BambuLabPrinter
    IMPORTS_OK = True
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running from the project root and dependencies are installed.")
    IMPORTS_OK = False


class BambuDownloadManager:
    """Manages file downloads from multiple Bambu Lab printers."""

    def __init__(self, download_base_dir: str = "downloads"):
        """
        Initialize download manager.

        Args:
            download_base_dir: Base directory for downloaded files
        """
        self.download_base_dir = Path(download_base_dir)
        self.download_base_dir.mkdir(parents=True, exist_ok=True)

        self.stats = {
            'printers_connected': 0,
            'printers_failed': 0,
            'files_discovered': 0,
            'files_downloaded': 0,
            'files_failed': 0,
            'bytes_downloaded': 0,
            'start_time': None,
            'end_time': None
        }

    async def download_from_bambulab_printers(self,
                                            printer_configs: List[Dict[str, str]],
                                            file_filter: Optional[str] = None,
                                            download_all: bool = False) -> Dict[str, Any]:
        """
        Download files from multiple Bambu Lab printers.

        Args:
            printer_configs: List of printer configuration dicts with 'ip', 'access_code', 'name'
            file_filter: Optional filename filter (None = interactive selection)
            download_all: Download all 3D files automatically

        Returns:
            Summary dictionary with download results
        """
        self.stats['start_time'] = datetime.now()

        print("🖨️ Bambu Lab File Download Manager")
        print("=" * 50)
        print(f"📂 Download directory: {self.download_base_dir.absolute()}")
        print(f"🔧 Printers to process: {len(printer_configs)}")
        print(f"⏰ Started: {self.stats['start_time'].strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        results = {}

        for i, config in enumerate(printer_configs, 1):
            printer_name = config.get('name', f"Printer-{config['ip']}")
            print(f"🖨️ Processing printer {i}/{len(printer_configs)}: {printer_name}")
            print(f"   IP: {config['ip']}")

            try:
                result = await self._process_single_printer(config, file_filter, download_all)
                results[printer_name] = result
                self.stats['printers_connected'] += 1

            except Exception as e:
                print(f"❌ Failed to process printer {printer_name}: {e}")
                results[printer_name] = {
                    'success': False,
                    'error': str(e),
                    'files_downloaded': 0,
                    'bytes_downloaded': 0
                }
                self.stats['printers_failed'] += 1

            print()  # Add spacing between printers

        self.stats['end_time'] = datetime.now()
        duration = self.stats['end_time'] - self.stats['start_time']

        # Generate summary
        summary = self._generate_summary(results, duration)
        self._print_summary(summary)

        return summary

    async def _process_single_printer(self, config: Dict[str, str],
                                    file_filter: Optional[str],
                                    download_all: bool) -> Dict[str, Any]:
        """Process a single printer for file downloads."""
        printer_name = config.get('name', f"Printer-{config['ip']}")

        # Create FTP service
        ftp_service = BambuFTPService(config['ip'], config['access_code'])

        # Test connection
        success, message = await ftp_service.test_connection()
        if not success:
            raise ConnectionError(f"Cannot connect to printer: {message}")

        print(f"✅ Connected successfully")

        # List available files
        print(f"📁 Listing files...")
        files = await ftp_service.list_files("/cache")

        # Filter to 3D files only
        files_3d = [f for f in files if f.is_3d_file]

        self.stats['files_discovered'] += len(files_3d)
        print(f"📋 Found {len(files_3d)} 3D files (total: {len(files)} files)")

        if not files_3d:
            return {
                'success': True,
                'files_downloaded': 0,
                'bytes_downloaded': 0,
                'message': 'No 3D files found'
            }

        # Determine which files to download
        files_to_download = []

        if download_all:
            files_to_download = files_3d
            print(f"⬇️ Downloading all {len(files_to_download)} files")

        elif file_filter:
            # Filter by filename
            files_to_download = [f for f in files_3d if file_filter.lower() in f.name.lower()]
            print(f"🔍 Filter '{file_filter}' matches {len(files_to_download)} files")

        else:
            # Interactive selection
            files_to_download = await self._interactive_file_selection(files_3d)

        if not files_to_download:
            return {
                'success': True,
                'files_downloaded': 0,
                'bytes_downloaded': 0,
                'message': 'No files selected for download'
            }

        # Create printer-specific download directory
        printer_dir = self.download_base_dir / self._sanitize_name(printer_name)
        date_dir = printer_dir / datetime.now().strftime("%Y-%m-%d")
        date_dir.mkdir(parents=True, exist_ok=True)

        # Download selected files
        downloaded_count = 0
        downloaded_bytes = 0

        for file_obj in files_to_download:
            print(f"⬇️ Downloading: {file_obj.name} ({file_obj.size / 1024 / 1024:.2f} MB)")

            local_path = date_dir / file_obj.name

            try:
                success = await ftp_service.download_file(file_obj.name, str(local_path), "/cache")

                if success and local_path.exists():
                    actual_size = local_path.stat().st_size
                    downloaded_count += 1
                    downloaded_bytes += actual_size
                    self.stats['files_downloaded'] += 1
                    self.stats['bytes_downloaded'] += actual_size
                    print(f"   ✅ Download successful ({actual_size:,} bytes)")
                else:
                    print(f"   ❌ Download failed")
                    self.stats['files_failed'] += 1

            except Exception as e:
                print(f"   ❌ Download error: {e}")
                self.stats['files_failed'] += 1

        return {
            'success': True,
            'files_downloaded': downloaded_count,
            'bytes_downloaded': downloaded_bytes,
            'download_directory': str(date_dir),
            'files_available': len(files_3d)
        }

    async def _interactive_file_selection(self, files: List[BambuFTPFile]) -> List[BambuFTPFile]:
        """Interactive file selection for download."""
        if not files:
            return []

        print("\n📋 Available files:")
        print("=" * 60)
        for i, file_obj in enumerate(files, 1):
            size_mb = file_obj.size / 1024 / 1024 if file_obj.size > 0 else 0
            print(f"{i:2d}. {file_obj.name:<40} ({size_mb:>6.2f} MB) [{file_obj.file_type}]")

        print("\nSelect files to download:")
        print("  - Enter numbers separated by commas (e.g., 1,3,5)")
        print("  - Enter 'all' to download all files")
        print("  - Enter 'none' or press Enter to skip")

        try:
            selection = input("Selection: ").strip().lower()

            if not selection or selection == 'none':
                return []

            if selection == 'all':
                return files

            # Parse comma-separated numbers
            indices = []
            for part in selection.split(','):
                try:
                    index = int(part.strip()) - 1  # Convert to 0-based index
                    if 0 <= index < len(files):
                        indices.append(index)
                    else:
                        print(f"⚠️ Invalid file number: {index + 1}")
                except ValueError:
                    print(f"⚠️ Invalid input: {part}")

            selected_files = [files[i] for i in indices]
            print(f"✅ Selected {len(selected_files)} files")
            return selected_files

        except (EOFError, KeyboardInterrupt):
            print("\n⏹️ Selection cancelled")
            return []

    def _sanitize_name(self, name: str) -> str:
        """Sanitize name for use as directory name."""
        import re
        # Replace invalid characters with underscores
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', name)
        # Remove multiple consecutive underscores
        sanitized = re.sub(r'_+', '_', sanitized)
        # Strip leading/trailing underscores
        return sanitized.strip('_')

    def _generate_summary(self, results: Dict[str, Any], duration) -> Dict[str, Any]:
        """Generate download summary."""
        return {
            'duration_seconds': duration.total_seconds(),
            'duration_formatted': str(duration).split('.')[0],  # Remove microseconds
            'printers': {
                'total': self.stats['printers_connected'] + self.stats['printers_failed'],
                'connected': self.stats['printers_connected'],
                'failed': self.stats['printers_failed']
            },
            'files': {
                'discovered': self.stats['files_discovered'],
                'downloaded': self.stats['files_downloaded'],
                'failed': self.stats['files_failed']
            },
            'data': {
                'bytes_downloaded': self.stats['bytes_downloaded'],
                'mb_downloaded': self.stats['bytes_downloaded'] / 1024 / 1024,
                'gb_downloaded': self.stats['bytes_downloaded'] / 1024 / 1024 / 1024
            },
            'results': results,
            'download_directory': str(self.download_base_dir.absolute())
        }

    def _print_summary(self, summary: Dict[str, Any]):
        """Print download summary."""
        print("=" * 60)
        print("📊 DOWNLOAD SUMMARY")
        print("=" * 60)
        print(f"⏱️  Duration: {summary['duration_formatted']}")
        print(f"🖨️  Printers: {summary['printers']['connected']}/{summary['printers']['total']} successful")
        print(f"📁 Files discovered: {summary['files']['discovered']}")
        print(f"⬇️  Files downloaded: {summary['files']['downloaded']}")
        if summary['files']['failed'] > 0:
            print(f"❌ Files failed: {summary['files']['failed']}")
        print(f"💾 Data downloaded: {summary['data']['mb_downloaded']:.2f} MB")
        print(f"📂 Saved to: {summary['download_directory']}")
        print("=" * 60)


async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Download files from Bambu Lab printers")
    parser.add_argument("--ip", help="Single printer IP address")
    parser.add_argument("--code", help="Single printer access code")
    parser.add_argument("--name", help="Single printer name", default="Bambu-A1")
    parser.add_argument("--file", help="Specific filename to download")
    parser.add_argument("--all", action="store_true", help="Download all 3D files")
    parser.add_argument("--interactive", action="store_true", help="Interactive file selection")
    parser.add_argument("--config", help="JSON config file with printer settings")
    parser.add_argument("--output", help="Output directory", default="downloads")

    args = parser.parse_args()

    if not IMPORTS_OK:
        return 1

    # Determine printer configurations
    printer_configs = []

    if args.config:
        # Load from config file
        try:
            with open(args.config, 'r') as f:
                config_data = json.load(f)
                printer_configs = config_data.get('bambu_printers', [])
        except Exception as e:
            print(f"❌ Failed to load config file: {e}")
            return 1

    elif args.ip and args.code:
        # Single printer from command line
        printer_configs = [{
            'ip': args.ip,
            'access_code': args.code,
            'name': args.name
        }]

    else:
        # Try environment variables
        ip = os.getenv("BAMBU_IP")
        code = os.getenv("BAMBU_ACCESS_CODE")

        if ip and code:
            printer_configs = [{
                'ip': ip,
                'access_code': code,
                'name': 'Bambu-A1'
            }]
        else:
            print("❌ No printer configuration provided")
            print("Options:")
            print("  1. Use --ip and --code for single printer")
            print("  2. Use --config with JSON configuration file")
            print("  3. Set BAMBU_IP and BAMBU_ACCESS_CODE environment variables")
            return 1

    if not printer_configs:
        print("❌ No printers configured")
        return 1

    try:
        # Create download manager
        manager = BambuDownloadManager(args.output)

        # Determine download mode
        file_filter = args.file if args.file else None
        download_all = args.all

        if not download_all and not file_filter and not args.interactive:
            # Default to interactive if no specific mode chosen
            args.interactive = True

        # Run downloads
        summary = await manager.download_from_bambulab_printers(
            printer_configs,
            file_filter=file_filter,
            download_all=download_all
        )

        # Return appropriate exit code
        if summary['files']['downloaded'] > 0:
            print("🎉 Download completed successfully!")
            return 0
        elif summary['files']['discovered'] == 0:
            print("ℹ️ No files found to download")
            return 0
        else:
            print("⚠️ Download completed with issues")
            return 1

    except KeyboardInterrupt:
        print("\n⏹️ Download cancelled by user")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))