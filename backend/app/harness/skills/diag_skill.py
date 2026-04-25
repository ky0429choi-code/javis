from typing import Dict, Any
from app.harness.skills.base_skill import BaseSkill
from app.tools.diagnostic_tool import diagnostic_tool

class DiagnosticSkill(BaseSkill):
    """
    System Diagnostic skill.
    Wraps DiagnosticTool for system health checks.
    """
    name = "diag_skill"
    description = "Run a full system diagnostic (Cache, Metrics, LLM status)."
    version = "1.0"

    async def execute(self, task: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        try:
            res = await diagnostic_tool.run_diagnostic()
            return self._create_result(True, result=res)
        except Exception as e:
            return self._create_result(False, error=str(e))

    async def validate_input(self, task: Dict[str, Any]) -> tuple[bool, str]:
        return True, ""
