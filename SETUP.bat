@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

:: ==============================================================================
:: JARVIS v5 - 초기화 및 설정 스크립트
:: 백엔드와 프론트엔드를 설정합니다.
:: ==============================================================================

for /F %%i in ('cd') do set "PATH_WORKSPACE=%%i"
set "PATH_BACKEND=%PATH_WORKSPACE%\backend"
set "PATH_FRONTEND=%PATH_WORKSPACE%\frontend"
set "PATH_VENV=%PATH_WORKSPACE%\.venv"
set "PYTHON_EXE=%PATH_VENV%\Scripts\python.exe"
set "PIP_EXE=%PATH_VENV%\Scripts\pip.exe"

echo.
echo ╔═══════════════════════════════════════════════════════════════╗
echo ║ JARVIS v5 - 초기 설정 가이드 (Setup Guide)                    ║
echo ╚═══════════════════════════════════════════════════════════════╝
echo.

REM Step 1: Python 가상환경 확인
echo [STEP 1/4] Python 가상환경 확인...
if exist "%PYTHON_EXE%" (
    echo [OK] 가상환경 찾음: %PYTHON_EXE%
) else (
    echo [ERROR] 가상환경을 찾을 수 없습니다.
    echo [INFO] 다음 명령어를 실행하세요:
    echo        python -m venv .venv
    echo.
    pause
    exit /b 1
)

REM Step 2: 백엔드 의존성 설치
echo.
echo [STEP 2/4] 백엔드 의존성 설치...
cd /d "%PATH_BACKEND%"
if exist "requirements.txt" (
    echo [INSTALL] requirements.txt 설치 중...
    "%PIP_EXE%" install -r requirements.txt --quiet
    if errorlevel 0 (
        echo [OK] 백엔드 의존성 설치 완료
    ) else (
        echo [WARNING] 설치 중 오류가 발생했습니다.
    )
) else (
    echo [WARNING] requirements.txt를 찾을 수 없습니다.
)

REM Step 3: .env 파일 확인
echo.
echo [STEP 3/4] 환경 설정 파일 확인...
if exist "%PATH_BACKEND%\.env" (
    echo [OK] .env 파일 찾음
) else (
    echo [WARNING] .env 파일을 찾을 수 없습니다.
    echo [ACTION] .env.example 를 복사합니다.
    if exist "..\backend\.env" (
        copy "..\backend\.env" .env >nul 2>&1
        echo [OK] .env 파일 생성 완료
    ) else (
        echo [ERROR] .env 또는 .env.example 을 찾을 수 없습니다.
    )
)

REM Step 4: 프론트엔드 의존성 설치 및 빌드
echo.
echo [STEP 4/4] 프론트엔드 설정...
cd /d "%PATH_FRONTEND%"
if exist "package.json" (
    if exist "node_modules" (
        echo [OK] node_modules 찾음 (설치 스킵)
    ) else (
        echo [INSTALL] npm dependencies 설치 중...
        call npm install --legacy-peer-deps --quiet
        if errorlevel 0 (
            echo [OK] npm 설치 완료
        ) else (
            echo [WARNING] npm 설치 중 오류 발생
        )
    )
    
    if not exist "dist" (
        echo [BUILD] React 프로젝트 빌드 중...
        call npm run build --silent
        if errorlevel 0 (
            echo [OK] 프론트엔드 빌드 완료
        ) else (
            echo [WARNING] 빌드 중 오류 발생
        )
    ) else (
        echo [OK] 빌드된 dist 폴더 찾음
    )
) else (
    echo [WARNING] package.json을 찾을 수 없습니다.
)

REM Complete
echo.
echo ╔═══════════════════════════════════════════════════════════════╗
echo ║ ✅ JARVIS 초기화 완료!                                         ║
echo ║                                                               ║
echo ║ 다음 단계:                                                     ║
echo ║ 1. JARVIS.bat 를 실행하여 서버를 시작합니다.                   ║
echo ║ 2. http://localhost:8000 에서 UI에 접속합니다.                 ║
echo ║ 3. 채팅으로 자비스에게 명령을 내립니다.                        ║
echo ║                                                               ║
echo ║ 모바일 앱 연동:                                                ║
echo ║ - 모바일에서 'http://당신의IP:8000' 로 접속                   ║
echo ║ - 또는 모바일 앱에서 API_SERVER를 설정                         ║
echo ╚═══════════════════════════════════════════════════════════════╝
echo.

pause
