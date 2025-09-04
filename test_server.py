"""
Minimal Printernizer test server
Quick way to test if the system can start
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
import os
from pathlib import Path

app = FastAPI(title="Printernizer Test Server", version="1.0.0")

# CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/v1/health")
async def health():
    return {"status": "ok", "message": "Printernizer test server is running"}

@app.get("/api/v1/printers")
async def get_printers():
    return {"printers": []}

@app.get("/api/v1/jobs")
async def get_jobs():
    return {"jobs": []}

# Static files and frontend
frontend_path = Path(__file__).parent / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")
    
    @app.get("/")
    async def read_index():
        return FileResponse(str(frontend_path / "index.html"))
else:
    @app.get("/")
    async def read_index():
        return {"message": "Printernizer Test Server", "frontend": "not found", "backend": "running"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)