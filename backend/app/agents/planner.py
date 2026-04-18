import logging
import json
import re
from typing import Dict, List, Any
from app.llm_router import router
from app.harness.rules_engine import rules_engine

logger = logging.getLogger(__name__)

class Planner:
    def __init__(self):
        self.identity = "Jarvis"
        self.system_base = f"당신은 {self.identity}입니다. 사용자의 요청을 분석하고 실행 가능한 단계별 계획을 수립하세요."

    async def auto_plan_today(self, message: str) -> Dict[str, Any]:
        """
        Analyzes the user input and breaks it down into subtasks.
        Returns structured JSON with 'goal', 'steps', 'priority'.
        """
        logger.info(f"Planner: Planning for request: {message[:50]}...")
        
        # 1. Build system prompt for structured output
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
        
        # 2. Call LLM Router
        response = await router.call(prompt=message, system=system_prompt)
        logger.debug(f"Planner LLM Response: {response[:200]}...")
        
        # 3. Parse JSON from response
        parsed = self._extract_json_from_response(response)
        
        if not parsed:
            logger.warning("Planner: JSON parsing failed, creating fallback plan")
            return {
                "identity": self.identity,
                "goal": f"사용자 요청: {message}",
                "priority": "medium",
                "steps": [
                    {
                        "title": "기본 처리",
                        "action": "research",
                        "path": "사용자_요청",
                        "instruction": message
                    }
                ],
                "status": "planned_fallback",
                "raw_response": response[:500]
            }
        
        return {
            "identity": self.identity,
            "goal": parsed.get("goal", "작업 실행"),
            "priority": parsed.get("priority", "medium"),
            "steps": parsed.get("steps", []),
            "status": "planned",
            "raw_response": response[:500]
        }
    
    def _extract_json_from_response(self, text: str) -> Dict[str, Any] | None:
        """
        Extracts JSON from LLM response, handling markdown code blocks.
        """
        try:
            # Try direct JSON parse first
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        # Try extracting from markdown code blocks
        patterns = [
            r"```json\s*(.*?)\s*```",
            r"```\s*(.*?)\s*```"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except json.JSONDecodeError:
                    continue
        
        # Try finding { ... } pattern
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
        
        logger.error(f"Planner: Could not extract JSON from response: {text[:200]}")
        return None

    async def search_vault(self, query: str) -> List[str]:
        """
        RAG placeholder: Search AX_Vault/02_Knowledge for related context.
        """
        logger.info(f"Planner: Searching vault for context: {query}")
        return []

planner = Planner()
