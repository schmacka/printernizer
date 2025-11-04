@echo off
REM Kill process running on port 8000
REM Usage: kill-port-8000.bat

echo Finding process on port 8000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    echo Found PID: %%a
    echo Killing process...
    taskkill /PID %%a /F
    if errorlevel 1 (
        echo Failed to kill process. You may need administrator privileges.
        exit /b 1
    ) else (
        echo Process killed successfully.
        exit /b 0
    )
)

echo No process found listening on port 8000.
exit /b 0
