"""
build123d engine wrapper.

build123d is a pure-Python CAD library built on OpenCascade (via the OCP
bindings), so unlike the previous OpenSCAD integration there is no external
binary: templates are executed in-process and exported to STL. The library is
treated as an optional dependency — it requires a glibc platform (OCP ships
manylinux wheels only), so the service detects availability on import and the
rest of the application degrades gracefully when it is missing.

Renders run in a thread pool with a timeout. Templates are trusted, bundled
modules (no user-supplied code is executed), so a cooperative timeout is
sufficient; a runaway build cannot be force-killed but cannot occur from
untrusted input either.
"""
import asyncio
import functools
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple

import structlog

from src.utils.config import get_settings
from src.utils.errors import GeneratorRenderError

logger = structlog.get_logger(__name__)

try:  # pragma: no cover - import guard depends on platform
    import build123d as _build123d
    from build123d import export_stl as _export_stl

    BUILD123D_AVAILABLE = True
    _BUILD123D_VERSION: Optional[str] = getattr(_build123d, "__version__", None)
    _IMPORT_ERROR: Optional[str] = None
except Exception as exc:  # noqa: BLE001 - we want to swallow any import failure
    BUILD123D_AVAILABLE = False
    _BUILD123D_VERSION = None
    _IMPORT_ERROR = str(exc)
    _export_stl = None  # type: ignore[assignment]


class Build123dService:
    """Thin wrapper that renders build123d template functions to STL/PNG."""

    def __init__(self):
        settings = get_settings()
        self._timeout = settings.generator_render_timeout
        self._available = BUILD123D_AVAILABLE
        self._version = _BUILD123D_VERSION
        if not self._available:
            logger.info("build123d not available; generator module disabled",
                        error=_IMPORT_ERROR)

    @property
    def available(self) -> bool:
        return self._available

    def get_status(self) -> Dict[str, Any]:
        """Status payload for GeneratorStatus."""
        return {
            "available": self._available,
            "engine": "build123d",
            "version": self._version,
        }

    async def render_stl(self, build_fn: Callable[..., Any],
                         params: Dict[str, Any], stl_path: Path) -> None:
        """Execute a template build function and export the result to STL."""
        if not self._available:
            raise GeneratorRenderError("build123d is not available")
        loop = asyncio.get_event_loop()
        try:
            await asyncio.wait_for(
                loop.run_in_executor(
                    None, functools.partial(self._build_and_export, build_fn, params, stl_path)
                ),
                timeout=self._timeout,
            )
        except asyncio.TimeoutError:
            raise GeneratorRenderError(
                f"Render exceeded the {self._timeout}s timeout"
            )
        except GeneratorRenderError:
            raise
        except Exception as exc:  # noqa: BLE001 - surface build errors uniformly
            raise GeneratorRenderError(str(exc))

    @staticmethod
    def _build_and_export(build_fn: Callable[..., Any],
                          params: Dict[str, Any], stl_path: Path) -> None:
        """Synchronous build + export (runs in a worker thread)."""
        shape = build_fn(**params)
        if shape is None:
            raise GeneratorRenderError("Template did not return a shape")
        ok = _export_stl(shape, str(stl_path))
        # build123d's export_stl returns True on success; some versions return None.
        if ok is False or not stl_path.exists():
            raise GeneratorRenderError("STL export produced no output")

    async def render_preview(self, stl_path: Path, png_path: Path,
                             size: Tuple[int, int] = (600, 600)) -> bool:
        """
        Best-effort PNG thumbnail of a rendered STL.

        Reuses the existing trimesh/matplotlib preview pipeline, which already
        degrades gracefully. Returns True if a PNG was written.
        """
        try:
            from src.services.preview_render_service import (
                PreviewRenderService,
                RENDERING_AVAILABLE,
            )
        except Exception:  # noqa: BLE001
            return False
        if not RENDERING_AVAILABLE:
            return False

        loop = asyncio.get_event_loop()
        renderer = PreviewRenderService()
        png_bytes = await loop.run_in_executor(
            None, functools.partial(renderer._render_stl, str(stl_path), size)
        )
        if not png_bytes:
            return False
        png_path.write_bytes(png_bytes)
        return True
