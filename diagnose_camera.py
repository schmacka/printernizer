#!/usr/bin/env python3
"""
Diagnostic script for Bambu Lab camera connection issues.

Tests various connection aspects to help identify the problem.
"""

import socket
import ssl
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# UPDATE THESE
PRINTER_IP = "192.168.176.101"
PRINTER_SERIAL = "03919C431601127"

print("\n" + "="*70)
print("Bambu Lab Camera Connection Diagnostics")
print("="*70)
print(f"\nPrinter IP: {PRINTER_IP}")
print(f"Serial: {PRINTER_SERIAL}\n")

# Test 1: Basic network connectivity
print("[Test 1] Basic Network Connectivity")
print("-" * 70)
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    result = sock.connect_ex((PRINTER_IP, 6000))
    sock.close()

    if result == 0:
        print(f"[OK] Port 6000 is OPEN on {PRINTER_IP}")
        print("  -> The printer is listening on the camera port")
    else:
        print(f"[FAIL] Port 6000 is CLOSED or FILTERED on {PRINTER_IP}")
        print("  -> Possible issues:")
        print("     - Printer is offline or powered off")
        print("     - Camera feature disabled in printer settings")
        print("     - Firewall blocking port 6000")
        print("     - Wrong IP address")
except Exception as e:
    print(f"[ERROR] Network error: {e}")

print()

# Test 2: Ping printer
print("[Test 2] Ping Printer")
print("-" * 70)
import subprocess
try:
    # Windows ping command
    result = subprocess.run(
        ["ping", "-n", "1", "-w", "1000", PRINTER_IP],
        capture_output=True,
        text=True,
        timeout=3
    )
    if result.returncode == 0:
        print(f"[OK] Printer responds to ping")
        print(f"  -> Network connection is good")
    else:
        print(f"[FAIL] Printer does not respond to ping")
        print("  -> Check if printer is on the same network")
except Exception as e:
    print(f"[WARN] Could not ping: {e}")

print()

# Test 3: Check other Bambu Lab ports
print("[Test 3] Other Bambu Lab Ports")
print("-" * 70)
ports_to_test = {
    8883: "MQTT (printer status)",
    990: "FTP (file transfers)",
    6000: "Camera (video stream)",
}

for port, description in ports_to_test.items():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((PRINTER_IP, port))
        sock.close()

        status = "[OK]    " if result == 0 else "[CLOSED]"
        print(f"{status:10} Port {port:5} - {description}")
    except Exception as e:
        print(f"[ERROR]    Port {port:5} - {description}: {e}")

print()

# Test 4: TLS connection attempt
print("[Test 4] TLS Connection (without authentication)")
print("-" * 70)

async def test_tls():
    try:
        # Try to open TLS connection
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE  # Bypass verification for testing

        print(f"Attempting TLS connection to {PRINTER_IP}:6000...")
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(
                host=PRINTER_IP,
                port=6000,
                ssl=context,
                server_hostname=PRINTER_SERIAL,
            ),
            timeout=5
        )

        print("[OK] TLS connection established!")
        print("  -> Basic TCP/TLS works, issue might be with authentication")

        writer.close()
        await writer.wait_closed()

        return True

    except asyncio.TimeoutError:
        print("[FAIL] TLS connection timeout")
        print("  -> Port is not responding to TLS handshake")
        print("  -> Possible issues:")
        print("     - Port 6000 might not be the camera port")
        print("     - Printer firmware might be incompatible")
        print("     - Camera feature might need to be enabled")
        return False

    except ssl.SSLError as e:
        print(f"[FAIL] TLS error: {e}")
        print("  -> TLS handshake failed")
        print("  -> This might be a certificate issue")
        return False

    except OSError as e:
        print(f"[FAIL] Network error: {e}")
        return False

try:
    asyncio.run(test_tls())
except Exception as e:
    print(f"[ERROR] Unexpected error: {e}")

print()

# Summary and recommendations
print("="*70)
print("DIAGNOSTIC SUMMARY")
print("="*70)
print("\nTroubleshooting steps:")
print("\n1. CHECK PRINTER STATUS:")
print("   - Ensure printer is powered on")
print("   - Check printer is connected to WiFi")
print("   - Verify IP address is correct (check printer LCD or router)")
print()
print("2. ENABLE LAN MODE:")
print("   - Go to printer: Settings → Network")
print("   - Enable 'LAN Mode'")
print("   - Note the LAN Access Code (8 digits)")
print()
print("3. VERIFY CAMERA IS WORKING:")
print("   - Open BambuStudio on your computer")
print("   - Connect to printer")
print("   - Check if you can see the camera feed there")
print()
print("4. CHECK NETWORK:")
print("   - Ensure computer and printer are on same network")
print("   - Try pinging the printer from command line:")
print(f"     ping {PRINTER_IP}")
print()
print("5. FIREWALL:")
print("   - Temporarily disable firewall to test")
print("   - If that fixes it, add exception for port 6000")
print()
print("="*70)
print()
