import logging
import os
import re
from typing import Dict, Any, Optional
from app.llm_router import router
from app.harness.rules_engine import rules_engine
from app.harness.hooks import protection_hook
from app.tools.file_tool import FileTool

logger = logging.getLogger(__name__)

class Executor:
    def __init__(self):
        self.identity = "Jarvis"
        self.file_tool = FileTool()
        self.system_base = f"당신은 {self.identity}입니다. 사용자의 요청에 따라 최적화된 코드를 작성하고 수정하세요."

    async def execute_task(self, subtask: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates code and applies changes to the filesystem.
        Returns structured result with ok, path, output, error fields.
        """
        action_type = subtask.get("action_type", "create_file")
        target_path = subtask.get("target_path", "")
        instruction = subtask.get("instruction", "")
        content = subtask.get("content")  # Direct content if provided
        
        logger.info(f"Executor: Processing {action_type} for {target_path}")

        # 1. Validate inputs
        if not target_path:
            return {
                "ok": False,
                "action": action_type,
                "path": target_path,
                "error": "target_path is required",
                "agent": self.identity
            }

        # 2. Protection Hook Check
        try:
            protection_hook(action_type, target_path)
        except Exception as e:
            logger.warning(f"Executor: Protection hook blocked action: {e}")
            return {
                "ok": False,
                "action": action_type,
                "path": target_path,
                "error": f"Protected: {str(e)}",
                "agent": self.identity
            }

        # 3. Generate content if not provided
        if not content:
            try:
                rules = rules_engine.get_system_prompt_extension("BACKEND")
                prompt = f"대상: {target_path}\n명령: {instruction}\n적절한 코드/내용을 생성하세요."
                system_prompt = self.system_base + rules + "\n마크다운 코드 블록으로 감싸주세요."
                
                code_result = await router.call(prompt=prompt, system=system_prompt)
                content = self._extract_code_from_markdown(code_result)
                
                if not content:
                    content = code_result  # Fallback to raw LLM response
                    
            except Exception as e:
                logger.error(f"Executor: LLM call failed: {e}")
                return {
                    "ok": False,
                    "action": action_type,
                    "path": target_path,
                    "error": f"Code generation failed: {str(e)}",
                    "agent": self.identity
                }

        # 4. Execute file operation
        try:
            if action_type == "create_file":
                res = self.file_tool.create_file(target_path, content)
            elif action_type in ["update_file", "modify_file"]:
                res = self.file_tool.update_file(target_path, content)
            else:
                return {
                    "ok": False,
                    "action": action_type,
                    "path": target_path,
                    "error": f"Unsupported action: {action_type}",
                    "agent": self.identity
                }
            
            if res.get("ok"):
                logger.info(f"Executor: Successfully {action_type} at {target_path}")
                return {
                    "ok": True,
                    "action": action_type,
                    "path": target_path,
                    "output": f"Applied {action_type} to {target_path}",
                    "agent": self.identity
                }
            else:
                logger.error(f"Executor: File operation failed: {res.get('error')}")
                return {
                    "ok": False,
                    "action": action_type,
                    "path": target_path,
                    "error": res.get("error", "Unknown file operation error"),
                    "agent": self.identity
                }
                
        except Exception as e:
            logger.error(f"Executor: Unexpected error during {action_type}: {e}")
            return {
                "ok": False,
                "action": action_type,
                "path": target_path,
                "error": f"Execution error: {str(e)}",
                "agent": self.identity
            }

    def _extract_code_from_markdown(self, text: str) -> str:
        """
        Extracts code from markdown code blocks.
        Handles multiple formats: ```python, ```json, plain ```.
        """
        # Try to find markdown code block
        patterns = [
            r"```(?:[\w]*)\s*\n([\s\S]*?)\n```",  # ```python ... ```
            r"```([\s\S]*?)```",  # ``` ... ```
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                extracted = match.group(1).strip()
                if extracted:
                    return extracted
        
        # If no code block found, return text as-is (might be plain text)
        return text.strip()

executor = Executor()