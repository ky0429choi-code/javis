# JARVIS v5 - 완벽한 설정 가이드 📖

**마지막 업데이트**: 2026-04-17  
**상태**: ✅ 구조 완성, 대화 기능 준비, 모바일 연동 설계 완료

---

## 📋 개요

JARVIS v5는 다음 기능을 포함하는 통합 AI 에이전트 시스템입니다:

✅ **웹 UI**: React 기반 아름다운 대시보드  
✅ **백엔드 API**: FastAPI 기반 강력한 REST API  
✅ **채팅 기능**: AI 자비스와의 실시간 대화  
✅ **작업 관리**: 자동 작업 생성 및 추적  
✅ **승인 워크플로우**: 중요 작업 승인 프로세스  
✅ **모바일 연동**: 모바일 앱 완벽 지원  

---

## 🚀 빠른 시작 (3단계)

### Step 1: 초기 설정

```bash
# Windows
SETUP.bat

# macOS/Linux
chmod +x SETUP.sh
./SETUP.sh
```

이 스크립트는:
- Python 가상환경 확인
- 백엔드 의존성 설치 (requirements.txt)
- .env 파일 설정
- 프론트엔드 빌드 (npm build)

### Step 2: 서버 실행

```bash
JARVIS.bat
```

또는 PowerShell에서:

```powershell
cd backend
.\..\venv\Scripts\Activate.ps1
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Step 3: 접속

- 🌐 웹: **http://localhost:8000**
- 📚 API 문서: **http://localhost:8000/docs**
- 📱 모바일: **http://당신의IP:8000**

---

## 📁 프로젝트 구조

```
jarvis_agent_office_v1/
├── backend/                    # FastAPI 백엔드
│   ├── app/
│   │   ├── main.py            # 메인 앱 진입점
│   │   ├── api/
│   │   │   ├── routers/
│   │   │   │   ├── chat.py     # 채팅 API
│   │   │   │   ├── tasks.py    # 작업 API
│   │   │   │   ├── approvals.py # 승인 API
│   │   │   │   ├── health.py   # 헬스 체크
│   │   │   │   └── mobile.py   # 모바일 API ✨ NEW
│   │   ├── agents/             # AI 에이전트들
│   │   │   ├── planner.py      # 계획 에이전트
│   │   │   ├── executor.py     # 실행 에이전트
│   │   │   ├── reviewer.py     # 검토 에이전트
│   │   │   └── wiki_agent.py   # 위키 에이전트
│   │   └── core/
│   │       ├── orchestrator.py # 오케스트레이터
│   │       ├── bootstrap.py    # 부팅 시퀀스
│   │       └── conductor.py    # 지휘자
│   ├── requirements.txt        # Python 의존성
│   ├── .env                    # 환경 변수
│   └── startup_sync/
│       └── mobile_bridge.ts    # 모바일 브릿지 ✨ NEW
├── frontend/                   # React 프론트엔드
│   ├── src/
│   │   ├── pages/App.tsx       # 메인 UI
│   │   ├── components/         # UI 컴포넌트
│   │   └── lib/api.ts          # API 클라이언트
│   ├── package.json
│   └── dist/                   # 빌드 결과 (프로덕션)
├── docs/
│   ├── MOBILE_INTEGRATION.md   # 모바일 연동 가이드 ✨ NEW
│   └── ...
├── JARVIS.bat                  # 🔧 개선됨 - 더 안정적인 실행 스크립트
├── SETUP.bat                   # ✨ NEW - 초기 설정 스크립트
├── jarvis_cli.py               # CLI 버전
└── AX_Vault/                   # 데이터 저장소
    ├── 00_Raw/
    ├── 01_Rules/
    ├── 02_Knowledge/
    ├── 03_Retrospective/
    └── 04_Audit/
```

---

## ⚙️ 환경 설정

### .env 파일

`backend/.env` 에 다음 설정:

```env
# 애플리케이션
APP_NAME=Jarvis Agent Office vNext
APP_ENV=local
APP_SHARED_KEY=AIN_PAPA_SHARED_KEY

# LLM 모델 설정
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_CHAT_PATH=/api/chat
JARVIS_MODEL=JARVIS           # Ollama 모델명
GPT_OSS_MODEL=gpt-oss:20b     # 대체 모델
QWEN_MODEL=qwen2.5-coder:14b  # Qwen 모델

# 데이터베이스
SQLITE_PATH=../data/jarvis.db
```

### 필수 설치 사항

```bash
# Python 3.9+
python --version

# 가상환경 생성 (한 번만)
python -m venv .venv

# 가상환경 활성화 (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# 또는 (Command Prompt)
.venv\Scripts\activate.bat

# 의존성 설치
pip install -r backend/requirements.txt

# 프론트엔드 의존성 (옵션, 개발 시)
cd frontend
npm install
npm run build
```

---

## 🎯 주요 기능 사용법

### 1️⃣ 웹 인터페이스에서 대화

**URL**: http://localhost:8000

```
사용자: 자비스, txt 파일을 만들어줄래?
자비스: 파일을 생성하겠습니다. 어느 경로에 생성할까요?
사용자: /data/test.txt로 만들어줘
자비스: 파일을 생성했습니다. 검토해주세요.
[승인 필요]
```

### 2️⃣ CLI에서 대화 (터미널)

```bash
python jarvis_cli.py
```

```
🤖 JARVIS 대화 모드 시작
>> 자비스, 좋은 아침입니다
자비스: 좋은 아침입니다. 오늘 뭐를 도와드릴까요?
>> 
```

### 3️⃣ 모바일 앱에서 접속

```javascript
// React Native / Flutter
const response = await fetch('http://SERVER_IP:8000/api/mobile/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'x-shared-key': 'AIN_PAPA_SHARED_KEY'
  },
  body: JSON.stringify({
    message: '자비스, 좋은 아침입니다',
    mode: 'chat'
  })
})
```

---

## 🔌 API 엔드포인트

### 기본 엔드포인트

```
기본 URL: http://localhost:8000/api
공유 키 헤더: x-shared-key: AIN_PAPA_SHARED_KEY
```

### 사용 가능한 API

| 엔드포인트 | 메서드 | 설명 |
|-----------|--------|------|
| `/health` | GET | 서버 상태 확인 |
| `/jarvis/chat` | POST | 채팅 메시지 전송 |
| `/tasks` | GET | 작업 목록 |
| `/tasks` | POST | 작업 생성 |
| `/approvals` | GET | 승인 요청 목록 |
| `/approvals/{id}/approve` | POST | 승인 |
| `/approvals/{id}/reject` | POST | 반려 |
| `/mobile/info` | GET | 모바일 정보 |
| `/mobile/chat` | POST | 모바일 채팅 |
| `/mobile/status` | GET | 실시간 상태 |
| `/mobile/sync` | POST | 동기화 |

**상세**: http://localhost:8000/docs 방문

---

## 🔧 문제 해결

### 문제 1: JARVIS.bat 실행 안 됨

**원인**: Python 경로 또는 가상환경 없음

**해결**:
```bash
# 현재 디렉토리 확인
cd /d "C:\Users\ky042\AI\개발\jarvis_agent_office_v1"

# 가상환경 생성
python -m venv .venv

# 다시 SETUP.bat 실행
SETUP.bat
```

### 문제 2: "포트 8000이 이미 사용 중"

**원인**: 다른 프로세스의 포트 사용

**해결**:
```bash
# Windows: 포트 사용 프로세스 종료
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# 또는 다른 포트 사용
uvicorn app.main:app --port 8001
```

### 문제 3: "모듈을 찾을 수 없음" (ImportError)

**원인**: 의존성 미설치

**해결**:
```bash
# 가상환경 활성화
.venv\Scripts\activate

# 의존성 재설치
pip install --upgrade -r backend/requirements.txt
```

### 문제 4: 프론트엔드 반응 없음

**원인**: dist 폴더 없거나 빌드 실패

**해결**:
```bash
cd frontend
npm install
npm run build

cd ..
# JARVIS.bat 다시 실행
```

---

## 📊 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                    모바일 / 웹 클라이언트                      │
│                   (React / React Native)                   │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP(S)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI 서버 (8000)                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  API 라우터                                            │  │
│  │  ├─ /api/health         (헬스 체크)                  │  │
│  │  ├─ /api/jarvis/chat    (채팅)                      │  │
│  │  ├─ /api/tasks          (작업)                      │  │
│  │  ├─ /api/approvals      (승인)                      │  │
│  │  └─ /api/mobile/*       (모바일)  ✨ NEW            │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  JARVIS 오케스트레이터                                │  │
│  │  ├─ Planner     (계획 단계)                         │  │
│  │  ├─ Executor    (실행 단계)                         │  │
│  │  ├─ Reviewer    (검토 단계)                         │  │
│  │  └─ WikiAgent   (지식 통합)                         │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  LLMS (Ollama / API)                                 │  │
│  │  ├─ JARVIS 모델                                      │  │
│  │  ├─ GPT-OSS 모델                                     │  │
│  │  └─ Qwen 모델                                        │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  메모리 & 스토리지                                     │  │
│  │  ├─ SQLite DB (tasks, approvals)                    │  │
│  │  ├─ File System (AX_Vault)                          │  │
│  │  └─ Memory Repository                               │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 📵 모바일 연동 방식 (3가지)

### 방식 1️⃣: 모바일 웹 (가장 간단)

```
모바일 브라우저 → http://PC_IP:8000 → 웹 UI 그대로 사용
```

**장점**: 개발 없음, 즉시 사용 가능  
**단점**: 반응성 최적화 부족

### 방식 2️⃣: 네이티브 모바일 앱 + REST API

```
React Native/Flutter 앱 → REST API (/api/mobile/*) → 백엔드
```

**장점**: 최적화된 UX, 오프라인 지원 가능  
**단점**: 앱 개발 필요

**예시 (React Native)**:
```tsx
const sendMessage = async (message: string) => {
  const res = await fetch(`http://${SERVER_IP}:8000/api/mobile/chat`, {
    method: 'POST',
    headers: { 'x-shared-key': 'AIN_PAPA_SHARED_KEY' },
    body: JSON.stringify({ message, mode: 'chat' })
  })
  return res.json()
}
```

### 방식 3️⃣: 하이브리드 앱 + WebView

```
React Native/Flutter 앱 → WebView → React 웹 UI
```

**공개 리소스**:
- `mobile_bridge.ts` - JavaScript Bridge
- `MOBILE_INTEGRATION.md` - 상세 가이드

**상세**: [docs/MOBILE_INTEGRATION.md](docs/MOBILE_INTEGRATION.md) 참고

---

## 🔐 보안 주의사항

### 개발 환경
```env
APP_ENV=local
APP_SHARED_KEY=AIN_PAPA_SHARED_KEY
```

### 프로덕션 환경
```env
APP_ENV=production
APP_SHARED_KEY=<강력한_랜덤_키>  # 변경 필수!
```

### 권장사항
- ✅ HTTPS 사용 (프로덕션)
- ✅ 방화벽으로 포트 8000 보호
- ✅ 정기적인 보안 업데이트
- ✅ 공유 키 정기 변경

---

## 📚 추가 리소스

- 📖 [모바일 통합 가이드](docs/MOBILE_INTEGRATION.md)
- 📖 [README.md](README.md) - 프로젝트 개요
- 📖 [API 문서](http://localhost:8000/docs) - Swagger UI
- 🐛 [문제 보고](https://github.com/yourrepo/issues)

---

## ✅ 체크리스트

완벽한 설정을 완료했는지 확인하세요:

- [ ] Python 3.9+ 설치됨
- [ ] 가상환경 생성 및 활성화 완료
- [ ] SETUP.bat 실행 완료
- [ ] `backend/.env` 파일 확인
- [ ] JARVIS.bat 실행 가능
- [ ] http://localhost:8000 접속 성공
- [ ] 채팅 메시지 전송 테스트 완료
- [ ] API 문서 (http://localhost:8000/docs) 확인
- [ ] 모바일 앱 개발 시작 (선택사항)

---

## 🎉 축하합니다!

JARVIS v5 설정이 완료되었습니다! 🚀

이제 다음을 할 수 있습니다:
- 🤖 자비스와 대화하기
- 📋 작업 자동 생성 및 관리
- ✅ 승인 워크플로우 실행
- 📱 모바일 앱 연동

**다음 단계**:
1. 웹 UI에서 자비스와 대화해보기
2. 모바일 앱 개발 계획
3. LLM 모델 통합 및 최적화
4. 프로덕션 배포 준비

---

**문의**: support@jarvis.ai  
**마지막 업데이트**: 2026-04-17
