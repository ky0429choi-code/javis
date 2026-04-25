import re
import logging
from typing import Optional
from app.schemas.v4_core import HookResult, HookAction

logger = logging.getLogger(__name__)

class HooksEngine:
    """
    JARVIS Layer 4: Hooks.
    Monitors and intercepts agent output at the code level 
    to prevent security breaches or policy violations.
    """
    
    # Stage 1: Absolute Blocking (Fatal patterns)
    BLOCK_PATTERNS = [
        r"rm\s+-rf",                 # Force recursive delete
        r"shutil\.rmtree",           # Python directory delete
        r"os\.remove",               # Python file remove
        r"DROP\s+TABLE",             # Database destruction
        r"\.env",                    # Environment secret access
        r"secrets\.",                # Security secrets access
        r"keyboard\.",               # Keylogging prevention
        r"pyautogui\.",              # UI capture prevention
    ]
    
    # Stage 2: Requires Approval (Context-sensitive actions)
    REQUIRE_APPROVAL = [
        r"open\(.+['\"]w['\"]",      # File write operations
        r"subprocess\.run",          # System command execution
        r"os\.system",               # Legacy system execution
        r"requests\.post",           # Outbound data transmission
    ]

    async def intercept(self, agent_output: str, context: Optional[dict] = None) -> HookResult:
        """
        Analyzes the provided text against security rules.
        """
        if not agent_output:
            return HookResult(action=HookAction.PASS)

        # 1. Absolute Blocking Check (Critical)
        for pattern in self.BLOCK_PATTERNS:
            if re.search(pattern, agent_output, re.IGNORECASE):
                logger.error(f"🛡️ Hooks: BLOCKED pattern matching '{pattern}'")
                return HookResult(
                    action=HookAction.BLOCK,
                    reason=f"Security violation: Pattern '{pattern}' is strictly prohibited.",
                    pattern=pattern
                )

        # 2. Approval Requirement Check
        for pattern in self.REQUIRE_APPROVAL:
            if re.search(pattern, agent_output, re.IGNORECASE):
                logger.warning(f"🛡️ Hooks: PENDING_APPROVAL for pattern matching '{pattern}'")
                return HookResult(
                    action=HookAction.PENDING_APPROVAL,
                    reason=f"Context sensitive action detected: '{pattern}' requires user verification.",
                    pattern=pattern
                )

        # 3. Default: Path is clear
        return HookResult(action=HookAction.PASS)

hooks_engine = HooksEngine()
