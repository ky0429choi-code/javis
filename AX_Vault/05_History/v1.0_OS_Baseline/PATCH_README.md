# JARVIS v5 Rebuild Patch

## 📋 주요 변경사항 요약

### 종적 기반 신뢰도 시스템 (2026-04-19)
- ✅ **파이프라인 신뢰도 수치화**: 각 단계(Planner/Executor/Reviewer/Wiki) 0.0~1.0 자동 점수화
- ✅ **종적 추적 (EMA)**: SQLite 시계열 누적 + 지수이동평균 트렌드 분석
- ✅ **동적 프로바이더 라우팅**: 실측 신뢰도 기반 우선순위 자동 결정
- ✅ **완료보고서 자동 생성**: JSON + Markdown → AX_Vault/04_Audit/ 저장
- ✅ **이상탐지**: 2σ 기반 신뢰도 급락 경고
- ✅ **REST API 8개**: `/api/confidence/*` 엔드포인트
- ✅ **테스트 4/4 PASS** (스키마/DB/수집기/보고서)

| 파일 | 유형 | 상세 |
|---|---|---|
| `backend/app/schemas/confidence.py` | 신규 | Pydantic 신뢰도 모델 (StepConfidence, CompletionReport 등) |
| `backend/app/core/confidence_collector.py` | 신규 | EMA 수집기, 이상탐지, 동적 라우팅 |
| `backend/app/core/completion_reporter.py` | 신규 | 완료보고서 생성기 (일일/주간 포함) |
| `backend/app/api/routers/confidence.py` | 신규 | REST API 엔드포인트 |
| `backend/app/core/conductor.py` | 수정 | 파이프라인 신뢰도 계측 삽입 |
| `backend/app/llm/router.py` | 수정 | 종적 신뢰도 기반 동적 라우팅 |
| `backend/app/memory/repository.py` | 수정 | confidence_log + completion_reports 테이블 |
| `backend/app/main.py` | 수정 | 신뢰도 API 라우터 등록 |

### Red Team 피드백 반영 (2026-04-18)
- ✅ **무료 한도 과신 제거**: API 한도 명확화 (∞ 무료 → Rate Limited)
- ✅ **캐시 일관성 버그 수정**: 버전 추적 추가 (versioned keys)
- ✅ **민감 데이터 보안 추가**: 클라우드 전송 전 필터링
- ✅ **배치 API SLA 명확화**: 실시간 vs 배치 분리

### 반영된 파일
| 파일 | Red Team 수정 | 상세 |
|---|---|---|
| `HYBRID_RESOURCE_STRATEGY.md` | API 테이블 정정 | "∞ 무료" 제거, Rate Limit 명확화 |
| `HYBRID_REALITY_CHECK.md` | 새로 생성 | 4가지 심각 결함 모두 해결 with 코드 |
| `backend/app/llm_router_v2.py` | DataSensitivityFilter 추가 | 민감 정보 자동 감지 + 로컬만 사용 |
| `backend/app/llm_router/smart_router.py` | 민감 데이터 필터링 + 버전 추가 | Safe routing + cache coherence |

---

## ⚠️ 이전 문제점과 해결책

### 1️⃣ 무료 한도 과신
**문제:** "∞ 무료 API로 운영 가능"
**해결:** [HYBRID_REALITY_CHECK.md](./HYBRID_REALITY_CHECK.md#1️⃣-무료-한도-과신-가장-위험) 참조
- Groq: Rate Limited (~30k tokens/min)
- HuggingFace: Queue-based (지연 가능)
- **권장:** Claude API + 명시 예산

### 2️⃣ 캐시 일관성 버그
**문제:** Redis 만료 → SQLite 구버전 반환 (모델 업그레이드 무시)
**해결:** Versioned keys 도입
```python
# 이전: key = "llm_response:{query}"
# 현재: key = "llm_response:{query}:v{model_version}"
```
**코드 위치:** [smart_router.py 라인 343-360](./backend/app/llm_router/smart_router.py#L343-L360)

### 3️⃣ 민감 데이터 유출
**문제:** 내부 정보 (연봉, 고객사, 계약)를 외부 API로 전송
**해결:** 자동 필터링 추가
```python
# 감지되는 키워드: "연봉", "조직도", "고객정보", "계약", etc.
# 정책: 민감 정보 감지 시 로컬 Ollama만 사용 (절대 클라우드 전송 금지)
```
**코드 위치:** [smart_router.py 라인 15-40](./backend/app/llm_router/smart_router.py#L15-L40) 및 [llm_router_v2.py 라인 15-40](./backend/app/llm_router_v2.py#L15-L40)

### 4️⃣ 배치 API SLA 모순
**문제:** 실시간 (100 req/sec) + Batch API (1-24시간)를 동시에 지원 불가
**해결:** task_type별로 분리
- `task_type="simple"`: 실시간 (0.2-3초)
- `task_type="complex"`: 저비용 (1-5초)
- `task_type="bulk"`: 배치 전용 (1-24시간, 이메일 결과)

---

## 수정된 파일 목록 (구 버전)

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
pip install fastapi uvicorn httpx python-dotenv redis  # ← redis 추가 (일반 계층만)
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

**일반 쿼리 (안전):**
```bash
curl -X POST http://127.0.0.1:8000/api/jarvis/chat \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"오늘 날씨 알아봐줘\"}"
```

**민감 쿼리 (필터링 테스트):**
```bash
# 이 쿼리는 자동으로 로컬 Ollama만 사용됨
curl -X POST http://127.0.0.1:8000/api/jarvis/chat \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"우리 회사 직원 연봉 정보를 분석해줘\"}"
# → 응답: "🚨 민감 정보 감지 → 로컬만 처리"
```

---

## 🔒 보안 체크리스트

- [ ] 민감 키워드 필터링 활성화 확인 (연봉, 조직도, 고객정보, etc.)
- [ ] Groq/HF API 키가 `.env`에만 저장되었는지 확인
- [ ] Redis 비밀번호가 설정되었는지 확인 (운영 환경)
- [ ] 클라우드 API 호출률 모니터링 설정 (과도한 비용 방지)
- [ ] 월 예산 제한 설정 (MONTHLY_BUDGET in settings)

---

## 🆕 API 비용 정책 변동 대응 (2026-04-18)

### 새로 추가된 기능

**문제: "API 비용이 언제든 올라갈 수 있다"**

**해결책:**
1. ✅ [동적 API 라우터](./backend/app/core/dynamic_api_router.py) 생성
   - 공식 무료/저비용 API만 조합
   - 웹 자동화 완전 거부 (안정성)
   - 자동 페일오버 (한 곳 실패 시 다음 API)

2. ✅ [API 정책 모니터링](./API_PRICING_RESILIENCE.md) 시스템
   - 매일 04:00에 각 API 상태 확인
   - 정책 변경 감지 시 즉시 알림
   - 비용 추적 및 예산 오버 방지

3. ✅ [HYBRID_RESOURCE_STRATEGY.md](./HYBRID_RESOURCE_STRATEGY.md) 업데이트
   - 웹 자동화 제거 (약관 위반)
   - 공식 API만 사용 (합법적)
   - 동적 라우팅 전략 설명

### 파일 변경 내역

| 파일 | 변경 사항 |
|------|---------|
| `backend/app/core/dynamic_api_router.py` | 새로 생성 - 공식 API 동적 라우팅 |
| `API_PRICING_RESILIENCE.md` | 새로 생성 - 정책 변동 대응 전략 |
| `HYBRID_RESOURCE_STRATEGY.md` | 웹 자동화 제거, 공식 API 중심으로 수정 |

### 사용 예시

```python
# 1. 동적 라우터 초기화
from backend.app.core.dynamic_api_router import get_dynamic_router

router = await get_dynamic_router()

# 2. 쿼리 라우팅 (자동 페일오버)
result = await router.route(
    query="Python으로 웹 크롤러 만들어줘",
    system_prompt="당신은 프로그래밍 전문가입니다"
)

# 3. 결과
# {
#   "ok": True,
#   "response": "...",
#   "provider": "ollama",  # 또는 groq, claude 등
#   "cost": 0.0,
#   "time_ms": 245,
#   "retry_count": 1
# }

# 4. 정책 모니터링 (별도 프로세스)
# 매일 04:00에 자동 실행:
# - Groq Rate Limit 확인
# - Claude 가격 확인
# - HuggingFace 정책 확인
# → 변경 시 관리자에게 알림
```

---

## 📊 성능 기댓값 (현실적)

### Tier 0: 로컬만 (Ollama + SQLite)
- 응답: 0.2-0.5초
- 비용: ₩0/월
- 유지기간: 1-2개월 (메모리 여유에 따라)

### Tier 1: 로컬 + Groq + Claude
- 응답: 
  - 캐시 히트: 0.01초
  - 로컬: 0.2초
  - Claude: 1-2초
  - Groq (rate limited): 2-5초
- 비용: ₩5,000-50,000/월
- 설정: `HYBRID_MODE=true`

### Tier 2: +Redis (선택사항)
- 캐시 히트 개선: 1h TTL (vs 30days SQLite)
- 추가 비용: EC2 t3.nano (~₩10,000/월)

---

## 🚀 구현 계획

### Phase 1: 동적 라우터 통합 (1일)
```bash
# 1. API 키 설정
export GROQ_API_KEY="..."
export CLAUDE_API_KEY="..."
export HUGGINGFACE_API_KEY="..."

# 2. 라우터 활성화
# backend/app/main.py에 추가:
from app.core.dynamic_api_router import get_dynamic_router
router = await get_dynamic_router()

# 3. 정책 모니터링 스케줄러 활성화
# cron: 매일 04:00
scheduler.add_job(router.monitor_policies, 'cron', hour=4)
```

### Phase 2: 비용 추적 활성화 (1일)
```bash
# 1. 월 예산 설정 (settings.py)
MONTHLY_BUDGET = 50.0  # $50/month

# 2. 비용 DB 마이그레이션
alembic upgrade head

# 3. 대시보드 활성화
# /api/dashboard/costs → 비용 추적
```

### Phase 3: 모니터링 알림 설정 (1일)
```bash
# Slack webhook 설정
SLACK_WEBHOOK="https://hooks.slack.com/..."

# Email 설정
ADMIN_EMAIL="admin@example.com"
SMTP_PASSWORD="..."

# 알림 테스트
python -m backend.app.core.dynamic_api_router test_alerts
```

### Phase 4: 검증 및 테스트 (2-3일)
```bash
# 1. 각 API 테스트
pytest backend/tests/test_dynamic_router.py -v

# 2. 페일오버 테스트
pytest backend/tests/test_fallback.py -v

# 3. 비용 추적 테스트
pytest backend/tests/test_cost_tracking.py -v

# 4. 모니터링 테스트
pytest backend/tests/test_monitoring.py -v
```

**소요 시간: 5-7일**

---

## ⚠️ 금지 사항 (법적/기술적)

### 절대 금지
```
❌ ChatGPT 웹 자동화 (Selenium/Playwright)
   → 약관 위반, 24시간 내 계정 정지
   → 기술적 대안: Groq/Claude API

❌ Claude 무료 웹 자동화
   → 자동 탐지 및 차단
   → 기술적 대안: Claude API

❌ Gemini 웹 자동화
   → IP 차단
   → 기술적 대안: Google Vertex AI (유료)

❌ 공식 API 문서 무시
   → Rate limit 무시, 계정 정지
   → 대안: 공식 한도 준수, 페일오버
```

---

## 운영 팁

1. **첫 주**: Tier 0만 운영, 캐시 히트율 모니터링
2. **1주 후**: Tier 1 활성화 (Groq 추가, 예산 추적)
3. **1개월 후**: 비용 추세 분석 후 Claude 추가 검토
4. **지속**: 
   - 매일 정책 모니터링 확인
   - 주일 API 헬스체크 (수동)
   - 월말 비용 검토

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
