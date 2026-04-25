import logging
import os
from pathlib import Path

from app.utils.settings import get_settings
from app.config import HOOK_MODE, ACTIVE_HOOKS, HookMode

logger = logging.getLogger(__name__)
settings = get_settings()

class HarnessHookError(Exception):
    """Custom exception for hook violations."""
    pass

def protection_hook(action: str, target_path: str, agent_name: str = "Unknown") -> bool:
    """
    Layer 4: Protection Hook - Blocks destructive or unauthorized actions.
    Uses canonical path resolution to prevent bypass via symlinks or '..'.
    """
    if not ACTIVE_HOOKS.get('protection_enabled', False):
        logger.warning(f"🟡 [Phase {HOOK_MODE.value}] Hook bypassed: {action} on {target_path}")
        return True

    try:
        abs_target = Path(target_path).resolve()
        workspace_root = Path(os.getcwd()).resolve()

        if workspace_root not in abs_target.parents and abs_target != workspace_root:
            logger.warning("Security Alert: Attempted access outside workspace: %s", target_path)
            raise HarnessHookError(f"❌ 보안 위반: 프로젝트 외부 파일({target_path})에 접근할 수 없습니다.")

        blocked_names = {".env", "settings.py", "hooks.py"}
        if abs_target.name in blocked_names or "secrets" in abs_target.parts:
            logger.warning("Hook Violation: Unauthorized access to system file: %s", target_path)
            raise HarnessHookError(f"❌ 접근 금지: 핵심 시스템 가동 파일({abs_target.name})은 보호되어 있습니다.")

        if action == "git_push" and "main" in target_path.lower():
            raise HarnessHookError("❌ 보안 정책: main 브랜치 직접 푸시는 금지됩니다. (Hooks Layer 4)")

        return True
    except HarnessHookError:
        raise
    except Exception as e:
        logger.error("Hook internal error: %s", e)
        raise HarnessHookError(f"❌ 보호 계층 내부 오류: {str(e)}")

def reminder_hook(phase: str, context: dict = None) -> bool:
    """
    Layer 4: Reminder Hook - Enforces required processes (e.g., TDD).
    """
    context = context or {}
    if not ACTIVE_HOOKS.get('reminder_enabled', False):
        logger.warning(f"🟡 [Phase {HOOK_MODE.value}] Reminder bypassed: {phase}")
        return True

    if phase == "executor_complete":
        if not context.get("has_tests", False):
            logger.warning("Hook Violation: Process missing tests")
            raise HarnessHookError("❌ 테스트 코드 없이 작업을 완료할 수 없습니다. Reviewer가 반려했습니다.")

    return True

def audit_hook(agent_name: str, action: str, details: str) -> None:
    """
    Optional Hook for auditing every action.
    """
    if not ACTIVE_HOOKS.get('audit_enabled', True):
        return
    logger.info("Audit: Agent '%s' performed '%s' -> %s", agent_name, action, details)

def get_hook_status() -> dict:
    """현재 Hook 상태"""
    return {
        'mode': HOOK_MODE.value,
        'protection': ACTIVE_HOOKS.get('protection_enabled', False),
        'reminder': ACTIVE_HOOKS.get('reminder_enabled', False),
    }