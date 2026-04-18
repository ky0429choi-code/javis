# JARVIS v5 Rebuild Patch

## 수정된 파일 목록

| 파일 | 수정 내용 |
|---|---|
| `core/planner.py` | Orchestrator 계약 일치 (steps 반환 보장), JSON 파싱 + fallback |
| `core/orchestrator.py` | Plan.steps 기반 실행, 위상 정렬, retry/skip 정책 |
| `core/llm_router.py` | model_key→모델명 매핑, /api/chat, 순차 lock, 재시도 강화 |
| `core/bootstrap.py` | /api/tags 헬스체크, degraded mode, ollama 자동 시작 |
| `core/hooks.py` | WARN/SOFT/STRICT 3단계 완화 전략 |
| `core/tool_registry.py` | Tool 등록/조회 레지스트리 |
| `api/main.py` | FastAPI 앱, /api/health, /api/jarvis/chat |
| `start_jarvis.bat` | 부트 순서 재구성 (Ollama 선행 → backend) |
| `.env.example` | 환경변수 템플릿 |

---

## 적용 방법

### 1. .env 설정
```
cp .env.example .env
# .env를 열고 실제 Ollama 모델명 확인
ollama list
```

### 2. 의존성 설치
```
python -m venv .venv
.venv\Scripts\activate
pip install fastapi uvicorn httpx python-dotenv
```

### 3. 실행
```
start_jarvis.bat
```

### 4. 헬스 확인
```
curl http://127.0.0.1:8000/api/health
```

### 5. 채팅 테스트
```
curl -X POST http://127.0.0.1:8000/api/jarvis/chat \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"오늘 날씨 알아봐줘\"}"
```

---

## 주요 변경 설명

### Planner ↔ Orchestrator 계약
- 기존: Planner가 `steps` 없이 반환 → Orchestrator KeyError
- 수정: Planner는 항상 `Plan(goal, steps)` 반환, 실패 시 `fallback_plan` 생성

### LLM 모델 라우팅
- `.env`의 `JARVIS_MODEL`, `PLANNER_MODEL` 등을 LLMRouter가 자동 매핑
- 설치 안된 모델 → 경고 후 첫 번째 available 모델로 대체

### Hook 모드 전환
- `HOOK_MODE=WARN` (기본): 로그만
- `HOOK_MODE=SOFT`: 응답에 warnings 배열 추가
- `HOOK_MODE=STRICT`: 위반 즉시 차단 (HTTP 500)

### 부트스트랩 안정화
- `/api/tags` 엔드포인트로 Ollama 헬스체크
- 모델 미존재 → 경고만, 부팅 계속
- Ollama 미실행 → `ollama serve` subprocess 자동 시작 시도
