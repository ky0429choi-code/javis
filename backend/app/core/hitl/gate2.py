"""
HITL Gate 2 — API 비용 게이트.

설계 원칙 (변경 금지):
- 독립 모듈로 동작한다 (Router에 인라인 삽입 금지)
- Cloud Provider 호출 시 예상 비용 > 임계값이면 마스터 확인
- 위치: LLM Router에서 Cloud Provider 선택 직후

트리거: Cloud API 비용 임계값 초과 ($0.01 기본)
"""

import logging
from typing import Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class CostDecision(str, Enum):
    PASS = "pass"
    HOLD = "hold"       # 비용 초과 → 마스터 확인 필요


@dataclass
class Gate2Result:
    decision: CostDecision
    estimated_cost: float = 0.0
    provider: str = ""
    reason: str = ""


# 프로바이더별 예상 비용 (per 1K tokens, 입력 기준)
PROVIDER_COSTS = {
    "local_ollama": 0.0,
    "groq": 0.0,           # 무료 티어
    "huggingface": 0.0,    # 무료 티어
    "claude_haiku": 0.00025,
    "openai_batch": 0.00015,
}

# 평균 요청 토큰 수 (추정)
AVG_TOKENS_PER_REQUEST = 2000


class HITLGate2:
    """
    API 비용 게이트.
    Cloud Provider 호출 전 예상 비용을 체크하고,
    임계값을 넘으면 마스터에게 확인을 받습니다.
    """

    def __init__(self, cost_threshold: float = 0.01):
        self.cost_threshold = cost_threshold
        self.session_cost = 0.0  # 세션 누적 비용

    def evaluate(self, provider_key: str) -> Gate2Result:
        """
        Cloud 호출 전 비용을 평가합니다.

        Returns:
            Gate2Result with decision: PASS / HOLD
        """
        cost_per_1k = PROVIDER_COSTS.get(provider_key, 0.0)

        # 무료 프로바이더는 무조건 통과
        if cost_per_1k == 0.0:
            return Gate2Result(
                decision=CostDecision.PASS,
                estimated_cost=0.0,
                provider=provider_key,
            )

        # 예상 비용 계산
        estimated = cost_per_1k * (AVG_TOKENS_PER_REQUEST / 1000)

        # 임계값 체크
        if estimated > self.cost_threshold:
            logger.warning(
                f"Gate2: HOLD — {provider_key} estimated ${estimated:.4f} "
                f"exceeds threshold ${self.cost_threshold}"
            )
            return Gate2Result(
                decision=CostDecision.HOLD,
                estimated_cost=estimated,
                provider=provider_key,
                reason=f"Estimated cost ${estimated:.4f} > threshold ${self.cost_threshold}",
            )

        # 통과 + 비용 누적
        self.session_cost += estimated
        logger.debug(f"Gate2: PASS — {provider_key} ${estimated:.4f} (session: ${self.session_cost:.4f})")
        return Gate2Result(
            decision=CostDecision.PASS,
            estimated_cost=estimated,
            provider=provider_key,
        )

    def get_session_cost(self) -> float:
        return self.session_cost

    def reset_session(self):
        self.session_cost = 0.0


gate2 = HITLGate2()
