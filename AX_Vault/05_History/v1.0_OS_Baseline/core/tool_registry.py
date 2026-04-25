"""
JARVIS v5  Tool Registry

역할: Orchestrator가 step 실행 시 tool 이름으로 조회할 수 있는 레지스트리.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict

logger = logging.getLogger(__name__)


class BaseTool(ABC):
    """모든 tool의 베이스 클래스"""

    name: str = ""

    @abstractmethod
    async def run(self, args: Dict[str, Any]) -> Any:
        ...


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        assert tool.name, "Tool must have a non-empty 'name'"
        self._tools[tool.name] = tool
        logger.info("Tool registered: %s", tool.name)

    def get(self, name: str) -> BaseTool:
        tool = self._tools.get(name)
        if tool is None:
            raise KeyError(f"Tool '{name}' not found in registry")
        return tool

    @property
    def names(self):
        return list(self._tools.keys())
