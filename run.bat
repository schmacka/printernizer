@echo off
REM Printernizer Startup Script
REM Ensures proper Python path and working directory

cd /d "%~dp0"
set PYTHONPATH=%CD%
set ENVIRONMENT=development
python -m src.main