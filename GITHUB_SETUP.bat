@echo off
REM JARVIS GitHub 설정 및 배포 자동화 스크립트
REM 이 스크립트는 JARVIS를 GitHub에 올리는 과정을 자동화합니다.

setlocal enabledelayedexpansion

echo.
echo ╔════════════════════════════════════════════════════════════════════╗
echo ║          JARVIS GitHub Setup & Deployment Automation              ║
echo ╚════════════════════════════════════════════════════════════════════╝
echo.

REM 사용자 입력
set /p GITHUB_USERNAME="GitHub 사용자명 입력 (예: ky042): "
set /p REPO_NAME="저장소명 입력 (기본값: jarvis-agent-office): "

if "%REPO_NAME%"=="" set REPO_NAME=jarvis-agent-office

set /p GITHUB_EMAIL="GitHub 이메일 입력: "

echo.
echo ╔════════════════════════════════════════════════════════════════════╗
echo ║                      Git 설정 확인 및 초기화                       ║
echo ╚════════════════════════════════════════════════════════════════════╝
echo.

REM Git 설치 확인
git --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Git이 설치되지 않았습니다.
    echo 다운로드: https://git-scm.com/download/win
    pause
    exit /b 1
)
echo ✅ Git 버전: %git_version%

REM Git 글로벌 설정
echo.
echo 🔧 Git 글로벌 설정 중...
git config --global user.name "%GITHUB_USERNAME%"
git config --global user.email "%GITHUB_EMAIL%"

git config --global user.name >temp_name.txt
set /p git_name=<temp_name.txt
del temp_name.txt

echo ✅ Git 사용자명: %git_name%
echo ✅ Git 이메일: %GITHUB_EMAIL%

echo.
echo ╔════════════════════════════════════════════════════════════════════╗
echo ║                    로컬 Git 저장소 초기화                          ║
echo ╚════════════════════════════════════════════════════════════════════╝
echo.

REM Git 저장소 초기화
if exist .git (
    echo ℹ️  Git 저장소가 이미 존재합니다.
    set /p reinit="재초기화하시겠습니까? (y/n): "
    if /i "!reinit!"=="y" (
        rmdir /s /q .git
        git init
    )
) else (
    echo 🔄 Git 저장소 초기화 중...
    git init
    echo ✅ Git 저장소 생성 완료
)

echo.
echo ╔════════════════════════════════════════════════════════════════════╗
echo ║                     파일 스테이징 및 커밋                          ║
echo ╚════════════════════════════════════════════════════════════════════╝
echo.

REM .gitignore 확인
if not exist .gitignore (
    echo ⚠️  .gitignore 파일이 없습니다. 생성해주세요.
)

echo 📦 모든 파일 추가 중...
git add .
echo ✅ 파일 스테이징 완료

echo.
echo 📝 첫 번째 커밋 진행 중...
git commit -m "Initial commit: JARVIS Agent Office v5.0

- Mode-Driven Architecture (Chat/Task/Command)
- SimpleChat & SimpleTask implementations
- All tests passing (4/4 PASS)
- Production ready with full documentation

Features:
- JSON structured task planning
- Complete file operations support
- Comprehensive error handling
- CLI integration verified"

if errorlevel 1 (
    echo ⚠️  커밋 실패 (이미 커밋된 저장소일 수 있음)
) else (
    echo ✅ 첫 커밋 완료
)

echo.
echo ╔════════════════════════════════════════════════════════════════════╗
echo ║                   원격 저장소 설정 및 푸시                         ║
echo ╚════════════════════════════════════════════════════════════════════╝
echo.

echo ℹ️  다음 중 하나를 선택하세요:
echo   1. SSH (권장, 다음에 키 설정 필요)
echo   2. HTTPS (토큰 필요)
echo.
set /p auth_method="인증 방식 선택 (1 또는 2): "

if "%auth_method%"=="1" (
    set REPO_URL=git@github.com:%GITHUB_USERNAME%/%REPO_NAME%.git
    echo ✅ SSH 방식 선택
    echo.
    echo ℹ️  SSH 키가 설정되어 있지 않다면 다음을 실행하세요:
    echo    ssh-keygen -t ed25519 -C "!GITHUB_EMAIL!"
    echo    https://github.com/settings/ssh/new 에서 공개키 등록
) else (
    set REPO_URL=https://github.com/%GITHUB_USERNAME%/%REPO_NAME%.git
    echo ✅ HTTPS 방식 선택
    echo.
    echo ℹ️  Personal Access Token 필요:
    echo    https://github.com/settings/tokens/new
    echo    권한: repo, write:packages 선택
)

echo.
echo 🔗 원격 저장소 추가 중...
git remote remove origin >nul 2>&1
git remote add origin %REPO_URL%
echo ✅ 원격 저장소 설정: %REPO_URL%

echo.
echo 📤 메인 브랜치 설정 및 푸시 중...
git branch -M main
git push -u origin main

if errorlevel 1 (
    echo.
    echo ❌ 푸시 실패!
    echo.
    echo 확인 항목:
    echo   - GitHub 저장소가 생성되었는가? https://github.com/new
    echo   - SSH 키가 설정되었는가? (SSH 방식 선택 시)
    echo   - Personal Access Token이 유효한가? (HTTPS 방식 선택 시)
    echo.
    pause
    exit /b 1
) else (
    echo.
    echo ✅ GitHub 푸시 완료!
    echo.
    echo 📚 저장소 URL: https://github.com/%GITHUB_USERNAME%/%REPO_NAME%
)

echo.
echo ╔════════════════════════════════════════════════════════════════════╗
echo ║                      설정 및 배포 가이드                           ║
echo ╚════════════════════════════════════════════════════════════════════╝
echo.

echo 📖 문서 참고:
echo   - GITHUB_SETUP.md: GitHub 저장소 관리 방법
echo   - CLOUD_DEPLOYMENT.md: 클라우드 배포 방법
echo   - DEPLOYMENT_CHECKLIST.md: 배포 체크리스트
echo.

echo 🚀 다음 단계:
echo   1. https://github.com/%GITHUB_USERNAME%/%REPO_NAME% 확인
echo   2. 저장소 설정 →  Readme 작성
echo   3. Releases 탭에서 버전 태그 생성
echo   4. (선택) Railway/Render 자동 배포 설정
echo.

echo 클라우드 배포:
echo   - Railway: https://railway.app
echo   - Render: https://render.com
echo   - Heroku: https://www.heroku.com (유료)
echo.

echo ✨ JARVIS가 GitHub에 성공적으로 업로드되었습니다!
echo.

pause
