# JARVIS 현재 상태 진단

## 🔴 심각한 구현 미흡 상황

### 1️⃣ Planner (계획 수립) - 구현도 20%

#### 현재 상태
```python
# planner.py
async def auto_plan_today(self, message: str) -> Dict[str, Any]:
    """
    문제점:
    1. JSON 파싱만 함 (LLM 응답을 받고 파싱하기만)
    2. 실제 계획 수립 로직 없음
    3. 의존성 분석 없음
    4. 병렬화 식별 불가
    5. 단계별 리소스 할당 없음
    """
```

#### 결과물 예시
```python
{
    "goal": "사용자 요청: JavaScript로 할일 앱 만들어줘",
    "priority": "medium",
    "steps": [
        {
            "title": "기본 처리",
            "action": "research",
            "path": "사용자_요청",
            "instruction": "..."
        }
    ]
}
# → 너무 단순함. 실제 실행 불가능
```

#### 필요한 개선
```
✅ 할 일
├─ 실제 계획 수립 로직 추가
│  ├─ 요청 분석 (어떤 종류의 작업인가?)
│  ├─ 태스크 분해 (몇 개의 단계?)
│  ├─ 의존성 그래프 구성
│  └─ 병렬 그룹 식별
│
├─ Skill 자동 맵핑
│  ├─ "코드" → CodeGenSkill
│  ├─ "데이터" → DataProcessSkill
│  └─ "분석" → AnalysisSkill
│
├─ 예상 시간 계산
│
└─ 에러 처리
   ├─ 복잡도 초과 시 경고
   └─ 불가능한 작업 감지
```

---

### 2️⃣ Executor (실행) - 구현도 35%

#### 현재 상태
```python
# executor.py
async def execute_task(self, subtask: Dict[str, Any]) -> Dict[str, Any]:
    """
    문제점:
    1. 파일 생성/수정만 지원 (create_file, update_file)
    2. 코드 생성만 지원
    3. 다른 종류의 작업 불가능:
       - 웹 크롤링 안 함
       - 데이터 처리 안 함
       - 이미지 생성 안 함
       - API 호출 안 함
    4. 순차 실행만 지원 (병렬 안 됨)
    5. 컨텍스트 전달 미약
    """
```

#### 구현된 것
```
✅ create_file - O
✅ update_file - O
❌ data_process - X
❌ web_scrape - X
❌ image_generate - X
❌ api_call - X
❌ parallel_exec - X
```

#### 필요한 개선
```
✅ 해야 할 일
├─ 다양한 Skill 구현
│  ├─ CodeGenSkill (코드 생성)
│  ├─ DataProcessSkill (데이터 처리)
│  ├─ WebScraperSkill (웹 크롤링)
│  ├─ ImageGenSkill (이미지 생성)
│  ├─ APICallerSkill (API 호출)
│  └─ AnalysisSkill (분석)
│
├─ 병렬 실행 지원
│  ├─ asyncio.gather() 활용
│  ├─ 최대 동시 작업 수 제한
│  └─ 순환 대기(deadlock) 방지
│
├─ 컨텍스트 관리
│  ├─ 이전 결과 전달
│  ├─ Memory 접근
│  └─ 상태 추적
│
└─ 에러 처리
   ├─ 재시도 로직
   ├─ 롤백 기능
   └─ 상세 오류 메시지
```

---

### 3️⃣ Reviewer (검증) - 구현도 10%

#### 현재 상태
```python
# reviewer.py
async def review_result(self, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    문제점:
    1. LLM에게 "검토해줄래?"만 함
    2. 실제 컴파일/테스트 안 함
    3. 자동 수정 기능 없음
    4. 메트릭 수집 안 함
    5. 재작업 지시 기능 없음
    """
```

#### 구현된 것
```
✅ "✅ PASS" 또는 "❌ FAIL" 문자열만 생성
❌ 실제 문법 체크 - X
❌ 실제 테스트 - X
❌ 자동 수정 - X
❌ 메트릭 수집 - X
```

#### 필요한 개선
```
✅ 해야 할 일
├─ 실제 검증 로직
│  ├─ 언어별 컴파일 체크
│  │  ├─ Python: ast.parse()
│  │  ├─ JavaScript: eslint
│  │  └─ Java: javac
│  │
│  ├─ 단위 테스트 실행
│  └─ 리팩토링 제안
│
├─ 자동 수정
│  ├─ 에러 메시지 분석
│  ├─ 수정 코드 생성
│  └─ 재실행
│
├─ 메트릭 수집
│  ├─ 코드 길이
│  ├─ 복잡도
│  ├─ 커버리지
│  └─ 성능
│
└─ 통계
   ├─ 성공률
   ├─ 평균 재시도
   └─ 개선 추이
```

---

### 4️⃣ WikiAgent (지식 저장) - 구현도 0%

#### 현재 상태
```python
# wiki_agent.py
# 파일이 거의 비어있거나 기본만 있음
# 실제 지식 저장/로드 기능 없음
```

#### 필요한 개선
```
✅ 해야 할 일
├─ 지식 저장
│  ├─ 실행 이력 저장
│  ├─ 성공 패턴 기록
│  └─ 실패 사례 기록
│
├─ 지식 조회
│  ├─ 유사 작업 검색
│  └─ 과거 솔루션 제시
│
├─ 효과도 관리
│  ├─ 사용 횟수 추적
│  ├─ 성공률 계산
│  └─ 개선 제안
│
└─ 학습
   ├─ 패턴 추출
   ├─ 사용자 선호 학습
   └─ 점진적 최적화
```

---

### 5️⃣ Memory (메모리 시스템) - 구현도 20%

#### 현재 상태
```python
# memory/repository.py
# 기본 저장소만 있음
# 컨텍스트 관리 미흡
# 검색 기능 없음
```

#### 필요한 개선
```
✅ 해야 할 일
├─ 사용자 컨텍스트
│  ├─ 선호 언어
│  ├─ 선호 스타일
│  └─ 과거 요청
│
├─ 프로젝트 컨텍스트
│  ├─ 프로젝트 구조
│  ├─ 사용 라이브러리
│  └─ 네이밍 규칙
│
├─ 실행 이력
│  ├─ 각 작업별 결과
│  ├─ 소요 시간
│  └─ 성공/실패 여부
│
└─ 검색
   ├─ 의미 기반 검색
   ├─ 태그 기반 검색
   └─ 유사도 계산
```

---

## 💡 현실적인 개선 전략

### 우선순위 (지금 해야 할 것)

#### 1순위: Planner 완성도 확보 (1-2일)
```
이것이 없으면 다른 모든 것이 작동 안 함

✅ 해야 할 일
├─ 요청 분석 (사용자 요청의 종류 파악)
├─ 작은 태스크로 분해
├─ 의존성 파악
├─ 병렬화 가능 영역 식별
└─ 각 태스크별 Skill 할당

예시:
입력: "JavaScript로 할일 앱 만들어줘"

현재:
{
    "steps": [
        {"title": "기본 처리", "action": "research"}
    ]
}

개선 후:
{
    "steps": [
        {"id": 1, "title": "프로젝트 구조 설계", "skill": "CodeGenSkill.design"},
        {"id": 2, "title": "HTML 작성", "skill": "CodeGenSkill", "depends_on": [1]},
        {"id": 3, "title": "CSS 작성", "skill": "CodeGenSkill", "depends_on": [1]},
        {"id": 4, "title": "JavaScript 로직", "skill": "CodeGenSkill", "depends_on": [1]},
        {"id": 5, "title": "테스트", "skill": "TestGenSkill", "depends_on": [2,3,4]},
        {"id": 6, "title": "문서화", "skill": "DocGenSkill", "depends_on": [1,2,3,4]}
    ],
    "parallelizable": [[2,3,4], [5], [6]]
}
```

#### 2순위: Executor 확장 (1-2일)
```
Planner가 하는 일에 따라 실제 실행

✅ 해야 할 일
├─ CodeGenSkill 강화 (다양한 언어 지원)
├─ 한두 개 추가 Skill 구현
│  ├─ DataProcessSkill (핵심)
│  └─ TestGenSkill (테스트 생성)
└─ 순차 실행은 유지 (병렬은 나중)
```

#### 3순위: Reviewer 강화 (1-2일)
```
생성된 결과물 검증

✅ 해야 할 일
├─ 언어별 문법 검사 추가
├─ 자동 재작업 로직 추가
└─ 피드백 개선
```

#### 4순위: Memory 활성화 (1일)
```
각 작업 결과 저장

✅ 해야 할 일
├─ 작업 이력 저장
├─ 간단한 검색
└─ 컨텍스트 로드
```

---

## 📊 현재 vs 개선 후

### 현재 (구현도 낮음)
```
User: "JavaScript 앱 만들어줘"
  ↓
Planner: {"steps": [{"title": "기본 처리"}]} (너무 간단)
  ↓
Executor: 뭘 해야 할지 모름 (에러)
  ↓
결과: 실패
```

### 개선 후 (구현도 높음)
```
User: "JavaScript 앱 만들어줘"
  ↓
Planner: 6개 단계 계획, 병렬 가능 식별
  ↓
Executor: 각 단계 명확하게 실행 (병렬 가능하면 한번에)
  ↓
Reviewer: 각 결과 자동 검증
  ↓
Memory: 패턴 저장
  ↓
결과: 성공 ✅
```

---

## 🎯 지금부터 해야 할 일

### 이번 주 목표
```
□ Planner 구현도 80% 이상
  ├─ 실제 태스크 분해 로직 추가
  └─ 의존성 파악 로직 추가

□ 최소 2개 Executor Skill 완성
  ├─ CodeGenSkill (있는 것 강화)
  └─ DataProcessSkill (신규)

□ Executor 순차 실행은 완벽하게
  ├─ 에러 처리 강화
  └─ 컨텍스트 전달 개선

□ Reviewer 자동 수정 기능 추가
  ├─ 에러 감지 → 수정 생성 → 재실행

□ Memory에 실행 이력 저장
```

### 다음 주 목표
```
□ Executor 병렬화
  ├─ asyncio.gather() 기반
  └─ 의존성 순서 유지

□ WikiAgent 활성화
  ├─ 성공 패턴 저장
  └─ 재사용 제안

□ 40% 이상 성공률 달성
```

---

## 📋 구체적 Task (우선순위 순)

### Task 1: Planner 재작성 (가장 중요)
**파일**: `backend/app/agents/planner.py`

```
목표: 실제 작동하는 계획 수립
시간: 2-3시간

요구사항:
✅ 요청 분석
   - "코드 생성" vs "데이터 분석" vs "보고서"
   - 복잡도 판단

✅ 태스크 분해
   - 큰 작업을 작은 단계로 쪼개기
   - 예: "앱 만들기" → 6개 단계

✅ 의존성 파악
   - 어떤 단계가 먼저 와야 하는가?
   - 동시 실행 가능한가?

✅ Skill 할당
   - 각 단계에 적절한 Skill 선택

✅ 예상 시간 계산
   - 과거 이력 기반
```

### Task 2: CodeGenSkill 강화
**파일**: `backend/app/harness/skills/code_gen_skill.py` (또는 신규)

```
목표: 다양한 언어, 다양한 코드 생성
시간: 1-2시간

지원 대상:
✅ Python
✅ JavaScript  
✅ Java
✅ 웹 (HTML/CSS)
```

### Task 3: Executor 강화
**파일**: `backend/app/agents/executor.py`

```
목표: Planner가 주는 명확한 지시 실행
시간: 1-2시간

요구사항:
✅ Skill 호출 개선
✅ 컨텍스트 전달
✅ 에러 처리
```

### Task 4: Reviewer 개선
**파일**: `backend/app/agents/reviewer.py`

```
목표: 자동 검증 + 수정
시간: 1-2시간

요구사항:
✅ 언어별 문법 검사
✅ 자동 수정 시도
✅ 재실행
```

---

## ✅ 최종 결론

**새로운 기능 추가 전에:**

❌ 약한 부분 먼저 강화하자
- Planner (계획 수립) 완성
- Executor (실행) 완성
- Reviewer (검증) 완성
- 그 다음 병렬화/지식축적

**이렇게 하면:**
- 기초가 탄탄해짐
- 에이전트가 실제로 작동
- 나중에 확장이 쉬움

---

**우선순위**: Planner → Executor → Reviewer → 병렬화 → 지식

