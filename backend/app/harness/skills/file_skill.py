from typing import Dict, Any
from app.harness.skills.base_skill import BaseSkill
from app.tools.file_tool import FileTool

class FileSkill(BaseSkill):
    """
    File manipulation skill.
    Wraps FileTool for create, update, and delete actions.
    """
    name = "file_skill"
    description = "Create, update, or delete files in the workspace."
    version = "1.0"

    def __init__(self):
        self.tool = FileTool()

    async def execute(self, task: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        action = task.get("action")
        path = task.get("path")
        content = task.get("content", "")

        try:
            if action in ["create_file", "write_file", "code_gen"]:
                res = self.tool.create_file(path, content)
            elif action in ["update_file", "modify_file"]:
                res = self.tool.update_file(path, content)
            elif action == "delete_file":
                res = self.tool.delete_file(path)
            else:
                return self._create_result(False, error=f"Unsupported action: {action}")

            return self._create_result(res.get("ok", False), result=res)
        except Exception as e:
            return self._create_result(False, error=str(e))

    async def validate_input(self, task: Dict[str, Any]) -> tuple[bool, str]:
        if not task.get("path"):
            return False, "Target 'path' is required."
        if not task.get("action"):
            return False, "Target 'action' is required."
        return True, ""
