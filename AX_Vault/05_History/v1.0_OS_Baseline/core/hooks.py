"""
JARVIS v5  Hook System

역할: 요청/응답 파이프라인에 끼어들어 정책을 적용하는 미들웨어 훅.

완화 전략 (rebuild patch):
  WARN    위반 감지 시 로그만, 파이프라인은 계속
  SOFT    위반 감지 시 로그 + 응답에 경고 플래그 추가
  STRICT  위반 감지 시 즉시 차단 (예외 발생)

환경변수 HOOK_MODE=WARN|SOFT|STRICT 로 제어 (기본 WARN)
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class HookMode(str, Enum):
    WARN   = "WARN"
    SOFT   = "SOFT"
    STRICT = "STRICT"

_DEFAULT_MODE = HookMode(os.getenv("HOOK_MODE", "WARN").upper())


@dataclass
class Violation:
    rule: str
    detail: str
    severity: str = "medium"


class HookViolationError(RuntimeError):
    def __init__(self, violations: List[Violation]) -> None:
        self.violations = violations
        super().__init__(
            f"{len(violations)} hook violation(s): "
            + "; ".join(f"[{v.rule}] {v.detail}" for v in violations)
        )


HookFn = Callable[[Dict[str, Any]], List[Violation]]


class HookManager:
    def __init__(self, mode: HookMode = _DEFAULT_MODE) -> None:
        self.mode = mode
        self._hooks: Dict[str, List[HookFn]] = {}
        logger.info("HookManager initialized in %s mode", self.mode)

    def register(self, stage: str, fn: HookFn) -> None:
        self._hooks.setdefault(stage, []).append(fn)
        logger.debug("Hook registered: stage=%s  fn=%s", stage, fn.__name__)

    def run(
        self, stage: str, context: Dict[str, Any]
    ) -> List[Violation]:
        all_violations: List[Violation] = []

        for fn in self._hooks.get(stage, []):
            try:
                violations = fn(context)
                all_violations.extend(violations)
            except Exception as exc:
                logger.error("Hook '%s' raised unexpectedly: %s", fn.__name__, exc)

        if not all_violations:
            return []

        self._handle_violations(all_violations)
        return all_violations

    def _handle_violations(self, violations: List[Violation]) -> None:
        summary = "; ".join(f"[{v.rule}] {v.detail}" for v in violations)

        if self.mode == HookMode.WARN:
            logger.warning("Hook violations (WARN mode, not blocking): %s", summary)

        elif self.mode == HookMode.SOFT:
            logger.warning("Hook violations (SOFT mode, flagging): %s", summary)

        elif self.mode == HookMode.STRICT:
            logger.error("Hook violations (STRICT mode, blocking): %s", summary)
            raise HookViolationError(violations)


def input_length_hook(context: Dict[str, Any]) -> List[Violation]:
    violations: List[Violation] = []
    messages = context.get("messages", [])
    for i, msg in enumerate(messages):
        if len(str(msg.get("content", ""))) > 32_000:
            violations.append(
                Violation(
                    rule="input_length",
                    detail=f"message[{i}] exceeds 32k chars",
                    severity="medium",
                )
            )
    return violations


def unsafe_tool_hook(context: Dict[str, Any]) -> List[Violation]:
    BLOCKED_TOOLS = set(os.getenv("BLOCKED_TOOLS", "shell,exec").split(","))
    violations: List[Violation] = []
    steps = context.get("steps", [])
    for step in steps:
        tool = step.get("tool")
        if tool and tool in BLOCKED_TOOLS:
            violations.append(
                Violation(
                    rule="unsafe_tool",
                    detail=f"Tool '{tool}' is blocked",
                    severity="high",
                )
            )
    return violations


def register_default_hooks(manager: HookManager) -> None:
    manager.register("input",  input_length_hook)
    manager.register("plan",   unsafe_tool_hook)
