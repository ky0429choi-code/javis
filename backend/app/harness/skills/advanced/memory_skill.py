import logging
from typing import Dict, Any
from app.harness.skills.base_skill import BaseSkill
from app.vault.ax_vault import ax_vault

logger = logging.getLogger(__name__)

class MemorySkill(BaseSkill):
    """
    Skill for direct long-term memory access (AX_Vault).
    Allows agents to read, write, and delete persistent knowledge patterns.
    """
    name = "memory"
    description = "장기 기억(AX_Vault) 직접 접근 - 쓰기, 읽기, 삭제 지원"
    version = "1.0.0"

    async def execute(self, task: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        action = task.get("action", "read").lower()
        key = task.get("key") or task.get("title")
        value = task.get("value") or task.get("content")
        folder = task.get("folder", "02_Patterns")

        if not key:
            return {"ok": False, "error": "Key/Title is required"}

        try:
            if action == "write":
                if not value:
                    return {"ok": False, "error": "Value/Content is required for write action"}
                await ax_vault.store(folder, {"title": key, "content": value})
                return {"ok": True, "status": "stored", "key": key, "folder": folder}

            elif action == "read":
                results = await ax_vault.search(folder, key)
                if not results:
                    return {"ok": False, "error": f"Entry not found for key: {key}"}
                
                # 가깝게 일치하는 결과 반환
                match = results[0]
                return {
                    "ok": True, 
                    "status": "found", 
                    "key": match["title"], 
                    "content": match["content"],
                    "folder": folder
                }

            elif action == "delete":
                res = await ax_vault.delete(folder, key)
                return res

            else:
                return {"ok": False, "error": f"Unsupported action: {action}"}

        except Exception as e:
            logger.error(f"MemorySkill: 작업 중 오류 발생 ({action}): {e}")
            return {"ok": False, "error": str(e)}

    async def validate_input(self, task: Dict[str, Any]) -> (bool, str):
        action = task.get("action")
        if not action or action not in ["read", "write", "delete"]:
            return False, "Action must be 'read', 'write', or 'delete'"
        if not task.get("key") and not task.get("title"):
            return False, "Missing key/title for memory operation"
        return True, None
