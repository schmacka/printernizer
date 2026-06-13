"""
OpenSCAD CLI wrapper.

OpenSCAD is an external binary (unlike the trimesh/numpy-stl Python stack used
elsewhere), so this service shells out to it. Rendering runs in a thread pool
executor with a timeout, mirroring ``PreviewRenderService``. The binary is
treated as an optional dependency: the service detects availability on init and
the rest of the application degrades gracefully when it is missing.
"""
import asyncio
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import structlog

from src.utils.config import get_settings
from src.utils.errors import OpenSCADNotAvailableError, OpenSCADRenderError

logger = structlog.get_logger(__name__)

# Default camera for PNG previews: translate(x,y,z), rotate(x,y,z), distance.
DEFAULT_CAMERA = "0,0,0,55,0,25,140"
DEFAULT_IMGSIZE = (600, 600)


class OpenSCADService:
    """Thin wrapper around the OpenSCAD command-line binary."""

    def __init__(self):
        settings = get_settings()
        self._timeout = settings.openscad_render_timeout
        self._max_output_bytes = settings.openscad_max_output_mb * 1024 * 1024
        self._configured_path = settings.openscad_binary_path
        self._binary: Optional[str] = None
        self._version: Optional[str] = None
        self._available = False
        self.detect()

    def detect(self) -> bool:
        """Locate the OpenSCAD binary and cache its version. Returns availability."""
        binary = self._configured_path or shutil.which("openscad")
        if not binary or not Path(binary).exists():
            self._available = False
            self._binary = None
            logger.info("OpenSCAD not available; generator module disabled",
                        configured_path=self._configured_path)
            return False

        self._binary = binary
        # If no X server is present, OpenSCAD needs a virtual framebuffer for PNG.
        self._xvfb = shutil.which("xvfb-run")
        try:
            result = subprocess.run(
                [binary, "--version"],
                capture_output=True, text=True, timeout=15
            )
            # OpenSCAD prints the version to stderr.
            output = (result.stderr or result.stdout or "").strip()
            self._version = output.replace("OpenSCAD version", "").strip() or output
            self._available = True
            logger.info("OpenSCAD detected", path=binary, version=self._version)
        except Exception as e:  # noqa: BLE001 - any failure means unusable
            self._available = False
            self._binary = None
            logger.warning("OpenSCAD found but not runnable", path=binary, error=str(e))
        return self._available

    @property
    def available(self) -> bool:
        return self._available

    @property
    def version(self) -> Optional[str]:
        return self._version

    @property
    def path(self) -> Optional[str]:
        return self._binary

    def _require_available(self) -> None:
        if not self._available:
            raise OpenSCADNotAvailableError(details={"configured_path": self._configured_path})

    @staticmethod
    def serialize_value(value: Any) -> str:
        """Serialize a Python value to an OpenSCAD ``-D`` literal."""
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, (int, float)):
            return repr(value)
        if isinstance(value, (list, tuple)):
            return "[" + ",".join(OpenSCADService.serialize_value(v) for v in value) + "]"
        # Strings: quote and escape.
        escaped = str(value).replace("\\", "\\\\").replace("\"", "\\\"")
        return f"\"{escaped}\""

    def _build_command(
        self,
        scad_path: Path,
        output_path: Path,
        params: Dict[str, Any],
        fmt: str,
        camera: Optional[str],
    ) -> List[str]:
        cmd: List[str] = [self._binary, "-o", str(output_path)]
        if fmt == "png":
            cmd += [
                "--camera", camera or DEFAULT_CAMERA,
                "--imgsize", f"{DEFAULT_IMGSIZE[0]},{DEFAULT_IMGSIZE[1]}",
                "--colorscheme", "Tomorrow",
                "--render",
            ]
        for key, value in params.items():
            cmd += ["-D", f"{key}={self.serialize_value(value)}"]
        cmd.append(str(scad_path))
        if fmt == "png" and getattr(self, "_xvfb", None):
            # Wrap with virtual framebuffer for headless PNG rendering.
            cmd = [self._xvfb, "-a", "--server-args=-screen 0 800x600x24"] + cmd
        return cmd

    async def render(
        self,
        scad_path: Path,
        output_path: Path,
        params: Optional[Dict[str, Any]] = None,
        fmt: str = "stl",
        camera: Optional[str] = None,
    ) -> Path:
        """
        Render an OpenSCAD file to ``output_path`` (``stl`` or ``png``).

        Runs in an executor with a timeout and enforces an output-size cap.
        Raises OpenSCADNotAvailableError / OpenSCADRenderError on failure.
        """
        self._require_available()
        params = params or {}
        loop = asyncio.get_event_loop()
        cmd = self._build_command(scad_path, output_path, params, fmt, camera)
        logger.info("Running OpenSCAD render", fmt=fmt, output=str(output_path))
        try:
            await asyncio.wait_for(
                loop.run_in_executor(None, self._run, cmd),
                timeout=self._timeout + 10,
            )
        except asyncio.TimeoutError:
            raise OpenSCADRenderError("render timed out", details={"timeout": self._timeout})

        if not output_path.exists():
            raise OpenSCADRenderError("no output produced")
        size = output_path.stat().st_size
        if size == 0:
            raise OpenSCADRenderError("empty output produced")
        if size > self._max_output_bytes:
            output_path.unlink(missing_ok=True)
            raise OpenSCADRenderError(
                "output exceeds size limit",
                details={"size_mb": round(size / (1024 * 1024), 1)},
            )
        return output_path

    def _run(self, cmd: List[str]) -> None:
        """Blocking subprocess invocation (executed in a thread pool)."""
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=self._timeout
            )
        except subprocess.TimeoutExpired:
            raise OpenSCADRenderError("render timed out", details={"timeout": self._timeout})
        if result.returncode != 0:
            stderr = (result.stderr or "").strip()
            # Keep the message compact; surface the most relevant line.
            reason = stderr.splitlines()[-1] if stderr else f"exit code {result.returncode}"
            logger.warning("OpenSCAD render failed", returncode=result.returncode, stderr=stderr[:500])
            raise OpenSCADRenderError(reason, details={"returncode": result.returncode})

    async def render_to_temp(
        self,
        source: str,
        params: Optional[Dict[str, Any]] = None,
        fmt: str = "stl",
        camera: Optional[str] = None,
        work_dir: Optional[Path] = None,
    ) -> Tuple[Path, Path]:
        """
        Write ``source`` to an isolated working dir and render it.

        Returns (scad_path, output_path). The caller owns cleanup of work_dir.
        """
        self._require_available()
        base = Path(work_dir) if work_dir else Path(tempfile.mkdtemp(prefix="openscad_"))
        base.mkdir(parents=True, exist_ok=True)
        scad_path = base / "model.scad"
        scad_path.write_text(source, encoding="utf-8")
        output_path = base / f"model.{fmt}"
        await self.render(scad_path, output_path, params=params, fmt=fmt, camera=camera)
        return scad_path, output_path

    def get_status(self) -> Dict[str, Any]:
        """Return availability info for the status endpoint."""
        return {
            "available": self._available,
            "version": self._version,
            "path": self._binary,
        }
