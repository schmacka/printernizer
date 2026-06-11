# Bambu Lab Direct FTP Implementation

## Overview

This document describes the new direct FTP implementation for Bambu Lab printer file operations in Printernizer. This implementation replaces the dependency on the `bambulabs-api` library with a direct FTP connection using Python's built-in `ftplib` with SSL/TLS support.

## Key Benefits

- **Reliability**: Direct FTP connection without third-party library dependencies
- **Security**: Uses implicit TLS on port 990 for encrypted file transfers
- **Performance**: Direct file access without API abstraction overhead
- **Compatibility**: Works with all Bambu Lab printers that support FTP access
- **Fallback**: Maintains compatibility with existing `bambulabs-api` implementation

## Technical Specifications

### Connection Parameters
- **Protocol**: FTP with implicit TLS
- **Port**: 990
- **Username**: `bblp` (fixed for all Bambu Lab printers)
- **Password**: Bambu Lab access code from printer settings
- **Directory**: `/cache` (primary location for 3D printing files)

### Security
- Uses implicit TLS encryption for all data transfers
- Self-signed certificates are accepted (common for printer appliances)
- Passive mode FTP for home network compatibility
- Connection timeout and retry logic for reliability

## Implementation Components

### 1. Core FTP Service (`src/services/bambu_ftp_service.py`)

```python
from services.bambu_ftp_service import BambuFTPService

# Create service instance
service = BambuFTPService("192.168.1.100", "12345678")

# Test connection
success, message = await service.test_connection()

# List files
files = await service.list_files("/cache")

# Download file
success = await service.download_file("model.3mf", "local_path.3mf")
```

**Features:**
- Async/await support using thread executor
- Connection pooling with context manager
- Automatic retry logic
- File metadata parsing
- Error handling and logging

### 2. Updated Printer Class (`src/printers/bambu_lab.py`)

The `BambuLabPrinter` class now automatically initializes the direct FTP service alongside the existing `bambulabs-api` connection:

```python
# FTP service is automatically initialized during printer connection
printer = BambuLabPrinter(
    printer_id="bambu_a1",
    name="Bambu A1",
    ip_address="192.168.1.100",
    access_code="12345678",
    serial_number="ABC123456789"
)

await printer.connect()

# File operations now use direct FTP first, with fallback to bambulabs-api
files = await printer.list_files()  # Uses direct FTP
success = await printer.download_file("model.3mf", "local.3mf")  # Uses direct FTP
```

**Priority Order:**
1. Direct FTP service (new implementation)
2. `bambulabs-api` FTP client (fallback)
3. HTTP download (final fallback)

### 3. File Download Manager (`scripts/download_bambu_files.py`)

High-level interface for bulk file operations:

```python
# Download all 3D files from all configured printers
python scripts/download_bambu_files.py --all

# Download specific file from specific printer
python scripts/download_bambu_files.py --ip 192.168.1.100 --code 12345678 --file model.3mf

# Interactive file selection
python scripts/download_bambu_files.py --interactive
```

## Testing Scripts

### 1. Basic FTP Test (`scripts/test_bambu_ftp_direct.py`)

Tests direct FTP connectivity without Printernizer dependencies:

```bash
python scripts/test_bambu_ftp_direct.py --ip 192.168.1.100 --code 12345678
```

**Tests:**
- FTP connection with implicit TLS
- Directory listing
- File download
- Error handling

### 2. Complete Implementation Test (`scripts/test_complete_bambu_ftp.py`)

Comprehensive test of the entire implementation:

```bash
python scripts/test_complete_bambu_ftp.py --ip 192.168.1.100 --code 12345678
```

**Tests:**
- FTP service module
- Printer class integration
- File listing through printer interface
- File download through printer interface
- Error handling scenarios

### 3. Windows Batch File (`test_bambu_ftp.bat`)

Easy testing on Windows systems:

```batch
REM Edit the IP and access code in the file, then run:
test_bambu_ftp.bat
```

### 4. Enhanced Verification (`scripts/verify_bambu_download.py`)

Updated verification script that tests both old and new implementations:

```bash
python scripts/verify_bambu_download.py --ip 192.168.1.100 --code 12345678 --serial ABC123456789
```

## File Structure

```
printernizer/
├── src/
│   ├── services/
│   │   └── bambu_ftp_service.py          # Core FTP service
│   └── printers/
│       └── bambu_lab.py                  # Updated printer class
├── scripts/
│   ├── test_bambu_ftp_direct.py          # Basic FTP test
│   ├── test_complete_bambu_ftp.py        # Complete implementation test
│   ├── download_bambu_files.py           # File download manager
│   └── verify_bambu_download.py          # Enhanced verification
└── test_bambu_ftp.bat                    # Windows test script
```

## Usage Examples

### Getting Started

1. **Test basic connectivity:**
   ```bash
   python scripts/test_bambu_ftp_direct.py --ip 192.168.1.100 --code 12345678
   ```

2. **Run complete tests:**
   ```bash
   python scripts/test_complete_bambu_ftp.py --ip 192.168.1.100 --code 12345678
   ```

3. **Download files:**
   ```bash
   # Interactive selection
   python scripts/download_bambu_files.py --ip 192.168.1.100 --code 12345678

   # Download all files
   python scripts/download_bambu_files.py --ip 192.168.1.100 --code 12345678 --all
   ```

### Integration with Printernizer

The new FTP implementation is automatically used when a Bambu Lab printer is configured in Printernizer. No configuration changes are required - the system will:

1. Try direct FTP first
2. Fall back to `bambulabs-api` if FTP fails
3. Fall back to HTTP download as final option

### Configuration

No additional configuration is required. The implementation uses the same printer settings:

- **IP Address**: From printer configuration
- **Access Code**: From printer configuration
- **Port**: Hardcoded to 990 (FTP implicit TLS standard)
- **Username**: Hardcoded to `bblp` (Bambu Lab standard)

## Error Handling

The implementation includes comprehensive error handling:

### Connection Errors
- Network timeouts
- Connection refused (printer offline, FTP disabled)
- SSL/TLS errors (certificate issues)

### Authentication Errors
- Invalid access code
- FTP authentication failures

### File Operation Errors
- File not found
- Permission denied
- Directory access errors
- Download interruptions

### Fallback Behavior
If direct FTP fails, the system automatically falls back to the existing `bambulabs-api` implementation, ensuring continued functionality.

## Troubleshooting

### Common Issues

1. **Connection Timeout**
   - Check printer IP address
   - Verify network connectivity
   - Ensure printer is powered on

2. **Authentication Failed**
   - Verify access code is correct
   - Check printer FTP settings

3. **SSL/TLS Errors**
   - Normal for printers with self-signed certificates
   - Implementation automatically handles this

4. **No Files Found**
   - Normal if cache directory is empty
   - Upload files to printer first

### Diagnostic Tools

1. **Basic connectivity:**
   ```bash
   python scripts/test_bambu_ftp_direct.py --ip [IP] --code [CODE]
   ```

2. **Ping test:**
   ```bash
   ping 192.168.1.100
   ```

3. **Telnet test (port check):**
   ```bash
   telnet 192.168.1.100 990
   ```

## Performance Considerations

- **Connection Pooling**: FTP connections are reused within operations
- **Async Operations**: All FTP operations are non-blocking
- **Retry Logic**: Automatic retry on transient failures
- **Timeout Handling**: Configurable timeouts prevent hanging
- **Parallel Downloads**: Multiple files can be downloaded concurrently

## Future Enhancements

1. **Connection Caching**: Keep FTP connections alive between operations
2. **Progress Tracking**: Real-time download progress for large files
3. **Bandwidth Limiting**: Configurable transfer rate limits
4. **Multiple Directories**: Support for other printer directories beyond `/cache`
5. **File Monitoring**: Watch for new files on printer

## Dependencies

The direct FTP implementation uses only Python standard library components:

- `ftplib` - FTP client functionality
- `ssl` - TLS/SSL support
- `asyncio` - Async operation support
- `pathlib` - Path handling
- `socket` - Network operations

No additional packages are required, making the implementation lightweight and dependency-free.

## Conclusion

The new direct FTP implementation provides a robust, secure, and reliable method for accessing files on Bambu Lab printers. It eliminates dependency on third-party libraries while providing better error handling and performance than the previous implementation.

The implementation maintains full backward compatibility and includes comprehensive testing tools to ensure proper functionality in your environment.