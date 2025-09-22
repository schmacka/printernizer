#!/usr/bin/env python3
"""
Debug script to test Bambu Lab file listing and understand what's not working.
"""
import asyncio
import json
from pathlib import Path
import sys

# Add the src directory to the path
sys.path.append(str(Path(__file__).parent / "src"))

from printers.bambu_lab import BambuLabPrinter

async def debug_bambu_file_listing():
    """Debug what's happening with Bambu Lab file listing."""
    print("🔧 Debugging Bambu Lab File Listing")
    print("="*50)
    
    # Use actual configuration
    bambu = BambuLabPrinter(
        printer_id="debug-bambu",
        name="Debug Bambu",
        ip_address="192.168.176.101",
        access_code="40722898",  # Correct access code from config
        serial_number="03919C431601127"
    )
    
    try:
        print("🔌 Connecting to Bambu Lab printer...")
        connected = await bambu.connect()
        
        if not connected:
            print("❌ Connection failed!")
            return
            
        print("✅ Connected successfully")
        print(f"   - Using bambulabs_api: {bambu.use_bambu_api}")
        
        # Wait for initial data
        print("\n⏳ Waiting 5 seconds for initial data...")
        await asyncio.sleep(5)
        
        # Check what's available in the client
        if bambu.bambu_client:
            print("\n🔧 Checking bambulabs_api client capabilities:")
            methods_to_check = ['get_files', 'ftp_client', 'mqtt_dump', 'uploaded_files']
            for method in methods_to_check:
                has_method = hasattr(bambu.bambu_client, method)
                print(f"   - {method}: {'✅' if has_method else '❌'}")
                
                if has_method:
                    try:
                        attr = getattr(bambu.bambu_client, method)
                        if callable(attr):
                            print(f"     (callable method)")
                        else:
                            print(f"     (attribute: {type(attr)})")
                    except Exception as e:
                        print(f"     (error accessing: {e})")
        
        # Check status data
        print("\n📊 Status data availability:")
        if hasattr(bambu, 'latest_status') and bambu.latest_status:
            print(f"   - latest_status keys: {list(bambu.latest_status.keys())}")
        else:
            print("   - latest_status: None or empty")
            
        if hasattr(bambu, 'latest_data') and bambu.latest_data:
            print(f"   - latest_data keys: {list(bambu.latest_data.keys())}")
        else:
            print("   - latest_data: None or empty")
        
        # Try each discovery method individually
        print("\n🔍 Testing individual discovery methods:")
        
        # Method 1: Direct API
        print("\n1. Testing direct get_files() API...")
        try:
            if hasattr(bambu.bambu_client, 'get_files'):
                files = bambu.bambu_client.get_files()
                print(f"   ✅ get_files() returned: {files}")
                if files:
                    print(f"   📁 Files: {len(files)}")
                    for f in files[:3]:
                        print(f"      - {f}")
                else:
                    print("   📁 No files returned")
            else:
                print("   ❌ get_files() method not available")
        except Exception as e:
            print(f"   ❌ get_files() failed: {e}")
        
        # Method 2: FTP discovery
        print("\n2. Testing FTP discovery...")
        try:
            ftp_files = await bambu._discover_files_via_ftp()
            print(f"   ✅ FTP discovery found {len(ftp_files)} files")
            for f in ftp_files[:3]:
                print(f"      - {f.filename} ({f.path})")
        except Exception as e:
            print(f"   ❌ FTP discovery failed: {e}")
        
        # Method 3: MQTT dump
        print("\n3. Testing MQTT dump discovery...")
        try:
            mqtt_files = await bambu._discover_files_via_mqtt_dump()
            print(f"   ✅ MQTT dump found {len(mqtt_files)} files")
            for f in mqtt_files[:3]:
                print(f"      - {f.filename} ({f.path})")
        except Exception as e:
            print(f"   ❌ MQTT dump discovery failed: {e}")
            
        # Method 4: MQTT fallback
        print("\n4. Testing MQTT fallback...")
        try:
            mqtt_fallback_files = await bambu._list_files_mqtt()
            print(f"   ✅ MQTT fallback found {len(mqtt_fallback_files)} files")
            for f in mqtt_fallback_files[:3]:
                print(f"      - {f.filename} ({f.path})")
        except Exception as e:
            print(f"   ❌ MQTT fallback failed: {e}")
        
        # Main method
        print("\n🎯 Testing main list_files() method...")
        try:
            all_files = await bambu.list_files()
            print(f"   ✅ Main method found {len(all_files)} files")
            for f in all_files[:5]:
                print(f"      - {f.filename} (size: {f.size}, type: {f.file_type})")
        except Exception as e:
            print(f"   ❌ Main method failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Show raw data if available
        if hasattr(bambu.bambu_client, 'mqtt_dump'):
            try:
                raw_data = bambu.bambu_client.mqtt_dump()
                if raw_data:
                    print(f"\n📡 Raw MQTT dump (first 1000 chars):")
                    print(str(raw_data)[:1000] + "..." if len(str(raw_data)) > 1000 else str(raw_data))
                else:
                    print(f"\n📡 Raw MQTT dump is empty")
            except Exception as e:
                print(f"\n📡 Could not get MQTT dump: {e}")
                
    except Exception as e:
        print(f"❌ Debug script failed: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        try:
            await bambu.disconnect()
            print("\n🔌 Disconnected")
        except:
            pass

if __name__ == "__main__":
    asyncio.run(debug_bambu_file_listing())