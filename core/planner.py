"""
JARVIS v5  Planner

역할: 사용자 입력을 받아 Orchestrator가 소비할 수 있는
      { "goal": str, "steps": List[Step] } 형태의 계획을 생성한다.

수정 이력 (rebuild patch):
  - Orchestrator와의 계약 불일치 수정: 반환값에 반드시 'steps' 포함
  - JSON 파싱 실패 시 fallback single-step 생성
  - steps 스키마 검증 추가
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from core.llm_router import LLMRouter

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
#  Data contracts
# ──────────────────────────────────────────────

@dataclass
class Step:
    id: int
    action: str
    tool: Optional[str] = None
    args: Dict[str, Any] = field(default_factory=dict)
    depends_on: List[int] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "action": self.action,
            "tool": self.tool,
            "args": self.args,
            "depends_on": self.depends_on,
        }


@dataclass
class Plan:
    goal: str
    steps: List[Step]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "goal": self.goal,
            "steps": [s.to_dict() for s in self.steps],
        }


# ──────────────────────────────────────────────
#  Planner
# ──────────────────────────────────────────────

_SYSTEM_PROMPT = """\
You are a planning agent. Given a user goal, produce a JSON execution plan.

Output ONLY valid JSON — no markdown fences, no commentary.

Schema:
{
  "goal": "<restate the goal concisely>",
  "steps": [
    {
      "id": 1,
      "action": "<short verb phrase>",
      "tool": "<tool_name or null>",
      "args": {},
      "depends_on": []
    }
  ]
}

Rules:
- steps must be a non-empty array.
- Each step must have id (int, 1-based), action (str), tool (str | null),
  args (object), depends_on (array of int).
- depends_on lists ids of steps that must complete before this one.
"""


class Planner:
    def __init__(self, router: LLMRouter) -> None:
        self._router = router

    # ── public ──────────────────────────────

    def create_plan(self, user_input: str) -> Plan:
        """
        LLM을 호출해 계획을 생성한다.
        파싱에 실패하면 fallback Plan을 반환한다 (절대 예외를 올리지 않음).
        """
        raw = self._call_llm(user_input)
        plan = self._parse_plan(raw, user_input)
        logger.info("Plan created: goal=%r  steps=%d", plan.goal, len(plan.steps))
        return plan

    # ── private ─────────────────────────────

    def _call_llm(self, user_input: str) -> str:
        messages = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_input},
        ]
        try:
            return self._router.complete_sync(model_key="planner", messages=messages)
        except Exception as exc:
            logger.warning("Planner LLM call failed: %s", exc)
            return ""

    def _parse_plan(self, raw: str, original_input: str) -> Plan:
        """JSON 파싱 → 스키마 검증 → fallback 순서로 처리"""
        # 1) JSON 블록 추출 (```json ... ``` 래핑 방어)
        cleaned = self._strip_fences(raw)

        # 2) 파싱 시도
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            logger.warning("Planner: JSON decode failed, using fallback")
            return self._fallback_plan(original_input)

        # 3) 스키마 검증
        if not isinstance(data, dict):
            logger.warning("Planner: top-level is not object, fallback")
            return self._fallback_plan(original_input)

        raw_steps = data.get("steps")
        if not isinstance(raw_steps, list) or len(raw_steps) == 0:
            logger.warning("Planner: 'steps' missing or empty, fallback")
            return self._fallback_plan(original_input)

        # 4) Step 객체 변환
        steps: List[Step] = []
        for idx, s in enumerate(raw_steps, start=1):
            if not isinstance(s, dict):
                continue
            steps.append(
                Step(
                    id=int(s.get("id", idx)),
                    action=str(s.get("action", f"step_{idx}")),
                    tool=s.get("tool"),
                    args=s.get("args", {}),
                    depends_on=s.get("depends_on", []),
                )
            )

        if not steps:
            return self._fallback_plan(original_input)

        return Plan(goal=str(data.get("goal", original_input)), steps=steps)

    @staticmethod
    def _strip_fences(text: str) -> str:
        """```json ... ``` 혹은 ``` ... ``` 제거"""
        text = text.strip()
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        return text.strip()

    @staticmethod
    def _fallback_plan(original_input: str) -> Plan:
        """LLM 실패 시 단일 direct-answer 스텝으로 구성된 최소 계획"""
        return Plan(
            goal=original_input,
            steps=[
                Step(
                    id=1,
                    action="direct_answer",
                    tool=None,
                    args={"query": original_input},
                    depends_on=[],
                )
            ],
        )
