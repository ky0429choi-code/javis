@echo off
setlocal EnableDelayedExpansion

REM JARVIS v5 - Integrated Execution Script
REM Simple batch runner without Korean characters

set "PATH_WORKSPACE=%cd%"
set "PATH_BACKEND=%PATH_WORKSPACE%\backend"
set "PATH_VENV=%PATH_WORKSPACE%\.venv"
set "PYTHON_EXE=%PATH_VENV%\Scripts\python.exe"
set "UVICORN_EXE=%PATH_VENV%\Scripts\uvicorn.exe"
set "BACKEND_PORT=8000"

echo.
echo ===== JARVIS v5 - Starting Server =====
echo.

if not exist "%PYTHON_EXE%" (
    echo ERROR: Python venv not found
    echo Please run setup first
    pause
    exit /b 1
)

cd /d "%PATH_WORKSPACE%"

REM Check if server is running
echo Checking backend status...
powershell -NoProfile -Command "try { $r=Invoke-WebRequest -Uri 'http://127.0.0.1:8000/api/health' -UseBasicParsing -TimeoutSec 2; if ($r.StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }" 2>nul

if errorlevel 1 (
    echo Starting JARVIS server...
    cd /d "%PATH_BACKEND%"
    start "JARVIS Backend" cmd /c "%UVICORN_EXE% app.main:app --host 127.0.0.1 --port %BACKEND_PORT% --reload"
    echo Waiting for server startup...
    timeout /t 6 /nobreak
    echo Server started at http://127.0.0.1:%BACKEND_PORT%
) else (
    echo Server is already running
)

echo.
echo Starting CLI...
cd /d "%PATH_WORKSPACE%"
python jarvis_cli.py

echo.
pause
