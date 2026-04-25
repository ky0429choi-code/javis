from typing import Dict, Any
from app.harness.skills.base_skill import BaseSkill
from app.tools.backup_tool import BackupTool

class BackupSkill(BaseSkill):
    """
    Backup skill.
    Wraps BackupTool for text backup actions.
    """
    name = "backup_skill"
    description = "Backup text content with timestamp."
    version = "1.0"

    def __init__(self):
        self.tool = BackupTool()

    async def execute(self, task: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        path = task.get("path")
        content = task.get("content", "")
        base_dir = task.get("base_dir", "backups")

        try:
            res = self.tool.backup_text(base_dir, path, content)
            return self._create_result(res.get("ok", False), result=res)
        except Exception as e:
            return self._create_result(False, error=str(e))

    async def validate_input(self, task: Dict[str, Any]) -> tuple[bool, str]:
        if not task.get("path"):
            return False, "Target 'path' is required for backup naming."
        return True, ""
