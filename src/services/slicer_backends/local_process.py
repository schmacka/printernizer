"""Backend that runs a slicer binary installed on the same host."""
import asyncio
import json
from pathlib import Path
from typing import Optional, List
import structlog

from src.models.slicer import SlicerConfig, SlicerProfile
from src.services.slicer_backends.base import SlicerBackend, SliceResult, ProgressCb
from src.utils.gcode_metadata import parse_gcode_metadata

logger = structlog.get_logger()


def build_command(slicer_type: str, executable: str, input_path: str,
                  profile: SlicerProfile, output_path: str) -> List[str]:
    """Build the slicer CLI command for the given engine.

    OrcaSlicer/BambuStudio use a native CLI (--load-settings/--load-filaments/
    --slice) that differs from PrusaSlicer's --export-gcode.
    """
    if slicer_type in ("orcaslicer", "bambustudio"):
        s = json.loads(profile.settings_json or "{}")
        settings = ";".join(p for p in (s.get("process"), s.get("machine")) if p)
        cmd = [executable, "--slice", "0", "--outputdir", str(Path(output_path).parent)]
        if settings:
            cmd += ["--load-settings", settings]
        if s.get("filament"):
            cmd += ["--load-filaments", s["filament"]]
        cmd.append(input_path)
        return cmd
    # PrusaSlicer / SuperSlicer
    cmd = [executable, "--export-gcode", "--output", output_path]
    if profile.profile_path:
        cmd += ["--load", profile.profile_path]
    cmd.append(input_path)
    return cmd


class LocalProcessBackend(SlicerBackend):
    def __init__(self, slicer: SlicerConfig):
        self.slicer = slicer

    async def slice(self, input_path: str, profile: SlicerProfile,
                    output_path: str, progress_cb: ProgressCb = None) -> SliceResult:
        cmd = build_command(self.slicer.slicer_type, self.slicer.executable_path,
                            input_path, profile, output_path)
        logger.info("Local slice", cmd=cmd)
        if progress_cb:
            await progress_cb(20)
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            return SliceResult(False, None, None, None,
                               stderr.decode("utf-8", "ignore")[:2000])
        if not Path(output_path).exists():
            return SliceResult(False, None, None, None, "Output file was not created")
        md = parse_gcode_metadata(output_path)
        if progress_cb:
            await progress_cb(100)
        return SliceResult(True, output_path, md.estimated_print_time, md.filament_used)

    async def verify(self) -> bool:
        return bool(self.slicer.executable_path and Path(self.slicer.executable_path).exists())

    async def version(self) -> Optional[str]:
        return self.slicer.version
