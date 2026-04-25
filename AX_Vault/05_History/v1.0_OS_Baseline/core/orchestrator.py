"""
JARVIS v5  Orchestrator

역할: Planner가 생성한 Plan을 받아 steps를 순서대로 실행한다.

수정 이력 (rebuild patch):
  - Plan.steps 존재를 전제로 실행 (계약 일치)
  - depends_on 기반 위상 정렬 실행
  - 각 step 결과를 context로 전달
  - 실패 step에 대한 retry / skip 정책 추가
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from core.planner import Plan, Step
from core.tool_registry import ToolRegistry

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
#  Result types
# ──────────────────────────────────────────────

@dataclass
class StepResult:
    step_id: int
    success: bool
    output: Any = None
    error: Optional[str] = None


@dataclass
class OrchestrationResult:
    goal: str
    step_results: List[StepResult] = field(default_factory=list)
    final_output: Any = None

    @property
    def success(self) -> bool:
        return all(r.success for r in self.step_results)

    @property
    def failed_steps(self) -> List[StepResult]:
        return [r for r in self.step_results if not r.success]


# ──────────────────────────────────────────────
#  Orchestrator
# ──────────────────────────────────────────────

class Orchestrator:
    """
    Plan을 받아 steps를 의존성 순서로 실행한다.

    Parameters
    ----------
    tool_registry : ToolRegistry
        사용 가능한 tool 집합
    max_retries : int
        step 실패 시 재시도 횟수 (기본 2)
    skip_on_failure : bool
        True면 실패 step을 스킵하고 계속 진행,
        False면 즉시 중단 (기본 True)
    """

    def __init__(
        self,
        tool_registry: ToolRegistry,
        max_retries: int = 2,
        skip_on_failure: bool = True,
    ) -> None:
        self._registry = tool_registry
        self._max_retries = max_retries
        self._skip_on_failure = skip_on_failure

    # ── public ──────────────────────────────

    async def run(self, plan: Plan) -> OrchestrationResult:
        """Plan의 steps를 의존성 순서로 실행한다."""
        # Plan.steps 계약 확인 (Planner가 항상 보장하지만 방어적으로 체크)
        if not plan.steps:
            logger.error("Orchestrator received a plan with no steps — aborting")
            return OrchestrationResult(goal=plan.goal)

        result = OrchestrationResult(goal=plan.goal)
        context: Dict[int, Any] = {}          # step_id → output
        order = self._topological_sort(plan.steps)

        for step in order:
            step_result = await self._execute_step(step, context)
            result.step_results.append(step_result)

            if step_result.success:
                context[step.id] = step_result.output
            else:
                logger.warning(
                    "Step %d failed: %s", step.id, step_result.error
                )
                if not self._skip_on_failure:
                    logger.error("Aborting orchestration at step %d", step.id)
                    break

        result.final_output = self._collect_output(result.step_results, context)
        return result

    # ──────────────────────────────────────────────
# ──────────────────────────────────────────────

    async def _execute_step(
        self, step: Step, context: Dict[int, Any]
    ) -> StepResult:
        enriched_args = {**step.args, "_context": context}

        for attempt in range(1, self._max_retries + 2):
            try:
                if step.tool:
                    tool = self._registry.get(step.tool)
                    output = await tool.run(enriched_args)
                else:
                    # tool 없는 step: context를 그대로 output으로
                    output = enriched_args.get("query", step.action)

                logger.debug(
                    "Step %d (%s) succeeded on attempt %d",
                    step.id, step.action, attempt,
                )
                return StepResult(step_id=step.id, success=True, output=output)

            except Exception as exc:
                if attempt <= self._max_retries:
                    wait = 2 ** (attempt - 1)   # 지수 백오프
                    logger.warning(
                        "Step %d attempt %d/%d failed (%s), retrying in %ds",
                        step.id, attempt, self._max_retries + 1, exc, wait,
                    )
                    await asyncio.sleep(wait)
                else:
                    return StepResult(
                        step_id=step.id,
                        success=False,
                        error=str(exc),
                    )

        # 이 줄에는 도달하지 않음
        return StepResult(step_id=step.id, success=False, error="unknown")

    @staticmethod
    def _topological_sort(steps: List[Step]) -> List[Step]:
        """Kahn's algorithm으로 depends_on 기반 위상 정렬"""
        id_map = {s.id: s for s in steps}
        in_degree: Dict[int, int] = {s.id: 0 for s in steps}
        adj: Dict[int, List[int]] = {s.id: [] for s in steps}

        for s in steps:
            for dep in s.depends_on:
                if dep in adj:
                    adj[dep].append(s.id)
                    in_degree[s.id] += 1

        queue = [sid for sid, deg in in_degree.items() if deg == 0]
        ordered: List[Step] = []

        while queue:
            sid = queue.pop(0)
            ordered.append(id_map[sid])
            for neighbor in adj[sid]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(ordered) != len(steps):
            logger.warning("Cycle detected in plan steps — falling back to original order")
            return steps

        return ordered

    @staticmethod
    def _collect_output(
        results: List[StepResult], context: Dict[int, Any]
    ) -> Any:
        """마지막 성공 step의 output을 최종 결과로 반환"""
        successful = [r for r in results if r.success]
        if not successful:
            return None
        last_id = successful[-1].step_id
        return context.get(last_id)
