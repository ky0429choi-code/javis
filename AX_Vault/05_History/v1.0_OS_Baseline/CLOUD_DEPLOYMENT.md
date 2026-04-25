# JARVIS 클라우드 배포 가이드 (외부 접속 활성화)

## 📌 개요

현재 JARVIS는 로컬 (127.0.0.1:8000) 에서만 접근 가능합니다.  
이 문서는 **외부에서도 접근 가능하게 배포하는 방법**을 설명합니다.

---

## 방식 비교

| 방식 | 난이도 | 비용 | 속도 | 추천 |
|------|--------|------|------|------|
| **Ngrok** (임시) | ⭐ | 무료 | 즉시 | 테스트/데모 |
| **Railway** | ⭐⭐ | 무료 | 10분 | 초보자 |
| **Render** | ⭐⭐ | 무료 | 10분 | 초보자 |
| **Docker + AWS** | ⭐⭐⭐ | 월 $20 | 30분 | 중급자 |
| **Heroku** | ⭐⭐ | 유료($7+) | 10분 | 불추천 (유료) |

---

## 1️⃣ 빠른 테스트: Ngrok (5분)

외부에서 한 번 테스트해보고 싶다면:

### 1.1 Ngrok 설치
```bash
# 다운로드: https://ngrok.com/download
# 또는 Windows 패키지 매니저
choco install ngrok

# 또는 직접 실행
```

### 1.2 Ngrok 연결
```powershell
# JARVIS 백엔드 실행 후 ...

# NEW 터미널에서
ngrok http 8000

# 결과:
# Session Status                online
# Account                       your@email.com (Plan: Free)
# Version                       3.3.5
# Region                        us (United States)
# Forwarding                    https://random-id.ngrok.io -> http://localhost:8000
```

### 1.3 외부에서 접속
```bash
# 어디서든 접속 가능
curl https://random-id.ngrok.io/api/health

# 또는 브라우저
https://random-id.ngrok.io/docs
```

**주의**: 
- ✅ 테스트/데모용
- ❌ 장기 운영용 아님 (세션 재시작 시 URL 변경)
- ❌ 무료 플랜은 시간 제한 있음

---

## 2️⃣ **권장**: Railway 배포 (10분, 무료)

### 2.1 사전 준비
- GitHub 계정
- JARVIS 프로젝트를 GitHub에 올림 (upstream 설정됨)
- Railway 계정

### 2.2 Railway 계정 생성
1. https://railway.app 접속
2. **Sign Up** → GitHub 로그인
3. 계정 생성 완료

### 2.3 새 프로젝트 생성

#### Option A: GitHub 저장소 연결 (권장)
1. Railway Dashboard 에서 **New Project** 클릭
2. **Deploy from GitHub repo** 선택
3. 저장소 선택: `jarvis-agent-office`
4. **Deploy** 클릭

#### Option B: 템플릿 사용
1. **New Project** → **Template** → Python
2. 커스터마이징

### 2.4 환경 변수 설정

Railway Dashboard → Variables 탭:
```
PORT=8000
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=jarvis
DATABASE_URL=sqlite:///jarvis.db
LOG_LEVEL=INFO
```

⚠️ **주의**: Ollama는 로컬 모델이므로 배포 서버에도 설치 필요 (다음 섹션 참고)

### 2.5 배포 완료

1. 배포 상태: Railway Dashboard 에서 확인
2. 공개 URL: `https://jarvis-xxxx.railway.app`
3. 외부 접속: `https://jarvis-xxxx.railway.app/api/health`

#### 도메인 연결 (선택사항)
1. Settings → Domains
2. Custom Domain 추가
3. DNS 설정 (3-24시간 소요)

---

## 3️⃣ Docker 이미지 빌드 (배포용)

클라우드에 배포하려면 Docker 이미지 필요:

### 3.1 Dockerfile 생성

```dockerfile
# backend/Dockerfile
FROM python:3.10-slim

WORKDIR /app

# 의존성 설치
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드
COPY backend/ .

# 포트 설정
EXPOSE 8000

# 시작 명령어
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 3.2 .dockerignore 생성

```
.venv/
__pycache__/
*.pyc
.git/
.gitignore
*.db
*.sqlite
.env
.DS_Store
```

### 3.3 로컬에서 테스트

```bash
# Docker 빌드
docker build -f backend/Dockerfile -t jarvis-backend:latest .

# 실행 테스트
docker run -p 8000:8000 \
  -e OLLAMA_HOST=http://localhost:11434 \
  jarvis-backend:latest

# 확인
curl http://localhost:8000/api/health
```

---

## 4️⃣ AWS EC2 배포 (중급, 월 ~$20)

### 4.1 EC2 인스턴스 생성
1. AWS 콘솔 → EC2 → Instances → Launch
2. **AMI**: Ubuntu 20.04 LTS
3. **Type**: t3.micro (프리티어) 또는 t3.small
4. **Storage**: 30GB
5. **Security Group**: 80, 443, 8000 포트 개방

### 4.2 서버 설정

```bash
# SSH로 접속
ssh -i key.pem ubuntu@your-ec2-ip

# 시스템 업데이트
sudo apt update && sudo apt upgrade -y

# Docker 설치
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Docker Compose 설치
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# JARVIS 클론
git clone https://github.com/YOUR_USERNAME/jarvis-agent-office.git
cd jarvis-agent-office
```

### 4.3 Docker Compose로 시작

**docker-compose.yml** 생성:
```yaml
version: '3.8'
services:
  backend:
    build:
      context: .
      dockerfile: backend/Dockerfile
    ports:
      - "8000:8000"
    environment:
      - OLLAMA_HOST=http://ollama:11434
      - OLLAMA_MODEL=jarvis
      - PORT=8000
    depends_on:
      - ollama
  
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    command: serve

volumes:
  ollama_data:
```

### 4.4 실행

```bash
# 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f backend

# 외부 접속
https://your-ec2-ip:8000/api/health
```

---

## 5️⃣ Render 배포 (무료, 권장)

### 5.1 계정 생성
https://render.com → GitHub 연결

### 5.2 New Web Service
1. **New +** → **Web Service**
2. GitHub 저장소 선택
3. 설정:
   - **Name**: jarvis-backend
   - **Environment**: Docker
   - **Region**: Recommended
   - **Plan**: Free

### 5.3 환경 변수
```
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=jarvis
DATABASE_URL=sqlite:///jarvis.db
```

### 5.4 배포
자동 배포 시작 → 공개 URL 할당

---

## 6️⃣ 보안 설정 (필수)

### 6.1 API 인증

**Backend 수정** (backend/app/api/deps.py):

```python
from fastapi import Header, HTTPException

# 현재: 간단한 키 검증
API_KEY = os.getenv("API_KEY", "AIN_PAPA_SHARED_KEY")

async def verify_shared_key(x_shared_key: str = Header(...)):
    if x_shared_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return x_shared_key

# 향후: JWT 토큰
```

### 6.2 HTTPS 설정

```python
# backend/app/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # 특정 도메인만
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

### 6.3 환경 변수 관리

```bash
# .env.production (배포 서버에서)
API_KEY=strong_random_key_12345
DATABASE_URL=postgresql://user:pass@host:5432/jarvis_db
OLLAMA_HOST=http://localhost:11434
LOG_LEVEL=WARNING
DEBUG=False
```

---

## 7️⃣ 모니터링 & 로깅

### 7.1 로그 수집

```python
# backend/app/main.py
import logging
from loguru import logger

# Loguru 설정
logger.add(
    "logs/jarvis_{time}.log",
    rotation="500 MB",
    retention="7 days",
    level="INFO"
)
```

### 7.2 성능 모니터링

```bash
# Railway/Render vs 로컬 비교
# Railway 대시보드에서 CPU, Memory, Network 확인
```

---

## 8️⃣ 문제 해결

### 포트 이미 사용 중
```bash
# Railway/Render: 자동으로 PORT 환경변수 설정
# EC2: 8000 포트 개방 확인
```

### Ollama 연결 실패
```bash
# 배포 서버에도 Ollama 설치 필요
docker run -d -p 11434:11434 ollama/ollama:latest
```

### 느린 응답
- GPU 활성화 (AWS: g4dn 인스턴스)
- 모델 크기 축소 (JARVIS → llama2)
- 캐싱 추가 (Redis)

---

## 9️⃣ 추천 흐름도

```
개발 (로컬)
    ↓
GitHub 푸시
    ↓
Ngrok 테스트 (5분)
    ↓
Railway 배포 (10분) ← 무료, 추천
    ↓ (또는)
Docker + AWS EC2
    ↓
도메인 연결 (yourdomain.com)
    ↓
모니터링 설정
    ↓
✅ 프로덕션 런칭
```

---

## 🔟 체크리스트

- [ ] Docker 이미지 빌드 & 테스트
- [ ] Railway/Render 계정 생성
- [ ] 저장소 연결 및 배포
- [ ] 환경변수 설정
- [ ] 외부 접속 테스트
- [ ] API 인증 설정
- [ ] 도메인 연결 (선택사항)
- [ ] 모니터링/로깅 설정
- [ ] CI/CD 자동배포 설정

---

## 문의 & 지원

- Railway 문서: https://railway.app/docs
- Render 문서: https://docs.render.com
- AWS 시작 가이드: https://aws.amazon.com/getting-started

---

**문서 작성일**: 2026-04-18  
**버전**: Cloud Deployment v1.0
