# JARVIS Agent Office — 전체 개발 히스토리

**문서 생성일**: 2026-04-19  
**현재 버전**: Core 4.0 + Confidence System  
**상태**: 🟢 운영 중

---

## 📌 프로젝트 개요

JARVIS(Jarvis Agent Repository Intelligence Virtual System)는 로컬 AI 기반 자율형 오피스 에이전트입니다.
Zero-Token(무료) 로컬 LLM을 기본으로 구동하며, 다중 에이전트 파이프라인과 자가 성장 지식망을 갖춘 AI 비서 시스템입니다.

---

## 📅 개발 타임라인

### Phase 1: 기초 구조 (2026-04-11 ~ 04-12)
> 대화 ID: `311c2d31`, `2f9a44c1`, `402fc5a9`

| 작업 | 상세 |
|------|------|
| 프로젝트 초기화 | FastAPI + React 기반 Agent Office 프로젝트 생성 |
| 시스템 트레이 런처 | Windows 백그라운드 실행 + 시스템 트레이 아이콘 |
| Ollama 연동 | 로컬 LLM(Qwen, Gemma) 연동 및 API 라우팅 |
| 리브랜딩 | 'Ollama' → 'JARVIS Intelligence Engine' 통일 |

**주요 파일:**
- `backend/app/main.py` — FastAPI 앱 진입점
- `backend/app/brains/base.py` — LLM 호출 기본 클래스
- `backend/app/llm_router.py` — v1 LLM 라우터 (레거시)

---

### Phase 2: 자율 에이전트 도입 (2026-04-13 ~ 04-14)
> 대화 ID: `30b5cc9b`, `4bc999e4`

| 작업 | 상세 |
|------|------|
| Autopus-ADK 통합 | Meta-Agent(Conductor) + 전문 에이전트 체계 |
| Agent Factory | Planner, Executor, Reviewer, Wiki Agent 구현 |
| RALF 루프 | Red-Green-Refactor 자가 수정 루프 설계 |
| AX_Vault | Obsidian 호환 지식 저장소 구조 생성 |

**주요 파일:**
- `backend/app/core/conductor.py` — 중앙 지휘 모듈
- `backend/app/agents/planner.py` — 기획 에이전트
- `backend/app/agents/executor.py` — 실행 에이전트
- `backend/app/agents/reviewer.py` — 검증 에이전트 (Ruff 린팅)
- `backend/app/agents/wiki.py` — 지식 성장 에이전트

**아키텍처 정의서:** `JARVIS AI Core 4.0 최종 통합 아키텍처 정의서.md`

---

### Phase 3: Hook 시스템 & 안정화 (2026-04-15 ~ 04-16)
> 대화 ID: `8bcf6e99`, `363bdfc3`

| 작업 | 상태 |
|------|------|
| Hook 3단계 전략 | WARN → SOFT → STRICT 단계적 완화 |
| 부트스트랩 안정화 | Ollama 헬스체크, 자동 시작 |
| Frontend 통합 | React build → FastAPI static 서빙 |
| SPA 라우팅 | catch-all 라우트로 프론트엔드 통합 |
| JARVIS.bat | 통합 런처 (포트 8000) |

**주요 파일:**
- `backend/app/harness/hooks_engine.py` — 보안 Hook 엔진
- `backend/app/harness/rules_engine.py` — 규칙 엔진
- `backend/app/core/bootstrap.py` — 부트스트랩 초기화
- `JARVIS.bat` — Windows 런처

---

### Phase 4: 하이브리드 리소스 & Red Team (2026-04-18)
> 대화 ID: `a8325ad8`

| 작업 | 상세 |
|------|------|
| 하이브리드 LLM 라우터 | Local + Cloud(Groq/Claude/HF) 하이브리드 라우팅 |
| Red Team 피드백 | 4가지 심각 결함 수정 (무료 한도, 캐시, 보안, SLA) |
| 민감 데이터 필터링 | 연봉/조직도/고객정보 → 로컬만 사용 |
| 동적 API 라우터 | 공식 API 페일오버 체계 |
| 비용 추적 | MetricsCollector SQLite 기반 |

**주요 파일:**
- `backend/app/llm/router.py` — v4 Smart Router (운영 중)
- `backend/app/llm/providers.py` — Ollama/Groq/Claude/HF 프로바이더
- `backend/app/llm/sensitivity.py` — 민감 데이터 필터링
- `backend/app/llm/cache.py` — 캐시 관리자
- `backend/app/core/metrics_collector.py` — 성능 메트릭 수집
- `backend/app/core/dynamic_api_router.py` — 동적 API 라우터

---

### Phase 5: 종적 신뢰도 시스템 (2026-04-19)
> 대화 ID: `8e4c3aa2` (현재)

| 작업 | 상태 |
|------|------|
| 신뢰도 스키마 | ✅ StepConfidence, PipelineConfidence, CompletionReport |
| 신뢰도 수집 엔진 | ✅ EMA 기반 종적 추적, 이상탐지, 동적 프로바이더 순위 |
| 완료보고서 생성기 | ✅ JSON + Markdown 자동 생성, AX_Vault 저장 |
| Conductor 계측 | ✅ 각 단계별 신뢰도 자동 기록 |
| LLM Router 동적화 | ✅ 실측 신뢰도 기반 프로바이더 우선순위 |
| REST API | ✅ `/api/confidence/*` 8개 엔드포인트 |
| 대화 모드 분류 수정 | ✅ ChatModeClassifier (chat/task/command) |
| 테스트 | ✅ 4/4 PASSED |

**신규 파일:**
- `backend/app/schemas/confidence.py` — 신뢰도 데이터 모델
- `backend/app/core/confidence_collector.py` — 신뢰도 수집 엔진
- `backend/app/core/completion_reporter.py` — 완료보고서 생성기
- `backend/app/api/routers/confidence.py` — 신뢰도 API

**수정 파일:**
- `backend/app/core/conductor.py` — 신뢰도 계측 삽입
- `backend/app/core/orchestrator.py` — ChatModeClassifier + 대화 모드 분리
- `backend/app/llm/router.py` — 종적 신뢰도 기반 동적 라우팅
- `backend/app/memory/repository.py` — DB 테이블 추가
- `backend/app/main.py` — 신뢰도 라우터 등록
- `backend/app/api/routers/chat.py` — 모드 전달 수정

---

## 🔧 파일 구조 정리 (중복 파일 분류)

### 운영 중 (Active)
```
backend/app/
├── api/routers/
│   ├── chat.py              ← 채팅 API (ChatModeClassifier 연동)
│   ├── confidence.py        ← 신뢰도 API (신규)
│   ├── health.py            ← 헬스체크
│   ├── hybrid.py            ← 하이브리드 리소스 관리
│   ├── mobile.py            ← 모바일 API
│   ├── tasks.py             ← 태스크 API
│   ├── approvals.py         ← 승인 API
│   └── prompts.py           ← 프롬프트 API
├── core/
│   ├── orchestrator.py      ← 메인 라우팅 (chat/task/command 분류)
│   ├── conductor.py         ← Conductor 파이프라인 (task 모드)
│   ├── confidence_collector.py ← 종적 신뢰도 수집 (신규)
│   ├── completion_reporter.py  ← 완료보고서 생성 (신규)
│   ├── bootstrap.py         ← 부트스트랩
│   ├── metrics_collector.py ← 성능 메트릭
│   └── cache_layer.py       ← 캐시 계층
├── agents/
│   ├── planner.py           ← 기획 에이전트 (운영)
│   ├── executor.py          ← 실행 에이전트 (운영)
│   ├── reviewer.py          ← 검증 에이전트 (운영)
│   └── wiki.py              ← 지식 에이전트 (운영)
├── llm/
│   ├── router.py            ← v4 Smart Router (운영 - 신뢰도 통합)
│   ├── providers.py         ← LLM 프로바이더들
│   ├── sensitivity.py       ← 민감 데이터 필터
│   └── cache.py             ← LLM 캐시
├── schemas/
│   ├── v4_core.py           ← Core 4.0 스키마
│   ├── confidence.py        ← 신뢰도 스키마 (신규)
│   └── chat.py              ← 채팅 스키마
├── memory/
│   └── repository.py        ← SQLite 저장소 (신뢰도 테이블 포함)
└── main.py                  ← FastAPI 앱 (라우터 등록)
```

### 레거시 (미사용 - 참조용)
```
backend/app/
├── llm_router.py            ← v1 LLM Router (llm/router.py로 대체)
├── llm_router_v2.py         ← v2 LLM Router (llm/router.py로 대체)
├── llm_router/
│   └── smart_router.py      ← v3 Smart Router (llm/router.py로 대체)
├── agents/
│   ├── planner_v2.py        ← v2 Planner (planner.py로 대체)
│   ├── planner_v4.py        ← v4 Planner (planner.py로 대체)
│   ├── executor_v4.py       ← v4 Executor (executor.py로 대체)
│   └── wiki_agent.py        ← 이전 WikiAgent (wiki.py로 대체)
├── brains/
│   ├── base.py              ← 이전 Brain 시스템 (llm/providers.py로 대체)
│   ├── qwen_brain.py        ← Qwen Brain (통합됨)
│   ├── gemma_brain.py       ← Gemma Brain (통합됨)
│   └── gpt_oss_brain.py     ← GPT-OSS Brain (통합됨)
└── core_v4/                 ← v4 마이그레이션 잔여 (llm/으로 통합)
```

---

## 🚨 해결된 주요 이슈

### Issue 1: 대화가 안 되는 문제 (2026-04-19)
**증상**: 모든 메시지에 "✅ 작업 완료 (상태: completed, 단계: 0)" 반환
**원인**: `orchestrator.py`가 모든 메시지를 `conductor`(Plan→Execute→Review)로 전달
**해결**: `ChatModeClassifier` 도입 — chat/task/command 3가지 모드 분류
- "안녕" → chat 모드 → LLM 직접 응답 (자연스러운 대화)
- "파일 만들어" → task 모드 → Conductor 파이프라인
- "/help" → command 모드 → 슬래시 명령어 처리

### Issue 2: 중복 파일 충돌
**증상**: 같은 기능의 파일이 여러 버전으로 존재
**원인**: v1→v2→v4 마이그레이션 과정에서 이전 파일 미삭제
**해결**: 운영/레거시 파일 분류 문서화 (위 참조)

### Issue 3: 신뢰도 추적 부재
**증상**: 파이프라인 성공/실패만 기록, 품질 수치화 없음
**해결**: 종적 신뢰도 시스템 구현 (EMA 기반 추적, 완료보고서 자동 생성)

---

## 📊 현재 시스템 아키텍처

```
사용자 요청 (CLI / Web UI / Mobile)
        ↓
┌─────────────────────────────────┐
│  ChatModeClassifier             │
│  "안녕" → chat | "파일 만들어" → task | "/help" → command
└─────────┬────────┬────────┬─────┘
          ↓        ↓        ↓
       [Chat]   [Task]   [Command]
          ↓        ↓        ↓
      LLM직접  Conductor  명령처리
          ↓    ┌───┴───┐
          ↓    ↓       ↓
          ↓  Planner → Executor → Reviewer → Wiki
          ↓    ↓       ↓           ↓          ↓
          ↓    └── confidence_collector ──────┘
          ↓              ↓
          ↓    completion_reporter
          ↓        ↓
     ┌────┴────────┴───────┐
     │    SmartRouterV4     │
     │  (신뢰도 기반 라우팅) │
     ├─ Local Ollama (기본)  │
     ├─ Groq (페일오버)      │
     ├─ Claude (페일오버)    │
     └─ HuggingFace (보조)  │
     └─────────────────────┘
```

---

## ✅ 운영 체크리스트

- [x] 대화 모드 분류기 구현 (chat/task/command)
- [x] 파이프라인 신뢰도 수치화 (0.0~1.0)
- [x] 종적 추적 (EMA 기반 시계열)
- [x] 완료보고서 자동 생성 (AX_Vault)
- [x] 동적 프로바이더 라우팅 (신뢰도 기반)
- [x] REST API 8개 (`/api/confidence/*`)
- [x] 테스트 4/4 PASSED
- [x] 운영/레거시 파일 분류 정리
- [x] 전체 히스토리 문서화

---

**마지막 업데이트**: 2026-04-19 23:32  
**다음 목표**: 레거시 파일 정리 (archives/ 이동), Frontend 신뢰도 대시보드
