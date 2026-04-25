# JARVIS 시간 설정 조정 가이드

## 📅 현재 상태
- 현재 시스템 시간: 2026년 4월 19일
- JARVIS가 사용하는 시간: Python `datetime.now()` (시스템 시간 기준)
- 타임존: 기본값 (시스템 기본 타임존)

---

## 🔧 시간 조정 방법 (3가지)

### 방법 1: Windows 시스템 시간 조정 (근본적인 방법)

**파워셀에서 실행:**
```powershell
# 현재 시간 확인
Get-Date

# 시간 설정 예시 (2024년 5월 16일 18:35:00)
$NewTime = Get-Date -Year 2024 -Month 5 -Day 16 -Hour 18 -Minute 35 -Second 0
Set-Date -Date $NewTime

# 다시 현재 시간으로 복원 (2026년 4월 19일 10:44)
$NewTime = Get-Date -Year 2026 -Month 4 -Day 19 -Hour 10 -Minute 44 -Second 0
Set-Date -Date $NewTime
```

**주의**: 관리자 권한 필요

---

### 방법 2: 환경 변수로 타임존 설정 (권장)

**파워셀에서 실행 (임시):**
```powershell
# 한국 표준시 설정
$env:TZ = "Asia/Seoul"

# 또는 UTC+9 (한국)
$env:TZ = "Etc/GMT-9"

# JARVIS 실행
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

**영구 설정 (Windows 환경 변수):**
1. `Win + X` → "시스템" 선택
2. "고급 시스템 설정" → "환경 변수"
3. 새 환경 변수 생성:
   - 변수 이름: `TZ`
   - 변수 값: `Asia/Seoul`
4. 컴퓨터 재시작

---

### 방법 3: JARVIS .env 파일에서 설정 (가장 권장)

**파일 생성: `backend/.env`**
```
# 타임존 설정
TIMEZONE=Asia/Seoul
VERBOSE=true

# 또는 UTC 기반
# TIMEZONE=UTC
```

**Python 코드 수정: `backend/app/utils/settings.py`**

현재 코드:
```python
# (기존 코드)
```

수정할 코드:
```python
import os
from datetime import datetime, timezone
import pytz

# .env에서 TIMEZONE 읽기
TIMEZONE_STR = os.getenv("TIMEZONE", "Asia/Seoul")
TIMEZONE = pytz.timezone(TIMEZONE_STR)

def get_current_time_formatted():
    """JARVIS가 사용할 현재 시간 (타임존 적용)"""
    tz = pytz.timezone(TIMEZONE_STR)
    return datetime.now(tz).strftime("%Y년 %m월 %d일 %H시 %M분")

def get_current_datetime(timezone_name: str = None):
    """타임존과 함께 현재 시간 반환"""
    tz = pytz.timezone(timezone_name or TIMEZONE_STR)
    return datetime.now(tz)
```

**백엔드 health 라우터 수정: `backend/app/api/routers/health.py`**

```python
from fastapi import APIRouter
from datetime import datetime
import os
import pytz

router = APIRouter(tags=["health"])

def get_jarvis_time():
    """JARVIS의 현재 시간 반환"""
    timezone_str = os.getenv("TIMEZONE", "Asia/Seoul")
    tz = pytz.timezone(timezone_str)
    now = datetime.now(tz)
    return now.strftime("%Y년 %m월 %d일 %H시 %M분 %S초")

@router.get("/health")
def health() -> dict:
    return {
        "ok": True,
        "service": "jarvis-agent-office-vnext",
        "timestamp": get_jarvis_time(),
        "timezone": os.getenv("TIMEZONE", "Asia/Seoul")
    }
```

---

## 🎯 적용 단계

### Step 1: .env 파일 생성
```bash
cd backend
echo "TIMEZONE=Asia/Seoul" > .env
```

### Step 2: requirements.txt에 pytz 추가 (필요 시)
```bash
pip install pytz
```

### Step 3: backend 재시작
```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

### Step 4: 시간 확인
```bash
curl http://localhost:8000/api/health
```

---

## ⏰ 타임존 옵션

| 지역 | 값 | 설명 |
|------|-----|------|
| 한국 | `Asia/Seoul` | UTC+9 (권장) |
| 일본 | `Asia/Tokyo` | UTC+9 |
| 중국 | `Asia/Shanghai` | UTC+8 |
| 미국 동부 | `America/New_York` | UTC-5/-4 |
| 미국 서부 | `America/Los_Angeles` | UTC-8/-7 |
| UTC | `UTC` | 표준시 |

---

## 🔄 JARVIS에서 시간 표시 (협력 시뮬레이션)

사용자: "자비스, 지금 몇 시야?"

```
JARVIS 응답:
- Intent Engine: "시간 정보 요청" (low-risk)
- Planning Engine: "현재 시간 반환"
- Routing Engine: "Gemma Brain (일상 대화)"
- Execution: 
  ```python
  # backend/app/llm_router.py에서
  current_time = get_jarvis_time()  # "2026년 4월 19일 10시 44분 30초"
  response = f"지금은 {current_time}이에요."
  ```
- Reflection: "시간 정보 정확하게 제공됨 ✓"
- Audit: 요청-응답 기록 저장
```

---

## ✅ 연쇄 조정 체크리스트

```
[ ] 1. Windows 시스템 시간 확인 (Get-Date)
[ ] 2. backend/.env 파일 생성 (TIMEZONE 설정)
[ ] 3. health.py 라우터 업데이트
[ ] 4. pytz 라이브러리 설치 확인
[ ] 5. 백엔드 재시작
[ ] 6. http://localhost:8000/api/health 확인
[ ] 7. JARVIS UI에서 시간 표시 확인
```

---

## 🆘 트러블슈팅

**문제**: 시간이 여전히 잘못됨
```
해결책:
1. 시스템 시간 확인: Get-Date
2. 타임존 확인: tzutil /g
3. 백엔드 로그 확인: python -m uvicorn app.main:app --log-level debug
```

**문제**: pytz not found
```
해결책:
pip install pytz
또는:
pip install -r backend/requirements.txt
```

**문제**: .env 파일이 인식 안 됨
```
해결책:
python-dotenv 설치: pip install python-dotenv
또는 os.getenv()로 직접 읽기
```
