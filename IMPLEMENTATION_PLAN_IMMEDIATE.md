# JARVIS 현재 상태 개선 - 실제 구현 가이드

## 🎯 현재 상태: 구현도 20% 미만

**핵심 문제**: 에이전트들이 기본만 하고 실제 작동 안 함

```
Planner: LLM 응답 받고 JSON 파싱만 함 → 계획 이상함
Executor: 파일 생성만 함 → 다른 작업 불가
Reviewer: "좋습니다/안 좋습니다"만 함 → 검증 미흡
Memory: 저장만 함 → 활용 안 함
WikiAgent: 존재만 함 → 기능 없음
```

---

## 📋 현재 코드 문제점 살펴보기

### 1. Planner 문제점 (planner.py)

#### 문제 코드
```python
async def auto_plan_today(self, message: str) -> Dict[str, Any]:
    # LLM에게 "계획해줄래?" 물어보기만 함
    response = await router.call(prompt=message, system=system_prompt)
    
    # JSON 파싱하기
    parsed = self._extract_json_from_response(response)
    
    # 항상 폴백 (계획 실패)
    if not parsed:
        return {
            "steps": [{"title": "기본 처리", "action": "research"}]  # 너무 단순
        }
    return parsed
```

**결과**: "JavaScript 앱 만들어" 요청이 들어와도 "기본 처리" 한 단계만 반환

#### 개선 방향
```python
async def auto_plan_today(self, message: str) -> Dict[str, Any]:
    # 1. 요청 분석 (종류 파악)
    analysis = await self._analyze_request(message)
    # → 결과: {"type": "code_generation", "complexity": "high", ...}
    
    # 2. 태스크 분해
    subtasks = await self._decompose_tasks(message, analysis)
    # → 결과: [
    #    {"id": 1, "title": "구조 설계"},
    #    {"id": 2, "title": "HTML", "depends_on": [1]},
    #    ...
    # ]
    
    # 3. 의존성 파악
    dependencies = self._identify_dependencies(subtasks)
    # → 결과: {"2,3,4": "can_run_parallel"}
    
    # 4. Skill 할당
    self._assign_skills(subtasks)
    # → 결과: subtasks[0]["skill"] = "CodeGenSkill"
    
    return {
        "steps": subtasks,
        "parallelizable": dependencies,
        "quality": "high"
    }
```

---

### 2. Executor 문제점 (executor.py)

#### 문제 코드
```python
async def execute_task(self, subtask: Dict[str, Any]) -> Dict[str, Any]:
    action_type = subtask.get("action_type", "create_file")
    
    # 지원 가능: create_file, update_file만...
    if action_type == "create_file":
        res = self.file_tool.create_file(target_path, content)
    elif action_type in ["update_file", "modify_file"]:
        res = self.file_tool.update_file(target_path, content)
    else:
        # 다른 작업? 모두 실패
        return {"ok": False, "error": "Unsupported action"}
```

**결과**: 파일 생성만 가능, 차트 분석/데이터 처리/API 호출 등 불가

#### 개선 방향
```python
async def execute_task(self, subtask: Dict[str, Any]) -> Dict[str, Any]:
    skill_name = subtask.get("skill")  # "CodeGenSkill"
    
    # Skill 레지스트리에서 Skill 로드
    skill = await self.skill_registry.get_skill(skill_name)
    
    # Skill에 맞게 실행
    if skill_name == "CodeGenSkill":
        return await skill.generate_code(subtask)
    elif skill_name == "DataProcessSkill":
        return await skill.process_data(subtask)
    elif skill_name == "AnalysisSkill":
        return await skill.analyze(subtask)
    # ... 기타 skills
```

---

### 3. Reviewer 문제점 (reviewer.py)

#### 문제 코드
```python
async def review_result(self, context: Dict[str, Any]) -> Dict[str, Any]:
    # LLM에게 "이거 맞나요?"만 물어보기
    review_text = await router.call(prompt=prompt, system=system_prompt)
    
    # "✅ PASS" 또는 "❌ FAIL" 있는지만 확인
    is_pass = "✅ PASS" in review_text
    return {"ok": is_pass, "feedback": review_text}
```

**결과**: 실제 검증 안 하고 LLM 감정만 묻기

#### 개선 방향
```python
async def review_result(self, context: Dict[str, Any]) -> Dict[str, Any]:
    # 1. 실제 검증
    syntax_errors = await self._check_syntax(context["code"], context["language"])
    if syntax_errors:
        return {"ok": False, "errors": syntax_errors}
    
    # 2. 테스트 실행
    test_results = await self._run_tests(context["code"])
    if not test_results["ok"]:
        return {"ok": False, "test_failures": test_results}
    
    # 3. 자동 수정 시도
    if syntax_errors or test_failures:
        fixed_code = await self._auto_fix(context["code"], errors)
        return {"ok": True, "code": fixed_code, "auto_fixed": True}
    
    # 4. 메트릭 수집
    metrics = await self._collect_metrics(context["code"])
    return {
        "ok": True,
        "metrics": metrics,
        "quality_score": 0.95
    }
```

---

## ✅ 즉시 해야 할 일 (우선순위)

### Step 1: Planner 개선 (오늘/내일) ⏱️ 3시간

**목표**: 실제 작동하는 계획 수립

#### 1-1. 요청 분석 함수 추가
```python
# planner.py에 추가
async def _analyze_request(self, message: str) -> dict:
    """
    사용자 요청의 종류 파악
    
    예)
    "JavaScript 앱 만들어" 
    → {"type": "code_generation", "framework": "vanilla", "target": "web"}
    
    "차트 분석해줘"
    → {"type": "data_analysis", "data_type": "chart", "goal": "insights"}
    """
    analyze_prompt = f"""
    사용자 요청 분석:
    "{message}"
    
    다음을 판단하고 JSON으로 반환:
    - type: code_generation | data_analysis | reporting | video_creation
    - complexity: simple | medium | complex
    - estimated_steps: 예상 단계 수
    - requires_external: API, 웹 크롤링 필요 여부
    """
    
    response = await router.call(analyze_prompt, self.system_base)
    return self._extract_json_from_response(response)
```

#### 1-2. 태스크 분해 함수 추가
```python
async def _decompose_tasks(self, message: str, analysis: dict) -> list:
    """
    구체적인 태스크 리스트 생성
    
    예)
    "JavaScript 앱 만들어"
    → [
        {"id": 1, "title": "프로젝트 구조 설계", "skill": "CodeGenSkill"},
        {"id": 2, "title": "HTML 템플릿 작성", "skill": "CodeGenSkill", "depends": [1]},
        ...
    ]
    """
    decompose_prompt = f"""
    사용자 요청을 구체적 단계로 분해하세요:
    "{message}"
    
    각 단계마다:
    - id: 1, 2, 3, ...
    - title: 단계 이름
    - description: 상세 설명
    - skill: CodeGenSkill | DataProcessSkill | ...
    - depends_on: [이전 단계 id]
    - estimated_time: 초 단위
    
    JSON 배열로 반환하세요.
    """
    
    response = await router.call(decompose_prompt, self.system_base)
    return self._extract_json_from_response(response) or []
```

#### 1-3. 의존성/병렬화 파악
```python
def _identify_parallelizable_groups(self, steps: list) -> list:
    """
    병렬 실행 가능한 그룹 식별
    
    예)
    steps = [
        {"id": 2, "depends": [1]},
        {"id": 3, "depends": [1]},
        {"id": 4, "depends": [1]},
    ]
    
    → [[2, 3, 4]]  # 이 3개는 동시에 실행 가능
    """
    # 의존성 없는 단계들 찾기
    independent_groups = []
    for step in steps:
        if not step.get("depends_on"):
            independent_groups.append(step["id"])
    
    return [independent_groups] + ... # 더 복잡한 로직
```

---

### Step 2: Executor Skill 개선 (내일) ⏱️ 2-3시간

**목표**: Skill 시스템 구현

#### 2-1. BaseSkill 클래스 (공통 인터페이스)
```python
# backend/app/harness/skills/base_skill.py
class BaseSkill:
    name: str  # "CodeGenSkill"
    description: str
    
    async def execute(self, task: dict, context: dict) -> dict:
        """Skill 실행 (구현 필수)"""
        raise NotImplementedError
    
    async def validate_input(self, task: dict) -> bool:
        """입력 유효성 검사"""
        return True
    
    async def estimate_duration(self, task: dict) -> float:
        """예상 소요 시간"""
        return 5.0  # 기본값 5초
```

#### 2-2. CodeGenSkill 구현 (기존 개선)
```python
# backend/app/harness/skills/code_gen_skill.py
class CodeGenSkill(BaseSkill):
    name = "CodeGenSkill"
    
    async def generate_code(self, task: dict, context: dict) -> dict:
        """
        코드 생성
        
        task:
        {
            "language": "python",
            "description": "팩토리알 함수",
            "style": "pythonic"
        }
        
        context:
        {
            "user_style": "prefer_type_hints",
            "project": {...}
        }
        """
        language = task.get("language", "python")
        description = task.get("description", "")
        
        prompt = f"""
        Generate {language} code:
        {description}
        
        Style: {context.get('user_style', 'default')}
        """
        
        code = await router.call(prompt, self.system_prompt)
        
        return {
            "ok": True,
            "code": code,
            "language": language,
            "quality": 0.8
        }
```

#### 2-3. DataProcessSkill 구현 (신규)
```python
# backend/app/harness/skills/data_process_skill.py
class DataProcessSkill(BaseSkill):
    name = "DataProcessSkill"
    
    async def process_data(self, task: dict, context: dict) -> dict:
        """
        데이터 처리
        - CSV 읽기
        - 데이터 정제
        - 통계 계산
        """
        operation = task.get("operation")  # read, clean, analyze
        
        if operation == "read":
            return await self._read_data(task)
        elif operation == "clean":
            return await self._clean_data(task)
        elif operation == "analyze":
            return await self._analyze_data(task)
```

#### 2-4. Skill Registry (Skill 관리)
```python
# backend/app/harness/skills/registry.py
class SkillRegistry:
    def __init__(self):
        self.skills = {
            "CodeGenSkill": CodeGenSkill(),
            "DataProcessSkill": DataProcessSkill(),
            # ... 추가 skills
        }
    
    async def get_skill(self, name: str) -> BaseSkill:
        skill = self.skills.get(name)
        if not skill:
            raise ValueError(f"Skill not found: {name}")
        return skill
    
    async def execute(self, skill_name: str, task: dict, context: dict) -> dict:
        skill = await self.get_skill(skill_name)
        return await skill.execute(task, context)
```

---

### Step 3: Executor 개선 (내일/모레) ⏱️ 2시간

**목표**: Skill을 실제로 사용

#### 3-1. execute_task 재작성
```python
# executor.py 수정
async def execute_task(self, task: dict, context: dict) -> dict:
    """
    Skill 기반 실행
    """
    skill_name = task.get("skill")
    
    if not skill_name:
        return {"ok": False, "error": "No skill specified"}
    
    try:
        # 1. Skill 로드
        skill = await self.skill_registry.get_skill(skill_name)
        
        # 2. Skill 실행
        result = await skill.execute(task, context)
        
        # 3. 결과 저장
        await self.memory.save_task_result(task["id"], result)
        
        return result
        
    except Exception as e:
        logger.error(f"Executor error: {e}")
        return {"ok": False, "error": str(e)}
```

---

### Step 4: Reviewer 개선 (모레) ⏱️ 2시간

**목표**: 실제 검증 + 자동 수정

#### 4-1. 언어별 문법 검사
```python
async def _check_syntax(self, code: str, language: str) -> list:
    """
    언어별 문법 검사
    """
    if language == "python":
        try:
            ast.parse(code)  # Python 문법 검사
            return []  # 에러 없음
        except SyntaxError as e:
            return [{"line": e.lineno, "error": e.msg}]
    
    elif language == "javascript":
        # eslint 호출
        result = subprocess.run([
            "eslint", "--format=json", "--stdin",
            "--stdin-filename=temp.js"
        ], input=code.encode(), capture_output=True)
        
        if result.returncode != 0:
            errors = json.loads(result.stdout)
            return errors
        return []
    
    # ... 다른 언어
```

#### 4-2. 자동 수정
```python
async def _auto_fix(self, code: str, errors: list) -> str:
    """
    에러 기반 자동 수정
    """
    fix_prompt = f"""
    다음 코드의 에러를 수정해주세요:
    
    에러:
    {errors}
    
    코드:
    {code}
    
    수정된 코드만 반환하세요.
    """
    
    fixed_code = await router.call(fix_prompt, self.system_prompt)
    return fixed_code
```

---

## 📊 실행 계획 요약

```
Day 1 (오늘/내일):
├─ Planner 개선 (3시간)
│  ├─ _analyze_request() 구현
│  ├─ _decompose_tasks() 구현
│  └─ _identify_parallelizable_groups() 구현
│
└─ Skill 시스템 개발 (2-3시간)
   ├─ BaseSkill 클래스 작성
   ├─ CodeGenSkill 개선
   ├─ DataProcessSkill 신규 작성
   └─ SkillRegistry 작성

Day 2 (모레):
├─ Executor 개선 (2시간)
│  └─ Skill 기반 execute_task() 재작성
│
└─ Reviewer 강화 (2시간)
   ├─ 실제 문법 검사 추가
   └─ 자동 수정 기능 추가

Day 3 (그 다음):
├─ 통합 테스트
├─ 디버깅
└─ 문서 작성
```

---

## 🎯 이렇게 하면 어떻게 되나?

### Before (현재)
```
User: "JavaScript 앱 만들어"
→ Planner: 계획 실패 (너무 단순)
→ 결과: 작동 안 함 ❌
```

### After (개선 후)
```
User: "JavaScript 앱 만들어"
→ Planner: 6개 단계 명확히 계획 ✅
→ Executor: Skill 기반 실행 ✅
→ Reviewer: 자동 검증 + 수정 ✅
→ Memory: 패턴 저장 ✅
→ 결과: 완성된 앱 ✅
```

---

**이 계획을 따르면 1-2주 내에 JARVIS가 실제로 작동하게 됩니다!**

