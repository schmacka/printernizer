#!/usr/bin/env python3
"""
Bambu Lab Download Verification Script

This script can be used to verify that file downloads work with real Bambu Lab printer credentials.

Usage:
    export BAMBU_IP=192.168.1.100
    export BAMBU_ACCESS_CODE=12345678  
    export BAMBU_SERIAL=ABC123456789
    python scripts/verify_bambu_download.py

Or run with parameters:
    python scripts/verify_bambu_download.py --ip 192.168.1.100 --code 12345678 --serial ABC123456789
"""

import asyncio
import argparse
import os
import sys
from pathlib import Path
import tempfile

# Add source directory to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))
sys.path.insert(0, str(project_root))

try:
    from printers.bambu_lab import BambuLabPrinter
    from services.bambu_ftp_service import BambuFTPService
    IMPORTS_OK = True
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running from the project root and dependencies are installed.")
    IMPORTS_OK = False


async def verify_download(ip_address: str, access_code: str, serial_number: str, target_file: str | None = None):
    """Verify download functionality with real printer."""
    print("🖨️ Bambu Lab Download Verification")
    print("=" * 40)
    print(f"Printer IP: {ip_address}")
    print(f"Serial: {serial_number}")
    print(f"Access Code: {'*' * len(access_code)}")
    print()
    
    if not IMPORTS_OK:
        return False
    
    # Create printer instance
    printer = BambuLabPrinter(
        printer_id="verification_test",
        name="Verification Test Printer",
        ip_address=ip_address,
        access_code=access_code,
        serial_number=serial_number
    )
    
    try:
        # Step 1: Connect to printer
        print("🔌 Connecting to printer...")
        connected = await printer.connect()
        
        if not connected:
            print("❌ Failed to connect to printer")
            print("   Check IP address, access code, and network connectivity")
            return False
        
        print("✅ Connected successfully")
        
        # Step 1.5: Test direct FTP service (new implementation)
        print("🔧 Testing direct FTP service...")
        try:
            ftp_service = BambuFTPService(ip_address, access_code)
            ftp_success, ftp_message = await ftp_service.test_connection()
            if ftp_success:
                print(f"✅ Direct FTP service: {ftp_message}")

                # Test file listing via direct FTP
                ftp_files = await ftp_service.list_files("/cache")
                print(f"✅ Direct FTP found {len(ftp_files)} files in /cache")
            else:
                print(f"⚠️ Direct FTP failed: {ftp_message}")
        except Exception as e:
            print(f"⚠️ Direct FTP service error: {e}")

        # Step 2: Get printer status
        print("📊 Checking printer status...")
        try:
            status = await printer.get_status()
            print(f"✅ Printer status: {status.status.value if hasattr(status, 'status') else 'Unknown'}")
        except Exception as e:
            print(f"⚠️ Status check failed: {e}")
        
        # Step 3: List files
        print("📁 Listing available files...")
        try:
            files = await printer.list_files()
            
            if not files:
                print("ℹ️ No files found on printer")
                print("   This is normal if no files have been uploaded or cache is empty")
                return True
            
            print(f"✅ Found {len(files)} files:")
            for i, file_info in enumerate(files[:5]):  # Show first 5 files
                filename = getattr(file_info, 'filename', str(file_info))
                file_type = getattr(file_info, 'file_type', 'unknown')
                print(f"   {i+1}. {filename} ({file_type})")
            
            if len(files) > 5:
                print(f"   ... and {len(files) - 5} more files")
            
        except Exception as e:
            print(f"⚠️ File listing failed: {e}")
            files = []
        
        # Step 4: Select file
        filename = None
        if target_file:
            # Attempt to find exact or fuzzy match
            target_lower = target_file.lower()
            exact = next((f for f in files if getattr(f, 'filename', str(f)).lower() == target_lower), None)
            if exact:
                filename = getattr(exact, 'filename', str(exact))
            else:
                fuzzy = [f for f in files if target_lower.split('.')[0] in getattr(f, 'filename', str(f)).lower()]
                if fuzzy:
                    filename = getattr(fuzzy[0], 'filename', str(fuzzy[0]))
                    print(f"🔍 Requested file not exact; using closest match: {filename}")
                else:
                    print(f"❌ Target file not found in listing: {target_file}")
        if not filename and files:
            test_file = files[0]
            filename = getattr(test_file, 'filename', str(test_file))
            
        # Step 5: Test download if a file was selected
        if filename:
            print(f"⬇️ Testing download of: {filename}")
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{filename}") as temp_file:
                temp_path = temp_file.name
            
            try:
                success = await printer.download_file(filename, temp_path)
                
                if success and Path(temp_path).exists():
                    file_size = Path(temp_path).stat().st_size
                    print(f"✅ Download successful!")
                    print(f"   File size: {file_size:,} bytes")
                    print(f"   Saved to: {temp_path}")
                    
                    # Cleanup
                    Path(temp_path).unlink()
                    return True
                else:
                    print("❌ Download failed - file not created")
                    return False
                    
            except Exception as e:
                print(f"❌ Download failed with error: {e}")
                return False
            finally:
                # Cleanup temp file
                try:
                    Path(temp_path).unlink()
                except:
                    pass
        
        return True
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False
        
    finally:
        # Cleanup connection
        try:
            await printer.disconnect()
        except:
            pass


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Verify Bambu Lab file download functionality")
    parser.add_argument("--ip", help="Printer IP address", default=os.getenv("BAMBU_IP"))
    parser.add_argument("--code", help="Access code", default=os.getenv("BAMBU_ACCESS_CODE"))  
    parser.add_argument("--serial", help="Printer serial number", default=os.getenv("BAMBU_SERIAL"))
    parser.add_argument("--file", help="Specific filename to attempt (e.g., top-option-2-color-change_plate_1.3mf)")
    
    args = parser.parse_args()
    
    if not all([args.ip, args.code, args.serial]):
        print("❌ Missing required parameters")
        print("Set environment variables or use command line arguments:")
        print("  --ip <printer_ip>")
        print("  --code <access_code>") 
        print("  --serial <serial_number>")
        print()
        print("Or set environment variables:")
        print("  export BAMBU_IP=192.168.1.100")
        print("  export BAMBU_ACCESS_CODE=12345678")
        print("  export BAMBU_SERIAL=ABC123456789")
        return 1
    
    try:
        result = asyncio.run(verify_download(args.ip, args.code, args.serial, args.file))

        print("\n" + "=" * 40)
        if result:
            print("🎉 VERIFICATION SUCCESSFUL")
            print("   Bambu Lab file download is working!")
        else:
            print("❌ VERIFICATION FAILED")
            print("   Check printer connection and configuration")
        print("=" * 40)

        return 0 if result else 1

    except KeyboardInterrupt:
        print("\n⏹️ Verification cancelled by user")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())