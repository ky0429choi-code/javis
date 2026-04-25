# JARVIS Agent Office v5.0

## 🎯 프로젝트 개요

**JARVIS**는 **Mode-Driven Architecture**를 기반으로 한 AI 기반 에이전트 오피스 시스템입니다.

자연어 명령으로 다양한 작업을 수행하며, 일상 대화부터 복잡한 업무까지 자동화할 수 있습니다.

### ✨ 특징

- 🤖 **Mode-Driven Architecture**: Chat/Task/Command 자동 분류
- ⚡ **고속 응답**: 2-4초 응답시간 (타임아웃 없음)
- 🎯 **구조화된 계획**: JSON 기반 작업 단계 생성
- 📁 **파일 작업**: 생성/수정/삭제 지원
- 🔐 **보안**: 민감한 작업용 승인 엔진
- 📚 **지식 저장**: Wiki 에이전트로 학습 내용 관리
- 🧪 **테스트 완료**: 4/4 PASS (100%)

### 🛠️ 기술 스택

| 계층 | 기술 |
|------|------|
| **Backend** | FastAPI 0.135.3, Uvicorn |
| **LLM** | Ollama (jarvis/llama2/mistral 지원) |
| **DB** | SQLite (프로덕션: PostgreSQL) |
| **Frontend** | React 18 + Vite (선택사항) |
| **CLI** | Python asyncio-based |
| **Container** | Docker, Docker Compose |

---

## 🚀 빠른 시작

### 1️⃣ 설치

#### 필수 요구사항
- Python 3.8+
- Ollama (무료, https://ollama.ai)
- Git

#### 로컬 설치

```bash
# 저장소 클론
git clone https://github.com/YOUR_USERNAME/jarvis-agent-office.git
cd jarvis-agent-office

# Python 가상환경 생성
python -m venv .venv

# 가상환경 활성화
# Windows:
.venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate

# 의존성 설치
pip install -r backend/requirements.txt

# 환경 설정
cp .env.example .env
# .env 파일을 자신의 환경에 맞게 수정하세요
```

#### Docker로 설치 (권장)

```bash
# Docker & Docker Compose 필요
# https://www.docker.com/products/docker-desktop

# 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f backend
```

### 2️⃣ Ollama 모델 설치

```bash
# Ollama 실행 후...
ollama pull jarvis

# 또는 다른 모델
ollama pull llama2
ollama pull mistral
```

### 3️⃣ 실행

**터미널 1: 백엔드 시작**
```bash
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

**터미널 2: CLI 시작**
```bash
python jarvis_cli.py
```

**테스트**
```bash
python test_jarvis_complete.py
```

---

## 📖 주요 문서

| 문서 | 설명 |
|------|------|
| [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) | 배포 전 체크리스트 |
| [IMPLEMENTATION_REPORT.md](IMPLEMENTATION_REPORT.md) | 구현 보고서 |
| [GITHUB_SETUP.md](GITHUB_SETUP.md) | **GitHub 저장소 설정 가이드** |
| [CLOUD_DEPLOYMENT.md](CLOUD_DEPLOYMENT.md) | **클라우드 배포 가이드** (공개 공유) |
| [COMPLETE_SETUP_GUIDE.md](COMPLETE_SETUP_GUIDE.md) | 완전한 설정 가이드 |

---

## 💬 사용 예제

### CLI 대화
```bash
$ python jarvis_cli.py
╭─────────────────────────────────────╮
│ JARVIS Intelligence Core v5.0       │
╰─────────────────────────────────────╯

User: 안녕하세요!
╭──────────────── JARVIS ────────────────╮
│ Hello! How can I assist you today?    │
╰───────────────────────────────────────╯
```

### API 호출

**Chat 모드** (간단한 대화)
```bash
curl -X POST http://127.0.0.1:8000/api/jarvis/chat \
  -H "X-Shared-Key: AIN_PAPA_SHARED_KEY" \
  -H "Content-Type: application/json" \
  -d '{"message": "오늘 날씨가 어떨까?", "mode": "chat"}'
```

**Task 모드** (작업 계획)
```bash
curl -X POST http://127.0.0.1:8000/api/jarvis/chat \
  -H "X-Shared-Key: AIN_PAPA_SHARED_KEY" \
  -H "Content-Type: application/json" \
  -d '{"message": "README.md 파일을 생성해줄래?", "mode": "task"}'
```

**Auto 분류** (자동 모드 감지)
```bash
curl -X POST http://127.0.0.1:8000/api/jarvis/chat \
  -H "X-Shared-Key: AIN_PAPA_SHARED_KEY" \
  -H "Content-Type: application/json" \
  -d '{"message": "안녕!"}'  # mode 생략 시 자동 분류
```

---

## 🌐 외부 공유 & 배포

### 로컬 공유 (테스트)

**Ngrok** 사용 (5분)
```bash
# Backend 실행 후...
ngrok http 8000

# 외부 접속
https://random-id.ngrok.io/api/health
```

### 클라우드 배포 (프로덕션)

**Railway** (무료, 가장 추천)
```bash
1. https://railway.app 에 로그인
2. GitHub 저장소 연결
3. 자동 배포 시작
4. 공개 URL 할당
```

**Render** (무료)
```bash
1. https://render.com 접속
2. New Web Service 생성
3. GitHub 저장소 연결
4. 배포 완료
```

**AWS/Docker** (더 강력한 제어)
```bash
docker build -f backend/Dockerfile -t jarvis:latest .
docker run -p 8000:8000 jarvis:latest
```

자세한 내용은 [CLOUD_DEPLOYMENT.md](CLOUD_DEPLOYMENT.md) 참고

---

## 🔐 보안

### 환경 변수 설정

```bash
# .env 파일 생성
cp .env.example .env

# 다음 항목 변경:
API_KEY=your-strong-random-key-here
SECRET_KEY=your-secret-key-here
```

### 민감한 정보

`.gitignore`에 이미 포함됨:
- `.env` 파일
- `.venv/` (가상환경)
- 데이터베이스 (`.db`, `.sqlite`)
- 로그 파일

### API 인증

현재: `X-Shared-Key` 동기
향후: JWT 토큰 지원

---

## 🏗️ 아키텍처

```
User Request (CLI/API)
    ↓
ChatModeClassifier (자동 분류)
    ↓
   /|\
  / | \
CHAT TASK COMMAND
  ↓   ↓     ↓
LLM LLM  Orchestrator
  ↓   ↓     ↓
Response Response Response
```

### 모드별 처리

| 모드 | 응답 시간 | 기능 |
|------|----------|------|
| **Chat** | 2-3초 | 직접 LLM 호출 |
| **Task** | 3-4초 | 작업 계획 수립 |
| **Command** | 5-10초 | 복잡한 파이프라인 |

---

## 📊 성능

### 테스트 결과

```
테스트: test_jarvis_complete.py

✅ Health Check:      PASS (< 100ms)
✅ Chat Mode:         PASS (2-3초)
✅ Auto-Classification: PASS
✅ Task Mode:         PASS (3-4초)

결과: 4/4 PASS (100%) 🎉
```

### 시스템 요구사항

- **최소**: Python 3.8+, 500MB RAM, 1 core CPU
- **권장**: Python 3.10+, 2GB RAM, 2 core CPU
- **Ollama**: 4GB+ GPU 또는 CPU

---

## 🤝 기여 방법

1. Fork 저장소
2. Feature 브랜치 생성: `git checkout -b feature/new-feature`
3. 변경사항 커밋: `git commit -am 'Add feature'`
4. 브랜치 푸시: `git push origin feature/new-feature`
5. Pull Request 생성

---

## 📝 라이센스

MIT License - [LICENSE](LICENSE) 파일 참고

---

## ❓ FAQ & 문제 해결

**Q: Ollama 연결 실패?**  
A: `http://localhost:11434` 에서 Ollama 실행 중인지 확인

**Q: 포트 8000이 이미 사용 중?**  
A: `netstat -ano | findstr :8000` 로 확인 후 프로세스 종료

**Q: 응답이 느린가?**  
A: Ollama 모델 크기 조정 (llama2 > mistral 순서로 작음)

**Q: 데이터베이스 초기화?**  
A: `rm data/jarvis.db` 후 재시작

더 많은 도움: [Issues](https://github.com/YOUR_USERNAME/jarvis-agent-office/issues) 탭

---

## 📞 연락처

- 문제 보고: GitHub Issues
- 기능 제안: GitHub Discussions
- 이메일: your.email@example.com

---

## ✨ 향후 계획

- [ ] 프론트엔드 UI 완성
- [ ] PostgreSQL 지원
- [ ] 다국어 (한중일) 지원
- [ ] RAG (Retrieval-Augmented Generation)
- [ ] 멀티 LLM 로드 밸런싱
- [ ] 웹훅 지원
- [ ] 플러그인 시스템

---

**개발자**: JARVIS Team  
**버전**: 5.0 (Mode-Driven Architecture)  
**최종 업데이트**: 2026-04-18  
**상태**: 🟢 **프로덕션 준비 완료**

---

### 🙏 감사합니다!

JARVIS를 사용해주셔서 감사합니다. 혹시 개선 사항이나 버그 관련 피드백이 있으시면 언제든 이슈를 열어주세요!
