# JARVIS 아키텍처 재검토 및 개선안

## 📋 Executive Summary

현재 JARVIS는 **복잡한 설계**와 **단순한 실제 구현** 사이의 **불일치**가 발생하고 있습니다.
특히 클라우드 배포(Railway) 시 로컬 Ollama 연결 문제로 인해 실제 운영이 어렵습니다.

---

## 🔍 현재 상태 분석

### 1️⃣ 로컬 에이전트(Ollama) 연결 문제

#### 문제점
```
로컬 (127.0.0.1:8000)
    ↓ [LLM Router]
    ↓ settings.intelligence_engine_url = localhost:11434
    ↓ ✅ 작동됨

클라우드 (Railway/AWS/GCP)
    ↓ [LLM Router]
    ↓ settings.intelligence_engine_url = localhost:11434
    ↓ ❌ 접근 불가능!
       (Railway 서버는 로컬 Ollama 없음)
```

#### 코드 위치
- **llm_router.py** (Line 46-60): 로컬 Ollama 연결 시도
- **base.py** (Line 31): Fallback 메커니즘 미흡
- **.env**: `INTELLIGENCE_ENGINE_URL=http://localhost:11434` (고정값)

#### 현재 Fallback
```python
# base.py - fallback() 메서드
"사장님, 현재 로컬 지능형 엔진(JARVIS)과의 연결이 원활하지 않습니다."
# → 단순 에러 메시지만 반환, 실제 처리 안 함
```

---

### 2️⃣ 사용 목적 불명확

#### 설계 의도 (복잡)
```
Orchestrator
  ├─ Planner (계획 수립)
  ├─ Executor (실행)
  ├─ Reviewer (검토)
  └─ WikiAgent (지식 저장)

Harness (규칙 엔진)
  ├─ commands.py (슬래시 명령어)
  ├─ rules_engine.py (규칙 적용)
  ├─ hooks.py (훅 시스템)
  └─ skills/ (스킬 모음)

Multiple Engines
  ├─ approval_engine.py
  ├─ audit_engine.py
  ├─ intent_engine.py
  ├─ planning_engine.py
  ├─ reflection_engine.py
  └─ routing_engine.py
```

#### 실제 구현 (단순)
```
ChatRequest
  ↓
ChatModeClassifier
  ├─ "chat" → SimpleChat (직접 LLM 호출)
  ├─ "task" → SimpleTask (직접 LLM 호출)
  └─ "command" → Orchestrator (명령어 처리)

결과: Planner, Reviewer, WikiAgent는 거의 미사용
```

#### 미사용 컴포넌트
- ❌ `orchestrator.py`: 복잡하지만 실제로는 SimpleChat/SimpleTask 사용
- ❌ `planner.py`: Task 모드에서 미사용
- ❌ `reviewer.py`: 미사용 (검토 단계 없음)
- ❌ `wiki_agent.py`: 미사용 (지식 저장 안 함)
- ❌ Multiple engines: 대부분 미사용
- ❌ `memory/repository.py`: 메모리 시스템 미사용
- ❌ `harness/hooks.py`: 훅 시스템 미사용
- ❌ `harness/rules_engine.py`: 규칙 엔진 미사용

---

### 3️⃣ Harness 과도한 복잡성

#### 현재 상태
```
backend/app/harness/
├─ commands.py (200+ 라인) - 명령어 파싱/실행
├─ rules_engine.py - 규칙 기반 처리 (특별히 구현 안 함)
├─ hooks.py - 이벤트 훅 (특별히 구현 안 함)
└─ skills/
    ├─ __init__.py
    └─ (실제 스킬 없음)
```

#### 실제 사용
- CLI에서 슬래시 명령어(`/help`, `/save` 등) 처리
- 대부분 "구현 예정" 상태

#### 문제점
- 복잡한 구조 vs 단순한 기능
- 확장성 과대설계
- 유지보수 어려움

---

## 💡 개선안

### 🎯 전략: 3계층 아키텍처로 단순화

```
┌─────────────────────────────────────────┐
│  API Layer                              │
│  ├─ /chat (사용자 대화)                  │
│  ├─ /task (작업 요청)                    │
│  └─ /command (명령어)                   │
└────────────┬────────────────────────────┘
             │
┌────────────▼────────────────────────────┐
│  Router Layer (Mode Classifier)         │
│  ├─ chat → DirectChat                   │
│  ├─ task → DirectTask                   │
│  └─ command → SimpleCommand             │
└────────────┬────────────────────────────┘
             │
┌────────────▼────────────────────────────┐
│  LLM Layer (지능형 엔진)                  │
│  ├─ Local Ollama (로컬 모드)             │
│  ├─ Cloud API (클라우드 모드)            │
│  └─ Hybrid (실패 시 폴백)                │
└─────────────────────────────────────────┘
```

---

## 🔧 실행 계획

### Phase 1: 로컬 연결 문제 해결 (우선순위 🔴 높음)

#### 1-1. LLMRouter 재설계
```python
# 현재
async def call(self, prompt, system, model_key=None):
    # 로컬 Ollama만 시도 → 실패하면 에러

# 개선
async def call(self, prompt, system, fallback_model="gpt-4-mini"):
    """
    모드별 동작:
    - LOCAL_ONLY: 로컬만 시도
    - CLOUD_ONLY: API만 사용
    - HYBRID: 로컬 시도 → 실패 시 API
    """
    mode = settings.llm_mode  # "local" | "cloud" | "hybrid"
    
    if mode == "local":
        return await self._call_local()
    elif mode == "cloud":
        return await self._call_cloud()
    elif mode == "hybrid":
        try:
            return await self._call_local()
        except Exception:
            logger.warning("Local failed, trying cloud...")
            return await self._call_cloud()
```

#### 1-2. 환경변수 정리
```env
# 현재
INTELLIGENCE_ENGINE_URL=http://localhost:11434
OLLAMA_HOST=http://localhost:11434
JARVIS_MODEL=jarvis

# 개선
# Local 설정
JARVIS_MODE=hybrid              # local | cloud | hybrid
LOCAL_OLLAMA_URL=http://localhost:11434
LOCAL_MODEL=jarvis

# Cloud 설정
CLOUD_PROVIDER=openai           # openai | anthropic | etc
CLOUD_API_KEY=sk-...
CLOUD_MODEL=gpt-4-mini

# 우선순위
LLM_PRIORITY=local              # local > cloud (우선순위)
```

#### 1-3. Fallback 강화
```python
# base.py - fallback() 함수 개선
async def fallback(self, prompt, system):
    """실패 시 클라우드 API 또는 간단한 응답"""
    if settings.fallback_api_key:
        # 클라우드 API로 재시도
        return await self._call_cloud(prompt, system)
    else:
        # 오프라인 응답
        return "현재 AI 엔진이 작동 중이 아닙니다. 나중에 다시 시도해주세요."
```

#### 결과
```
로컬 (개발/데모)
  ✅ Ollama 실행 중 → LocalOllama 사용
  
로컬 (Ollama 실패)
  ✅ 환경변수 설정 있음 → Cloud API 사용
  
클라우드 (Railway/AWS)
  ✅ Ollama 없음 → Cloud API 사용
  
클라우드 (API 키 없음)
  ✅ Offline 응답
```

---

### Phase 2: 아키텍처 단순화 (우선순위 🟡 중간)

#### 2-1. 미사용 컴포넌트 제거/보관
```
삭제 후보
├─ orchestrator.py (SimpleChat/SimpleTask로 통합)
├─ planner.py (복잡한 계획 로직 제거)
├─ reviewer.py (검토 단계 없음)
├─ wiki_agent.py (지식 저장 미구현)
├─ memory/repository.py (미사용)
├─ harness/rules_engine.py (규칙 엔진 미사용)
├─ harness/hooks.py (훅 시스템 미사용)
├─ engines/approval_engine.py (미사용)
├─ engines/audit_engine.py (미사용)
├─ engines/planning_engine.py (미사용)
├─ engines/reflection_engine.py (미사용)
└─ engines/routing_engine.py (미사용)

보관 디렉토리
  archives/
  ├─ _old_orchestrator.py
  ├─ _old_engines/
  └─ _old_harness/
```

#### 2-2. 단순화된 라우터
```python
# backend/app/core/simple_router.py
class SimpleRouter:
    """Chat, Task, Command 3가지만 처리"""
    
    async def route(self, message: str, mode: str = None) -> dict:
        """
        - mode == "chat" or 단순 질문: SimpleChat
        - mode == "task" or 복잡 작업: SimpleTask
        - mode == "command" or /로 시작: SimpleCommand
        """
        mode = mode or self._classify(message)
        
        if mode == "chat":
            return await SimpleChat().chat(message)
        elif mode == "task":
            return await SimpleTask().execute(message)
        elif mode == "command":
            return await SimpleCommand().execute(message)
```

#### 2-3. 새로운 디렉토리 구조
```
backend/app/
├─ api/
│  └─ routers/
│      ├─ chat.py → chat/task/command 통합 처리
│      ├─ health.py
│      └─ mobile.py
├─ core/
│  ├─ simple_router.py (새로움)
│  └─ bootstrap.py
├─ handlers/
│  ├─ chat.py (SimpleChat)
│  ├─ task.py (SimpleTask)
│  └─ command.py (SimpleCommand)
├─ llm/
│  ├─ router.py (LLMRouter)
│  ├─ local.py (Ollama 연결)
│  └─ cloud.py (API 연결)
├─ utils/ (settings, helpers)
└─ archives/ (old code backup)
    ├─ _old_orchestrator.py
    ├─ _old_engines/
    └─ _old_harness/
```

---

### Phase 3: Harness 미니멀화 (우선순위 🟢 낮음)

#### 3-1. Command 시스템만 유지
```python
# backend/app/harness/commands.py (간소화)
COMMANDS = {
    "/help": "도움말",
    "/status": "상태 확인",
    "/config": "설정 보기",
    # 나머지는 제거
}

async def execute_command(cmd: str) -> str:
    """간단한 명령어만 처리"""
    if cmd not in COMMANDS:
        return f"Unknown command: {cmd}"
    # ... 로직
```

#### 3-2. Rules Engine 제거 또는 보관
- 현재 사용 안 함
- `archives/_old_harness/rules_engine.py`로 이동

#### 3-3. Hooks 시스템 제거
- 현재 사용 안 함
- 필요시 나중에 추가

---

## 📊 마이그레이션 로드맵

### Week 1: 로컬 연결 해결 (Quick Win)
```
1. .env 파일 수정 (JARVIS_MODE=hybrid 추가)
2. llm_router.py 개선 (fallback 강화)
3. base.py 수정 (cloud API 폴백)
4. 테스트 (로컬 + Railway)
```

### Week 2: 아키텍처 정리
```
1. handlers/ 디렉토리 생성
2. SimpleChat/SimpleTask/SimpleCommand 이동
3. simple_router.py 작성
4. chat.py 라우터 업데이트
```

### Week 3: 미사용 코드 정리
```
1. archives/ 디렉토리 생성
2. 미사용 파일 이동
3. 폴더 구조 정리
4. 전체 테스트
```

---

## 🎯 목표

| 지표 | 현재 | 개선 후 |
|------|------|--------|
| **복잡도** | 매우 높음 (7개 engines) | 낮음 (3가지 모드) |
| **로컬 연결** | ❌ 실패 | ✅ Ollama or API |
| **클라우드 배포** | ❌ Ollama 연결 불가 | ✅ API 이용 |
| **유지보수** | 어려움 | 쉬움 |
| **기능** | 95% 미사용 | 100% 활용 |
| **응답 속도** | 2-4초 | 2-4초 (동일) |
| **코드 라인** | ~2000 라인 (미사용) | ~500 라인 (활용) |

---

## ⚠️ 주의사항

### 롤백 계획
```
1. archives/ 디렉토리에 기존 코드 백업
2. Git 커밋으로 이력 유지
3. 문제 발생 시 쉽게 복원 가능
```

### 호환성
```
- API 엔드포인트는 변경 없음
- 클라이언트 코드 수정 불필요
- 내부 로직만 변경
```

---

## 🚀 다음 단계

**사용자의 동의 후:**

1. [ ] Phase 1 실행: 로컬 연결 문제 해결
2. [ ] 테스트: 로컬 + Railway에서 동작 확인
3. [ ] Phase 2 실행: 아키텍처 단순화
4. [ ] Phase 3 실행: Harness 미니멀화

---

**작성일**: 2026-04-18  
**상태**: 검토 대기

