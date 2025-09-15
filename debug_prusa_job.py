#!/usr/bin/env python3
"""
Debug script to test Prusa job information retrieval.
"""
import asyncio
import json
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from printers.prusa import PrusaPrinter

async def test_prusa_job_info():
    """Test Prusa job information retrieval."""
    print("🔍 Prusa Job Information Debug")
    print("=" * 40)
    
    # You'll need to replace these with your actual Prusa printer credentials
    printer_config = {
        'printer_id': 'prusa_test',
        'name': 'Test Prusa',
        'ip_address': '192.168.1.100',  # Replace with your Prusa IP
        'api_key': 'your_api_key_here'   # Replace with your API key
    }
    
    print(f"Testing Prusa printer at {printer_config['ip_address']}")
    
    try:
        # Initialize printer
        prusa = PrusaPrinter(**printer_config)
        
        # Connect to printer
        print("🔗 Connecting to Prusa printer...")
        connected = await prusa.connect()
        
        if not connected:
            print("❌ Failed to connect to Prusa printer")
            return
        
        print("✅ Connected successfully")
        
        # Get status information
        print("\n📊 Getting printer status...")
        status = await prusa.get_status()
        print(f"Status: {status.status}")
        print(f"Message: {status.message}")
        print(f"Current Job: {status.current_job}")
        print(f"Progress: {status.progress}%")
        
        # Get detailed job info
        print("\n🎯 Getting detailed job information...")
        job_info = await prusa.get_job_info()
        
        if job_info:
            print(f"Job ID: {job_info.job_id}")
            print(f"Job Name: {job_info.name}")
            print(f"Status: {job_info.status}")
            print(f"Progress: {job_info.progress}%")
            print(f"Estimated Time: {job_info.estimated_time}")
            print(f"Elapsed Time: {job_info.elapsed_time}")
        else:
            print("❌ No job information available")
        
        # Print raw data for debugging
        print(f"\n🔍 Raw status data:")
        print(json.dumps(status.raw_data, indent=2))
        
        await prusa.disconnect()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("This script needs to be configured with your Prusa printer credentials.")
    print("Edit the printer_config dictionary in the script with your actual values:")
    print("- ip_address: Your Prusa printer IP")  
    print("- api_key: Your PrusaLink API key")
    print("\nThen run: python debug_prusa_job.py")
    
    # Uncomment the line below once configured
    # asyncio.run(test_prusa_job_info())