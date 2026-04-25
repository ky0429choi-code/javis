"""
API 라우터 초기화 - 모든 라우터 expose
"""

from . import chat, tasks, approvals, prompts, health, mobile

# 🆕 하이브리드 리소스 시스템 (4/18/2026)
try:
    from . import hybrid
    __all__ = ["chat", "tasks", "approvals", "prompts", "health", "mobile", "hybrid"]
except ImportError:
    __all__ = ["chat", "tasks", "approvals", "prompts", "health", "mobile"]
