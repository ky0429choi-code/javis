# JARVIS 이식 로드맵 (Migration Roadmap)

**작성일**: 2026.04.18  
**목표**: 기존 코드를 새 JARVIS v1 설계도에 체계적으로 이식  
**원칙**: 파일 단위 복붙 금지, 기능별 재배치, 역할 우선

---

## 📌 이식 원칙 (4가지)

### 1. 파일 단위 이식 금지
❌ 기존 파일을 통째로 복붙하지 않음  
✅ 기능을 분해해서 새 구조에 재배치

### 2. 이름보다 역할 우선
❌ 기존 파일 이름 기준 배치 금지  
✅ 실제 역할을 기준으로 위치 결정

### 3. 승인 규칙 고정
❌ 기존 코드의 자동 실행 유지 금지  
✅ 새 구조에서는 승인 큐를 반드시 통과

### 4. 메모리 우선 저장
❌ 실행 후 기록  
✅ 기록 후 실행

---

## 🎯 분류: 살릴 것 / 수정 후 이식 / 폐기

### ✅ 살릴 것 (그대로 유지 또는 최소 수정)

```
기능 단위:
┌─────────────────────────────────────┐
│ 1. 일상 대화 흐름                   │
│    현위치: backend/app/api/chat.py  │
│    새위치: api/routers/chat.py      │
│    수정: Approval Engine 통합       │
│                                     │
│ 2. 승인 요청 개념                   │
│    현위치: backend/app/engines/     │
│           approval_engine.py        │
│    새위치: engines/approval_engine  │
│    수정: 데이터 구조 표준화         │
│                                     │
│ 3. 로그 & 히스토리 개념             │
│    현위치: backend/app/core/        │
│    새위치: engines/audit_engine.py  │
│    수정: 구조화된 로깅 확대         │
│                                     │
│ 4. 문서 링크 & 자료 연결 개념       │
│    현위치: backend/app/tools/       │
│    새위치: tools/document_tool.py   │
│    수정: 메모리 통합               │
│                                     │
│ 5. 픽셀 UI 아이디어                 │
│    현위치: frontend/src/            │
│    새위치: ui/pixel_office/         │
│    수정: 6가지 메모리 패널 추가     │
│                                     │
│ 6. Ollama JARVIS 모델 연결          │
│    현위치: backend/app/llm_router   │
│    새위치: core/model_connector.py  │
│    수정: Conductor와 통합           │
└─────────────────────────────────────┘
```

### 🔧 수정 후 이식할 것

```
기능 단위:
┌─────────────────────────────────────┐
│ 1. 멀티 브레인 라우팅               │
│    현위치: backend/app/llm_router   │
│           smart_router.py           │
│    이슈: 3개 Brain이 불분명함      │
│           라우팅 규칙 모호          │
│    수정: Routing Engine로 통합      │
│           역할 명확화              │
│    새위치: engines/routing_engine   │
│                                     │
│ 2. 기존 API 엔드포인트              │
│    현위치: backend/app/api/routers/ │
│    이슈: 승인 로직 없음             │
│    수정: Approval Engine 추가      │
│    새위치: api/routers/             │
│                                     │
│ 3. 파일 작업 로직                   │
│    현위치: backend/app/tools/       │
│           file_tool.py              │
│    이슈: 직접 실행, 기록 미흡       │
│    수정: Approval → Audit 파이프   │
│    새위치: tools/file_tool.py       │
│                                     │
│ 4. 프롬프트 저장 구조               │
│    현위치: backend/app/             │
│           prompts_loader.py         │
│    이슈: 메모리 미연계              │
│    수정: Prompt Memory 통합         │
│    새위치: memory/prompt_memory.py  │
│                                     │
│ 5. KPI 저장 구조                    │
│    현위치: backend/app/models/      │
│    이슈: 고정 규칙 적용             │
│    수정: 사용자 유동 지정 방식      │
│    새위치: memory/kpi_memory.py     │
└─────────────────────────────────────┘
```

### ❌ 폐기할 것 (새 구조에 맞지 않음)

```
파일/기능:
┌─────────────────────────────────────┐
│ 1. 중복 엔트리포인트                │
│    backend/launch_demo.py           │
│    backend/startup_sync.py          │
│    backend/test_*.py                │
│    → Unified launcher로 통합        │
│                                     │
│ 2. 레거시 실행기                   │
│    core/planner.py (구 설계)        │
│    core/orchestrator.py (구 설계)   │
│    → Conductor Core로 재설계        │
│                                     │
│ 3. 중복 대시보드 UI                 │
│    frontend/pages/App.tsx (구)      │
│    → Pixel Agent Office로 통합      │
│                                     │
│ 4. 로컬 샘플 상태만 쓰는 임시 파일 │
│    data/sample_state.json           │
│    → 실제 Memory 시스템으로        │
│                                     │
│ 5. 승인 없는 자동 실행 흐름        │
│    backend/app/core/bootstrap.py    │
│    (자동 모델 검증만)               │
│    → Approval 통합 후 재설계        │
│                                     │
│ 6. 구조상 같은 역할을 하는 중복 폴더│
│    backend/llm_router/ (폴더)       │
│    core/llm_router.py (파일)        │
│    → 통합하여 core/에 유지          │
└─────────────────────────────────────┘
```

---

## 🚀 이식 5단계

### **Step 1: Core 우선 이식** (기초 다지기)
**목표**: 지휘 중추 완성  
**예상 시간**: 1-2주  
**산출물**: 새 구조 골격 완성

```
이동 대상:
┌─────────────────────────────────────┐
│ backend/app/core/ → core/           │
│  ├─ conductor.py ✅ 새로 구현       │
│  ├─ bootstrap.py (수정)             │
│  └─ identity.py (새로 생성)         │
│                                     │
│ backend/app/engines/ → engines/     │
│  ├─ intent_engine.py ✅ 새로 구현   │
│  ├─ planning_engine.py ✅ 새로 구현 │
│  ├─ routing_engine.py ✅ 새로 구현  │
│  ├─ approval_engine.py (수정)       │
│  ├─ memory_engine.py ✅ 새로 구현   │
│  ├─ reflection_engine.py ✅ 새로 구현
│  └─ audit_engine.py ✅ 새로 구현    │
│                                     │
│ backend/app/brains/ → brains/       │
│  ├─ gpt_oss_brain.py (수정)         │
│  ├─ gemma_brain.py (수정)           │
│  ├─ qwen_brain.py (수정)            │
│  └─ brain_registry.py ✅ 새로 구현  │
│                                     │
│ backend/app/tools/ → tools/         │
│  └─ base_tool.py ✅ 새로 구현       │
└─────────────────────────────────────┘

검증:
✓ Conductor 고정 실시
✓ 7개 엔진 상호호출 시뮬레이션
✓ Brain 라우팅 테스트
```

---

### **Step 2: Memory / Approval 이식** (기억 체계)
**목표**: 장기 기억과 승인 시스템 완성  
**예상 시간**: 1주  
**산출물**: 메모리 저장소 + 승인 큐

```
이동 대상:
┌─────────────────────────────────────┐
│ backend/app/memory/ → memory/       │
│  ├─ personal_memory.py ✅ 새로 구현 │
│  ├─ work_memory.py ✅ 새로 구현     │
│  ├─ prompt_memory.py ✅ 새로 구현   │
│  ├─ approval_memory.py ✅ 새로 구현 │
│  ├─ kpi_memory.py ✅ 새로 구현      │
│  ├─ file_action_memory.py ✅ 새로   │
│  └─ memory_store.py ✅ 새로 구현    │
│                                     │
│ backend/app/models/ → models/       │
│  ├─ approval.py (수정)              │
│  ├─ state.py (수정)                 │
│  └─ memory_item.py ✅ 새로 구현     │
│                                     │
│ runtime/                            │
│  ├─ approval_queue.py ✅ 새로 구현  │
│  └─ task_runner.py ✅ 새로 구현     │
└─────────────────────────────────────┘

검증:
✓ 6가지 메모리 타입 저장/조회
✓ 승인 큐 CRUD 작동
✓ Approval Flow 완전 실행
```

---

### **Step 3: Pixel Office 이식** (시각 인터페이스)
**목표**: UI를 새 메모리 시스템에 맞춤  
**예상 시간**: 2주  
**산출물**: 통합 대시보드

```
이동 대상:
┌─────────────────────────────────────┐
│ frontend/src/ → ui/pixel_office/    │
│  ├─ components/                     │
│  │  ├─ PixelStage.tsx ✅ 기본 유지  │
│  │  ├─ AgentPanel.tsx ✅ 상태 표시  │
│  │  ├─ PromptStudio.tsx ✅ 프롬프트 │
│  │  ├─ ApprovalPanel.tsx ✅ 승인 UI │
│  │  ├─ FilePanel.tsx ✅ 파일 관리   │
│  │  ├─ ChatPanel.tsx ✅ 대화창      │
│  │  ├─ MemoryPanel.tsx ✅ 새로 추가 │
│  │  │  (6가지 메모리 표시)          │
│  │  ├─ LogTicker.tsx ✅ 활동 로그   │
│  │  └─ KPITracker.tsx ✅ KPI 추적   │
│  │                                  │
│  ├─ pages/                          │
│  │  └─ Pixel.tsx (새로 생성)        │
│  │                                  │
│  ├─ lib/                            │
│  │  ├─ memory_client.ts ✅ 새로     │
│  │  ├─ approval_client.ts ✅ 새로   │
│  │  └─ api.ts (수정)                │
│  │                                  │
│  └─ styles/                         │
│     └─ pixel_office.css ✅ 새로     │
└─────────────────────────────────────┘

검증:
✓ 6가지 메모리 패널 실시간 표시
✓ 승인 큐 UI ↔ Backend 동기화
✓ 라이브 로그 티커 작동
```

---

### **Step 4: Legacy 기능 흡수** (기존 자산 통합)
**목표**: 기존 코드의 가치 있는 부분 추출  
**예상 시간**: 1주  
**산출물**: 확장 도구 및 유틸리티

```
추출 대상:
┌─────────────────────────────────────┐
│ 1. 문서 로더                        │
│    backend/app/tools/ → tools/      │
│    → document_tool.py (수정)        │
│                                     │
│ 2. 외부 자료 수집기                 │
│    core/orchestrator.py (구) → →    │
│    → tools/research_tool.py ✅ 새로 │
│                                     │
│ 3. 트렌드 분석기                   │
│    (기존 코드 검토 후) →            │
│    → tools/trend_analyzer.py ✅ 새로│
│                                     │
│ 4. 로그 보기                        │
│    backend/app/tools/log_tool.py → │
│    → tools/log_tool.py (수정)       │
│                                     │
│ 5. 백업 기능                        │
│    backend/app/tools/ → tools/      │
│    → backup_tool.py (유지)          │
└─────────────────────────────────────┘

검증:
✓ 각 도구가 Conductor와 통합
✓ 각 도구가 Audit Engine 기록
✓ 각 도구가 적절한 Memory에 저장
```

---

### **Step 5: 하네스/자동 운영 이식** (자동화 체계)
**목표**: 자동 실행 워크플로우 구현  
**예상 시간**: 1주  
**산출물**: Setup → Plan → Go → Sync 루프

```
구현 대상:
┌─────────────────────────────────────┐
│ 1. Setup / Plan / Go / Sync 개념    │
│    core/bootstrap.py (수정) →       │
│    → runtime/harness.py ✅ 새로     │
│                                     │
│ 2. Lore 기록 개념 (작업 로그)       │
│    → memory/lore_memory.py ✅ 새로  │
│                                     │
│ 3. 승인형 auto-run                  │
│    (기존 자동화 제거) →             │
│    → runtime/approval_runner.py ✅  │
│       (승인 후에만 실행)             │
│                                     │
│ 4. 스케줄러                         │
│    → runtime/scheduler.py ✅ 새로   │
│       (Daily Mode, Learn Mode 등)   │
└─────────────────────────────────────┘

검증:
✓ Setup 실행 → 모델 확인
✓ Plan 생성 → Intent 분석
✓ Go 승인 → 실행 대기
✓ Sync 저장 → Memory 기록
```

---

## 📊 현재 상태 vs 목표 상태

### 현재 상태 (Before)
```
❌ 입력 → 직접 실행 (승인 없음)
❌ 3개 Brain이 혼재됨
❌ 로그가 산재적
❌ 메모리 종류가 명확하지 않음
❌ 파일 변경 감시 미흡
❌ 자동 실행으로 인한 위험
```

### 목표 상태 (After)
```
✅ 입력 → Intent 해석 → 계획 → 라우팅 → 승인 확인 → 실행 → 기록
✅ 각 Brain의 역할 분명함
✅ Audit Engine이 모든 내용을 기록
✅ 6가지 메모리로 정보 체계화
✅ File Action Memory로 전체 히스토리 추적
✅ 승인 기반으로 안전성 확보
✅ Pixel Office에서 전체 통제 가능
```

---

## ⏱️ 전체 이식 일정

| Step | 작업 | 예상 시간 | 누적 | 상태 |
|-----|------|---------|------|------|
| 1 | Core 우선 이식 | 1-2주 | 1-2주 | ❌ 미시작 |
| 2 | Memory/Approval 이식 | 1주 | 2-3주 | ❌ 미시작 |
| 3 | Pixel Office 이식 | 2주 | 4-5주 | ❌ 미시작 |
| 4 | Legacy 흡수 | 1주 | 5-6주 | ❌ 미시작 |
| 5 | 하네스/자동 운영 | 1주 | 6-7주 | ❌ 미시작 |

**목표**: 7주 이내 전체 마이그레이션 완료

---

## ✅ 이식 완료 검증 체크리스트

- [ ] Core Conductor 정상 작동
- [ ] 7개 엔진 상호 호출 완료
- [ ] 6가지 메모리 저장/조회 완료
- [ ] 승인 큐 CRUD 작동
- [ ] Brain 라우팅 정상
- [ ] Ollama JARVIS 모델 연결
- [ ] Pixel Office 모든 패널 작동
- [ ] Audit Engine 기록 완전
- [ ] File Action History 추적
- [ ] 사용자 지정 KPI 저장 가능
- [ ] 승인 없는 자동 실행 제거됨
- [ ] 모든 오류 처리 구현됨

---

## 📝 이식 중 주의사항

1. **역할 우선 사고**
   - "이 파일은 기존에 어디 있었나?" ❌
   - "이 파일이 하는 역할이 뭔가?" ✅

2. **승인 규칙 엄격히**
   - 기존 코드가 자동 실행해도 새 구조에서는 승인 필수

3. **메모리 먼저 기록**
   - 실행하기 전에 Memory Engine에 기록

4. **테스트 주기적**
   - 각 단계마다 통합 테스트 실시

5. **롤백 계획**
   - 각 Step 완료 후 백업 지점 생성

