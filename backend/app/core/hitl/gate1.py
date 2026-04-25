"""
HITL Gate 1 — 실행 전 위험도 게이트.

설계 원칙 (변경 금지):
- 독립 모듈로 동작한다 (Executor/Router에 인라인 삽입 금지)
- 위험 패턴 감지 시 실행 보류 → 승인 큐 등록 → 마스터 대기
- 타임아웃 후 자동 거부

트리거: rm -rf, DROP TABLE, .env 접근, os.system 등
위치: Executor 진입 직전
"""

import logging
import asyncio
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class GateDecision(str, Enum):
    PASS = "pass"
    HOLD = "hold"       # 승인 대기
    BLOCK = "block"     # 즉시 차단


@dataclass
class Gate1Result:
    decision: GateDecision
    reason: str = ""
    approval_id: Optional[str] = None
    pattern: Optional[str] = None


class HITLGate1:
    """
    실행 전 위험도 게이트.
    HooksEngine과 별개로 작동하는 독립 안전 레이어.
    HooksEngine은 '코드 패턴' 검사, Gate1은 '행위 위험도' 검사.
    """

    # 절대 차단 — 어떤 승인으로도 실행 불가
    FATAL_PATTERNS = [
        "rm -rf /",
        "format c:",
        "DROP DATABASE",
        ":(){:|:&};:",  # fork bomb
    ]

    # 승인 필요 — 마스터가 OK하면 실행
    HOLD_ACTIONS = {
        "delete_file",
        "move_file",
        "modify_file",
        "execute_shell",
        "deploy",
    }

    # 핵심 경로 — 이 경로의 파일은 무조건 승인 필요
    PROTECTED_PATHS = [
        "core/",
        "harness/",
        "main.py",
        "config.py",
        "repository.py",
        "hitl/",
    ]

    APPROVAL_TIMEOUT_SECONDS = 300  # 5분

    async def evaluate(
        self,
        action: str,
        target_path: str,
        content: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Gate1Result:
        """
        실행 전 위험도를 평가합니다.

        Returns:
            Gate1Result with decision: PASS / HOLD / BLOCK
        """
        # 1. 절대 차단 검사
        if content:
            for pattern in self.FATAL_PATTERNS:
                if pattern in content:
                    logger.error(f"Gate1: BLOCK — Fatal pattern detected: {pattern}")
                    return Gate1Result(
                        decision=GateDecision.BLOCK,
                        reason=f"Fatal pattern: {pattern}",
                        pattern=pattern,
                    )

        # 2. 핵심 경로 보호 검사
        for protected in self.PROTECTED_PATHS:
            if protected in target_path:
                logger.warning(f"Gate1: HOLD — Protected path: {target_path}")
                return Gate1Result(
                    decision=GateDecision.HOLD,
                    reason=f"Protected path requires approval: {protected}",
                    pattern=f"PROTECTED_PATH:{protected}",
                )

        # 3. 위험 행위 검사
        if action in self.HOLD_ACTIONS:
            logger.info(f"Gate1: HOLD — Action '{action}' requires approval")
            return Gate1Result(
                decision=GateDecision.HOLD,
                reason=f"Action '{action}' requires master approval",
                pattern=f"HOLD_ACTION:{action}",
            )

        # 4. 통과
        return Gate1Result(decision=GateDecision.PASS)


gate1 = HITLGate1()
