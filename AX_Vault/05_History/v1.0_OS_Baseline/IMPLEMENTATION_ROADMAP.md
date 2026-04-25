# JARVIS 아키텍처 강화 - 실행 계획

## 📋 최우선 순위: 로컬 Ollama 연결 안정화

이미 준비된 것 ✅:
- `llm_router_v2.py` (하이브리드 모드)
- `settings_v2.py` (환경 설정)
- `.env.example_v2` (템플릿)

### 1단계: llm_router_v2 통합 (1시간)
```bash
# 선택사항
# Option 1: 기존 llm_router.py 교체
cp backend/app/llm_router_v2.py backend/app/llm_router.py

# Option 2: 병행 운영 (안전)
# chat.py에서 import 변경하면 됨
```

### 2단계: 환경 설정 (30분)
```bash
# .env 또는 .env.local
LLM_MODE=hybrid
OPENAI_API_KEY=sk-proj-xxx  # 선택사항
```

### 3단계: 테스트 (30분)
```bash
# 로컬 테스트
ollama serve

# 별도 터미널
python jarvis_cli.py
# → "코드 생성해줘" 입력
# → ✅ 작동 확인
```

---

## 🎯 Phase별 강화 계획

### Phase 1️⃣: Planner 강화 (2-3시간)

#### 현재 상태
```python
# backend/app/agents/planner.py
async def auto_plan_today(message: str) -> dict:
    # 복잡한 계획 생성 시도
    # 결과: 대부분 empty
```

#### 강화안
```python
# 새로운 플래너
class EnhancedPlanner:
    """다목적 작업 계획 수립"""
    
    async def auto_plan_today(self, message: str) -> dict:
        """
        입력: "JavaScript로 할일 앱 만들어줘"
        
        출력:
        {
            "goal": "JavaScript Todo App 개발",
            "steps": [
                {
                    "id": 1,
                    "title": "프로젝트 구조 설계",
                    "dependencies": [],
                    "executable": True,
                    "parallel_safe": True,
                    "skill": "CodeGenSkill.design_architecture"
                },
                {
                    "id": 2,
                    "title": "HTML 템플릿 생성",
                    "dependencies": [1],
                    "executable": True,
                    "skill": "CodeGenSkill.generate_html"
                },
                {
                    "id": 3,
                    "title": "JavaScript 로직 생성",
                    "dependencies": [1],
                    "executable": True,
                    "skill": "CodeGenSkill.generate_js"
                },
                {
                    "id": 4,
                    "title": "CSS 스타일링",
                    "dependencies": [2],
                    "executable": True,
                    "skill": "CodeGenSkill.generate_css"
                },
                {
                    "id": 5,
                    "title": "테스트 코드 생성",
                    "dependencies": [3],
                    "executable": True,
                    "skill": "CodeGenSkill.generate_tests"
                },
                {
                    "id": 6,
                    "title": "README 작성",
                    "dependencies": [1,2,3,4,5],
                    "executable": True,
                    "skill": "CodeGenSkill.generate_docs"
                }
            ],
            "parallelizable_groups": [
                [2, 3],  # HTML과 JS 동시 생성 가능
                [4]      # CSS
            ],
            "estimated_time": 180,  # 초 단위
            "priority": "high"
        }
        """
```

#### 구현 방법
```python
# 1. 의존성 분석 추가
def analyze_dependencies(steps: List[dict]) -> List[List[int]]:
    # 병렬 실행 가능한 그룹 식별
    
# 2. Skill 맵핑
SKILL_MAP = {
    "코드": "CodeGenSkill",
    "차트": "ChartAnalysisSkill",
    "영상": "VideoCreationSkill",
    "보고서": "ReportGenSkill",
}

# 3. 예상 시간 계산
def estimate_time(steps: List[dict]) -> float:
    # 기존 실행 기록 기반 예측
    # Memory.get_average_execution_time(skill_name)
```

---

### Phase 2️⃣: Executor 병렬화 (2-3시간)

#### 현재 상태
```python
# 순차 실행만 지원
for step in steps:
    result = await executor.execute_step(step)
```

#### 강화안
```python
class EnhancedExecutor:
    """병렬 실행 지원"""
    
    async def execute_steps(self, steps: List[dict]) -> dict:
        """
        병렬성을 고려한 실행
        
        예) 6개 작업, 순차: 10초 → 병렬: 3초
        """
        # 의존성 그래프 구성
        graph = self._build_dependency_graph(steps)
        
        # 병렬 실행 가능한 레이어 식별
        layers = self._identify_parallel_layers(graph)
        
        # 각 레이어 병렬 실행
        results = {}
        for layer in layers:
            layer_results = await asyncio.gather([
                self._execute_step_with_context(step, results)
                for step in layer
            ])
            results.update(layer_results)
        
        return results
    
    async def _execute_step_with_context(self, step: dict, previous_results: dict):
        """
        단계별 실행
        - Skill 호출
        - Memory에서 컨텍스트 로드
        - 오류 처리
        - 결과 저장
        """
        skill_name = step.get("skill")  # "CodeGenSkill.generate_js"
        
        # 1. Skill 인스턴스 로드
        skill = await SkillRegistry.get_skill(skill_name)
        
        # 2. 컨텍스트 준비 (이전 결과 포함)
        context = {
            "previous_results": previous_results,
            "user_context": await Memory.load_user_context(),
            "project_context": await Memory.load_project_context(),
        }
        
        # 3. Skill 실행
        try:
            result = await skill.execute(step, context)
        except Exception as e:
            # 4. 오류 처리 및 복구
            result = await self._handle_error(step, e, context)
        
        # 5. 결과 저장
        await Memory.save_step_result(step["id"], result)
        
        return {step["id"]: result}
```

---

### Phase 3️⃣: Reviewer 구현 (2-3시간)

#### 새로운 컴포넌트
```python
class EnhancedReviewer:
    """생성 결과 품질 검증"""
    
    async def review(self, execution_results: dict, original_request: str) -> dict:
        """
        예) JavaScript 코드 생성 후 검토
        
        검증 항목:
        - 문법 오류
        - 성능 이슈
        - 보안 취약점
        - 요구사항 충족 여부
        - 개선안 제시
        """
        reviews = {}
        
        for step_id, result in execution_results.items():
            review = await self._review_single_result(
                step_id,
                result,
                original_request
            )
            reviews[step_id] = review
        
        # 종합 평가
        overall_score = sum(r["score"] for r in reviews.values()) / len(reviews)
        
        return {
            "overall_score": overall_score,
            "detailed_reviews": reviews,
            "suggestions": self._aggregate_suggestions(reviews),
            "passed_qa": overall_score >= 0.8
        }
    
    async def _review_single_result(self, step_id: int, result: dict, request: str):
        """단일 결과 검토"""
        
        if "code" in result:
            return await self._review_code(result["code"], request)
        elif "chart" in result:
            return await self._review_chart(result["chart"], request)
        elif "report" in result:
            return await self._review_report(result["report"], request)
        # ... 기타
```

---

### Phase 4️⃣: WikiAgent + Memory 구현 (2-3시간)

#### Memory 시스템 강화
```python
class EnhancedMemory:
    """장기 학습 및 누적"""
    
    async def save_execution_history(self, 
                                    request: str,
                                    steps: List[dict],
                                    results: dict,
                                    review: dict):
        """
        모든 실행 기록 저장하여 학습
        
        시간이 지날수록 더 똑똑해짐
        """
        history = {
            "timestamp": datetime.now(),
            "request": request,
            "steps": steps,
            "results": results,
            "review": review,
            "success": review["passed_qa"],
            "execution_time": sum(s.get("duration", 0) for s in steps)
        }
        
        # 1. 직접 저장
        await self.db.save_history(history)
        
        # 2. 패턴 추출 및 저장
        patterns = await self._extract_patterns(history)
        await self.db.save_patterns(patterns)
        
        # 3. 사용자 선호사항 업데이트
        await self._update_user_preferences(history)
    
    async def suggest_improvements(self, similar_past_tasks: List[dict]) -> List[str]:
        """
        과거 유사 작업 기반 개선안 제시
        """
        suggestions = []
        
        for past_task in similar_past_tasks:
            if past_task["success"]:
                # 성공한 방식은 추천
                suggestions.append(f"Previous successful approach: {past_task['approach']}")
            else:
                # 실패한 방식은 피하도록
                suggestions.append(f"Avoid: {past_task['failed_approach']}")
        
        return suggestions
```

#### WikiAgent 구현
```python
class EnhancedWikiAgent:
    """지식 기반 구축 및 활용"""
    
    async def store_knowledge(self, 
                             category: str,
                             content: dict,
                             tags: List[str]):
        """
        지식 저장
        
        예) 
        category: "code_patterns"
        content: {
            "pattern": "React Hook Pattern",
            "code": "...",
            "use_cases": ["state management", "side effects"],
            "benefits": ["reusable", "testable"]
        }
        tags: ["react", "hooks", "javascript"]
        """
        
        knowledge = {
            "id": self._generate_id(),
            "category": category,
            "content": content,
            "tags": tags,
            "created_at": datetime.now(),
            "usage_count": 0,
            "effectiveness_score": 0.5  # 초기값
        }
        
        await self.db.store_knowledge(knowledge)
    
    async def retrieve_relevant_knowledge(self, query: str, context: str) -> List[dict]:
        """
        관련 지식 검색 및 제시
        """
        # 쿼리 벡터화
        query_embedding = await self._vectorize(query)
        
        # 유사 지식 검색
        similar_knowledge = await self.db.search_by_embedding(
            query_embedding,
            limit=5,
            context_filter=context
        )
        
        # 효과도 순으로 정렬
        sorted_knowledge = sorted(
            similar_knowledge,
            key=lambda x: x["effectiveness_score"],
            reverse=True
        )
        
        return sorted_knowledge
    
    async def update_effectiveness(self, knowledge_id: str, success: bool):
        """
        지식의 효과도 업데이트
        (사용할수록 효과도 증가)
        """
        knowledge = await self.db.get_knowledge(knowledge_id)
        knowledge["usage_count"] += 1
        
        if success:
            knowledge["effectiveness_score"] *= 1.05  # 5% 증가
        else:
            knowledge["effectiveness_score"] *= 0.95  # 5% 감소
        
        await self.db.update_knowledge(knowledge)
```

---

### Phase 5️⃣: Skills 시스템 확장 (3-4시간)

#### 기본 Skill 인터페이스
```python
class BaseSkill:
    """모든 Skill의 기본 클래스"""
    
    name: str  # "CodeGenSkill"
    version: str = "1.0"
    required_models: List[str] = []
    
    async def execute(self, 
                     step: dict, 
                     context: dict) -> dict:
        """
        Skill 실행
        
        입력:
            step: {"id": 1, "title": "...", "params": {...}}
            context: {"previous_results": {...}, "user_context": {...}}
        
        출력:
            {"result": "...", "metadata": {...}, "duration": 2.5}
        """
        pass
    
    async def validate_input(self, step: dict) -> bool:
        """입력 검증"""
        pass
    
    async def estimate_duration(self, step: dict) -> float:
        """실행 시간 예측"""
        pass
```

#### 코드 생성 Skill
```python
class CodeGenSkill(BaseSkill):
    name = "CodeGenSkill"
    
    async def generate_function(self, 
                               spec: dict,
                               context: dict) -> dict:
        """
        함수 생성
        
        입력:
            spec: {
                "name": "validate_email",
                "language": "python",
                "description": "검증 로직...",
                "examples": [...]
            }
        """
        prompt = f"""
        Generate a {spec['language']} function:
        - Name: {spec['name']}
        - Description: {spec['description']}
        - Examples: {spec['examples']}
        
        Requirements:
        - Include error handling
        - Add docstring
        - Follow best practices
        """
        
        code = await llm_router.call(prompt, self.system_prompt)
        
        return {
            "code": code,
            "language": spec["language"],
            "metadata": {
                "generated_at": datetime.now(),
                "model": settings.jarvis_model
            }
        }
    
    async def generate_tests(self, 
                            code: str,
                            spec: dict) -> dict:
        """테스트 코드 생성"""
        # 마찬가지로 LLM 호출
        pass
    
    async def generate_docs(self, code: str) -> dict:
        """문서 생성"""
        pass
```

#### 차트 분석 Skill
```python
class ChartAnalysisSkill(BaseSkill):
    name = "ChartAnalysisSkill"
    
    async def collect_data(self, 
                          symbol: str,
                          period: str) -> dict:
        """
        주식/코인 데이터 수집
        
        예) BTC/KRW 1일봉 최近 100개
        """
        # API 호출 (yfinance, 등등)
        data = await self._fetch_market_data(symbol, period)
        
        return {
            "data": data,
            "symbol": symbol,
            "period": period,
            "count": len(data)
        }
    
    async def analyze(self, 
                     data: dict,
                     indicators: List[str]) -> dict:
        """
        기술적 분석
        
        지표: RSI, MACD, Bollinger Band, 등등
        """
        analysis = {}
        
        for indicator in indicators:
            analysis[indicator] = await self._calculate_indicator(
                data,
                indicator
            )
        
        # 신호 생성
        signals = await self._generate_signals(analysis)
        
        return {
            "analysis": analysis,
            "signals": signals,
            "confidence": 0.85
        }
    
    async def generate_report(self, analysis: dict) -> dict:
        """분석 보고서 생성"""
        pass
```

#### 영상 제작 Skill
```python
class VideoCreationSkill(BaseSkill):
    name = "VideoCreationSkill"
    
    async def create_script(self, topic: str, duration: int) -> dict:
        """
        유튜브 스크립트 생성
        
        입력:
            topic: "파이썬 초급 강좌"
            duration: 600 (10분)
        """
        prompt = f"""
        Create a {duration}초 YouTube script for: {topic}
        
        Structure:
        - Hook (0-10초): 흥미 유발
        - Intro (10-30초): 주제 소개
        - Body (30-500초): 핵심 내용
        - Outro (500-600초): 마무리
        
        Requirements:
        - Engaging and clear
        - Include timestamps
        - Add visual direction hints
        """
        
        script = await llm_router.call(prompt, self.system_prompt)
        
        return {
            "script": script,
            "duration": duration,
            "visual_cues": await self._extract_visual_cues(script)
        }
    
    async def create_editing_guide(self, script: dict) -> dict:
        """
        편집 가이드 생성
        
        - 카메라 위치
        - 음악 추천
        - 자막 타이밍
        - 효과음
        """
        pass
```

---

### Phase 6️⃣: 병렬화 최적화 (2-3시간)

#### Asyncio 기반 최적화
```python
class ParallelExecutor:
    """병렬 실행 관리"""
    
    async def execute_parallel_tasks(self, 
                                     tasks: List[Coroutine],
                                     max_concurrent: int = 5) -> List[dict]:
        """
        여러 작업을 병렬로 실행
        
        제어:
        - CPU 집약적 작업은 ProcessPool
        - I/O 작업은 asyncio
        - 최대 동시 실행 수 제한
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def bounded_task(task):
            async with semaphore:
                return await task
        
        results = await asyncio.gather(*[
            bounded_task(task) for task in tasks
        ], return_exceptions=True)
        
        return results
    
    async def execute_with_timeout(self, 
                                   coro: Coroutine,
                                   timeout: float) -> dict:
        """
        타임아웃 포함 실행
        """
        try:
            result = await asyncio.wait_for(coro, timeout=timeout)
            return {
                "success": True,
                "result": result,
                "timed_out": False
            }
        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": "Timeout exceeded",
                "timed_out": True
            }
```

---

## 📊 구현 일정

```
Week 1: 기초 (10-12시간)
├─ Day 1 (1-2h): llm_router_v2 통합 + 테스트
├─ Day 2 (2-3h): Planner 강화
├─ Day 3 (2-3h): Executor 병렬화
└─ Day 4 (2-3h): Reviewer 구현

Week 2: 지능화 (8-10시간)
├─ Day 1 (2-3h): Memory 강화
├─ Day 2 (2-3h): WikiAgent 구현
├─ Day 3 (2-3h): Skills 개발 (코드생성, 차트분석)
└─ Day 4 (2-3h): 추가 Skills (영상, 보고서)

Week 3: 최적화 (4-6시간)
├─ Day 1 (2-3h): 병렬화 최적화
├─ Day 2 (1-2h): 성능 테스트
└─ Day 3 (1-2h): 최종 통합 테스트
```

---

## ✅ 최종 목표

```
완성된 JARVIS v2.0
├─ ✅ 안정적인 로컬/클라우드 연결
├─ ✅ 지능형 계획 수립 (Planner)
├─ ✅ 병렬 실행 (Executor)
├─ ✅ 품질 검증 (Reviewer)
├─ ✅ 지식 누적 (WikiAgent + Memory)
├─ ✅ 다목적 Skills
│   ├─ CodeGenSkill
│   ├─ ChartAnalysisSkill
│   ├─ VideoCreationSkill
│   ├─ ParallelAgentSkill
│   └─ ReportGenSkill
└─ ✅ 3배 빠른 병렬화 성능

결과: 사용자 요청 → 2-3초 내 완성된 산출물
```

---

**작성일**: 2026-04-18  
**상태**: 구현 준비 완료  
**우선순위**: Phase 1부터 순차적 진행

