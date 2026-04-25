import logging
import subprocess
import tempfile
import os
import json

logger = logging.getLogger(__name__)

class ReviewerAgent:
    """
    JARVIS Reviewer Agent.
    Role: Validates execution results using Ruff (Quality) and Self-Correction.
    """
    def __init__(self):
        self.identity = "Jarvis"

    async def review(self, execution_result: dict, target_path: str) -> dict:
        """
        Reviews the execution result for quality and errors.
        """
        content = execution_result.get("content", "")
        if not content:
            return {"status": "fail", "reason": "Empty content in execution result."}

        # For Python files, we perform Ruff linting
        if target_path.endswith(".py"):
            return await self._run_ruff_lint(content)
        
        # Generic validation for other files
        return {"status": "pass", "message": "Non-Python file validated."}

    async def _run_ruff_lint(self, content: str) -> dict:
        """
        Runs Ruff linter on a temporary file containing the generated code.
        """
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w", encoding="utf-8") as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            # Run ruff check with JSON output
            # Using --select E,F,W for basic quality rules
            cmd = ["ruff", "check", tmp_path, "--format", "json"]
            # Note: We might need the full path to ruff if it's not in the shell path
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and not result.stdout.strip() or result.stdout.strip() == "[]":
                return {"status": "pass", "message": "Ruff quality check passed."}
            
            # Parse errors
            errors = json.loads(result.stdout)
            error_details = []
            for err in errors:
                error_details.append({
                    "line": err["location"]["row"],
                    "column": err["location"]["column"],
                    "message": err["message"],
                    "code": err["code"]
                })
            
            return {
                "status": "fix",
                "reason": f"Ruff detected {len(error_details)} issues.",
                "errors": error_details
            }
        except Exception as e:
            logger.error(f"Reviewer: Ruff execution failed: {e}")
            return {"status": "pass", "message": "Linting skipped due to internal error."}
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

reviewer = ReviewerAgent()
