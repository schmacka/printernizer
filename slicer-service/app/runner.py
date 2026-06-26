"""Slicer runners: a stub for tests, OrcaSlicer for production."""
import asyncio
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import structlog

from app.gcode_metadata import parse_gcode_metadata

logger = structlog.get_logger()


@dataclass
class RunnerResult:
    success: bool
    gcode_path: Optional[str]
    estimated_print_time: Optional[int]
    filament_used: Optional[float]
    error: Optional[str]


class BaseRunner:
    profiles_root: str = ""

    async def slice(self, model_path: str, profile: dict, output_dir: str) -> RunnerResult:
        raise NotImplementedError

    def version(self) -> str:
        return "stub"


class OrcaSlicerRunner(BaseRunner):
    """Runs the extracted OrcaSlicer AppRun headless under xvfb."""

    def __init__(self, apprun: str, profiles_root: str):
        self.apprun = apprun                # e.g. /opt/orca/squashfs-root/AppRun
        self.profiles_root = profiles_root  # .../resources/profiles

    def _resolve_preset(self, name: str, kind: str) -> Optional[str]:
        # kind in {machine, process, filament}; search vendor dirs for "<name>.json"
        root = Path(self.profiles_root)
        for path in root.glob(f"*/{kind}/{name}.json"):
            return str(path)
        return None

    def _build_settings(self, profile: dict, workdir: str):
        if "inline" in profile:
            inl = profile["inline"]
            paths = {}
            for kind in ("machine", "process", "filament"):
                if inl.get(kind):
                    p = Path(workdir) / f"_{kind}.json"
                    p.write_text(json.dumps(inl[kind]))
                    paths[kind] = str(p)
            return paths.get("process"), paths.get("machine"), paths.get("filament")
        sp = profile.get("system_preset", {})
        if isinstance(sp, str):
            sp = {"process": sp}
        process = self._resolve_preset(sp["process"], "process") if sp.get("process") else None
        machine = self._resolve_preset(sp["machine"], "machine") if sp.get("machine") else None
        filament = self._resolve_preset(sp["filament"], "filament") if sp.get("filament") else None
        return process, machine, filament

    def version(self) -> str:
        return os.environ.get("ORCA_VERSION", "orca")

    async def slice(self, model_path, profile, output_dir) -> RunnerResult:
        process, machine, filament = self._build_settings(profile, output_dir)
        settings = ";".join(p for p in (process, machine) if p)
        cmd = ["xvfb-run", "-a", self.apprun, "--debug", "2"]
        if settings:
            cmd += ["--load-settings", settings]
        if filament:
            cmd += ["--load-filaments", filament]
        cmd += ["--slice", "0", "--outputdir", output_dir, model_path]
        logger.info("orca slice", cmd=cmd)
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        _, stderr = await proc.communicate()
        result_json = Path(output_dir) / "result.json"
        if result_json.exists():
            rc = json.loads(result_json.read_text()).get("return_code", 1)
            if rc != 0:
                return RunnerResult(False, None, None, None, f"return_code={rc}")
        gcodes = sorted(Path(output_dir).glob("*.gcode"))
        if proc.returncode != 0 or not gcodes:
            return RunnerResult(False, None, None, None,
                                stderr.decode("utf-8", "ignore")[:2000] or "no gcode produced")
        md = parse_gcode_metadata(str(gcodes[0]))
        return RunnerResult(True, str(gcodes[0]), md.estimated_print_time, md.filament_used, None)
