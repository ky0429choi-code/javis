# GitHub 배포 가이드 (JARVIS Agent Office)

## 📌 개요

JARVIS를 GitHub에 올려서 외부에서도 다운로드받고 로컬에서 실행할 수 있도록 하는 방법을 설명합니다.

⚠️ **현재 설정**: 사용자 로컬에서 실행하는 방식입니다. 향후 클라우드 배포는 별도 설정이 필요합니다.

---

## 1️⃣ GitHub 저장소 생성

### 1.1 GitHub 계정 준비
```bash
# GitHub 계정 없으면 생성 (https://github.com/signup)
# Git 설치 확인
git --version
```

### 1.2 GitHub에서 새 저장소 생성
1. https://github.com/new 에 접속
2. **Repository name**: `jarvis-agent-office`
3. **Description**: `JARVIS: AI-Powered Agent Office System`
4. **Public** 선택 (누구나 다운로드 가능)
5. **.gitignore 추가 안 함** (이미 생성함)
6. **Create repository** 클릭

결과: `https://github.com/YOUR_USERNAME/jarvis-agent-office` 생성

---

## 2️⃣ 로컬에서 Git 설정

### 2.1 GitHub 인증 설정

**Option A: SSH (권장)**
```bash
# SSH 키 생성 (없으면)
ssh-keygen -t ed25519 -C "your.email@example.com"
# 결과 파일: ~/.ssh/id_ed25519.pub 의 내용을 GitHub 설정에 등록
# GitHub > Settings > SSH and GPG keys > New SSH key 에 붙여넣기
```

**Option B: Personal Access Token**
```bash
# GitHub > Settings > Developer settings > Personal access tokens > Generate new token
# 권한: repo, write:packages 선택
# 토큰 저장 (나중에 사용)
```

### 2.2 Git 글로벌 설정
```powershell
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# 확인
git config --global user.name
git config --global user.email
```

---

## 3️⃣ 프로젝트 GitHub에 올리기

### 3.1 로컬 저장소 초기화 (첫 편)

```powershell
# 프로젝트 폴더로 이동
cd "C:\Users\ky042\AI\개발\jarvis_agent_office_v1"

# Git 저장소 초기화
git init

# 모든 파일 스테이징 (.gitignore 제외)
git add .

# 첫 커밋
git commit -m "Initial commit: JARVIS Agent Office v5.0

- Mode-Driven Architecture
- SimpleChat & SimpleTask modes
- All tests passing (4/4)
- Production ready"

# 원격 저장소 추가
git remote add origin https://github.com/YOUR_USERNAME/jarvis-agent-office.git
# SSH 방식: git remote add origin git@github.com:YOUR_USERNAME/jarvis-agent-office.git

# 저장소로 푸시
git branch -M main
git push -u origin main
```

✅ 완료! `https://github.com/YOUR_USERNAME/jarvis-agent-office` 에서 확인 가능

### 3.2 이후 수정사항 올리기

```powershell
# 파일 수정 후...
git status                    # 변경사항 확인
git add [파일명] 또는 git add .  # 스테이징
git commit -m "설명"           # 커밋
git push                      # 푸시
```

---

## 4️⃣ 다른 사용자가 다운로드 & 실행

### 4.1 저장소 클론
```bash
git clone https://github.com/YOUR_USERNAME/jarvis-agent-office.git
cd jarvis-agent-office
```

### 4.2 환경 설정

**Python 환경 설정 (Windows)**
```powershell
# 가상환경 생성
python -m venv .venv

# 가상환경 활성화
.venv\Scripts\Activate.ps1

# 의존성 설치
pip install -r backend/requirements.txt
pip install -r requirements.txt  # 루트 레벨도 있으면
```

**설정 파일 준비**
```bash
# 필요한 설정 파일 생성
# backend/app/settings.json 확인/수정
# prompts/ 폴더의 프롬프트 확인
```

### 4.3 Ollama 모델 설치

```bash
# Ollama 다운로드 (https://ollama.ai)
# 설치 후 실행

# JARVIS 모델 풀
ollama pull jarvis

# 또는 다른 모델 (llama2, mistral 등)
ollama pull llama2
```

### 4.4 JARVIS 실행

```powershell
# 터미널 1: 백엔드 시작
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# 터미널 2: CLI 시작
python jarvis_cli.py
```

---

## 5️⃣ 외부 접속 가능하게 만들기 (미래)

현재: 로컬 (127.0.0.1:8000)에서만 접근 가능

### 옵션 1: 간단한 공유 (Ngrok)
```bash
# Ngrok 설치 (https://ngrok.com)
ngrok http 8000

# 결과: https://random-id.ngrok.io 로 외부에서 접근 가능
```

### 옵션 2: 클라우드 배포 (권장)

**Railway (무료 호스팅)**
1. https://railway.app 에서 회원가입
2. GitHub 저장소 연결
3. 자동 배포 설정
4. 공개 URL 할당

**AWS/GCP/Azure**
- Docker 이미지 생성
- 클라우드 인스턴스에 배포
- 고정 IP/도메인 설정

### 옵션 3: VPS 서버
- DigitalOcean, Linode 등에서 서버 구입
- SSH로 접속 후 JARVIS 설치
- Nginx/Apache로 리버스 프록시 설정

---

## 6️⃣ 보안 설정

### 6.1 민감한 정보 보호

✅ 이미 `.gitignore` 에 포함된 항목:
- `.env` 파일 (API 키, 토큰)
- `.venv/` (가상환경)
- 데이터베이스 (`.db`, `.sqlite`)
- 감사 로그 (`audit_*.json`)

### 6.2 ENV 파일 배포

사용자가 로컬에서 설정해야 할 환경변수:

**`.env.example` 생성** (공개):
```
# backend/.env.example
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=jarvis
DATABASE_URL=sqlite:///jarvis.db
SECRET_KEY=change_me_to_strong_secret
LOG_LEVEL=INFO
```

**사용자가 복사해서 설정**:
```bash
# 다운로드 후
cp backend/.env.example backend/.env
# backend/.env 를 자신의 설정으로 수정
```

### 6.3 API 인증

```python
# backend/app/api/deps.py 수정 (선택사항)
# 현재: X-Shared-Key 간단 인증
# 향후: JWT, OAuth 지원
```

---

## 7️⃣ README 작성 팁

프로젝트의 `README.md` 에 다음을 포함하세요:

```markdown
# JARVIS Agent Office

[![GitHub license](https://img.shields.io/github/license/YOUR/jarvis-agent-office)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

## 📋 소개

JARVIS는 AI 기반 에이전트 오피스 시스템으로...

## 🚀 빠른 시작

### 설치
\`\`\`bash
git clone https://github.com/YOUR_USERNAME/jarvis-agent-office.git
cd jarvis-agent-office
python -m venv .venv
.venv\\Scripts\\Activate.ps1
pip install -r backend/requirements.txt
\`\`\`

### 실행
\`\`\`bash
# 터미널 1
cd backend
python -m uvicorn app.main:app

# 터미널 2
python jarvis_cli.py
\`\`\`

### API
\`\`\`bash
curl -X POST http://127.0.0.1:8000/api/jarvis/chat \\
  -H "X-Shared-Key: AIN_PAPA_SHARED_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{"message": "안녕!"}'
\`\`\`

## 📚 문서
- [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)
- [IMPLEMENTATION_REPORT.md](IMPLEMENTATION_REPORT.md)
- [SETUP.bat](SETUP.bat)

## 🔧 기술 스택
- FastAPI, Ollama, SQLite, React/Vite

## 📝 라이센스
MIT - [LICENSE](LICENSE) 참고

## ✉️ 문의
Issue 또는 Discussion 등록
```

---

## 8️⃣ 이제 시작하세요! 🎯

### 단계별 체크리스트

- [ ] GitHub 계정 생성 (미보유 시)
- [ ] SSH 키 또는 토큰 설정
- [ ] 새 저장소 생성 (`jarvis-agent-office`)
- [ ] `git init` 및 첫 커밋
- [ ] `git push` 로 GitHub 에 올리기
- [ ] README.md 작성
- [ ] GitHub Pages 설정 (선택사항)
- [ ] 다른 사람과 공유 (URL 복사)

---

## ❓ FAQ

**Q: 코드를 비공개로 하면?**  
A: 저장소를 `Private` 으로 설정하고 협력자만 초대

**Q: 외부에서 API 로 접근하고 싶으면?**  
A: Railway/AWS 무료 클라우드 배포 참고 ([CLOUD_DEPLOYMENT.md](CLOUD_DEPLOYMENT.md))

**Q: GitHub에서 문제 리포팅?**  
A: Issues 탭에서 버그 보고, Discussions 에서 기능 제안

---

**문서 작성일**: 2026-04-18  
**버전**: GitHub Setup Guide v1.0
