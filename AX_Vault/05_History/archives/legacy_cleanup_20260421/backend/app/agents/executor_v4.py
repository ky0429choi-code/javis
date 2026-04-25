import logging
# Change: Import V4 router
from app.core_v4.llm.router import router_v4
from app.harness.rules_engine import rules_engine
from app.harness.hooks import protection_hook
from app.tools.file_tool import FileTool
import re

logger = logging.getLogger(__name__)

class ExecutorV4:
    """
    JARVIS Executor V4.
    Prototype utilizing SmartRouterV4 for code generation.
    """
    def __init__(self):
        self.identity = "Jarvis"
        self.file_tool = FileTool()
        self.system_base = f"당신은 {self.identity}입니다. 사용자의 요청에 따라 최적화된 코드를 작성하고 수정하세요."

    async def execute_task(self, subtask: dict) -> dict:
        """
        Generates code via V4 Router and applies changes.
        """
        action_type = subtask.get("action_type", "create_file")
        target_path = subtask.get("target_path", "")
        instruction = subtask.get("instruction", "")
        
        # 1. Protection Hook
        try:
            protection_hook(action_type, target_path)
        except Exception as e:
            return {"ok": False, "error": f"Security Block: {e}"}

        # 2. Code Generation (V4 Router)
        rules = rules_engine.get_system_prompt_extension("BACKEND")
        prompt = f"대상: {target_path}\n명령: {instruction}"
        system_prompt = self.system_base + rules + "\n마크다운 코드 블록으로 감싸주세요."
        
        # task_type="complex" to prioritize higher quality models if needed
        code_result = await router_v4.call(prompt=prompt, system=system_prompt, task_type="complex")
        content = self._extract_code(code_result)

        # 3. File Operation
        if action_type == "create_file":
            res = self.file_tool.create_file(target_path, content)
        elif action_type in ["update_file", "modify_file"]:
            res = self.file_tool.update_file(target_path, content)
        else:
            return {"ok": False, "error": f"Unsupported action: {action_type}"}

        return res

    def _extract_code(self, text: str) -> str:
        match = re.search(r"```(?:[\w]*)\s*\n([\s\S]*?)\n```", text)
        return match.group(1).strip() if match else text.strip()

executor_v4 = ExecutorV4()
