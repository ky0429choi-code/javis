"""
JARVIS 종적 신뢰도 API 엔드포인트.
시스템 신뢰도 요약, 종적 트렌드, 완료보고서 조회를 제공합니다.
"""

from fastapi import APIRouter, Query
from typing import Optional
import logging

from app.core.confidence_collector import get_confidence_collector
from app.core.completion_reporter import get_completion_reporter

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/confidence", tags=["confidence"])


@router.get("/summary")
async def confidence_summary(days: int = Query(7, ge=1, le=90)):
    """전체 시스템 신뢰도 요약.

    Returns:
        컴포넌트별 신뢰도, 프로바이더별 신뢰도, 성공률, 경고 목록.
    """
    collector = get_confidence_collector()
    summary = collector.get_system_summary(days=days)
    return {"ok": True, "data": summary}


@router.get("/health")
async def confidence_health():
    """시스템 신뢰도 헬스체크.

    Returns:
        전체 건강도(excellent/good/degraded/critical), 경고 목록.
    """
    collector = get_confidence_collector()
    summary = collector.get_system_summary(days=1)

    health = summary.get("overall_health", "unknown")
    is_healthy = health in ("excellent", "good")

    return {
        "ok": is_healthy,
        "health": health,
        "overall_score": summary.get("overall_score", 0),
        "warnings": summary.get("warnings", []),
    }


@router.get("/trends")
async def confidence_trends(
    period: str = Query("7d", regex="^[0-9]+d$"),
    component: Optional[str] = None,
):
    """종적 트렌드 조회.

    Args:
        period: 조회 기간 (예: 7d, 14d, 30d)
        component: 특정 컴포넌트만 조회 (planner/executor/reviewer/wiki/router)
    """
    days = int(period.replace("d", ""))
    collector = get_confidence_collector()

    if component:
        data = collector.get_component_confidence(component, days=days)
        return {"ok": True, "data": {component: data}}

    components = ["planner", "executor", "reviewer", "wiki", "router"]
    result = {}
    for comp in components:
        result[comp] = collector.get_component_confidence(comp, days=days)

    return {"ok": True, "data": result, "period": period}


@router.get("/providers")
async def provider_confidence(days: int = Query(7, ge=1, le=90)):
    """프로바이더별 종적 신뢰도.

    Returns:
        각 프로바이더의 EMA, 평균, 건강상태.
    """
    collector = get_confidence_collector()
    data = collector.get_provider_confidence(days=days)
    return {"ok": True, "data": data}


@router.get("/reports")
async def list_reports(limit: int = Query(10, ge=1, le=100)):
    """최근 완료보고서 목록 조회."""
    collector = get_confidence_collector()
    reports = collector.get_completion_reports(limit=limit)
    return {"ok": True, "data": reports, "total": len(reports)}


@router.get("/report/{task_id}")
async def get_report(task_id: str):
    """특정 작업의 완료보고서 조회 (마크다운 포함)."""
    collector = get_confidence_collector()
    report = collector.get_report_by_task(task_id)

    if not report:
        return {"ok": False, "error": f"보고서를 찾을 수 없습니다: {task_id}"}

    return {"ok": True, "data": report}


@router.get("/daily")
async def daily_summary():
    """일일 종적 요약 보고서."""
    reporter = get_completion_reporter()
    md = reporter.generate_daily_summary()
    return {"ok": True, "report_md": md}


@router.get("/weekly")
async def weekly_trend():
    """주간 트렌드 분석 보고서."""
    reporter = get_completion_reporter()
    md = reporter.generate_weekly_trend()
    return {"ok": True, "report_md": md}
