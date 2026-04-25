# JARVIS 설계도 v1 - 공식 아키텍처

**작성일**: 2026.04.18  
**버전**: v1.0  
**상태**: 현행 설계 기준

---

## 📋 개요

JARVIS는 단일 모델이 아니라, **상위 지휘 코어(Jarvis Conductor)** 가 여러 공개 모델과 로컬 도구를 통제하는 **개인 전용 로컬 Agent Office**다.

### 핵심 목표

- ✅ 사용자와 **일상 대화**
- ✅ 업무를 **구조화, 분해, 초안화, 검토, 기록**
- ✅ 파일 생성/수정/삭제 같은 민감 작업은 **승인 큐 기반 통제**
- ✅ 결과물, 승인 이력, 반려 사유, 프롬프트, KPI, 로그를 **장기 기억으로 저장**
- ✅ 외부 자료를 자율 수집·정리하되, **영구 반영과 자기개선 적용은 승인/검증 후**

---

## 🎯 핵심 정체성

### JARVIS란 무엇인가

JARVIS는 **작업자가 아니라 지휘자(Conductor)**다.

**역할:**
- 요청의 진짜 목적 해석
- 작업 단계 분해
- 적절한 Brain / Tool 선택
- 승인 필요 여부 판정
- 결과 평가 및 다음 행동 결정
- 모든 행동의 기록과 회고

### JARVIS가 아닌 것

- ❌ 승인 없이 시스템을 마음대로 수정하는 완전 자율 AI
- ❌ KPI를 임의 생성하고 강제하는 관리자
- ❌ 온라인에서 무제한 자기학습하며 실시간으로 자신을 바꾸는 모델

---

## 🏗️ 시스템 계층 구조

```
┌─────────────────────────────────────┐
│       Pixel Agent Office (UI)       │
│  - 픽셀 스테이지                      │
│  - 에이전트 상태 패널                  │
│  - 프롬프트 스튜디오                    │
│  - 승인 큐, 파일 패널                  │
│  - 대화창, 활동 로그 티커              │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  Runtime / API Layer (FastAPI)      │
│  - 라우터, 인증                       │
│  - 세션/요청 처리                     │
│  - 승인 요청 API                      │
│  - 대화 API, 작업 API                 │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  Jarvis Conductor Core (지휘 심장)  │
│  - Intent Engine                     │
│  - Planning Engine                   │
│  - Routing Engine                    │
│  - Approval Engine                   │
│  - Memory Engine                     │
│  - Reflection Engine                 │
│  - Audit Engine                      │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  Brains / Tools / Memory / Bus       │
│  ┌───────┬───────────┬──────────┐   │
│  │ Brain │   Tool    │  Memory  │   │
│  ├───────┼───────────┼──────────┤   │
│  │ GPT   │ File Tool │Personal  │   │
│  │ Gemma │ Search    │Work      │   │
│  │ Qwen  │ Backup    │Prompt    │   │
│  │       │ Log       │Approval  │   │
│  │       │ Document  │KPI       │   │
│  │       │           │File Act  │   │
│  └───────┴───────────┴──────────┘   │
└─────────────────────────────────────┘
```

---

## 🧠 Brain 구조 (3종)

### 1. GPT-OSS Brain
**역할:** 고난도 추론  
**특징:** 논리적, 신중, 위험 인식  
**호출 시기:** 중요 결정, 복잡한 문제, 비판 검토

```
책임 태스크:
- 작업 분해 및 아키텍처 설계
- 리드팀 / 비판적 검토
- 승인 전 논리 검증
- 고난도 의사결정 보조
```

### 2. Gemma Brain
**역할:** 일상 대화  
**특징:** 따뜻함, 빠름, 접근성  
**호출 시기:** 대화 유지, 빠른 반응 필요

```
책임 태스크:
- 일상 대화
- 친근한 설명
- 빠른 초안
- 요약
```

### 3. Qwen Brain
**역할:** 코드와 도구  
**특징:** 정확, 기술적, 실행 중심  
**호출 시기:** 구현, 파일 작업, 자동화

```
책임 태스크:
- 코드 생성/수정 보조
- 도구 호출
- 파일 작업 초안
- 시스템 명령 조합
```

### Brain 호출 원칙

**단일 선택 시:**
- 복잡도 ↑ → GPT-OSS
- 속도 중요 → Gemma
- 기술적 작업 → Qwen

**순차 호출 (다단계):**
```
GPT-OSS (계획) → Qwen (구현) → Gemma (설명)
```

---

## ⚙️ 내부 엔진 설계 (7개)

### 1️⃣ Intent Engine
**목표:** 요청의 진정한 목적 해석  
**입력:** 사용자 메시지 + 현재 상태 + 대화 기록  
**출력:**
```json
{
  "goal": "사용자의 진정한 목표",
  "constraints": ["제약 조건 1", "제약 조건 2"],
  "expected_output": "기대 결과",
  "risk_level": "low|medium|high"
}
```

### 2️⃣ Planning Engine
**목표:** 목표를 단계로 분해  
**입력:** goal + constraints  
**출력:**
```json
{
  "steps": ["단계 1", "단계 2", "단계 3"],
  "required_materials": ["자료 1", "자료 2"],
  "checkpoints": ["체크포인트 1"],
  "approval_points": ["승인 필요 지점"]
}
```

### 3️⃣ Routing Engine
**목표:** 어떤 Brain / Tool을 사용할지 결정  
**입력:** goal + steps  
**출력:**
```json
{
  "selected_brain": "qwen|gpt-oss|gemma",
  "selected_tool": "file|search|backup|log",
  "fallback_route": "대체 경로",
  "execution_mode": "sequential|parallel|approval"
}
```

### 4️⃣ Approval Engine
**목표:** 민감 작업을 승인 큐로 보냄  
**승인 대상:**
- 파일 생성/수정/삭제
- 폴더 생성/삭제
- 영구 메모리 반영
- KPI 핵심 변경
- 프롬프트 규칙 변경
- 외부 API 호출 (민감 데이터)

**승인 큐 데이터:**
```json
{
  "request_id": "REQ-001",
  "action_type": "create_file|modify_file|delete_file",
  "target_path": "/workspace/reports/file.md",
  "reason": "작업 사유",
  "requested_by": "Qwen Brain",
  "status": "pending_approval|approved|rejected"
}
```

### 5️⃣ Memory Engine
**목표:** 장기 기억과 작업 문맥 관리  
**메모리 유형:**

| 유형 | 보존 | 용도 |
|-----|------|------|
| Personal Memory | 영구 | 사람 정보, 선호도, 역사 |
| Work Memory | 영구 | 진행 중 작업 상태, 결과 |
| Prompt Memory | 영구 | 프롬프트 변경 이력 |
| Approval Memory | 영구 | 승인/반려 이력, 사유 |
| KPI Memory | 영구 | 사용자 지정 KPI, 진전도 |
| File Action Memory | 영구 | 파일 변경 이력, Diff |

### 6️⃣ Reflection Engine
**목표:** 작업 결과를 회고하고 개선 후보 생성  
**출력:**
```json
{
  "lessons": ["배운 점 1", "배운 점 2"],
  "improvement_candidates": ["개선 후보 1"],
  "next_action": "다음 행동 제안"
}
```

### 7️⃣ Audit Engine
**목표:** 모든 판단과 실행을 감사 로그로 남김  
**기록 대상:**
- 모든 Intent 분석
- 모든 Planning 결과
- 모든 Routing 결정
- 모든 승인/반려
- 모든 실행 결과
- 모든 Memory 변경

---

## 📋 승인 구조

### 승인 필수 작업

```yaml
파일 작업:
  - 파일 생성 (Create)
  - 파일 수정 (Modify)
  - 파일 삭제 (Delete)
  - 폴더 생성/삭제

메모리 & KPI:
  - 영구 메모리 반영
  - KPI 핵심 변경
  - 프롬프트 규칙 변경

외부 호출:
  - 외부 API (민감 데이터)
  - 시스템 설정 변경
```

### 자율 처리 (승인 불필요)

```yaml
일상:
  - 일상 대화
  - 정보 검색 & 요약
  - 초안 제안

로그:
  - 로그 조회
  - 임시 메모리 사용
  - 문제 분석
```

### 승인 흐름

```
1. Brain 또는 Tool이 민감 작업 필요성 제안
   ↓
2. Approval Engine이 승인 필요 판정
   ↓
3. Approval Queue 등록 → UI에 표시
   ↓
4. 사용자 승인 또는 반려
   ↓
5. 승인 시 → Tool 실행 + Audit 기록
   반려 시 → 반려 사유 기록 + Reflection 생성
```

---

## 📚 Memory 시스템 (6가지)

### Personal Memory
```yaml
보존: 영구
용도: 사용자 정보, 선호도, 역사
예시:
  - "사장님은 아침 7시에 업무 시작"
  - "좋아하는 브레인 스타일: 간결명확"
```

### Work Memory
```yaml
보존: 영구
용도: 진행 중 작업 상태, 결과
예시:
  - "프로젝트 A: 진행률 60%"
  - "마지막 보고서: 2026.04.15"
```

### Prompt Memory
```yaml
보존: 영구
용도: 프롬프트 변경 이력, 버전 관리
예시:
  - "v1.0: 기본 정체성 (2026.04.18)"
  - "v1.1: Intent 강화 (2026.04.18)"
```

### Approval Memory
```yaml
보존: 영구
용도: 승인/반려 기록, 사유 저장
예시:
  - "REQ-001: Create File → 승인 (2026.04.18 10:30)"
  - "REQ-002: Modify Settings → 반려 (사유: 위험도 높음)"
```

### KPI Memory
```yaml
보존: 영구
용도: 사용자 지정 KPI, 진전도 추적
예시:
  - "문서 작성: 월 5개 목표 (진행: 3개)"
  - "코드 리뷰: 주 2회 목표 (진행: 1회)"
```

### File Action Memory
```yaml
보존: 영구
용도: 파일 변경 이력, Diff 저장
예시:
  - "settings.py modified: +3 lines, -1 lines (2026.04.18 14:20)"
  - "backup created: 2026.04.18_backup.tar.gz (size: 145MB)"
```

---

## 🔄 자기개선 원칙

### 허용되는 것 ✅

- 외부 자료 **자율 수집**
- 정보 **자율 정리**
- 학습 후보 **자율 생성**
- 패턴 **자율 인식**

### 승인/검증 필요한 것 🔐

- 학습 결과의 **영구 메모리 반영**
- **프롬프트 핵심 규칙 변경**
- 새 Brain 또는 도구 **자동 호출 추가**
- **KPI 자동 생성 및 강제**

### 금지되는 것 ❌

- 온라인에서 **실시간 자기재학습**
- 사용자 알림 없이 **자신의 행동 규칙 변경**
- 승인 없이 **시스템 설정 수정**

---

## 🏃 운영 모드 (4가지)

### Daily Mode
```
목적: 일상 흐름 유지
활동: 대화, 일정 정리, 생각 발산
특징: 편안, 빠름, 기록만
```

### Work Mode
```
목적: 프로젝트 진행
활동: 계획 수립, 초안 작성, 검토, 승인 요청
특징: 구조화, 신중, 단계별
```

### Ops Mode
```
목적: 시스템 운영
활동: 파일 관리, 백업, 로그 확인, 설정 조정
특징: 기술적, 통제, 투명
```

### Learn Mode
```
목적: 지식 축적
활동: 자료 수집, 요약, 태깅, 승인 대기
특징: 자율적, 기다림, 기록
```

---

## 📁 권장 폴더 구조

```
jarvis_office/
├─ core/
│  ├─ jarvis_core.py
│  ├─ conductor.py
│  ├─ state_manager.py
│  └─ identity.py
├─ engines/
│  ├─ intent_engine.py
│  ├─ planning_engine.py
│  ├─ routing_engine.py
│  ├─ approval_engine.py
│  ├─ memory_engine.py
│  ├─ reflection_engine.py
│  └─ audit_engine.py
├─ brains/
│  ├─ gpt_oss_brain.py
│  ├─ gemma_brain.py
│  ├─ qwen_brain.py
│  └─ brain_registry.py
├─ memory/
│  ├─ personal_memory.py
│  ├─ work_memory.py
│  ├─ memory_store.py
│  └─ kpi_store.py
├─ tools/
│  ├─ file_tool.py
│  ├─ search_tool.py
│  ├─ backup_tool.py
│  ├─ log_tool.py
│  └─ document_tool.py
├─ runtime/
│  ├─ action_queue.py
│  ├─ approval_queue.py
│  ├─ task_runner.py
│  └─ scheduler.py
├─ api/
│  ├─ main.py
│  ├─ routers/
│  └─ auth.py
├─ ui/
│  ├─ pixel_office/
│  └─ assets/
├─ prompts/
├─ logs/
├─ backups/
└─ data/
```

---

## 🚀 필수 기술 스택

- **Python** 3.11+
- **FastAPI / Uvicorn** (API 서버)
- **Node.js / npm** (UI)
- **Ollama** (로컬 LLM 추론)
- **로컬 모델:**
  - JARVIS:latest (Gemma3 커스텀)
  - gemma3:4b
  - qwen 계열
  - gpt-oss 또는 대체 추론 모델

---

## ✨ 최종 정의

**JARVIS는 공개 모델 3종과 로컬 도구를 지휘하는 상위 Conductor이며, Pixel Agent Office를 몸체로 하고 승인 기반 파일 권한, 장기 기억, 유동 KPI 기록, 통제된 자기개선, 일상 대화를 포함하는 개인 전용 로컬 Agent OS다.**

---

## 📅 변경 이력

| 버전 | 날짜 | 변경 사항 |
|-----|------|---------|
| v1.0 | 2026.04.18 | 초안 작성 |

