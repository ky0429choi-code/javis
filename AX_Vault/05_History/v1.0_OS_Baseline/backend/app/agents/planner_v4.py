import logging
import json
import re
from typing import Dict, List, Any
# Change: Import V4 router
from app.core_v4.llm.router import router_v4
from app.harness.rules_engine import rules_engine

logger = logging.getLogger(__name__)

class PlannerV4:
    """
    JARVIS Planner V4. 
    Prototype for Unified Core 4.0 using SmartRouterV4.
    """
    def __init__(self):
        self.identity = "Jarvis"
        self.system_base = f"당신은 {self.identity}입니다. 사용자의 요청을 분석하고 실행 가능한 단계별 계획을 수립하세요."

    async def auto_plan_today(self, message: str) -> Dict[str, Any]:
        """
        Analyzes the user input and breaks it down into subtasks using V4 Router.
        """
        logger.info(f"Planner V4: Planning for request via SmartRouter...")
        
        # 1. Build system prompt
        rules = rules_engine.get_system_prompt_extension("BACKEND")
        system_prompt = (
            self.system_base + rules + 
            "\n\n[INSTRUCTION] 사용자의 요청을 분석하여 다음 JSON 형식으로 응답하세요:\n"
            "{\n"
            '  "goal": "최종 목표 (한 줄)",\n'
            '  "priority": "high|medium|low",\n'
            '  "steps": [\n'
            '    {"title": "단계 제목", "action": "create_file|update_file|code_gen|research|summary", "path": "대상 경로 또는 리소스", "instruction": "구체적인 지시사항"},\n'
            '    ...\n'
            '  ]\n'
            "}"
        )
        
        # 2. Call V4 Router (Benefit: Hybrid falling, Caching, Sensitivity protection)
        response = await router_v4.call(prompt=message, system=system_prompt, task_type="complex")
        
        # 3. Parse JSON from response
        parsed = self._extract_json_from_response(response)
        
        if not parsed:
            return {
                "identity": self.identity,
                "goal": f"사용자 요청: {message}",
                "priority": "medium",
                "steps": [{"title": "기본 처리", "action": "research", "path": "사용자_요청", "instruction": message}],
                "status": "planned_fallback_v4",
                "raw_response": response[:200]
            }
        
        return {
            "identity": self.identity,
            "goal": parsed.get("goal", "작업 실행"),
            "priority": parsed.get("priority", "medium"),
            "steps": parsed.get("steps", []),
            "status": "planned_v4",
            "raw_response": response[:200]
        }
    
    def _extract_json_from_response(self, text: str) -> Dict[str, Any] | None:
        """Extracts JSON with robust parsing."""
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        patterns = [r"```json\s*(.*?)\s*```", r"```\s*(.*?)\s*```", r"\{.*\}"]
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1 if "(" in pattern else 0))
                except json.JSONDecodeError:
                    continue
        return None

planner_v4 = PlannerV4()
