import logging
import json
import re
from typing import Dict, Any
from app.schemas.v4_core import PlanResult, SubTask

logger = logging.getLogger(__name__)

class PlannerAgent:
    """
    JARVIS Planner Agent.
    Role: Decomposes user intent into actionable subtasks.
    Constraint: DOES NOT call LLM directly (Fix B6).
    """
    def __init__(self):
        self.identity = "Jarvis"

    async def plan(self, goal: str, context: Dict[str, Any] = None) -> PlanResult:
        """
        Generates a planning prompt (context) that the Conductor will 
        use to invoke the Brain.
        """
        related_context = (context or {}).get("related_context", "관련 정보 없음")

        # Build the structured instruction for the Brain
        instruction = (
            f"최종 목표: {goal}\n"
            f"참고 컨텍스트: {related_context}\n\n"
            "위 목표와 참고 컨텍스트(시스템 지식 및 과거 경험)를 바탕으로 사용자의 요청을 분석하세요.\n"
            "특히 '과거 작업 경험 및 피드백'이 있다면 해당 실패 사례를 반복하지 말고 성공 사례를 따르십시오.\n"
            "다음 JSON 형식으로 실행 단계를 분해하세요:\n"
            "{\n"
            '  "goal": "최종 목표 (한 줄)",\n'
            '  "priority": "high|medium|low",\n'
            '  "steps": [\n'
            '    {"title": "단계 제목", "action": "create_file|update_file|code_gen|research|summary", '
            '"path": "대상 경로", "instruction": "상세 지침"}\n'
            '  ]\n'
            "}"
        )

        # Return a "Pre-Plan" result containing the instruction
        # The Conductor will take this instruction, call the Router, and parse the result.
        return PlanResult(
            goal=goal,
            status="awaiting_llm_generation",
            steps=[], # Empty until Brain fills it
            instruction=instruction
        )

    def parse_brain_response(self, text: str) -> PlanResult:
        """
        Helper called by Conductor to turn LLM text into a structured PlanResult.
        """
        try:
            # Robust JSON extraction
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
                steps = [SubTask(**s) for s in data.get("steps", [])]
                return PlanResult(
                    goal=data.get("goal", "작업 수행"),
                    priority=data.get("priority", "medium"),
                    steps=steps,
                    status="planned"
                )
        except Exception as e:
            logger.error(f"Planner: Failed to parse brain response: {e}")
            
        return PlanResult(goal="Error parsing plan", status="error")

planner = PlannerAgent()
