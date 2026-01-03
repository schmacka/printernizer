"""
Slicer detector service for cross-platform slicer discovery.

Detects PrusaSlicer, BambuStudio, OrcaSlicer, and SuperSlicer installations
on Windows, Linux, and macOS.
"""
import platform
import subprocess
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import structlog

from src.models.slicer import SlicerType

logger = structlog.get_logger()


class SlicerDetector:
    """
    Cross-platform slicer detection utility.

    Detects slicer installations by searching common installation paths
    and extracting version information.
    """

    # Common installation paths by OS and slicer type
    SLICER_PATHS = {
        "Windows": {
            SlicerType.PRUSASLICER: [
                Path(r"C:\Program Files\Prusa3D\PrusaSlicer\prusa-slicer.exe"),
                Path(r"C:\Program Files (x86)\Prusa3D\PrusaSlicer\prusa-slicer.exe"),
                Path.home() / "AppData/Local/Prusa3D/PrusaSlicer/prusa-slicer.exe",
            ],
            SlicerType.BAMBUSTUDIO: [
                Path(r"C:\Program Files\BambuStudio\bambustudio.exe"),
                Path(r"C:\Program Files (x86)\BambuStudio\bambustudio.exe"),
                Path.home() / "AppData/Local/BambuStudio/bambustudio.exe",
            ],
            SlicerType.ORCASLICER: [
                Path(r"C:\Program Files\OrcaSlicer\orca-slicer.exe"),
                Path(r"C:\Program Files (x86)\OrcaSlicer\orca-slicer.exe"),
                Path.home() / "AppData/Local/OrcaSlicer/orca-slicer.exe",
            ],
            SlicerType.SUPERSLICER: [
                Path(r"C:\Program Files\SuperSlicer\superslicer.exe"),
                Path(r"C:\Program Files (x86)\SuperSlicer\superslicer.exe"),
            ],
        },
        "Linux": {
            SlicerType.PRUSASLICER: [
                Path("/usr/bin/prusa-slicer"),
                Path("/usr/local/bin/prusa-slicer"),
                Path.home() / ".local/bin/prusa-slicer",
                Path("/opt/prusa3d/prusa-slicer"),
            ],
            SlicerType.BAMBUSTUDIO: [
                Path("/usr/bin/bambustudio"),
                Path("/usr/local/bin/bambustudio"),
                Path.home() / ".local/bin/bambustudio",
                Path("/opt/bambustudio/bambustudio"),
            ],
            SlicerType.ORCASLICER: [
                Path("/usr/bin/orca-slicer"),
                Path("/usr/local/bin/orca-slicer"),
                Path.home() / ".local/bin/orca-slicer",
                Path("/opt/orcaslicer/orca-slicer"),
            ],
            SlicerType.SUPERSLICER: [
                Path("/usr/bin/superslicer"),
                Path("/usr/local/bin/superslicer"),
                Path.home() / ".local/bin/superslicer",
            ],
        },
        "Darwin": {  # macOS
            SlicerType.PRUSASLICER: [
                Path("/Applications/PrusaSlicer.app/Contents/MacOS/PrusaSlicer"),
                Path.home() / "Applications/PrusaSlicer.app/Contents/MacOS/PrusaSlicer",
            ],
            SlicerType.BAMBUSTUDIO: [
                Path("/Applications/BambuStudio.app/Contents/MacOS/BambuStudio"),
                Path.home() / "Applications/BambuStudio.app/Contents/MacOS/BambuStudio",
            ],
            SlicerType.ORCASLICER: [
                Path("/Applications/OrcaSlicer.app/Contents/MacOS/OrcaSlicer"),
                Path.home() / "Applications/OrcaSlicer.app/Contents/MacOS/OrcaSlicer",
            ],
            SlicerType.SUPERSLICER: [
                Path("/Applications/SuperSlicer.app/Contents/MacOS/SuperSlicer"),
                Path.home() / "Applications/SuperSlicer.app/Contents/MacOS/SuperSlicer",
            ],
        },
    }

    # Config directory paths by OS and slicer type
    CONFIG_DIRS = {
        "Windows": {
            SlicerType.PRUSASLICER: Path.home() / "AppData/Roaming/PrusaSlicer",
            SlicerType.BAMBUSTUDIO: Path.home() / "AppData/Roaming/BambuStudio",
            SlicerType.ORCASLICER: Path.home() / "AppData/Roaming/OrcaSlicer",
            SlicerType.SUPERSLICER: Path.home() / "AppData/Roaming/SuperSlicer",
        },
        "Linux": {
            SlicerType.PRUSASLICER: Path.home() / ".config/PrusaSlicer",
            SlicerType.BAMBUSTUDIO: Path.home() / ".config/BambuStudio",
            SlicerType.ORCASLICER: Path.home() / ".config/OrcaSlicer",
            SlicerType.SUPERSLICER: Path.home() / ".config/SuperSlicer",
        },
        "Darwin": {
            SlicerType.PRUSASLICER: Path.home() / "Library/Application Support/PrusaSlicer",
            SlicerType.BAMBUSTUDIO: Path.home() / "Library/Application Support/BambuStudio",
            SlicerType.ORCASLICER: Path.home() / "Library/Application Support/OrcaSlicer",
            SlicerType.SUPERSLICER: Path.home() / "Library/Application Support/SuperSlicer",
        },
    }

    def __init__(self):
        """Initialize slicer detector."""
        self.os_type = platform.system()
        logger.info("Initialized slicer detector", os_type=self.os_type)

    def detect_all(self) -> List[Dict]:
        """
        Detect all available slicers on the system.

        Returns:
            List of detected slicer configurations
        """
        detected = []
        
        if self.os_type not in self.SLICER_PATHS:
            logger.warning("Unsupported OS for slicer detection", os_type=self.os_type)
            return detected

        for slicer_type in SlicerType:
            try:
                result = self.detect_slicer(slicer_type)
                if result:
                    detected.append(result)
                    logger.info(
                        "Detected slicer",
                        slicer_type=slicer_type.value,
                        version=result.get("version"),
                        path=result.get("executable_path")
                    )
            except Exception as e:
                logger.debug(
                    "Failed to detect slicer",
                    slicer_type=slicer_type.value,
                    error=str(e)
                )

        logger.info("Slicer detection completed", detected_count=len(detected))
        return detected

    def detect_slicer(self, slicer_type: SlicerType) -> Optional[Dict]:
        """
        Detect a specific slicer installation.

        Args:
            slicer_type: Type of slicer to detect

        Returns:
            Slicer configuration dict if found, None otherwise
        """
        paths = self.SLICER_PATHS.get(self.os_type, {}).get(slicer_type, [])
        
        for path in paths:
            if path.exists() and path.is_file():
                version = self._extract_version(path)
                config_dir = self._get_config_dir(slicer_type)
                
                return {
                    "slicer_type": slicer_type.value,
                    "name": self._get_slicer_name(slicer_type),
                    "executable_path": str(path),
                    "version": version,
                    "config_dir": str(config_dir) if config_dir and config_dir.exists() else None,
                }

        return None

    def _extract_version(self, executable_path: Path) -> Optional[str]:
        """
        Extract version from slicer executable.

        Args:
            executable_path: Path to slicer executable

        Returns:
            Version string if found, None otherwise
        """
        try:
            result = subprocess.run(
                [str(executable_path), "--version"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False
            )
            
            # Try to extract version from output
            output = result.stdout + result.stderr
            version_patterns = [
                r"version\s+(\d+\.\d+\.\d+)",
                r"(\d+\.\d+\.\d+)",
            ]
            
            for pattern in version_patterns:
                match = re.search(pattern, output, re.IGNORECASE)
                if match:
                    return match.group(1)
            
            return None
            
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            logger.debug(
                "Failed to extract version",
                executable=str(executable_path),
                error=str(e)
            )
            return None

    def _get_config_dir(self, slicer_type: SlicerType) -> Optional[Path]:
        """
        Get config directory for slicer type.

        Args:
            slicer_type: Type of slicer

        Returns:
            Config directory path if exists, None otherwise
        """
        config_dirs = self.CONFIG_DIRS.get(self.os_type, {})
        return config_dirs.get(slicer_type)

    def _get_slicer_name(self, slicer_type: SlicerType) -> str:
        """
        Get human-readable slicer name.

        Args:
            slicer_type: Type of slicer

        Returns:
            Human-readable name
        """
        names = {
            SlicerType.PRUSASLICER: "PrusaSlicer",
            SlicerType.BAMBUSTUDIO: "BambuStudio",
            SlicerType.ORCASLICER: "OrcaSlicer",
            SlicerType.SUPERSLICER: "SuperSlicer",
        }
        return names.get(slicer_type, slicer_type.value)

    def verify_slicer(self, executable_path: str) -> Tuple[bool, Optional[str]]:
        """
        Verify a slicer executable is valid and working.

        Args:
            executable_path: Path to slicer executable

        Returns:
            Tuple of (is_valid, error_message)
        """
        path = Path(executable_path)
        
        if not path.exists():
            return False, "Executable not found"
        
        if not path.is_file():
            return False, "Path is not a file"
        
        try:
            result = subprocess.run(
                [str(path), "--version"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False
            )
            
            if result.returncode == 0 or len(result.stdout + result.stderr) > 0:
                return True, None
            else:
                return False, "Executable did not respond correctly"
                
        except subprocess.TimeoutExpired:
            return False, "Executable timed out"
        except Exception as e:
            return False, f"Failed to verify: {str(e)}"
