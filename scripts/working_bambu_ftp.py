#!/usr/bin/env python3
"""
Working Bambu Lab FTP Implementation
"""

import ssl
import socket
import sys
import tempfile
from pathlib import Path

class BambuFTP:
    """Manual FTP implementation for Bambu Lab printers."""

    def __init__(self, host, port=990):
        self.host = host
        self.port = port
        self.sock = None
        self.ssl_sock = None

    def connect(self):
        """Connect to FTP server with SSL."""
        # Create socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(30)
        self.sock.connect((self.host, self.port))

        # Wrap with SSL
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        self.ssl_sock = context.wrap_socket(self.sock, server_hostname=self.host)

        # Read welcome message
        response = self._read_response()
        print(f"Server: {response}")

        if not response.startswith("220"):
            raise Exception(f"Unexpected server response: {response}")

    def login(self, username, password):
        """Login to FTP server."""
        # Send username
        self._send_command(f"USER {username}")
        response = self._read_response()
        print(f"USER response: {response}")

        if response.startswith("331"):
            # Send password
            self._send_command(f"PASS {password}")
            response = self._read_response()
            print(f"PASS response: {response}")

            if not response.startswith("230"):
                raise Exception(f"Login failed: {response}")
        elif not response.startswith("230"):
            raise Exception(f"Login failed: {response}")

    def cwd(self, directory):
        """Change working directory."""
        self._send_command(f"CWD {directory}")
        response = self._read_response()
        print(f"CWD response: {response}")

        if not response.startswith("250"):
            raise Exception(f"CWD failed: {response}")

    def list_files(self):
        """List files in current directory."""
        # Set passive mode
        self._send_command("PASV")
        response = self._read_response()
        print(f"PASV response: {response}")

        if not response.startswith("227"):
            raise Exception(f"PASV failed: {response}")

        # Parse passive mode response to get data connection info
        # Format: 227 Entering Passive Mode (h1,h2,h3,h4,p1,p2)
        import re
        match = re.search(r'\\((\\d+,\\d+,\\d+,\\d+,\\d+,\\d+)\\)', response)
        if not match:
            raise Exception(f"Could not parse PASV response: {response}")

        parts = match.group(1).split(',')
        data_host = '.'.join(parts[:4])
        data_port = int(parts[4]) * 256 + int(parts[5])

        print(f"Data connection: {data_host}:{data_port}")

        # Create data connection
        data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        data_sock.settimeout(30)
        data_sock.connect((data_host, data_port))

        # Wrap data connection with SSL too
        data_ssl_sock = ssl.create_default_context()
        data_ssl_sock.check_hostname = False
        data_ssl_sock.verify_mode = ssl.CERT_NONE
        data_ssl_sock = data_ssl_sock.wrap_socket(data_sock)

        # Send LIST command
        self._send_command("LIST")
        response = self._read_response()
        print(f"LIST response: {response}")

        # Read data
        file_list = []
        try:
            while True:
                data = data_ssl_sock.recv(1024)
                if not data:
                    break
                file_list.append(data.decode('utf-8', errors='ignore'))
        except:
            pass

        data_ssl_sock.close()

        # Read final response
        final_response = self._read_response()
        print(f"LIST final response: {final_response}")

        return ''.join(file_list).split('\\n')

    def download_file(self, filename, local_path):
        """Download a file."""
        # Set passive mode
        self._send_command("PASV")
        response = self._read_response()

        if not response.startswith("227"):
            raise Exception(f"PASV failed: {response}")

        # Parse passive mode response
        import re
        match = re.search(r'\\((\\d+,\\d+,\\d+,\\d+,\\d+,\\d+)\\)', response)
        if not match:
            raise Exception(f"Could not parse PASV response: {response}")

        parts = match.group(1).split(',')
        data_host = '.'.join(parts[:4])
        data_port = int(parts[4]) * 256 + int(parts[5])

        # Create data connection
        data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        data_sock.settimeout(30)
        data_sock.connect((data_host, data_port))

        # Wrap with SSL
        data_ssl_sock = ssl.create_default_context()
        data_ssl_sock.check_hostname = False
        data_ssl_sock.verify_mode = ssl.CERT_NONE
        data_ssl_sock = data_ssl_sock.wrap_socket(data_sock)

        # Send RETR command
        self._send_command(f"RETR {filename}")
        response = self._read_response()
        print(f"RETR response: {response}")

        if not response.startswith("150"):
            data_ssl_sock.close()
            raise Exception(f"RETR failed: {response}")

        # Download file
        with open(local_path, 'wb') as f:
            while True:
                data = data_ssl_sock.recv(8192)
                if not data:
                    break
                f.write(data)

        data_ssl_sock.close()

        # Read final response
        final_response = self._read_response()
        print(f"RETR final response: {final_response}")

        return True

    def quit(self):
        """Close connection."""
        self._send_command("QUIT")
        response = self._read_response()
        print(f"QUIT response: {response}")

        if self.ssl_sock:
            self.ssl_sock.close()
        if self.sock:
            self.sock.close()

    def _send_command(self, command):
        """Send FTP command."""
        command_bytes = (command + '\\r\\n').encode('utf-8')
        self.ssl_sock.send(command_bytes)
        print(f"Sent: {command}")

    def _read_response(self):
        """Read FTP response."""
        response = b''
        while True:
            data = self.ssl_sock.recv(1024)
            if not data:
                break
            response += data
            if b'\\r\\n' in response:
                break

        return response.decode('utf-8', errors='ignore').strip()

def test_working_ftp():
    """Test the working FTP implementation."""
    from bambu_credentials import get_bambu_credentials
    
    host = "192.168.176.101"
    target_file = "top-option-2-color-change_plate_1.3mf"

    print("Working Bambu Lab FTP Test")
    print("=" * 40)
    print(f"Host: {host}")
    print(f"Target: {target_file}")
    print()
    
    try:
        username, password = get_bambu_credentials(host)
        print(f"Using username: {username}")
    except ValueError as e:
        print(f"Error getting credentials: {e}")
        return

    try:
        # Connect
        ftp = BambuFTP(host)
        print("Connecting...")
        ftp.connect()

        # Login
        print("\\nLogging in...")
        ftp.login(username, password)

        # Change to cache directory
        print("\\nChanging to cache directory...")
        ftp.cwd("/cache")

        # List files
        print("\\nListing files...")
        files = ftp.list_files()

        print(f"\\nFound {len([f for f in files if f.strip()])} files:")
        valid_files = [f for f in files if f.strip() and not f.startswith('total')]
        for i, file_line in enumerate(valid_files[:10], 1):
            print(f"  {i:2d}. {file_line.strip()}")

        # Look for target file
        target_found = None
        for file_line in valid_files:
            if target_file.lower() in file_line.lower():
                target_found = file_line.strip()
                break

        if target_found:
            print(f"\\nFound target file: {target_found}")

            # Extract filename from listing
            filename = target_found.split()[-1]  # Last part is usually filename

            # Download
            downloads_dir = Path("downloads")
            downloads_dir.mkdir(exist_ok=True)
            local_path = downloads_dir / filename

            print(f"\\nDownloading to: {local_path}")
            ftp.download_file(filename, str(local_path))

            if local_path.exists():
                size = local_path.stat().st_size
                print(f"\\nSUCCESS! Downloaded {size:,} bytes")
                return True
            else:
                print("\\nDownload failed - file not created")
                return False
        else:
            print(f"\\nTarget file '{target_file}' not found")
            return False

        # Disconnect
        ftp.quit()

    except Exception as e:
        print(f"\\nError: {e}")
        return False

if __name__ == "__main__":
    success = test_working_ftp()
    print(f"\\nResult: {'SUCCESS' if success else 'FAILED'}")
    sys.exit(0 if success else 1)