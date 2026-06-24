"""Backend that delegates slicing to the standalone slicer microservice."""
import asyncio
import json
from pathlib import Path
from typing import Optional, Callable
import aiohttp
import structlog

from src.models.slicer import SlicerConfig, SlicerProfile
from src.services.slicer_backends.base import SlicerBackend, SliceResult, ProgressCb

logger = structlog.get_logger()

TERMINAL = {"completed", "failed"}


class RemoteHTTPBackend(SlicerBackend):
    def __init__(self, slicer: SlicerConfig,
                 session_factory: Callable[[], aiohttp.ClientSession] = aiohttp.ClientSession,
                 poll_interval: float = 2.0, timeout_s: int = 3600):
        self.slicer = slicer
        self.base = (slicer.endpoint_url or "").rstrip("/")
        self._session_factory = session_factory
        self._poll = poll_interval
        self._timeout = timeout_s

    def _profile_payload(self, profile: SlicerProfile) -> str:
        return profile.settings_json or json.dumps({"profile_name": profile.profile_name})

    async def slice(self, input_path: str, profile: SlicerProfile,
                    output_path: str, progress_cb: ProgressCb = None) -> SliceResult:
        async with self._session_factory() as session:
            form = aiohttp.FormData()
            form.add_field("profile", self._profile_payload(profile))
            form.add_field("file", open(input_path, "rb"),
                           filename=Path(input_path).name,
                           content_type="application/octet-stream")
            async with session.post(f"{self.base}/slice", data=form) as r:
                job_id = (await r.json())["job_id"]

            waited = 0.0
            while True:
                async with session.get(f"{self.base}/slice/{job_id}") as r:
                    st = await r.json()
                if progress_cb and st.get("progress") is not None:
                    await progress_cb(int(st["progress"]))
                if st["status"] in TERMINAL:
                    break
                if waited >= self._timeout:
                    return SliceResult(False, None, None, None, "Remote slice timed out")
                await asyncio.sleep(self._poll)
                waited += self._poll

            if st["status"] == "failed":
                return SliceResult(False, None, None, None, st.get("error") or "Remote slice failed")

            async with session.get(f"{self.base}/slice/{job_id}/result") as r:
                data = await r.read()
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(data)
            return SliceResult(True, output_path, st.get("estimated_print_time"),
                               st.get("filament_used"))

    async def verify(self) -> bool:
        try:
            async with self._session_factory() as session:
                async with session.get(f"{self.base}/health") as r:
                    return r.status == 200
        except Exception:
            return False

    async def version(self) -> Optional[str]:
        try:
            async with self._session_factory() as session:
                async with session.get(f"{self.base}/version") as r:
                    return (await r.json()).get("version")
        except Exception:
            return None
