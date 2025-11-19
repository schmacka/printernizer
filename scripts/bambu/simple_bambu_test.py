#!/usr/bin/env python3
"""
Simple Bambu Lab FTP Test (Windows-compatible, no emojis)
"""

import asyncio
import sys
import tempfile
from pathlib import Path

# Add source directory to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

from services.bambu_ftp_service import BambuFTPService


async def test_download_specific_file():
    """Test downloading the specific file requested."""
    from bambu_credentials import get_bambu_credentials
    
    ip = "192.168.176.101"
    target_file = "top-option-2-color-change_plate_1.3mf"

    print("Bambu Lab FTP Test")
    print("=" * 40)
    print(f"IP: {ip}")
    print(f"Target file: {target_file}")
    print()

    try:
        username, code = get_bambu_credentials(ip)
        print(f"Using username: {username}")
    except ValueError as e:
        print(f"Error getting credentials: {e}")
        return

    try:
        # Create FTP service
        print("Creating FTP service...")
        service = BambuFTPService(ip, code)

        # Test connection
        print("Testing connection...")
        success, message = await service.test_connection()
        if not success:
            print(f"Connection failed: {message}")
            return False
        print(f"Connection successful: {message}")

        # List files
        print("Listing files in /cache...")
        files = await service.list_files("/cache")
        print(f"Found {len(files)} files")

        if not files:
            print("No files found in cache directory")
            return False

        # Show all files
        print("\nAvailable files:")
        for i, file_obj in enumerate(files, 1):
            print(f"  {i:2d}. {file_obj.name} ({file_obj.size:,} bytes)")

        # Look for target file
        target_found = None
        for file_obj in files:
            if target_file.lower() in file_obj.name.lower():
                target_found = file_obj
                break

        if not target_found:
            print(f"\nTarget file '{target_file}' not found")
            print("Available files don't match the requested filename")
            return False

        print(f"\nFound target file: {target_found.name}")
        print(f"Size: {target_found.size:,} bytes")

        # Download the file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".3mf") as temp_file:
            temp_path = temp_file.name

        print(f"\nDownloading to: {temp_path}")
        success = await service.download_file(target_found.name, temp_path, "/cache")

        if success and Path(temp_path).exists():
            actual_size = Path(temp_path).stat().st_size
            print(f"Download successful! {actual_size:,} bytes downloaded")

            # Move to a more permanent location
            downloads_dir = Path("downloads")
            downloads_dir.mkdir(exist_ok=True)
            final_path = downloads_dir / target_found.name

            Path(temp_path).rename(final_path)
            print(f"File saved to: {final_path.absolute()}")

            return True
        else:
            print("Download failed")
            return False

    except Exception as e:
        print(f"Error: {e}")
        return False


async def main():
    success = await test_download_specific_file()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))