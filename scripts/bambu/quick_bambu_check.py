#!/usr/bin/env python3
"""
Quick Bambu Lab API Check
A simple one-file test to verify bambulabs-api installation and basic import.

Usage: python quick_bambu_check.py
"""

def main():
    print("🔍 Quick Bambu Lab API Check")
    print("="*40)
    
    # Test 1: Check if bambulabs-api is available
    try:
        from bambulabs_api import Printer
        print("✅ bambulabs-api library is installed")
        print(f"   Available classes: Printer")
    except ImportError as e:
        print("❌ bambulabs-api library is NOT installed")
        print("   Install with: pip install bambulabs-api")
        return False
    
    # Test 2: Check if we can create a printer instance (without connecting)
    try:
        # Create instance with dummy values - won't connect but tests the class
        test_printer = Printer(
            ip_address="127.0.0.1",
            access_code="00000000", 
            serial="TEST00000000"
        )
        print("✅ Printer class can be instantiated")
    except Exception as e:
        print(f"⚠️  Printer class instantiation issue: {str(e)}")
        print("   This might indicate a library version problem")
    
    # Test 3: Check for aiohttp (needed for camera functions)
    try:
        import aiohttp
        print("✅ aiohttp library is available (camera functions supported)")
    except ImportError:
        print("⚠️  aiohttp is not installed (camera functions won't work)")
        print("   Install with: pip install aiohttp")
    
    print("\n" + "="*40)
    print("🎯 Summary:")
    print("   Your system appears ready for Bambu Lab integration!")
    print("   Run the full test script with your actual credentials:")
    print("   python scripts/test_bambu_credentials.py")
    print("="*40)
    
    return True

if __name__ == "__main__":
    main()