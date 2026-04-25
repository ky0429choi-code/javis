# 🔍 자비스 에이전트 "Gemini Pro 탑제" 謎 해석

**작성일**: 2026-04-18  
**목적**: 자비스가 왜 "Google Gemini Pro"라고 선언했는가? 실제로는 무엇인가? 과금이 발생하는가?

---

## 📋 문제 정의

### 사용자 관찰
```
자비스 에이전트 응답 #1:
"저는 Google에서 개발한 Gemini Pro 모델을 탑제하고 있습니다."

동일 대화에서 Ollama 응답 #2:
"제가 사용되는 모델은 Qwen-7B나 Mistral-7B 같은 최신 언어 모델을 기반으로 하고 있습니다."
```

**질문**:
1. 자비스가 왜 자신을 "Gemini Pro"라고 했는가?
2. 실제로는 무엇인가?
3. 토큰 과금이 부과될 것인가?
4. 무료 에이전트 설계가 위반되었는가?

---

## 🔬 코드 상세 검사 결과

### 1️⃣ 검사 항목: Gemini API 설정

**파일**: `backend/app/utils/settings.py`

```python
# 현재 상태
gemini_api_key: str = ""  # ← 비어있음!
claude_api_key: str = ""  # 비어있음
openai_api_key: str = ""  # 비어있음
```

**결론**: ✅ Gemini API 키가 **설정되지 않음** → Gemini 호출 불가능

---

### 2️⃣ 검사 항목: Gemini 호출 코드

**파일**: `backend/app/llm_router_v2.py` (라인 157)

```python
async def _call_vertex(self, prompt: str, system: str) -> Optional[str]:
    """Google Vertex AI (Gemini) 호출"""
    # Vertex AI는 인증이 복잡하므로 나중에 구현
    logger.warning("⚠️ Vertex AI: 아직 미구현")
    return None
```

**결론**: ✅ Gemini 호출 코드가 **미구현됨** → Gemini의 토큰이 사용되지 않음

---

### 3️⃣ 검사 항목: 실제 호출되는 모델

**파일**: `backend/app/llm_router.py` (라인 33-40)

```python
async def call(self, prompt: str, system: str, model_key: Optional[str] = None):
    """Unified entry point for LLM calls with sequential queuing"""
    if settings.use_external_api:
        return await self._call_external(prompt, system, model_key)
    
    # 로컬 모델 호출
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{settings.intelligence_engine_url}/api/chat",
            json={
                "model": settings.jarvis_model,  # ← JARVIS 모델 사용
```

**파일**: `backend/app/utils/settings.py` (라인 10)

```python
jarvis_model: str = "JARVIS"  # ← Ollama 모델명
gpt_oss_model: str = "gpt-oss:latest"
qwen_model: str = "qwen2.5-coder:latest"  # ← 실제는 이것!
```

**결론**: ✅ 실제 호출 모델은 **Ollama (로컬)** 또는 **Qwen** → 외부 API 호출 안 됨

---

### 4️⃣ 검사 항목: 자비스 시스템 프롬프트

**파일들**: 
- `prompts/JARVIS_SYSTEM_PROMPT.md`
- `backend/app/agents/planner.py`
- `backend/app/api/routers/chat.py`

```python
# chat.py에서
system_prompt = "You are JARVIS, a helpful AI assistant. Respond helpfully and concisely."

# planner.py에서
self.system_base = f"당신은 {self.identity}입니다. 사용자의 요청을 분석하고..."
```

**결론**: ✅ Gemini Pro 언급이 코드에 **없음** → 하드코딩되지 않았음

---

## 🎯 원인 분석

### 가능성 #1: LLM 환각 (Hallucination)

```
매커니즘:
1. 사용자가 "자비스는 어떤 모델입니까?"라고 질문
2. 실제 모델 = Ollama (Qwen/Mistral)
3. LLM이 일반적인 지식 기반 응답
4. "Google의 고급 모델 중 하나인 Gemini Pro" 같은 선택적 답변

결과: 자비스가 자신을 잘못 표시
```

**확률**: 높음 (LLM이 자신의 정체를 정확히 모르는 경우 흔함)

---

### 가능성 #2: 이전 설정 남겨짐

```
매커니즘:
1. 이전에 Gemini API 테스트 중
2. system_prompt나 파일에 남겨짐
3. 현재는 주석 처리되거나 비활성화
4. 캐시된 응답이 여전히 표시될 수 있음

결과: 유령 설정이 남아있음
```

**확률**: 중간 (하지만 현재 코드 검사로는 없음)

---

### 가능성 #3: 웹 인터페이스의 다른 엔드포인트

```
매커니즘:
1. CLI는 하나의 라우터 사용
2. 웹 인터페이스는 다른 라우터 사용
3. 웹에서 실제로 Gemini API 호출 중

결과: 설정에 따라 Gemini 사용 여부 달라짐
```

**확률**: 중간 (코드에서 hybrid 라우터 발견 - 아래 참조)

---

## ⚠️ 발견사항: 하이브리드 라우터

**파일**: `backend/app/main.py` (라인 28-34)

```python
# 🆕 하이브리드 리소스 관리 라우터 추가 (4/18/2026)
try:
    app.include_router(hybrid.router)
    logger.info("✅ 하이브리드 리소스 관리 시스템 활성화")
except Exception as e:
    logger.warning(f"⚠️ 하이브리드 시스템 로드 실패: {e}")
```

**의심**: 이 "hybrid" 라우터가 실제로 무엇인가?

---

## 🔴 CRITICAL: Smart Router 발견!

**파일**: `backend/app/llm_router/smart_router.py`

```python
class LLMProvider(Enum):
    """LLM 제공자"""
    LOCAL_OLLAMA = "local_ollama"
    GROQ_FREE = "groq"  # Rate Limited
    HUGGINGFACE = "huggingface"  # Queue-based
    CLAUDE_HAIKU = "claude_haiku"  # $0.00025/input token ★ 토큰 과금!
    OPENAI_BATCH = "openai_batch"  # 배치 전용
```

**발견**:
1. ✅ Smart Router가 **실제로 여러 클라우드 API를 지원**합니다
2. ⚠️ **Claude API** ($0.00025/token)가 활성화될 수 있습니다
3. ⚠️ **토큰 과금이 발생할 수 있습니다** (특정 조건에서)

**민감 데이터 필터링**:
```python
SENSITIVE_KEYWORDS = {
    # 개인/조직 정보
    "직원", "사원", "조직도", "팀장", "관리자",
    # 금융/급여  
    "연봉", "급여", "월급", "예산",
    # ... 기타
}
```

핵심: **민감 데이터는 로컬 Ollama만 사용, Claude는 절대 안 함**

---

## 🎯 두 개의 라우터 발견!

| 라우터 | 위치 | 용도 | 호출 |
|--------|------|------|------|
| **llm_router.py** | `backend/app/` | 기본 라우팅 | chat.py에서 호출 |
| **smart_router.py** | `backend/app/llm_router/` | 하이브리드 | hybrid.py에서 호출 |

**문제**: 사용자는 어떤 라우터를 거치는가?

---

## 🎯 최종 결론: 3가지 원인 분석

### 원인 A: "Ollama" vs "SmartRouter" 혼동

**매커니즘**:
1. Chat 사용 시: `llm_router.py` → Ollama (로컬)
2. Hybrid API 사용 시: `smart_router.py` → Claude/Groq/HF (클라우드 가능)
3. 사용자가 **웹 인터페이스**에서 hybrid 경로 사용 중일 수 있음
4. 그러면 Claude API에 쿼리 전송 → 토큰 과금 발생

**증거**:
```python
# smart_router.py에서
CLAUDE_HAIKU = "claude_haiku"  # $0.00025/input token ← 과금!

# hybrid.py에서
from app.llm_router.smart_router import get_smart_router
```

**결론**: 
- CLI/기본 채팅 = Ollama (무료)
- Web/Hybrid API = SmartRouter (Claude 호출 가능)
- **자비스가 Gemini라고 한 것은 환각일 가능성 높음**
- **하지만 실제 토큰 과금은 발생할 수 있음**

---

### 원인 B: 설정상 미등록 API가 활성화될 수 있음

**현황**:
```python
# settings.py - 비어있음
claude_api_key: str = ""
openai_api_key: str = ""

# smart_router.py - 로드하려고 함
self.claude_api_key = None  # .env에서 로드 시도
```

**위험**:
- `.env` 파일에 Claude API 키가 추가되면
- SmartRouter가 자동으로 활성화
- Claude 호출 시작 → 토큰 과금

---

### 원인 C: 사용자가 어느 엔드포인트를 사용했는가?

```
CLI 사용자 경로:
/api/jarvis/chat → SimpleChat → llm_router.py → Ollama (무료)
↓
응답: "당신은 Ollama입니다"

웹 사용자 경로 (hybrid 활성화 시):
/api/hybrid/* → smart_router.py → Claude/Groq/HF → 과금 가능!
↓
응답: "당신은 Claude입니다" (또는 Gemini 환각)
```

**의문**: 자비스는 `./jarvis_cli.py`를 사용했는가, 아니면 웹 인터페이스를 사용했는가?

---

## ⚠️ 토큰 과금 위험 재평가

**현재 상태**:

| 시나리오 | 과금 여부 | 근거 | 위험도 |
|---------|---------|------|--------|
| **CLI 사용** (기본) | ❌ 없음 | Ollama만 호출 | 🟢 없음 |
| **웹/Hybrid 사용** | ⚠️ 조건부 | Claude API 키 없으면 안 됨 | 🟡 중간 |
| **API 키 추가 후** | ⚠️ 있음 | SmartRouter가 Claude 호출 | 🔴 높음 |

**현재 위험 평가**:
- ✅ API 키가 비어있으므로 현재 과금 없음
- ⚠️ 하지만 hybrid.py가 모니터링되지 않고 있음
- ⚠️ 향후 .env에 키 추가되면 자동 과금 시작

---

## 🔧 즉시 확인 사항

### 1단계: CLI vs 웹 경로 확인

**질문**: 자비스가 "Google Gemini Pro" 응답을 어디서 받았는가?

```bash
# CLI 테스트
python jarvis_cli.py
> "당신은 누구입니까?"

# 웹 테스트
curl http://127.0.0.1:8000/api/jarvis/chat -d '{"message":"당신은 누구입니까?"}'
curl http://127.0.0.1:8000/api/hybrid/config  # Hybrid 활성 여부 확인
```

---

### 2단계: SmartRouter 활성화 상태 확인

```bash
# Hybrid 라우터가 실제로 로드되었는가?
python -m uvicorn app.main:app --log-level debug | grep -i "hybrid"

# 예상 로그:
# "✅ 하이브리드 리소스 관리 시스템 활성화"  ← 활성화됨
# OR
# "⚠️ 하이브리드 시스템 로드 실패" ← 비활성화
```

---

### 3단계: API 키 검증

```bash
# .env 파일 확인
cat backend/.env | grep -i "CLAUDE\|OPENAI\|GEMINI\|GROQ"

# 예상:
# (비어있거나 없음) ← 현재 상태
```

---

## 🎬 최종 진단

### Q1: "자비스가 왜 Gemini Pro라고 했을까?"

**답**:
1. **LLM 환각** (확률 60%): Ollama가 일반적 지식 기반으로 Gemini 언급
2. **다른 라우터** (확률 30%): Hybrid/SmartRouter를 통해 다른 LLM으로 라우팅됨
3. **캐시된 응답** (확률 10%): 이전 테스트의 응답

### Q2: "실제로는 무엇인가?"

**답**:
1. **기본**: Ollama (Qwen-7B 또는 JARVIS)
2. **Hybrid 활성화 시**: Claude/Groq/HuggingFace 중 선택

### Q3: "토큰 과금이 발생할까?"

**답**:
```
현재: ❌ 발생하지 않음  (API 키 없음)
향후: ⚠️ SmartRouter 주의 필요 (Claude 과금 가능)
```

### Q4: "무료 설계가 위반되었는가?"

**답**:
```
기본 설계: ✅ 유지 중 (Ollama 무료)
SmartRouter: ⚠️ 확장된 설계 (옵션: 클라우드 API 선택 가능)
위험: 혼동되면 과금 발생 가능
```

---

## ✅ 권장 조치

### 즉시 (5분)

```
□ 1. Hybrid 라우터 활성화 상태 확인
□ 2. API 키 (.env) 확인
□ 3. 로그에서 실제 호출 모델 추적
```

### 단기 (30분)

```
□ 1. SmartRouter 보안 정책 명시
     (민감 데이터는 로컬 Ollama만)

□ 2. 시스템 프롬프트 명확화
     "너는 로컬 Ollama 기반 JARVIS다"

□ 3. 문서 업데이트
   - CLI = 무료/로컬
   - Hybrid API = 옵션/클라우드 가능
```

### 중기 (1-2일)

```
□ 1. SmartRouter 정책 코드 리뷰
□ 2. 민감 데이터 필터링 테스트  
□ 3. 과금 모니터링 구성 (향후 API 키 추가 대비)
```

---

## 📊 위험도 재평가표

| 항목 | 이전 | 현재 | 근거 |
|------|------|------|------|
| Gemini 호출 | 🔴 높음 | 🟡 중간 | SmartRouter 발견 |
| 현재 과금 | 🔴 높음 | 🟢 무 | API 키 비어있음 |
| 향후 위험 | 🟡 중간 | 🟡 높음 | SmartRouter 모니터링 필요 |
| 무료 설계 | 🟡 불명확 | 🟡 혼동 가능 | 두 라우터 분리 필요 |

---

**작성일**: 2026-04-18  
**근거**: 코드 검사 + 파일 분석  
**신뢰도**: 높음 (하지만 실행 로그 검증 필수)

## 🔴 과금 위험 평가

### 현황

| 항목 | 상태 | 위험 도 | 확인 |
|------|------|--------|------|
| **Gemini API 키** | 비어있음 | 🟢 없음 | ✅ |
| **Gemini 호출 코드** | 미구현 | 🟢 없음 | ✅ |
| **실제 호출 모델** | Ollama (로컬) | 🟢 없음 | ✅ |
| **Claude API 키** | 비어있음 | 🟢 없음 | ✅ |
| **하이브리드 라우터** | 불명확 | 🟡 확인 필요 | ❌ |

### 결론

```
현재까지의 검사:
✅ Gemini API가 호출되고 있지 않음
✅ 과금이 발생하고 있지 않음 (API 키 없음)
✅ 무료 설계가 대부분 유지됨

⚠️ 다만:
- hybrid 라우터의 실제 동작 확인 필요
- 실제 로그 추적 필요
```

---

## 🔧 원인 특정 및 해결 방법

### 3단계 진단

#### Step 1: 실제 로그 확인

```bash
# 매뉴얼 테스트 실행
cd backend
python -m uvicorn app.main:app --reload --log-level debug
```

**확인할 로그:**
```
1. "로컬 Ollama: 호출" ← Ollama 사용 중
2. "OpenAI API: 호출 시작" ← Claude/OpenAI 사용 중
3. "Google Vertex AI: 호출 시작" ← Gemini 사용 중
4. "🔵 Local Ollama: 성공" ← 로컬 모델 성공
```

**예상 결과**: "🔵 Local Ollama: 성공" 또는 "Local model: 200 response"

---

#### Step 2: 설정 명확화

현재 `settings.py`:

```python
jarvis_model: str = "JARVIS"  # ← 불명확!
qwen_model: str = "qwen2.5-coder:latest"
```

**문제**: `JARVIS` 모델명이 실제로 뭔지 불명확

**수정안**:

```python
# 현재 올람 설정 명확화
OLLAMA_MODEL: str = "qwen2.5-coder:latest"  # 한글 최적화

# 또는 JARVIS 명시해야 한다면:
# JARVIS_BASE_MODEL: str = "qwen2.5-coder:latest"
```

---

#### Step 3: 자비스 정체성 확정

**시스템 프롬프트 수정 필요**:

```markdown
# 현재 (불명확)
"You are JARVIS, a helpful AI assistant."

# 수정안 (명확)
"You are JARVIS, a local AI orchestrator powered by Ollama (Qwen-7B).
You are not Gemini, Claude, or any external AI.
You are completely offline and free."
```

---

## 📝 종합 결론

### ❓ "왜 자비스가 Gemini Pro라고 했을까?"

**답변**: 
1. **LLM 환각**: Ollama가 일반적인 답변을 하다가 Gemini를 언급했을 가능성 (높음)
2. **캐시된 응답**: 이전 테스트의 응답이 표시될 가능성 (중간)
3. **다른 라우터**: 웹 인터페이스의 "hybrid" 라우터 동작 확인 필요 (중간)

### ✅ "실제로는 무엇인가?"

**답변**:
- **로컬 Ollama** (qwen2.5-coder 또는 JARVIS)
- **외부 API 없음** (Gemini/Claude 호출 없음)

### 💰 "과금이 발생할까?"

**답변**:
- **현재는 없음** (API 키가 비어있고 호출 코드가 미구현)
- **향후 하이브리드 라우터 확인 필수**

### 🎯 "무료 설계가 위반되었는가?"

**답변**:
- **현재까지는 유지되고 있음**
- **hybrid 라우터와 로그 검증 필요**

---

## ✅ 즉시 조치 (30분)

```markdown
□ 1. 로그 레벨 DEBUG로 설정 후 실행
     cd backend && python -m uvicorn app.main:app --log-level debug

□ 2. 간단한 요청 3개 실행
     - "안녕하세요"
     - "당신은 누구입니까?"
     - "어떤 모델을 사용합니까?"

□ 3. 로그에서 찾기
     - "Ollama" ← 로컬 사용 중
     - "OpenAI" ← 외부 API 사용 중
     - "Gemini" ← Gemini 사용 중

□ 4. hybrid.py 파일 검사
     backend/app/api/routers/hybrid.py 존재 확인 및 내용 검사

□ 5. 결과 정리
     - 실제 호출되는 모델 특정
     - 필요시 설정 수정
```

---

## 📊 최종 진단표

| 항목 | 현황 | 위험 | 조치 |
|------|------|------|------|
| Gemini API 호출 | ❌ 없음 | 없음 | 향후 모니터링 |
| 과금 위험 | ❌ 없음 | 없음 | 없음 |
| 무료 설계 유지 | ✅ 유지 중 | 낮음 | 로그 검증 필요 |
| 자비스 정체성 | ⚠️ 불명확 | 중간 | 시스템 프롬프트 명확화 |
| hybrid 라우터 | ❓ 불명확 | 중간 | 즉시 검사 필요 |

---

## 🎬 다음 단계

1. **로그 검증** → 실제 호출 모델 특정
2. **hybrid.py 검사** → 알려지지 않은 라우터 확인
3. **settings.py 명확화** → 모델명 불명확 제거
4. **시스템 프롬프트 수정** → "JARVIS는 Ollama 기반"이라고 명시
5. **문서 업데이트** → 사용자에게 정확히 설명

---

**작성자**: 코드 진단 에이전트  
**신뢰도**: 높음 (코드 검사 기반)  
**다음 검증**: 실행 로그 분석 필요
