import logging
import re
from typing import Dict, Any, Optional
from app.schemas.v4_core import SubTask
from app.llm.router import router
from app.harness.hooks_engine import hooks_engine
from app.harness.rules_engine import rules_engine
from app.tools.file_tool import FileTool
from app.tools.backup_tool import BackupTool

logger = logging.getLogger(__name__)

class ExecutorAgent:
    """
    JARVIS Executor Agent.
    Role: Executes SubTasks (code gen, file ops) through Harness Hooks.
    """
    def __init__(self):
        self.identity = "Jarvis"

    async def execute(self, task: SubTask, context: Optional[dict] = None) -> Dict[str, Any]:
        """
        Executes a specific subtask using a 4-step hardened cycle:
        Generation -> Interception (Gate 1) -> Interception (Hooks) -> Registry Execution.
        """
        logger.info(f"Executor: Processing task '{task.title}'...")
        
        # 1. Generation Phase
        rules = rules_engine.get_system_prompt_extension("EXECUTOR")
        prompt = (
            f"대상 경로: {task.path}\n"
            f"지시 사항: {task.instruction}\n"
            "작업 결과물(코드 또는 텍스트)만 출력하세요. 설명은 생략합니다."
        )
        system_prompt = f"당신은 {self.identity}의 실행 모듈입니다. {rules}"
        
        raw_output = await router.call(
            prompt=prompt, 
            system=system_prompt,
            task_type="complex"
        )
        
        content = self._extract_content(raw_output)

        # 2. HITL Gate 1 — 실행 전 위험도 게이트 (독립 모듈)
        from app.core.hitl.gate1 import gate1, GateDecision
        gate1_result = await gate1.evaluate(
            action=task.action,
            target_path=task.path,
            content=content,
        )

        if gate1_result.decision == GateDecision.BLOCK:
            logger.error(f"Executor: BLOCKED by Gate 1 ({gate1_result.reason})")
            return {"ok": False, "status": "blocked", "reason": gate1_result.reason}

        if gate1_result.decision == GateDecision.HOLD:
            logger.warning(f"Executor: HOLD by Gate 1 ({gate1_result.reason})")
            return {
                "ok": False,
                "status": "pending_approval",
                "pattern": gate1_result.pattern,
                "content": content,
                "target_path": task.path,
            }

        # 3. Hooks Engine — 코드 패턴 보안 검사
        hook_res = await hooks_engine.intercept(content, {"task": task.title, "path": task.path})

        if hook_res.action == "block":
            logger.error(f"Executor: BLOCKED by Hook Engine ({hook_res.reason})")
            return {"ok": False, "status": "blocked", "reason": hook_res.reason}

        if hook_res.action == "pending_approval":
            logger.warning(f"Executor: HOLD by Hooks ({hook_res.pattern})")
            return {
                "ok": False,
                "status": "pending_approval",
                "pattern": hook_res.pattern,
                "content": content,
                "target_path": task.path,
            }

        # 4. Registry Execution Phase (SkillRegistry)
        try:
            from app.harness.skills.registry import skill_registry
            
            # Map action to skill
            skill_name = "file_skill"
            if task.action == "backup":
                skill_name = "backup_skill"
            elif task.action == "diagnostic":
                skill_name = "diag_skill"
            
            skill_task = {
                "action": task.action,
                "path": task.path,
                "content": content
            }
            
            res = await skill_registry.execute(skill_name, skill_task, context)
            
            return {
                "ok": res.get("ok", False),
                "status": "executed",
                "content": content,
                "tool_result": res.get("result", res.get("error", "Error in skill"))
            }
        except Exception as e:
            logger.error(f"Executor: Skill execution failed: {e}")
            return {"ok": False, "status": "execution_failed", "error": str(e)}

    def _extract_content(self, text: str) -> str:
        """Extracts code from markdown blocks if present."""
        match = re.search(r"```(?:[\w]*)\s*\n([\s\S]*?)\n```", text)
        if match:
            return match.group(1).strip()
        return text.strip()

executor = ExecutorAgent()