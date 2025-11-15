@echo off
REM ============================================================================
REM Printernizer Startup Script (DEPRECATED FOR PRODUCTION USE)
REM ============================================================================
REM
REM ⚠️  WARNING: This script is DEPRECATED for production deployments!
REM
REM For production use, please use one of these recommended methods:
REM   1. Docker Standalone (RECOMMENDED): cd docker && docker-compose up -d
REM   2. Home Assistant Add-on: Install via HA Add-on Store
REM
REM This script is maintained for:
REM   - Local development and testing
REM   - Contributing to the project
REM   - Quick prototyping and debugging
REM
REM See README.md for complete deployment options and guides.
REM ============================================================================

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