from enum import Enum
import os

class HookMode(Enum):
    WARN = "warn"
    SOFT = "soft"
    STRICT = "strict"

# 기본값: warn
HOOK_MODE = HookMode(os.getenv("HOOK_MODE", "warn"))

HOOK_CONFIG = {
    HookMode.WARN: {
        "protection_enabled": False,
        "reminder_enabled": False,
        "audit_enabled": True,
    },
    HookMode.SOFT: {
        "protection_enabled": True,
        "protection_strict": False,
        "reminder_enabled": False,
        "audit_enabled": True,
    },
    HookMode.STRICT: {
        "protection_enabled": True,
        "protection_strict": True,
        "reminder_enabled": True,
        "audit_enabled": True,
    },
}

ACTIVE_HOOKS = HOOK_CONFIG[HOOK_MODE]
