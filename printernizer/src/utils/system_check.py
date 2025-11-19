"""
System check utilities for checking installed dependencies and system tools.
"""
import subprocess
import structlog
from typing import Dict, Any

logger = structlog.get_logger()


def check_ffmpeg() -> Dict[str, Any]:
    """
    Check if ffmpeg is installed and available on the system.

    Returns:
        Dict with:
            - installed (bool): Whether ffmpeg is installed
            - version (str|None): Version string if found
            - error (str|None): Error message if check failed
    """
    try:
        # Try to run ffmpeg -version
        result = subprocess.run(
            ['ffmpeg', '-version'],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            # Extract version from output (first line usually contains version)
            output_lines = result.stdout.strip().split('\n')
            version_line = output_lines[0] if output_lines else "Unknown version"

            logger.info("ffmpeg check successful", version=version_line)

            return {
                'installed': True,
                'version': version_line,
                'error': None
            }
        else:
            logger.warning("ffmpeg command failed", returncode=result.returncode, stderr=result.stderr)
            return {
                'installed': False,
                'version': None,
                'error': f"ffmpeg command failed with code {result.returncode}"
            }

    except FileNotFoundError:
        logger.warning("ffmpeg not found on system")
        return {
            'installed': False,
            'version': None,
            'error': "ffmpeg is not installed or not in system PATH"
        }
    except subprocess.TimeoutExpired:
        logger.error("ffmpeg version check timed out")
        return {
            'installed': False,
            'version': None,
            'error': "ffmpeg check timed out"
        }
    except Exception as e:
        logger.error("Unexpected error checking ffmpeg", error=str(e), error_type=type(e).__name__)
        return {
            'installed': False,
            'version': None,
            'error': f"Unexpected error: {str(e)}"
        }
