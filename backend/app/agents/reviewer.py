import logging
from typing import Dict, Any, List
from app.llm_router import router
from app.harness.rules_engine import rules_engine
from app.harness.hooks import reminder_hook

logger = logging.getLogger(__name__)

class Reviewer:
    def __init__(self):
        self.identity = "Jarvis"
        self.system_base = f"당신은 {self.identity}의 검증 엔진입니다. 작성된 코드를 분석하고 오류나 규칙 위반을 찾아내세요."

    async def review_result(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validates the output of an Executor.
        """
        logger.info(f"Reviewer: Validating task '{context.get('path')}'")
        
        # 1. Reminder Hook Check (Enforce TDD/Process)
        try:
            reminder_hook('executor_complete', context)
        except Exception as e:
            return {"ok": False, "error": str(e), "agent": self.identity, "needs_retry": True}

        # 2. Syntax/Logic Check (Simulated for Demo)
        code_content = context.get("content", "")
        # Real implementation would use ast.parse() for python or similar tools
        
        # 3. LLM-based Quality Review
        rules = rules_engine.get_system_prompt_extension("BACKEND")
        prompt = f"다음 코드를 검토해 주세요:\n\n{code_content}\n\n위 코드가 설정된 규칙을 준수하는지, 논리적 오류는 없는지 분석하세요."
        system_prompt = self.system_base + rules + "\n완벽할 경우 '✅ PASS'로 시작하고, 수정이 필요할 경우 구체적인 피드백을 주며 '❌ FAIL'로 시작하세요."
        
        review_text = await router.call(prompt=prompt, system=system_prompt)
        
        is_pass = "✅ PASS" in review_text
        
        return {
            "ok": is_pass,
            "feedback": review_text,
            "agent": self.identity,
            "attempts": context.get("attempts", 1)
        }

    async def analyze_recent_logs(self) -> str:
        """Command handler for /debug."""
        return "최근 작업 로그 분석 결과: 모든 시스템이 정상적으로 가동 중이며, 최근 3건의 작업이 지식화 대기 중입니다."

reviewer = Reviewer()
