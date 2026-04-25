@echo off
REM JARVIS v5 - Integrated Execution Script
REM Backend(FastAPI) serves Frontend(React Build) directly.
setlocal EnableDelayedExpansion

REM Absolute path setup
for /F %%i in ('cd') do set "PATH_WORKSPACE=%%i"
if not "%~1"=="" set "PATH_WORKSPACE=%~1"

set "PATH_BACKEND=%PATH_WORKSPACE%\backend"
set "PATH_VENV=%PATH_WORKSPACE%\.venv"
set "PYTHON_EXE=%PATH_VENV%\Scripts\python.exe"
set "UVICORN_EXE=%PATH_VENV%\Scripts\uvicorn.exe"
set "BACKEND_PORT=8000"

echo.
echo ============================================================
echo JARVIS v5 - Agent Office (Integrated Mode)
echo Single Port Integration (UI + API)
echo ============================================================
echo.

REM Check virtual environment
if not exist "%PYTHON_EXE%" (
    echo [ERROR] Python venv not found: %PYTHON_EXE%
    echo [INFO] Check if '.venv' directory exists.
    pause
    exit /b 1
)

cd /d "%PATH_WORKSPACE%" || (
    echo [ERROR] Failed to access workspace: %PATH_WORKSPACE%
    pause
    exit /b 1
)

REM Check backend process status
echo [CHECK] Checking system status...
powershell -NoProfile -Command "try { $r=Invoke-WebRequest -Uri 'http://127.0.0.1:%BACKEND_PORT%/api/health' -UseBasicParsing -TimeoutSec 2; if ($r.StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }" 2>nul

if errorlevel 1 (
    echo [LAUNCH] Starting JARVIS integrated server...
    cd /d "%PATH_BACKEND%"
    if not exist ".env" (
        echo [WARNING] .env file not found. Copying from .env.example...
        copy "..\backend\.env" .env 2>nul || echo [WARNING] Please verify .env manually.
    )
    
    start "JARVIS Integrated Server" cmd /c "%UVICORN_EXE% app.main:app --host 127.0.0.1 --port %BACKEND_PORT% --reload"
    timeout /t 6 /nobreak >nul
    echo [SUCCESS] Server started: http://127.0.0.1:%BACKEND_PORT%
) else (
    echo [OK] Server is already running.
)

echo.
echo [LAUNCH] Launching browser...
timeout /t 2 /nobreak >nul
start "JARVIS UI" "http://localhost:%BACKEND_PORT%"

echo.
echo ============================================================
echo JARVIS v5 is running!
echo.
echo Integration URL: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo Chat API: /api/jarvis/chat
echo.
echo For development HMR server, open another terminal:
echo   cd frontend
echo   npm run dev
echo ============================================================
echo.
echo [INFO] JARVIS is ready. Press any key to close this window.
echo [INFO] Or keep this window open and minimize the other terminal.
echo.

REM Keep script running until user closes it
pause
