@echo off
REM Printernizer Startup Script
REM Ensures proper Python path and working directory

cd /d "%~dp0"
set PYTHONPATH=%CD%
set ENVIRONMENT=development

REM Performance optimization: Set DISABLE_RELOAD=true for faster startup
REM Normal mode (with auto-reload, ~82s startup):
REM   python -m src.main
REM Fast mode (no auto-reload, ~40s startup):
REM   set DISABLE_RELOAD=true
REM   python -m src.main

python -m src.main