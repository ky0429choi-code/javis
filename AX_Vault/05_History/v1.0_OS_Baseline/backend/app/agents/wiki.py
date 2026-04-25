import logging
import json
from typing import Dict, Any, List
from app.llm.router import router
from app.memory.repository import Repository
from app.vault.ax_vault import ax_vault

logger = logging.getLogger(__name__)

class WikiAgent:
    """
    JARVIS Wiki Agent (Growth Engine).
    Role: Transforms audit logs and execution traces into Knowledge & Lore.
    """
    def __init__(self):
        self.identity = "Jarvis"
        self.repo = Repository()

    async def process_task(self, goal: str, execution_trace: List[Dict[str, Any]]):
        """
        Processes a completed task to extract intelligence.
        Triggered asynchronously by the Conductor.
        """
        logger.info(f"Wiki Agent: Learning from task -> {goal[:50]}...")
        
        # 1. Prepare intelligence prompt
        trace_text = json.dumps(execution_trace, ensure_ascii=False, indent=2)
        prompt = (
            f"최종 목표: {goal}\n"
            f"실행 이력: {trace_text}\n\n"
            "위 작업 이력을 분석하여 다음 정보를 추출하세요:\n"
            "1. 결정 로어(Lore): 이 작업을 성공시키기 위한 핵심적인 판단 근거(왜 이 방식을 썼는가).\n"
            "2. 지식 패턴(Pattern): 향후 유사 작업 시 재사용 가능한 단계나 지식.\n"
            "3. KPI 점수: 작업의 완성도 (0-100).\n\n"
            "결과는 반드시 다음 JSON 형식으로 응답하세요:\n"
            '{"lore": "...", "pattern": "...", "kpi_score": 95, "best_practice": "마크다운 문서 내용"}'
        )
        
        system_prompt = f"당신은 {self.identity}의 지식 관리 모듈입니다. 모든 지식은 한국어로 작성됩니다."

        try:
            raw_res = await router.call(prompt=prompt, system=system_prompt, task_type="bulk")
            
            # 2. Parse Result
            import re
            match = re.search(r"\{.*\}", raw_res, re.DOTALL)
            if not match:
                logger.warning("Wiki Agent: Failed to find JSON in Brain response.")
                return

            intel = json.loads(match.group(0))

            # 3. Store in Functional Memory (SQLite)
            # Lore Memory
            self.repo.save_memory_node(
                type="lore",
                context=goal,
                content={"decision": intel.get("lore"), "pattern": intel.get("pattern")},
                metadata={"task_goal": goal}
            )
            # KPI Memory
            self.repo.save_memory_node(
                type="kpi",
                context=goal,
                content={"score": intel.get("kpi_score")},
                metadata={"task_goal": goal}
            )

            # 4. Store in AX_Vault (Markdown)
            title = f"Learning_{goal[:20]}"
            await ax_vault.save_node(
                title=title,
                content=intel.get("best_practice", "내용 없음"),
                folder="02_Knowledge"
            )

            logger.info("✅ Wiki Agent: Self-Learning process completed successfully.")

        except Exception as e:
            logger.error(f"Wiki Agent: Failed to process task intel: {e}")

wiki_agent = WikiAgent()
