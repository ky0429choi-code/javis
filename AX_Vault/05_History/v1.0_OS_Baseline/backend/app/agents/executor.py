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
        self.file_tool = FileTool()
        self.backup_tool = BackupTool()

    async def execute(self, task: SubTask, context: Optional[dict] = None) -> Dict[str, Any]:
        """
        Executes a specific subtask using a 3-step hardened cycle:
        Generation -> Interception -> Execution.
        """
        logger.info(f"Executor: Processing task '{task.title}'...")
        
        # 1. Generation Phase (via Conductor-approved Router)
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

        # 2. Interception Phase (Security Hook)
        hook_res = await hooks_engine.intercept(content, {"task": task.title, "path": task.path})
        
        if hook_res.action == "block":
            logger.error(f"Executor: BLOCKED by Hook Engine ({hook_res.reason})")
            return {"ok": False, "status": "blocked", "reason": hook_res.reason}
        
        if hook_res.action == "pending_approval":
            logger.warning("Executor: Action requires user approval.")
            return {
                "ok": False, 
                "status": "pending_approval", 
                "pattern": hook_res.pattern,
                "content": content,
                "target_path": task.path
            }

        # 3. Execution Phase (Actual Tool use)
        try:
            res = {"ok": False, "msg": "Unknown Action"}
            if task.action in ["create_file", "write_file", "code_gen"]:
                res = self.file_tool.create_file(task.path, content)
            elif task.action in ["update_file", "modify_file"]:
                res = self.file_tool.update_file(task.path, content)
            elif task.action == "backup":
                res = self.backup_tool.backup_text("backups", task.path, content)
            
            return {
                "ok": res.get("ok", False),
                "status": "executed",
                "content": content,
                "tool_result": res
            }
        except Exception as e:
            logger.error(f"Executor: Tool execution failed: {e}")
            return {"ok": False, "status": "execution_failed", "error": str(e)}

    def _extract_content(self, text: str) -> str:
        """Extracts code from markdown blocks if present."""
        match = re.search(r"```(?:[\w]*)\s*\n([\s\S]*?)\n```", text)
        if match:
            return match.group(1).strip()
        return text.strip()

executor = ExecutorAgent()