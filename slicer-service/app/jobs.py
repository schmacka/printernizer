"""In-memory job store + background slice execution."""
import asyncio
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict

from app.runner import BaseRunner


@dataclass
class Job:
    id: str
    status: str = "queued"           # queued|running|completed|failed
    progress: int = 0
    estimated_print_time: Optional[int] = None
    filament_used: Optional[float] = None
    error: Optional[str] = None
    gcode_path: Optional[str] = None
    workdir: str = ""


class JobStore:
    def __init__(self, runner: BaseRunner):
        self.runner = runner
        self._jobs: Dict[str, Job] = {}

    def get(self, job_id: str) -> Optional[Job]:
        return self._jobs.get(job_id)

    async def submit(self, model_bytes: bytes, model_name: str, profile: dict) -> str:
        job = Job(id=str(uuid.uuid4()))
        job.workdir = tempfile.mkdtemp(prefix="slice_")
        model_path = str(Path(job.workdir) / model_name)
        with open(model_path, "wb") as f:
            f.write(model_bytes)
        self._jobs[job.id] = job
        asyncio.create_task(self._run(job, model_path, profile))
        return job.id

    async def _run(self, job: Job, model_path: str, profile: dict):
        job.status, job.progress = "running", 20
        try:
            res = await self.runner.slice(model_path, profile, job.workdir)
            if res.success:
                job.status, job.progress = "completed", 100
                job.estimated_print_time = res.estimated_print_time
                job.filament_used = res.filament_used
                job.gcode_path = res.gcode_path
            else:
                job.status, job.error = "failed", res.error
        except Exception as e:  # noqa: BLE001
            job.status, job.error = "failed", str(e)
