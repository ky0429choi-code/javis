import logging
import asyncio
import time
import uuid
from typing import Dict, Any, Optional, List
from app.llm.router import router
from app.agents.planner import planner
from app.agents.executor import executor
from app.agents.reviewer import reviewer
from app.harness.rules_engine import rules_engine
from app.harness.hooks_engine import hooks_engine
from app.schemas.v4_core import IntentResult, PlanResult, SubTask, HookAction
from app.schemas.confidence import StepConfidence, PipelineConfidence, PipelineComponent
from app.engines.approval_engine import ApprovalEngine
from app.memory.repository import Repository
from app.core.confidence_collector import get_confidence_collector
from app.core.completion_reporter import get_completion_reporter

logger = logging.getLogger(__name__)


class JarvisConductor:
    """
    JARVIS Core 4.0 Orchestrator (Hardened + Confidence Instrumented).
    Implements the full Agent Pipeline: Plan -> Execute -> Review.
    Each step is instrumented with longitudinal confidence tracking.
    """
    def __init__(self):
        self.identity = "Jarvis"
        self.approval_engine = ApprovalEngine()
        self.repo = Repository()

    async def process_request(self, message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Entry point for all JARVIS operations."""
        context = context or {}
        task_id = f"TASK-{uuid.uuid4().hex[:8].upper()}"
        start_time = time.time()

        collector = get_confidence_collector()
        reporter = get_completion_reporter()

        # 파이프라인 신뢰도 컨테이너
        pipeline_confidence = PipelineConfidence(
            task_id=task_id,
            goal=message,
            created_at=__import__("datetime").datetime.now().isoformat(),
        )

        # 1. Intent Stage
        intent = IntentResult(goal=message, context=context)

        # 2. Planning Stage
        plan_start = time.time()
        pre_plan = await planner.plan(intent.goal, intent.context)
        rules = rules_engine.get_system_prompt_extension("PLANNER")
        system_prompt = f"당신은 {self.identity}의 기획 모듈입니다. {rules}"

        raw_plan_response = await router.call(prompt=intent.goal, system=system_prompt, task_type="complex")
        final_plan = planner.parse_brain_response(raw_plan_response)
        plan_latency = int((time.time() - plan_start) * 1000)

        plan_ok = final_plan.status != "error"
        plan_score = collector.record_step(
            task_id=task_id,
            component="planner",
            success=plan_ok,
            latency_ms=plan_latency,
            retries=0,
            provider=None,
            reason=f"status={final_plan.status}, steps={len(final_plan.steps)}",
        )
        pipeline_confidence.steps.append(StepConfidence(
            component=PipelineComponent.PLANNER,
            score=plan_score,
            latency_ms=plan_latency,
            reason=f"status={final_plan.status}",
        ))

        # 이상탐지
        anomaly = collector.detect_anomaly("planner", plan_score)
        if anomaly:
            logger.warning(anomaly)

        if not plan_ok:
            pipeline_confidence.success = False
            pipeline_confidence.duration_ms = int((time.time() - start_time) * 1000)
            reporter.generate_report(pipeline_confidence)
            return {"ok": False, "error": "Plan generation failed.", "task_id": task_id}

        # 3. Execution Pipeline Stage
        execution_trace = await self._run_agent_pipeline(final_plan, task_id, pipeline_confidence)

        # 4. Audit & Growth Stage (Wiki Agent)
        wiki_start = time.time()
        wiki_ok = False
        if all(step.get("result", {}).get("ok") for step in execution_trace):
            try:
                from app.agents.wiki import wiki_agent
                asyncio.create_task(wiki_agent.process_task(intent.goal, execution_trace))
                wiki_ok = True
                logger.info("Conductor: Wiki Agent 가동 (백그라운드 학습 시작)")
            except Exception as e:
                logger.warning(f"Wiki Agent 실행 실패: {e}")

        wiki_latency = int((time.time() - wiki_start) * 1000)
        wiki_score = collector.record_step(
            task_id=task_id,
            component="wiki",
            success=wiki_ok,
            latency_ms=wiki_latency,
            reason="background_learning" if wiki_ok else "skipped_or_failed",
        )
        pipeline_confidence.steps.append(StepConfidence(
            component=PipelineComponent.WIKI,
            score=wiki_score,
            latency_ms=wiki_latency,
            reason="background_learning" if wiki_ok else "skipped",
        ))

        # 5. 완료보고서 생성
        pipeline_confidence.duration_ms = int((time.time() - start_time) * 1000)
        pipeline_confidence.provider_used = getattr(router, '_last_provider', None)
        report = reporter.generate_report(pipeline_confidence)

        return {
            "ok": True,
            "task_id": task_id,
            "goal": intent.goal,
            "plan": final_plan.model_dump(),
            "execution_trace": execution_trace,
            "confidence": {
                "overall": report.overall_score,
                "level": report.level,
                "stars": report.stars,
                "pipeline": report.pipeline_scores,
            },
            "status": "completed_v4"
        }

    async def _run_agent_pipeline(
        self, plan: PlanResult, task_id: str, pipeline_confidence: PipelineConfidence
    ) -> List[Dict[str, Any]]:
        """The Loop: Step-by-step Execution with Hooks, Review, and Confidence."""
        trace = []
        collector = get_confidence_collector()

        for step in plan.steps:
            logger.info(f"Conductor: Starting step '{step.title}'")
            step_start = time.time()

            step_result, retries_used = await self._execute_step_with_retry(step)
            step_latency = int((time.time() - step_start) * 1000)

            step_ok = step_result.get("ok", False)

            # Executor 신뢰도 기록
            exec_score = collector.record_step(
                task_id=task_id,
                component="executor",
                success=step_ok,
                latency_ms=step_latency,
                retries=retries_used,
                reason=f"step={step.title}, status={step_result.get('status', 'unknown')}",
            )
            pipeline_confidence.steps.append(StepConfidence(
                component=PipelineComponent.EXECUTOR,
                score=exec_score,
                latency_ms=step_latency,
                retries=retries_used,
                reason=f"step={step.title}",
            ))

            trace.append({
                "step": step.title,
                "result": step_result,
                "confidence": exec_score,
            })

            if not step_ok:
                logger.error(f"Conductor: Pipeline halted at step '{step.title}'")
                break

        return trace

    async def _execute_step_with_retry(self, step: SubTask, retries: int = 3):
        """Executor + Reviewer Loop (Self-Healing) with retry tracking."""
        feedback = None
        collector = get_confidence_collector()

        for attempt in range(retries):
            # 1. Execute
            res = await executor.execute(step, {"attempt": attempt, "feedback": feedback})

            # Handle Security/Approval states from Executor
            if res.get("status") == "blocked":
                return res, attempt

            if res.get("status") == "pending_approval":
                approval_req = self.approval_engine.build_request(
                    action_type=step.action,
                    target_path=res["target_path"],
                    reason=f"Hook trigger: {res['pattern']}",
                    requested_by="jarvis-core-v4",
                    content=res["content"]
                ).model_dump()
                saved = self.repo.create_approval(approval_req)
                return {"ok": False, "status": "awaiting_approval", "approval_id": saved["request_id"]}, attempt

            # 2. Review
            review_start = time.time()
            review_res = await reviewer.review(res, step.path)
            review_latency = int((time.time() - review_start) * 1000)

            review_ok = review_res["status"] == "pass"

            # Reviewer 신뢰도 기록 (task_id는 상위에서 관리되므로 여기서는 stub ID 사용)
            collector.record_step(
                task_id="__current__",
                component="reviewer",
                success=review_ok,
                latency_ms=review_latency,
                retries=0,
                reason=review_res.get("message", review_res.get("reason", "")),
            )

            if review_ok:
                return {"ok": True, "step": step.title, "result": res}, attempt

            if review_res["status"] == "fix":
                logger.warning(f"Conductor: Step '{step.title}' failed review. Retry {attempt+1}/{retries}")
                feedback = review_res["reason"]
                continue

        return {"ok": False, "status": "failed_after_retries", "step": step.title}, retries


conductor = JarvisConductor()
