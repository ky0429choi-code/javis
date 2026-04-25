import logging
from typing import Dict, Any, List, Optional
from app.schemas.v4_core import SubTask
from app.vault.ax_vault import ax_vault

logger = logging.getLogger(__name__)

class RALFResult:
    def __init__(self, success: bool, attempts: int, reason: str = ""):
        self.success = success
        self.attempts = attempts
        self.reason = reason

class RALFLoop:
    """
    RALF (Red -> Analyze -> Loop -> Fix) Self-Healing Loop.
    Retries failed tasks by analyzing errors and applying strategies.
    """
    MAX_RETRIES = 3

    def __init__(self, executor, reviewer):
        self.executor = executor
        self.reviewer = reviewer

    async def run(self, task: SubTask, first_result: Dict[str, Any]) -> Dict[str, Any]:
        last_result = first_result
        
        # If already success or blocked, return immediately
        if last_result.get("ok"):
            return last_result

        logger.info(f"RALF: 자가 복구 루프 진입 (Task: {task.title})")

        for attempt in range(1, self.MAX_RETRIES + 1):
            # 1. Analyze Error
            error_msg = last_result.get("error", "Unknown error")
            logger.warning(f"RALF: 시도 {attempt}/{self.MAX_RETRIES} - 오류 분석 중: {error_msg}")

            # 2. Search AX_Vault for similar errors
            known_fix = await ax_vault.search("04_Errors", error_msg, top_k=1)
            
            # 3. Pick Strategy
            strategy = self._pick_strategy(error_msg, known_fix[0] if known_fix else None)
            logger.info(f"RALF: 선택된 전략 -> {strategy}")

            # 4. Modify Task based on strategy and Retry
            # We pass the feedback to the executor
            retry_res = await self.executor.execute(task, {
                "attempt": attempt,
                "strategy": strategy,
                "previous_error": error_msg
            })

            # 5. Review again
            review_res = await self.reviewer.review(retry_res, task.path)
            
            if review_res["status"] == "pass":
                logger.info(f"RALF: 자가 복구 성공! ({attempt}회 재시도)")
                # 기록 (성공 패턴 저장)
                await ax_vault.store("02_Patterns", {
                    "title": f"Fix_{task.action}_{attempt}",
                    "error": error_msg,
                    "strategy": strategy,
                    "task": task.instruction
                })
                return {"ok": True, "status": "fixed_by_ralf", "result": retry_res, "attempts": attempt}

            if review_res["status"] == "fail":
                logger.error("RALF: Reviewer가 즉시 실패(FAIL) 판정함. 에스컬레이션.")
                break

            # If still 'fix', continue loop
            last_result = retry_res
            last_result["error"] = review_res.get("reason", "Still failing review")

        logger.error(f"RALF: 최대 재시도({self.MAX_RETRIES}회) 초과. 복구 실패.")
        return {"ok": False, "status": "failed_after_ralf", "error": "Maximum retries exceeded"}

    def _pick_strategy(self, error: str, known_fix: Optional[Dict[str, Any]]) -> str:
        if known_fix and "strategy" in known_fix:
            return known_fix["strategy"]

        error_lower = error.lower()
        if "syntax" in error_lower:
            return "fix_syntax_and_reprompt"
        if "not found" in error_lower or "no such" in error_lower:
            return "create_missing_resource"
        if "timeout" in error_lower:
            return "increase_timeout_or_simplify"
        if "permission" in error_lower:
            return "check_permissions_and_retry"
            
        return "general_reprompt_correction"
