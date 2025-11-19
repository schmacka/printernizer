#!/usr/bin/env python3
"""Quick snapshot test - captures one frame and saves it."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.services.bambu_camera_client import BambuLabCameraClient

async def main():
    client = BambuLabCameraClient(
        ip_address="192.168.176.101",
        access_code="40722898",
        serial_number="03919C431601127",
        printer_id="test"
    )

    print("Connecting to camera...")
    await client.connect()
    print("Connected! Waiting for first frame...")

    # Wait for first frame
    await asyncio.sleep(3)

    frame = await client.get_latest_frame()
    if frame:
        Path("test_snapshot.jpg").write_bytes(frame)
        print(f"SUCCESS! Snapshot saved: {len(frame)} bytes -> test_snapshot.jpg")
    else:
        print("No frame received yet")

    await client.disconnect()
    print("Done!")

if __name__ == "__main__":
    asyncio.run(main())
