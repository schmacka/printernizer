# Bambu Lab Credentials Test Scripts

This directory contains helper scripts to test Bambu Lab printer credentials before adding them to your Printernizer configuration.

## What These Scripts Do

The test scripts will:
- ✅ Validate credential format
- 🔌 Test connection to your Bambu Lab printer
- 📊 Retrieve printer status
- 🌡️ Check temperature readings
- 📷 Test camera/snapshot access
- 🖨️ Get current job information (if any)

## Prerequisites

1. **Python 3.8+** installed on your system
2. **bambulabs-api** library installed (`pip install bambulabs-api`)
3. Your Bambu Lab printer must be:
   - Connected to the same network as your computer
   - Have LAN mode enabled
   - Access code available (found in printer settings)

## Required Information

Before running the test, gather these from your Bambu Lab printer:

- **IP Address**: Check your router or printer network settings
- **Access Code**: 8-digit code found in printer settings → Network → LAN Mode
- **Serial Number**: Usually on printer label or in Settings → General → Device Info

## Usage Options

### Option 0: Quick Dependency Check (Recommended First Step)
```bash
# Check if your system is ready for Bambu Lab integration:
python scripts\quick_bambu_check.py
```

### Option 1: Windows Batch File (Easiest)
```bash
# Double-click or run from command prompt:
scripts\test_bambu_credentials.bat

# With parameters (skip interactive input):
scripts\test_bambu_credentials.bat --ip 192.168.1.100 --access-code 12345678 --serial 01P00A123456789
```

### Option 2: Python Script Directly

#### Interactive Mode:
```bash
python scripts\test_bambu_credentials.py
```

#### Command Line Mode:
```bash
python scripts\test_bambu_credentials.py --ip 192.168.1.100 --access-code 12345678 --serial 01P00A123456789
```

#### JSON Output (for automation):
```bash
python scripts\test_bambu_credentials.py --ip 192.168.1.100 --access-code 12345678 --serial 01P00A123456789 --json
```

## Example Output

### Successful Test:
```
🚀 Bambu Lab API Credentials Test Script
==================================================
✅ Credential format validation passed

🔄 Testing connection to Bambu Lab printer...
   IP: 192.168.1.100
   Access Code: ******78
   Serial: 01P00A123456789

🔌 Creating Bambu Lab client...
✅ Client created successfully
📊 Testing status retrieval...
✅ Status retrieved: IDLE
🌡️  Temperatures - Bed: 25°C, Nozzle: 23°C
📭 No active print job
📷 Testing camera access...
✅ Camera snapshot accessible

============================================================
📋 TEST RESULTS SUMMARY
============================================================
🎉 OVERALL: SUCCESS - Credentials are working!

📊 Test Details:
   Connection:     ✅ Pass
   Status Check:   ✅ Pass
   Camera Check:   ✅ Pass

📝 Printer Information:
   Printer Status: IDLE
   Temperatures:
     bed: 25
     nozzle: 23
   Camera: Available

============================================================

💡 Next Steps:
   • Your credentials are working correctly
   • You can add this printer to your Printernizer config
   • Check config/printers.example.json for the format
```

### Failed Test:
```
❌ Connection failed: [Errno 111] Connection refused

============================================================
📋 TEST RESULTS SUMMARY
============================================================
💥 OVERALL: FAILED - Credentials have issues

📊 Test Details:
   Connection:     ❌ Fail
   Status Check:   ❌ Fail
   Camera Check:   ❌ Fail

❌ Errors Encountered:
   • Connection failed: [Errno 111] Connection refused

🔧 Troubleshooting Tips:
   • Verify printer is on the same network
   • Check access code in printer settings
   • Ensure serial number matches printer label
   • Try pinging the IP address first
```

## Troubleshooting

### Common Issues:

1. **"bambulabs-api library is not installed"**
   ```bash
   pip install bambulabs-api
   ```

2. **Connection refused**
   - Check if printer is on same network
   - Verify IP address is correct
   - Ensure LAN mode is enabled on printer

3. **Invalid credentials**
   - Access code must be exactly 8 digits
   - Serial number should be 8-20 alphanumeric characters
   - Check printer settings for correct values

4. **Camera not accessible**
   - Some network configurations block camera access
   - This doesn't affect basic printer functionality

### Finding Your Credentials:

**Access Code:**
1. Go to printer touchscreen
2. Settings → Network → LAN Mode
3. Enable if not already enabled
4. Note the 8-digit access code

**Serial Number:**
1. Check the label on your printer, OR
2. Settings → General → Device Info → Serial Number

**IP Address:**
1. Settings → Network → Network Info → IP Address, OR
2. Check your router's connected devices list

## Adding to Printernizer

Once your credentials test successfully, add your printer to `config/printers.json`:

```json
{
  "version": "1.0",
  "updated_at": "2025-09-15T00:00:00.000000",
  "printers": {
    "my_bambu_a1": {
      "name": "My Bambu A1",
      "type": "bambu_lab",
      "ip_address": "192.168.1.100",
      "api_key": null,
      "access_code": "12345678",
      "serial_number": "01P00A123456789",
      "is_active": true
    }
  }
}
```

## Security Note

The test scripts will partially hide your access code in the output (showing only last 2 digits) for security. However, be careful not to share your full credentials publicly.