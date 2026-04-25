# JARVIS 현재 코드 아키텍처 평가

**작성일**: 2026.04.18  
**목적**: 새 JARVIS v1 설계도와의 부합도 분석  
**결론**: 기초는 탄탄하지만, 엔진 통합 및 메모리 시스템이 필요

---

## 📊 현재 코드 구조 맵

```
backend/
├─ app/
│  ├─ main.py (FastAPI 진입점)
│  ├─ config.py (설정)
│  ├─ llm_router.py ⚠️ (Ollama 라우터)
│  ├─ prompts_loader.py (프롬프트 로드)
│  ├─ api/
│  │  ├─ routers/
│  │  │  ├─ chat.py (대화 API)
│  │  │  ├─ approvals.py (승인 API)
│  │  │  ├─ health.py (헬스 체크)
│  │  │  └─ ... (기타 라우터)
│  │  └─ deps.py (의존성)
│  ├─ brains/
│  │  ├─ base.py (Brain 기본 클래스)
│  │  ├─ gemma_brain.py ✅
│  │  ├─ gpt_oss_brain.py ✅
│  │  └─ qwen_brain.py ✅
│  ├─ engines/
│  │  ├─ approval_engine.py (승인 엔진)
│  │  ├─ audit_engine.py ✅ (감사 엔진)
│  │  ├─ intent_engine.py ⚠️ (의도 엔진)
│  │  ├─ planning_engine.py ⚠️ (계획 엔진)
│  │  ├─ reflection_engine.py ⚠️ (반성 엔진)
│  │  ├─ routing_engine.py ⚠️ (라우팅 엔진)
│  │  └─ ...
│  ├─ core/
│  │  ├─ bootstrap.py (부팅)
│  │  ├─ conductor.py ⚠️ (지휘자)
│  │  ├─ orchestrator.py (오케스트레이터)
│  │  └─ ...
│  ├─ memory/
│  │  ├─ repository.py (메모리 저장소)
│  │  └─ ... (단편적)
│  ├─ models/
│  │  ├─ approval.py (승인 모델)
│  │  ├─ state.py (상태 모델)
│  │  └─ ...
│  ├─ tools/
│  │  ├─ file_tool.py ✅
│  │  ├─ backup_tool.py ✅
│  │  └─ ...
│  └─ ...
├─ core/ (구조상 중복)
│  ├─ bootstrap.py (또 다른 부팅?)
│  ├─ llm_router.py (또 다른 라우터?)
│  ├─ orchestrator.py (또 다른 오케스트레이터?)
│  └─ ...
└─ ...
```

**분석**: 구조가 초기 스케치 상태, 엔진들이 분산되어 있고 일부는 실장 전 상태.

---

## ✅ 새 설계도와의 부합 분석

### 1. Brain 시스템
**현황**: ✅ 3개 Brain 모두 준비됨
```
✓ backend/app/brains/gemma_brain.py
✓ backend/app/brains/gpt_oss_brain.py
✓ backend/app/brains/qwen_brain.py
✓ base.py (기본 인터페이스)
```

**충족도**: 95% (Brain registry만 추가 필요)  
**예상 이식 비용**: 낮음

**할 일**:
- Brain registry 구현 (어떤 Brain을 선택할지)
- 각 Brain의 프롬프트 최적화

---

### 2. 7개 엔진

#### Intent Engine
**현황**: ⚠️ `intent_engine.py` 있음, 상태 미확인
```
위치: backend/app/engines/intent_engine.py
기능: 요청의 의도 파악
```

**충족도**: 40% (구조만 있는 상태로 추정)  
**예상 이식 비용**: 중간

**할 일**:
- Intent 분석 로직 강화
- Context 활용 개선
- constraint 및 risk_level 추출

---

#### Planning Engine
**현황**: ⚠️ `planning_engine.py` 있음, 기능 미명확
```
위치: backend/app/engines/planning_engine.py
연관: core/planner.py (구 방식)
```

**충족도**: 30%  
**예상 이식 비용**: 중간

**할 일**:
- 작업 단계 분해 로직 재설계
- checkpoint 및 approval_point 명확화

---

#### Routing Engine
**현황**: ⚠️ `routing_engine.py` 있음, Brain selection 로직 불명확
```
위치: backend/app/engines/routing_engine.py
또한: backend/app/llm_router.py (기본 라우팅)
또한: core/smart_router.py (하이브리드 라우팅)
```

**충족도**: 50% (3개 라우터가 중복)  
**예상 이식 비용**: 높음

**할 일**:
- 3개 라우터 통합하기
- Brain selection 로직 명확화
- fallback route 구현

---

#### Approval Engine
**현황**: ✅ `approval_engine.py` 준비됨
```
위치: backend/app/engines/approval_engine.py
API: backend/app/api/routers/approvals.py
모델: backend/app/models/approval.py
```

**충족도**: 85%  
**예상 이식 비용**: 낮음

**할 일**:
- approval_queue 구조 표준화
- status 전이 로직 명확화

---

#### Memory Engine
**현황**: ⚠️ `repository.py` 있음, 6가지 메모리 유형 미분리
```
위치: backend/app/memory/repository.py
상태: 단순 저장소, 메모리 타입 미구분
```

**충족도**: 20%  
**예상 이식 비용**: 높음

**할 일**:
- 6가지 메모리 타입 분리 (Personal, Work, Prompt, Approval, KPI, File Action)
- 각 타입별 저장소 구현
- 조회 API 표준화

---

#### Reflection Engine
**현황**: ⚠️ `reflection_engine.py` 있음, 기능 불명확
```
위치: backend/app/engines/reflection_engine.py
```

**충족도**: 30%  
**예상 이식 비용**: 중간

**할 일**:
- 실행 결과 회고 로직 구현
- improvement_candidates 생성 알고리즘
- next_action 추천 기능

---

#### Audit Engine
**현황**: ✅ `audit_engine.py` 준비됨, 기본 기능 있음
```
위치: backend/app/engines/audit_engine.py
파일: AX_Vault/04_Audit/ (감사 로그 저장 위치)
```

**충족도**: 75%  
**예상 이식 비용**: 낮음

**할 일**:
- 기록 대상의 철저함 확인
- 구조화된 로깅 확대

---

### 3. Conductor 지휘자
**현황**: ⚠️ `conductor.py` 있으나 상태 불명확
```
위치: backend/app/core/conductor.py
또한: core/conductor.py (구 설계?)
연관: core/orchestrator.py
```

**충족도**: 50% (구조는 있지만 통합 미흡)  
**예상 이식 비용**: 높음

**할 일**:
- 7개 엔진과의 통합 관계 명확화
- 상태 관리 시스템 구현
- 순차 호출 로직 표준화

---

### 4. API 계층
**현황**: ✅ FastAPI로 기본 구조 됨
```
위치: backend/app/api/
라우터:
  ✓ chat.py (대화)
  ✓ approvals.py (승인)
  ✓ health.py (헬스 체크)
  ✓ 기타
```

**충족도**: 90%  
**예상 이식 비용**: 낮음

**할 일**:
- 모든 라우터가 Memory Engine과 통합되도록 확인
- Audit Engine 호출 확대

---

### 5. Tools 시스템
**현황**: ✅ 기본 도구들 준비됨
```
file_tool.py ✓
backup_tool.py ✓
log_tool.py ✓ (추정)
document_tool.py ? (확인 필요)
```

**충족도**: 70%  
**예상 이식 비용**: 낮음

**할 일**:
- 각 Tool이 승인 큐를 통과하도록 개선
- Tool 실행 후 Memory에 자동 기록

---

### 6. UI 계층 (Pixel Office)
**현황**: ⚠️ React/TypeScript 기본 구조 있음, 새 설계에 맞춰 확장 필요
```
위치: frontend/
컴포넌트: src/components/
상태: 기본 UI 있음, 6가지 메모리 패널 미구현
```

**충족도**: 50%  
**예상 이식 비용**: 높음

**할 일**:
- MemoryPanel 컴포넌트 추가 (6가지 메모리)
- ApprovalPanel 개선
- FliePanel 확대
- KPI Tracker 추가
- LogTicker 개선

---

### 7. 모델 통합
**현황**: ✅ Ollama JARVIS:latest 확인됨
```
모델: JARVIS:latest (Gemma3, 3.3GB)
기능: 완벽하게 작동
상태: 방금 v1 정체성으로 업그레이드 완료 ✅
```

**충족도**: 100%  
**예상 이식 비용**: 무 (이미 작동)

**할 일**:
- 정체성 프롬프트 최적화 (선택사항)

---

## 🗂️ 코드 중복 & 병렬 구조 분석

### ⚠️ 중복 발견

| 파일/기능 | 위치 1 | 위치 2 | 위치 3 | 설명 |
|---------|---------|---------|---------|------|
| **Conductor** | backend/app/core/ | core/ | - | 2개 위치, 기능 불명확 |
| **LLM Router** | backend/app/llm_router.py | core/llm_router.py | backend/app/smart_router.py | 3개 라우터 병렬 |
| **Orchestrator** | backend/app/core/ | core/ | - | 2개 위치 |
| **Planner** | core/planner.py | backend/app/engines/ | - | 구 vs 신 설계 |
| **Bootstrap** | backend/app/core/ | core/ | - | 2개 위치 |

**정리 필요**: 컨벤션 확립, 하나의 primary source 선택

---

## 🎯 이식 난이도 평가

| 엔진/컴포넌트 | 현재 완성도 | 난이도 | 예상 시간 |
|-------------|-----------|--------|---------|
| Brain 시스템 | 95% | ⭐ 낮음 | 1-2일 |
| Approval Engine | 85% | ⭐ 낮음 | 1-2일 |
| Audit Engine | 75% | ⭐ 낮음 | 1-2일 |
| API 계층 | 90% | ⭐ 낮음 | 1-2일 |
| Tools 시스템 | 70% | ⭐ 낮음 | 2-3일 |
| Intent Engine | 40% | ⭐⭐ 중간 | 3-4일 |
| Planning Engine | 30% | ⭐⭐ 중간 | 3-4일 |
| Reflection Engine | 30% | ⭐⭐ 중간 | 3-4일 |
| Memory Engine | 20% | ⭐⭐⭐ 높음 | 5-7일 |
| Routing Engine | 50% | ⭐⭐⭐ 높음 | 5-7일 |
| Conductor 통합 | 50% | ⭐⭐⭐ 높음 | 5-7일 |
| Pixel Office UI | 50% | ⭐⭐⭐⭐ 매우 높음 | 10-14일 |

**전체 예상**: 1.5-2개월 (Step별 병렬 작업 시)

---

## 💡 이식 우선순위 (현명한 순서)

### 🟢 Phase 1: 기초 통합 (1-2주)
```
1. 중복 파일 정리 (Conductor, Router 선택)
2. Intent/Planning/Reflection Engine 강화
3. Brain Registry 구현
4. API ← Memory/Audit 연결
```

### 🟡 Phase 2: 메모리 시스템 (1-2주)
```
1. 6가지 메모리 타입 분리
2. Memory Repository 확장
3. File Action History 추가
4. KPI Memory 구현
```

### 🔴 Phase 3: UI 확장 (2-3주)
```
1. MemoryPanel 컴포넌트
2. ApprovalPanel 개선
3. KPI Tracker
4. LogTicker 강화
```

---

## ✅ 최종 권장사항

### 하지 말아야 할 것 ❌
- 기존 파일을 통째로 복붙하기
- 3개의 병렬 라우터 유지하기
- Memory를 일부만 기록하기
- 승인 없이 실행되는 작업 유지하기

### 해야 할 것 ✅
- 중복 정리 먼저 진행
- Conductor 통합 집중
- Memory 시스템 먼저 구현
- 각 엔진을 진정한 모듈로 개선
- UI는 마지막에 (백엔드 완성 후)

### 가장 중요한 것 🎯
**Memory Engine을 가장 먼저 완성하세요.**
→ 모든 엔진이 Memory에 기록하도록 설계되었기 때문입니다.
→ Memory가 튼튼하면 나머지 엔진들의 통합이 자연스럽습니다.

---

## 📝 체크리스트

- [ ] 중복 파일 정리 선택 완료
- [ ] Memory 6가지 타입 정의서 작성
- [ ] Intent Engine 상세 명세 검토
- [ ] Planning Engine 알고리즘 설계
- [ ] Conductor 호출 순서도 작성
- [ ] API 모든 라우터 감사 완료
- [ ] UI 와이어프레임 작성 (6가지 패널)
- [ ] 테스트 계획 수립

