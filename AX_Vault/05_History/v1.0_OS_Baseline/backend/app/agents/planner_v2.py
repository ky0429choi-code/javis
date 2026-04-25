"""
Enhanced Planner v2.0 - 실제 작동하는 계획 수립
"""

import logging
import json
import re
from typing import Dict, List, Any
from app.llm_router_v2 import router
import asyncio

logger = logging.getLogger(__name__)


class EnhancedPlanner:
    """실제 작동하는 계획 수립 엔진"""
    
    def __init__(self):
        self.identity = "Jarvis"
        self.system_base = f"당신은 {self.identity}입니다. 사용자의 요청을 분석하고 실행 가능한 단계별 계획을 수립하세요."
        
        # 요청 타입별 템플릿
        self.task_templates = {
            "code_generation": self._template_code_generation,
            "data_analysis": self._template_data_analysis,
            "reporting": self._template_reporting,
            "video_creation": self._template_video_creation,
        }
    
    async def auto_plan_today(self, message: str) -> Dict[str, Any]:
        """
        사용자 요청을 분석하여 실행 가능한 계획 수립
        
        예시:
        입력: "JavaScript로 할일 앱 만들어줘"
        출력: {
            "goal": "JavaScript Todo App 개발",
            "task_type": "code_generation",
            "steps": [
                {"id": 1, "title": "프로젝트 구조 설계", "skill": "CodeGenSkill", "depends_on": []},
                {"id": 2, "title": "HTML 작성", "skill": "CodeGenSkill", "depends_on": [1]},
                ...
            ],
            "parallelizable_groups": [[2,3,4], [5]],
            "estimated_duration": 600
        }
        """
        logger.info(f"EnhancedPlanner: Planning for: {message[:50]}...")
        
        try:
            # 1단계: 요청 분석
            analysis = await self._analyze_request(message)
            logger.debug(f"Analysis result: {analysis}")
            
            # 2단계: 태스크 분해
            steps = await self._decompose_tasks(message, analysis)
            logger.debug(f"Decomposed {len(steps)} steps")
            
            if not steps:
                # 폴백
                return self._create_fallback_plan(message)
            
            # 3단계: 의존성 파악
            self._identify_dependencies(steps)
            
            # 4단계: 병렬화 그룹 식별
            parallelizable = self._identify_parallelizable_groups(steps)
            
            # 5단계: 예상 시간 계산
            estimated_duration = self._estimate_total_duration(steps)
            
            return {
                "identity": self.identity,
                "goal": analysis.get("goal", message),
                "task_type": analysis.get("type", "unknown"),
                "complexity": analysis.get("complexity", "medium"),
                "steps": steps,
                "parallelizable_groups": parallelizable,
                "estimated_duration": estimated_duration,
                "status": "planned",
                "success": True
            }
            
        except Exception as e:
            logger.error(f"EnhancedPlanner error: {e}")
            return self._create_fallback_plan(message, error=str(e))
    
    async def _analyze_request(self, message: str) -> Dict[str, Any]:
        """
        사용자 요청 분석
        - 작업 타입 판단 (코드생성/데이터분석/보고서/영상 등)
        - 복잡도 평가
        - 외부 리소스 필요 여부
        """
        analyze_prompt = f"""
분석할 요청: "{message}"

다음을 JSON 형식으로 판단하고 반환하세요:
{{
    "goal": "최종 목표 (한 줄)",
    "type": "code_generation|data_analysis|reporting|video_creation|other",
    "complexity": "simple|medium|complex",
    "estimated_steps": "예상 단계 수 (숫자)",
    "requires_external": "true|false (API, 웹 크롤링 필요)",
    "programming_languages": ["언어 배열"],
    "key_requirements": ["주요 요구사항 배열"]
}}

JSON만 반환하세요.
        """
        
        response = await router.call(analyze_prompt, self.system_base)
        result = self._extract_json(response)
        
        if not result:
            # 기본값
            return {
                "goal": message,
                "type": "unknown",
                "complexity": "medium",
                "estimated_steps": 3
            }
        
        return result
    
    async def _decompose_tasks(self, message: str, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        구체적인 태스크로 분해
        
        예시:
        "JavaScript 앱 만들어"
        →
        [
            {"id": 1, "title": "프로젝트 구조", "skill": "CodeGenSkill", "depends_on": []},
            {"id": 2, "title": "HTML", "skill": "CodeGenSkill", "depends_on": [1]},
            ...
        ]
        """
        task_type = analysis.get("type", "unknown")
        complexity = analysis.get("complexity", "medium")
        
        # 템플릿이 있으면 사용
        if task_type in self.task_templates:
            template_func = self.task_templates[task_type]
            base_tasks = template_func(complexity)
        else:
            base_tasks = []
        
        # LLM으로 구체적인 태스크 생성
        decompose_prompt = f"""
사용자 요청을 구체적 단계로 분해하세요:
요청: "{message}"
분석: {json.dumps(analysis, ensure_ascii=False)}

각 단계마다:
- id: 1, 2, 3, ...
- title: 단계 이름
- description: 상세 설명
- skill: CodeGenSkill|DataProcessSkill|TestGenSkill|DocumentationSkill
- depends_on: [이미 완료된 단계 id]
- estimated_time: 초 단위 (예: 60, 120)

JSON 배열로 반환하세요. 예:
[
    {{"id": 1, "title": "구조 설계", "skill": "CodeGenSkill", "depends_on": []}},
    {{"id": 2, "title": "HTML", "skill": "CodeGenSkill", "depends_on": [1]}}
]
        """
        
        response = await router.call(decompose_prompt, self.system_base)
        tasks = self._extract_json(response)
        
        if not isinstance(tasks, list):
            # 기본 태스크 반환
            return base_tasks or [
                {
                    "id": 1,
                    "title": "작업 분석",
                    "description": message,
                    "skill": "CodeGenSkill",
                    "depends_on": [],
                    "estimated_time": 60
                }
            ]
        
        return tasks
    
    def _identify_dependencies(self, steps: List[Dict[str, Any]]) -> None:
        """의존성 그래프 검증 및 순환 참조 확인"""
        for step in steps:
            deps = step.get("depends_on", [])
            step_id = step.get("id")
            
            # 순환 참조 확인
            if step_id in deps:
                logger.warning(f"Step {step_id} has circular dependency")
                step["depends_on"] = [d for d in deps if d != step_id]
    
    def _identify_parallelizable_groups(self, steps: List[Dict[str, Any]]) -> List[List[int]]:
        """
        병렬 실행 가능한 그룹 식별
        
        예시:
        steps = [
            {"id": 1, "depends_on": []},
            {"id": 2, "depends_on": [1]},
            {"id": 3, "depends_on": [1]},
            {"id": 4, "depends_on": [1]},
            {"id": 5, "depends_on": [2,3,4]}
        ]
        
        →
        [[1], [2,3,4], [5]]
        """
        groups = []
        remaining = {step["id"]: step.get("depends_on", []) for step in steps}
        
        while remaining:
            # 완료된 단계 (의존성 없음)
            completed = [sid for sid, deps in remaining.items() if not deps]
            
            if not completed:
                # 순환 참조? 모든 것을 병렬로 처리
                groups.append(list(remaining.keys()))
                break
            
            groups.append(completed)
            
            # 완료된 단계 제거
            for cid in completed:
                del remaining[cid]
            
            # 의존성 업데이트
            for sid in remaining:
                remaining[sid] = [d for d in remaining[sid] if d not in completed]
        
        return groups
    
    def _estimate_total_duration(self, steps: List[Dict[str, Any]]) -> int:
        """
        총 소요 시간 계산
        
        병렬화를 고려하여 최대값으로 계산
        """
        total = 0
        for step in steps:
            duration = step.get("estimated_time", 60)
            if isinstance(duration, (int, float)):
                total += duration
        
        # 병렬화로 30% 단축 가정
        return max(total // 3, 60)  # 최소 60초
    
    def _extract_json(self, text: str) -> Any:
        """LLM 응답에서 JSON 추출"""
        try:
            return json.loads(text)
        except:
            pass
        
        # 마크다운 코드블록 찾기
        patterns = [
            r"```json\s*(.*?)\s*```",
            r"```\s*(.*?)\s*```"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except:
                    pass
        
        # {...} 패턴 찾기
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except:
                pass
        
        return None
    
    def _create_fallback_plan(self, message: str, error: str = None) -> Dict[str, Any]:
        """폴백 계획 생성"""
        return {
            "identity": self.identity,
            "goal": message,
            "task_type": "unknown",
            "complexity": "medium",
            "steps": [
                {
                    "id": 1,
                    "title": "작업 분석",
                    "description": message,
                    "skill": "CodeGenSkill",
                    "depends_on": [],
                    "estimated_time": 120
                }
            ],
            "parallelizable_groups": [[1]],
            "estimated_duration": 120,
            "status": "planned_fallback",
            "success": False,
            "error": error
        }
    
    # ==================== 작업 타입별 템플릿 ====================
    
    def _template_code_generation(self, complexity: str) -> List[Dict[str, Any]]:
        """코드 생성 템플릿"""
        if complexity == "simple":
            return [
                {"id": 1, "title": "함수 작성", "skill": "CodeGenSkill", "depends_on": [], "estimated_time": 60},
                {"id": 2, "title": "테스트 작성", "skill": "TestGenSkill", "depends_on": [1], "estimated_time": 60},
            ]
        elif complexity == "complex":
            return [
                {"id": 1, "title": "프로젝트 구조 설계", "skill": "CodeGenSkill", "depends_on": [], "estimated_time": 120},
                {"id": 2, "title": "핵심 기능 구현", "skill": "CodeGenSkill", "depends_on": [1], "estimated_time": 180},
                {"id": 3, "title": "부기능 구현", "skill": "CodeGenSkill", "depends_on": [1], "estimated_time": 180},
                {"id": 4, "title": "테스트 작성", "skill": "TestGenSkill", "depends_on": [2, 3], "estimated_time": 120},
                {"id": 5, "title": "문서화", "skill": "DocumentationSkill", "depends_on": [2, 3, 4], "estimated_time": 90},
            ]
        else:
            return [
                {"id": 1, "title": "구조 설계", "skill": "CodeGenSkill", "depends_on": [], "estimated_time": 90},
                {"id": 2, "title": "코드 생성", "skill": "CodeGenSkill", "depends_on": [1], "estimated_time": 120},
                {"id": 3, "title": "테스트", "skill": "TestGenSkill", "depends_on": [2], "estimated_time": 90},
            ]
    
    def _template_data_analysis(self, complexity: str) -> List[Dict[str, Any]]:
        """데이터 분석 템플릿"""
        return [
            {"id": 1, "title": "데이터 수집", "skill": "DataProcessSkill", "depends_on": [], "estimated_time": 120},
            {"id": 2, "title": "데이터 정제", "skill": "DataProcessSkill", "depends_on": [1], "estimated_time": 120},
            {"id": 3, "title": "분석 수행", "skill": "AnalysisSkill", "depends_on": [2], "estimated_time": 180},
            {"id": 4, "title": "보고서 작성", "skill": "ReportingSkill", "depends_on": [3], "estimated_time": 120},
        ]
    
    def _template_reporting(self, complexity: str) -> List[Dict[str, Any]]:
        """보고서 작성 템플릿"""
        return [
            {"id": 1, "title": "자료 수집", "skill": "DataProcessSkill", "depends_on": [], "estimated_time": 150},
            {"id": 2, "title": "분석", "skill": "AnalysisSkill", "depends_on": [1], "estimated_time": 150},
            {"id": 3, "title": "보고서 작성", "skill": "ReportingSkill", "depends_on": [2], "estimated_time": 180},
        ]
    
    def _template_video_creation(self, complexity: str) -> List[Dict[str, Any]]:
        """영상 제작 템플릿"""
        return [
            {"id": 1, "title": "스크립트 작성", "skill": "VideoCreationSkill", "depends_on": [], "estimated_time": 180},
            {"id": 2, "title": "자료 수집", "skill": "DataProcessSkill", "depends_on": [1], "estimated_time": 240},
            {"id": 3, "title": "편집책 작성", "skill": "VideoCreationSkill", "depends_on": [2], "estimated_time": 120},
        ]


# 싱글톤
enhanced_planner = EnhancedPlanner()
