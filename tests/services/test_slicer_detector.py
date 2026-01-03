"""
Unit tests for SlicerDetector service.
"""
import pytest
from unittest.mock import MagicMock, patch, Mock
from pathlib import Path
import platform

from src.services.slicer_detector import SlicerDetector
from src.models.slicer import SlicerType


class TestSlicerDetector:
    """Test slicer detector functionality."""

    @pytest.fixture
    def detector(self):
        """Create SlicerDetector instance."""
        return SlicerDetector()

    def test_initialization(self, detector):
        """Test detector initialization."""
        assert detector.os_type == platform.system()
        assert hasattr(detector, 'SLICER_PATHS')
        assert hasattr(detector, 'CONFIG_DIRS')

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.is_file')
    @patch('subprocess.run')
    def test_detect_slicer_found(self, mock_run, mock_is_file, mock_exists, detector):
        """Test detecting an available slicer."""
        # Mock path checks
        mock_exists.return_value = True
        mock_is_file.return_value = True
        
        # Mock version extraction
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="PrusaSlicer version 2.7.0",
            stderr=""
        )
        
        result = detector.detect_slicer(SlicerType.PRUSASLICER)
        
        assert result is not None
        assert result['slicer_type'] == SlicerType.PRUSASLICER.value
        assert result['name'] == 'PrusaSlicer'
        assert 'executable_path' in result
        assert result['version'] == '2.7.0'

    @patch('pathlib.Path.exists')
    def test_detect_slicer_not_found(self, mock_exists, detector):
        """Test detecting slicer when not installed."""
        mock_exists.return_value = False
        
        result = detector.detect_slicer(SlicerType.PRUSASLICER)
        
        assert result is None

    @patch.object(SlicerDetector, 'detect_slicer')
    def test_detect_all(self, mock_detect, detector):
        """Test detecting all slicers."""
        # Mock different results for different slicers
        def side_effect(slicer_type):
            if slicer_type == SlicerType.PRUSASLICER:
                return {
                    'slicer_type': SlicerType.PRUSASLICER.value,
                    'name': 'PrusaSlicer',
                    'executable_path': '/usr/bin/prusa-slicer',
                    'version': '2.7.0'
                }
            elif slicer_type == SlicerType.BAMBUSTUDIO:
                return {
                    'slicer_type': SlicerType.BAMBUSTUDIO.value,
                    'name': 'BambuStudio',
                    'executable_path': '/usr/bin/bambustudio',
                    'version': '1.9.0'
                }
            return None
        
        mock_detect.side_effect = side_effect
        
        results = detector.detect_all()
        
        assert len(results) == 2
        assert all('slicer_type' in r for r in results)
        assert all('name' in r for r in results)

    @patch('subprocess.run')
    def test_extract_version_success(self, mock_run, detector):
        """Test version extraction from slicer."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="PrusaSlicer version 2.7.0",
            stderr=""
        )
        
        version = detector._extract_version(Path("/usr/bin/prusa-slicer"))
        
        assert version == "2.7.0"

    @patch('subprocess.run')
    def test_extract_version_no_version(self, mock_run, detector):
        """Test version extraction when no version found."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Some output without version",
            stderr=""
        )
        
        version = detector._extract_version(Path("/usr/bin/prusa-slicer"))
        
        assert version is None

    @patch('subprocess.run')
    def test_extract_version_timeout(self, mock_run, detector):
        """Test version extraction with timeout."""
        from subprocess import TimeoutExpired
        mock_run.side_effect = TimeoutExpired("cmd", 5)
        
        version = detector._extract_version(Path("/usr/bin/prusa-slicer"))
        
        assert version is None

    def test_get_slicer_name(self, detector):
        """Test getting human-readable slicer names."""
        assert detector._get_slicer_name(SlicerType.PRUSASLICER) == "PrusaSlicer"
        assert detector._get_slicer_name(SlicerType.BAMBUSTUDIO) == "BambuStudio"
        assert detector._get_slicer_name(SlicerType.ORCASLICER) == "OrcaSlicer"
        assert detector._get_slicer_name(SlicerType.SUPERSLICER) == "SuperSlicer"

    @patch('pathlib.Path.exists')
    def test_verify_slicer_not_found(self, mock_exists, detector):
        """Test verifying non-existent slicer."""
        mock_exists.return_value = False
        
        is_valid, error = detector.verify_slicer("/nonexistent/slicer")
        
        assert not is_valid
        assert "not found" in error.lower()

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.is_file')
    @patch('subprocess.run')
    def test_verify_slicer_valid(self, mock_run, mock_is_file, mock_exists, detector):
        """Test verifying valid slicer."""
        mock_exists.return_value = True
        mock_is_file.return_value = True
        mock_run.return_value = MagicMock(returncode=0, stdout="version", stderr="")
        
        is_valid, error = detector.verify_slicer("/usr/bin/prusa-slicer")
        
        assert is_valid
        assert error is None

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.is_file')
    @patch('subprocess.run')
    def test_verify_slicer_timeout(self, mock_run, mock_is_file, mock_exists, detector):
        """Test verifying slicer with timeout."""
        from subprocess import TimeoutExpired
        mock_exists.return_value = True
        mock_is_file.return_value = True
        mock_run.side_effect = TimeoutExpired("cmd", 5)
        
        is_valid, error = detector.verify_slicer("/usr/bin/prusa-slicer")
        
        assert not is_valid
        assert "timed out" in error.lower()
