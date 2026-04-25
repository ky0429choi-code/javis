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
        """Processes a completed task (success or failure) to extract intelligence."""
        logger.info(f"Wiki Agent: Learning from task results -> {goal[:50]}...")
        
        # 성공 여부 판별
        all_ok = all(step.get("result", {}).get("ok") for step in execution_trace)
        status_label = "SUCCESS" if all_ok else "FAILURE"
        
        trace_text = json.dumps(execution_trace, ensure_ascii=False, indent=2)
        prompt = (
            f"최종 목표: {goal}\n결과 상태: {status_label}\n실행 이력: {trace_text}\n\n"
            "위 실행 이력을 분석하여 다음 정보를 추출하세요:\n"
            "1. 무엇이 잘 되었는가 (성공 패턴)\n"
            "2. 무엇이 문제였는가 (실패/안티 패턴 - 특히 실패 시 중요)\n"
            "3. 다음 번에 비슷한 작업을 할 때의 주의사항\n\n"
            "분석 결과 JSON: "
            '{"lore": "짧은 판단 근거", "pattern": "핵심 성공/실패 패턴 요약", "kpi_score": 95, "best_practice": "마크다운 문서 내용(상세 지침)"}'
        )
        system_prompt = "당신은 JARVIS AI OS의 지능형 지식 전파 모듈입니다. 실행 결과로부터 지표와 노하우를 정제합니다."
        try:
            raw_res = await router.call(prompt=prompt, system=system_prompt, task_type="bulk")
            import re
            match = re.search(r"\{.*\}", raw_res, re.DOTALL)
            if match:
                intel = json.loads(match.group(0))
                # Lore 저장 (DB)
                self.repo.save_memory_node("lore", goal, {"decision": intel.get("lore"), "status": status_label})
                # Pattern 저장 (AX_Vault)
                await ax_vault.save_node(f"Pattern_{goal[:20]}", intel.get("best_practice"), "02_Patterns")
            logger.info(f"✅ Wiki Agent: Task learning completed ({status_label}).")
        except Exception as e:
            logger.error(f"Wiki Agent task learning failed: {e}")

    async def sync_system_knowledge(self):
        """Ingests the own system's code and rules to build 'Self-Awareness'."""
        logger.info("Wiki Agent: Starting System Self-Ingestion...")
        from app.core.system_ingestor import SystemIngestor
        import os
        ingestor = SystemIngestor(os.getcwd())
        summary = ingestor.scan_project()
        prompt = ingestor.get_ingestion_prompt(summary)
        system_prompt = "JARVIS AI OS 코어 지식 아키텍트로서 시스템 맵을 작성하세요."
        try:
            raw_res = await router.call(prompt=prompt, system=system_prompt, task_type="bulk")
            await ax_vault.save_node("SYSTEM_MAP", raw_res, "02_Knowledge")
            await ax_vault.save_node("CORE_IDENTITY", "Identity: JARVIS AI OS Kernel", "02_Knowledge")
            logger.info("✅ Wiki Agent: System Ingestion completed.")
            return True
        except Exception as e:
            logger.error(f"Wiki Agent System Ingestion failed: {e}")
            return False

wiki_agent = WikiAgent()
