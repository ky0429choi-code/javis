"""
JARVIS 종적 기반 신뢰도 시스템 스키마.
파이프라인 각 단계의 신뢰도를 수치화하고 종적으로 추적합니다.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime


class PipelineComponent(str, Enum):
    """파이프라인 컴포넌트 식별자."""
    PLANNER = "planner"
    EXECUTOR = "executor"
    REVIEWER = "reviewer"
    WIKI = "wiki"
    ROUTER = "router"


class ConfidenceLevel(str, Enum):
    """신뢰도 등급."""
    CRITICAL = "critical"    # 0.0 ~ 0.3
    LOW = "low"              # 0.3 ~ 0.5
    MODERATE = "moderate"    # 0.5 ~ 0.7
    HIGH = "high"            # 0.7 ~ 0.9
    EXCELLENT = "excellent"  # 0.9 ~ 1.0


def score_to_level(score: float) -> ConfidenceLevel:
    """점수를 등급으로 변환."""
    if score < 0.3:
        return ConfidenceLevel.CRITICAL
    elif score < 0.5:
        return ConfidenceLevel.LOW
    elif score < 0.7:
        return ConfidenceLevel.MODERATE
    elif score < 0.9:
        return ConfidenceLevel.HIGH
    return ConfidenceLevel.EXCELLENT


def score_to_stars(score: float) -> str:
    """점수를 별점 문자열로 변환."""
    filled = round(score * 5)
    return "★" * filled + "☆" * (5 - filled)


class StepConfidence(BaseModel):
    """파이프라인 단일 스텝의 신뢰도."""
    component: PipelineComponent
    score: float = Field(ge=0.0, le=1.0, description="신뢰도 점수 (0.0 ~ 1.0)")
    reason: str = ""
    latency_ms: int = 0
    retries: int = 0
    provider: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @property
    def level(self) -> ConfidenceLevel:
        return score_to_level(self.score)

    @property
    def status_emoji(self) -> str:
        if self.score >= 0.9:
            return "✅"
        elif self.score >= 0.7:
            return "🟢"
        elif self.score >= 0.5:
            return "⚠️"
        return "🔴"


class PipelineConfidence(BaseModel):
    """전체 파이프라인 실행의 종합 신뢰도."""
    task_id: str
    goal: str
    steps: List[StepConfidence] = Field(default_factory=list)
    overall_score: float = Field(ge=0.0, le=1.0, default=0.0)
    duration_ms: int = 0
    provider_used: Optional[str] = None
    success: bool = True
    created_at: str = ""

    # 가중치: Planner 15%, Executor 35%, Reviewer 30%, Wiki 20%
    COMPONENT_WEIGHTS: Dict[str, float] = {
        "planner": 0.15,
        "executor": 0.35,
        "reviewer": 0.30,
        "wiki": 0.20,
    }

    def calculate_overall(self) -> float:
        """가중 평균으로 전체 신뢰도 계산."""
        if not self.steps:
            return 0.0

        weighted_sum = 0.0
        total_weight = 0.0

        for step in self.steps:
            weight = self.COMPONENT_WEIGHTS.get(step.component.value, 0.1)
            weighted_sum += step.score * weight
            total_weight += weight

        self.overall_score = round(weighted_sum / total_weight, 4) if total_weight > 0 else 0.0
        return self.overall_score


class CompletionReport(BaseModel):
    """종적 기반 완료보고서 모델."""
    task_id: str
    goal: str
    overall_score: float = 0.0
    level: str = ""
    stars: str = ""
    pipeline_scores: Dict[str, float] = Field(default_factory=dict)
    step_details: List[Dict[str, Any]] = Field(default_factory=list)
    provider_used: Optional[str] = None
    duration_ms: int = 0
    trends: Dict[str, Any] = Field(default_factory=dict)
    recommendations: List[str] = Field(default_factory=list)
    report_md: str = ""
    created_at: str = ""

    @classmethod
    def from_pipeline(cls, pipeline: PipelineConfidence, trends: Dict = None, recommendations: List[str] = None) -> "CompletionReport":
        """PipelineConfidence로부터 완료보고서 생성."""
        pipeline.calculate_overall()

        pipeline_scores = {}
        step_details = []
        for step in pipeline.steps:
            pipeline_scores[step.component.value] = step.score
            step_details.append({
                "component": step.component.value,
                "score": step.score,
                "status": step.status_emoji,
                "latency_ms": step.latency_ms,
                "retries": step.retries,
                "reason": step.reason,
            })

        return cls(
            task_id=pipeline.task_id,
            goal=pipeline.goal,
            overall_score=pipeline.overall_score,
            level=score_to_level(pipeline.overall_score).value,
            stars=score_to_stars(pipeline.overall_score),
            pipeline_scores=pipeline_scores,
            step_details=step_details,
            provider_used=pipeline.provider_used,
            duration_ms=pipeline.duration_ms,
            trends=trends or {},
            recommendations=recommendations or [],
            created_at=pipeline.created_at or datetime.now().isoformat(),
        )


class ConfidenceTrend(BaseModel):
    """시계열 신뢰도 트렌드."""
    component: str
    period: str = "7d"
    data_points: List[Dict[str, Any]] = Field(default_factory=list)
    current_ema: float = 0.0
    previous_ema: float = 0.0
    direction: str = "stable"  # improving, degrading, stable
    sample_count: int = 0

    @property
    def direction_emoji(self) -> str:
        if self.direction == "improving":
            return "↑"
        elif self.direction == "degrading":
            return "↓"
        return "→"


class ConfidenceSummary(BaseModel):
    """전체 시스템 신뢰도 요약."""
    overall_health: str = "unknown"
    overall_score: float = 0.0
    component_scores: Dict[str, float] = Field(default_factory=dict)
    provider_scores: Dict[str, float] = Field(default_factory=dict)
    total_tasks: int = 0
    success_rate: float = 0.0
    trends: List[ConfidenceTrend] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    last_updated: str = ""
