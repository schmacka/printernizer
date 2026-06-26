"""FastAPI app for the Printernizer Slicer Service."""
import json
import os

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse

from app.runner import BaseRunner
from app.jobs import JobStore
from app.profiles import list_bundled_profiles


def create_app(runner: BaseRunner) -> FastAPI:
    app = FastAPI(title="Printernizer Slicer Service")
    store = JobStore(runner)

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    @app.get("/version")
    async def version():
        return {"version": runner.version()}

    @app.get("/profiles")
    async def profiles():
        return list_bundled_profiles(getattr(runner, "profiles_root", ""))

    @app.post("/slice")
    async def slice_endpoint(file: UploadFile = File(...), profile: str = Form("{}")):
        data = await file.read()
        job_id = await store.submit(data, file.filename or "model.stl", json.loads(profile))
        return {"job_id": job_id}

    @app.get("/slice/{job_id}")
    async def job_status(job_id: str):
        job = store.get(job_id)
        if not job:
            raise HTTPException(404, "job not found")
        return {"status": job.status, "progress": job.progress,
                "estimated_print_time": job.estimated_print_time,
                "filament_used": job.filament_used, "error": job.error}

    @app.get("/slice/{job_id}/result")
    async def job_result(job_id: str):
        job = store.get(job_id)
        if not job or job.status != "completed" or not job.gcode_path:
            raise HTTPException(404, "result not ready")
        return FileResponse(job.gcode_path, filename="output.gcode")

    return app


def _default_app() -> FastAPI:
    apprun = os.environ.get("EMBEDDED_SLICER_PATH")
    profiles = os.environ.get("ORCA_PROFILES_ROOT", "")
    if apprun:
        from app.runner import OrcaSlicerRunner
        return create_app(OrcaSlicerRunner(apprun, profiles))
    return create_app(BaseRunner())


app = _default_app()
