"""
Unit tests for Prusa file download functionality.
Tests the correct API endpoint construction and binary download validation.

This test suite validates the fix for the Prusa download issue where files
were downloading as JSON metadata instead of binary content.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
import aiohttp
from pathlib import Path

from src.printers.prusa import PrusaPrinter
from src.utils.errors import PrinterConnectionError


class TestPrusaFileDownload:
    """Test Prusa file download endpoint construction and validation."""

    @pytest.fixture
    def prusa_printer(self):
        """Create a mock Prusa printer instance."""
        printer = PrusaPrinter(
            printer_id=str(uuid4()),
            name="Test Prusa Core One",
            ip_address="192.168.1.50",
            api_key="test_api_key_12345"
        )
        printer.is_connected = True
        return printer

    def _create_mock_response(self, status=200, content=b'BINARY_DATA'):
        """Create a mock aiohttp response."""
        mock_response = MagicMock()
        mock_response.status = status
        mock_response.reason = "OK" if status == 200 else "Error"

        # Mock the content.iter_chunked method
        async def iter_chunked(chunk_size):
            yield content

        mock_response.content.iter_chunked = iter_chunked
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock()

        return mock_response

    @pytest.mark.asyncio
    async def test_download_url_construction_usb_with_leading_slash(self, prusa_printer, tmp_path):
        """Test URL construction for USB file with leading slash."""
        file_info = {
            "name": "TEST.BGC",
            "display": "[USB] Test File.bgcode",
            "refs": {
                "download": "/usb/TEST.BGC"
            }
        }

        # Mock session
        mock_response = self._create_mock_response()
        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)

        prusa_printer.session = mock_session

        # Mock _find_file_by_display_name to return our test file_info
        with patch.object(prusa_printer, '_find_file_by_display_name',
                         new_callable=AsyncMock, return_value=file_info):
            test_file = tmp_path / "test.bgcode"
            result = await prusa_printer.download_file("Test File.bgcode", str(test_file))

        # Verify success
        assert result is True

        # Verify the correct URL was constructed
        expected_url = "http://192.168.1.50/api/v1/files/usb/TEST.BGC"
        mock_session.get.assert_called_once_with(expected_url)

    @pytest.mark.asyncio
    async def test_download_url_construction_usb_without_leading_slash(self, prusa_printer, tmp_path):
        """Test URL construction for USB file without leading slash."""
        file_info = {
            "name": "TEST.BGC",
            "refs": {
                "download": "usb/TEST.BGC"  # No leading slash
            }
        }

        mock_response = self._create_mock_response()
        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)

        prusa_printer.session = mock_session

        with patch.object(prusa_printer, '_find_file_by_display_name',
                         new_callable=AsyncMock, return_value=file_info):
            test_file = tmp_path / "test.bgcode"
            result = await prusa_printer.download_file("test.bgcode", str(test_file))

        assert result is True
        expected_url = "http://192.168.1.50/api/v1/files/usb/TEST.BGC"
        mock_session.get.assert_called_once_with(expected_url)

    @pytest.mark.asyncio
    async def test_download_url_construction_local_storage(self, prusa_printer, tmp_path):
        """Test URL construction for local storage file."""
        file_info = {
            "name": "example.gcode",
            "refs": {
                "download": "/local/examples/example.gcode"
            }
        }

        mock_response = self._create_mock_response(content=b'G28\nG1 Z10')
        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)

        prusa_printer.session = mock_session

        with patch.object(prusa_printer, '_find_file_by_display_name',
                         new_callable=AsyncMock, return_value=file_info):
            test_file = tmp_path / "example.gcode"
            result = await prusa_printer.download_file("example.gcode", str(test_file))

        assert result is True
        expected_url = "http://192.168.1.50/api/v1/files/local/examples/example.gcode"
        mock_session.get.assert_called_once_with(expected_url)

    @pytest.mark.asyncio
    async def test_download_url_construction_sdcard_storage(self, prusa_printer, tmp_path):
        """Test URL construction for SD card file."""
        file_info = {
            "name": "model.gcode",
            "refs": {
                "download": "/sdcard/model.gcode"
            }
        }

        mock_response = self._create_mock_response()
        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)

        prusa_printer.session = mock_session

        with patch.object(prusa_printer, '_find_file_by_display_name',
                         new_callable=AsyncMock, return_value=file_info):
            test_file = tmp_path / "model.gcode"
            result = await prusa_printer.download_file("model.gcode", str(test_file))

        assert result is True
        expected_url = "http://192.168.1.50/api/v1/files/sdcard/model.gcode"
        mock_session.get.assert_called_once_with(expected_url)

    @pytest.mark.asyncio
    async def test_download_rejects_json_response(self, prusa_printer, tmp_path):
        """Test that JSON metadata is detected and rejected."""
        file_info = {
            "name": "TEST.BGC",
            "refs": {
                "download": "/usb/TEST.BGC"
            }
        }

        # Mock response that returns JSON instead of binary
        json_data = b'{"name": "TEST.BGC", "size": 4181758, "type": "PRINT_FILE"}'
        mock_response = self._create_mock_response(content=json_data)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)

        prusa_printer.session = mock_session

        with patch.object(prusa_printer, '_find_file_by_display_name',
                         new_callable=AsyncMock, return_value=file_info):
            test_file = tmp_path / "test.bgcode"
            result = await prusa_printer.download_file("test.bgcode", str(test_file))

        # Should return False and not save the file
        assert result is False
        assert not test_file.exists()

    @pytest.mark.asyncio
    async def test_download_handles_invalid_download_ref_format(self, prusa_printer, tmp_path):
        """Test handling of malformed download reference."""
        file_info = {
            "name": "TEST.BGC",
            "refs": {
                "download": "INVALID_FORMAT"  # Missing storage/path structure
            }
        }

        prusa_printer.session = MagicMock()

        with patch.object(prusa_printer, '_find_file_by_display_name',
                         new_callable=AsyncMock, return_value=file_info):
            test_file = tmp_path / "test.bgcode"
            result = await prusa_printer.download_file("test.bgcode", str(test_file))

        # Should return False due to invalid format
        assert result is False

    @pytest.mark.asyncio
    async def test_download_handles_missing_download_ref(self, prusa_printer, tmp_path):
        """Test handling of missing download reference."""
        file_info = {
            "name": "TEST.BGC",
            "refs": {}  # No download ref
        }

        prusa_printer.session = MagicMock()

        with patch.object(prusa_printer, '_find_file_by_display_name',
                         new_callable=AsyncMock, return_value=file_info):
            test_file = tmp_path / "test.bgcode"
            result = await prusa_printer.download_file("test.bgcode", str(test_file))

        # Should return False due to missing ref
        assert result is False

    @pytest.mark.asyncio
    async def test_download_handles_404_not_found(self, prusa_printer, tmp_path):
        """Test handling of 404 file not found."""
        file_info = {
            "name": "TEST.BGC",
            "refs": {
                "download": "/usb/TEST.BGC"
            }
        }

        mock_response = self._create_mock_response(status=404)
        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)

        prusa_printer.session = mock_session

        with patch.object(prusa_printer, '_find_file_by_display_name',
                         new_callable=AsyncMock, return_value=file_info):
            test_file = tmp_path / "test.bgcode"
            result = await prusa_printer.download_file("test.bgcode", str(test_file))

        assert result is False

    @pytest.mark.asyncio
    async def test_download_handles_401_unauthorized(self, prusa_printer, tmp_path):
        """Test handling of 401 unauthorized."""
        file_info = {
            "name": "TEST.BGC",
            "refs": {
                "download": "/usb/TEST.BGC"
            }
        }

        mock_response = self._create_mock_response(status=401)
        mock_response.reason = "Unauthorized"
        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)

        prusa_printer.session = mock_session

        with patch.object(prusa_printer, '_find_file_by_display_name',
                         new_callable=AsyncMock, return_value=file_info):
            test_file = tmp_path / "test.bgcode"
            result = await prusa_printer.download_file("test.bgcode", str(test_file))

        assert result is False

    @pytest.mark.asyncio
    async def test_download_handles_403_forbidden(self, prusa_printer, tmp_path):
        """Test handling of 403 forbidden."""
        file_info = {
            "name": "TEST.BGC",
            "refs": {
                "download": "/usb/TEST.BGC"
            }
        }

        mock_response = self._create_mock_response(status=403)
        mock_response.reason = "Forbidden"
        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)

        prusa_printer.session = mock_session

        with patch.object(prusa_printer, '_find_file_by_display_name',
                         new_callable=AsyncMock, return_value=file_info):
            test_file = tmp_path / "test.bgcode"
            result = await prusa_printer.download_file("test.bgcode", str(test_file))

        assert result is False

    @pytest.mark.asyncio
    async def test_download_file_with_subdirectory(self, prusa_printer, tmp_path):
        """Test downloading file from subdirectory."""
        file_info = {
            "name": "model.bgcode",
            "refs": {
                "download": "/usb/projects/client/model.bgcode"
            }
        }

        mock_response = self._create_mock_response()
        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)

        prusa_printer.session = mock_session

        with patch.object(prusa_printer, '_find_file_by_display_name',
                         new_callable=AsyncMock, return_value=file_info):
            test_file = tmp_path / "model.bgcode"
            result = await prusa_printer.download_file("model.bgcode", str(test_file))

        assert result is True
        expected_url = "http://192.168.1.50/api/v1/files/usb/projects/client/model.bgcode"
        mock_session.get.assert_called_once_with(expected_url)

    @pytest.mark.asyncio
    async def test_download_file_not_found_in_printer_list(self, prusa_printer, tmp_path):
        """Test when file is not found in printer file list."""
        prusa_printer.session = MagicMock()

        # Mock _find_file_by_display_name to return None (file not found)
        with patch.object(prusa_printer, '_find_file_by_display_name',
                         new_callable=AsyncMock, return_value=None):
            test_file = tmp_path / "test.bgcode"
            result = await prusa_printer.download_file("nonexistent.bgcode", str(test_file))

        assert result is False

    @pytest.mark.asyncio
    async def test_download_creates_parent_directory(self, prusa_printer, tmp_path):
        """Test that download creates parent directory if it doesn't exist."""
        file_info = {
            "name": "TEST.BGC",
            "refs": {
                "download": "/usb/TEST.BGC"
            }
        }

        mock_response = self._create_mock_response()
        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)

        prusa_printer.session = mock_session

        # Use a nested directory that doesn't exist yet
        nested_dir = tmp_path / "downloads" / "prusa" / "files"
        test_file = nested_dir / "test.bgcode"

        with patch.object(prusa_printer, '_find_file_by_display_name',
                         new_callable=AsyncMock, return_value=file_info):
            result = await prusa_printer.download_file("test.bgcode", str(test_file))

        assert result is True
        assert test_file.exists()
        assert test_file.parent.exists()

    @pytest.mark.asyncio
    async def test_download_binary_content_saved_correctly(self, prusa_printer, tmp_path):
        """Test that binary content is saved correctly."""
        file_info = {
            "name": "TEST.BGC",
            "refs": {
                "download": "/usb/TEST.BGC"
            }
        }

        # Create test binary content (BGCode magic bytes)
        test_content = b'GCDE\x00\x01\x02\x03\x04\x05' + b'\x00' * 100
        mock_response = self._create_mock_response(content=test_content)
        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)

        prusa_printer.session = mock_session

        with patch.object(prusa_printer, '_find_file_by_display_name',
                         new_callable=AsyncMock, return_value=file_info):
            test_file = tmp_path / "test.bgcode"
            result = await prusa_printer.download_file("test.bgcode", str(test_file))

        assert result is True
        assert test_file.exists()

        # Verify content matches
        with open(test_file, 'rb') as f:
            saved_content = f.read()
        assert saved_content == test_content


class TestPrusaFileDownloadEdgeCases:
    """Test edge cases and error scenarios for Prusa file downloads."""

    @pytest.fixture
    def prusa_printer(self):
        """Create a mock Prusa printer instance."""
        printer = PrusaPrinter(
            printer_id=str(uuid4()),
            name="Test Prusa",
            ip_address="192.168.1.50",
            api_key="test_key"
        )
        printer.is_connected = True
        return printer

    @pytest.mark.asyncio
    async def test_download_when_not_connected(self, prusa_printer, tmp_path):
        """Test that download fails gracefully when not connected."""
        prusa_printer.is_connected = False
        prusa_printer.session = None

        test_file = tmp_path / "test.bgcode"

        with pytest.raises(PrinterConnectionError):
            await prusa_printer.download_file("test.bgcode", str(test_file))

    @pytest.mark.asyncio
    async def test_download_with_special_characters_in_filename(self, prusa_printer, tmp_path):
        """Test downloading files with special characters in names."""
        file_info = {
            "name": "Müller & Co - Teil #1.bgcode",
            "refs": {
                "download": "/usb/Müller & Co - Teil #1.bgcode"
            }
        }

        mock_response = MagicMock()
        mock_response.status = 200

        async def iter_chunked(chunk_size):
            yield b'BINARY_DATA'

        mock_response.content.iter_chunked = iter_chunked
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock()

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)

        prusa_printer.session = mock_session

        with patch.object(prusa_printer, '_find_file_by_display_name',
                         new_callable=AsyncMock, return_value=file_info):
            test_file = tmp_path / "test.bgcode"
            result = await prusa_printer.download_file("Müller & Co - Teil #1.bgcode", str(test_file))

        # aiohttp should handle URL encoding automatically
        assert result is True
