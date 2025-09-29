#!/usr/bin/env python3
"""
Download specific target file using working bambulabs-api
"""

import sys
from pathlib import Path

# Add source directory to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

try:
    from bambulabs_api import Printer as BambuClient
    BAMBU_API_AVAILABLE = True
except ImportError as e:
    print(f"bambulabs-api library not available: {e}")
    BAMBU_API_AVAILABLE = False
    sys.exit(1)

def download_target_file():
    """Download the specific target file."""
    ip = "192.168.176.101"
    access_code = "40722898"
    serial = "00M00A301901234"  # Dummy serial
    target_file = "top-option-2-color-change_plate_1.3mf"

    print("Downloading Target File from Bambu Lab")
    print("=" * 40)
    print(f"Target: {target_file}")
    print()

    try:
        # Create and connect client
        print("Connecting to printer...")
        client = BambuClient(
            ip_address=ip,
            access_code=access_code,
            serial=serial
        )
        client.connect()
        print("Connected!")

        # List all files
        print("Searching for target file...")
        result, files = client.ftp_client.list_cache_dir()
        print(f"Found {len(files)} total files")

        # Search for target file (case-insensitive)
        target_found = None
        target_filename = None

        for file_entry in files:
            if isinstance(file_entry, str):
                # Parse FTP listing line
                parts = file_entry.strip().split()
                if len(parts) >= 9:
                    filename = ' '.join(parts[8:])
                else:
                    filename = parts[-1] if parts else file_entry

                # Check if this matches our target (case-insensitive)
                if target_file.lower() in filename.lower():
                    target_found = file_entry
                    target_filename = filename
                    break

        if target_found:
            print(f"Found target file: {target_filename}")
            print(f"Full listing: {target_found}")

            # Download the file
            print("\\nDownloading...")
            try:
                file_data_io = client.ftp_client.download_file(f"cache/{target_filename}")
                if file_data_io:
                    file_data = file_data_io.getvalue()
                    if file_data and len(file_data) > 0:
                        # Save file
                        downloads_dir = Path("downloads")
                        downloads_dir.mkdir(exist_ok=True)
                        local_path = downloads_dir / target_filename

                        with open(local_path, 'wb') as f:
                            f.write(file_data)

                        print(f"SUCCESS!")
                        print(f"Downloaded: {len(file_data):,} bytes")
                        print(f"Saved to: {local_path.absolute()}")

                        client.disconnect()
                        return True
                    else:
                        print("Download returned empty data")
                else:
                    print("Download returned None")
            except Exception as e:
                print(f"Download error: {e}")

        else:
            print(f"Target file '{target_file}' not found")
            print("\\nAvailable files containing 'top' or 'option':")

            matches = []
            for file_entry in files:
                if isinstance(file_entry, str):
                    parts = file_entry.strip().split()
                    if len(parts) >= 9:
                        filename = ' '.join(parts[8:])
                    else:
                        filename = parts[-1] if parts else file_entry

                    if any(word in filename.lower() for word in ['top', 'option', 'color', 'change']):
                        matches.append((file_entry, filename))

            if matches:
                for i, (full_line, filename) in enumerate(matches, 1):
                    print(f"  {i}. {filename}")
                    print(f"     {full_line}")
            else:
                print("  No files found with those keywords")
                print("\\nFirst 10 files for reference:")
                for i, file_entry in enumerate(files[:10], 1):
                    parts = file_entry.strip().split()
                    if len(parts) >= 9:
                        filename = ' '.join(parts[8:])
                    else:
                        filename = parts[-1] if parts else file_entry
                    print(f"  {i:2d}. {filename}")

        client.disconnect()
        return False

    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    success = download_target_file()
    print(f"\\nResult: {'SUCCESS' if success else 'FAILED'}")
    sys.exit(0 if success else 1)