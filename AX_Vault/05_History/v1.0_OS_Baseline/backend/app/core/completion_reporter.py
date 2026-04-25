"""
JARVIS 종적 완료보고서 생성기.
파이프라인 완료 시 구조화된 완료보고서(JSON + Markdown)를 자동 생성합니다.
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

from app.schemas.confidence import (
    PipelineConfidence,
    CompletionReport,
    score_to_level,
    score_to_stars,
)
from app.core.confidence_collector import get_confidence_collector

logger = logging.getLogger(__name__)

# AX_Vault 경로
AX_VAULT_AUDIT = Path(__file__).resolve().parents[2] / "AX_Vault" / "04_Audit"


class CompletionReporter:
    """종적 완료보고서 생성기."""

    def __init__(self):
        self.collector = get_confidence_collector()
        AX_VAULT_AUDIT.mkdir(parents=True, exist_ok=True)

    def generate_report(self, pipeline: PipelineConfidence) -> CompletionReport:
        """단일 작업의 완료보고서를 생성합니다."""
        pipeline.calculate_overall()

        # 종적 트렌드 수집
        trends = self._collect_trends(pipeline)

        # 권장사항 생성
        recommendations = self._generate_recommendations(pipeline, trends)

        # CompletionReport 객체 생성
        report = CompletionReport.from_pipeline(
            pipeline=pipeline,
            trends=trends,
            recommendations=recommendations,
        )

        # 마크다운 렌더링
        report.report_md = self._render_markdown(report)

        # DB에 저장
        self.collector.record_completion(
            task_id=report.task_id,
            goal=report.goal,
            overall_score=report.overall_score,
            pipeline_scores=report.pipeline_scores,
            provider_used=report.provider_used,
            duration_ms=report.duration_ms,
            report_md=report.report_md,
        )

        # AX_Vault에 마크다운 파일 저장
        self._save_to_vault(report)

        logger.info(
            f"📋 완료보고서 생성: {report.task_id} "
            f"(score={report.overall_score:.2f}, level={report.level})"
        )

        return report

    def generate_daily_summary(self) -> str:
        """일일 종적 요약 보고서를 생성합니다."""
        summary = self.collector.get_system_summary(days=1)
        reports = self.collector.get_completion_reports(limit=50)

        # 오늘 날짜 보고서만 필터
        today = datetime.now().strftime("%Y-%m-%d")
        today_reports = [
            r for r in reports
            if r.get("created_at", "").startswith(today)
        ]

        md = f"""# JARVIS 일일 신뢰도 보고서
**날짜**: {today}
**전체 건강도**: {summary.get('overall_health', 'unknown')} ({summary.get('overall_score', 0):.2f})

## 오늘의 통계
| 지표 | 값 |
|------|---|
| 총 작업 수 | {len(today_reports)} |
| 성공률 | {summary.get('success_rate', 0):.1f}% |
| 평균 신뢰도 | {summary.get('overall_score', 0):.2f} |

## 컴포넌트별 신뢰도
"""
        for comp, score in summary.get("component_scores", {}).items():
            level = score_to_level(score).value if score > 0 else "N/A"
            md += f"| {comp} | {score:.2f} | {level} |\n"

        if summary.get("warnings"):
            md += "\n## ⚠️ 경고\n"
            for w in summary["warnings"]:
                md += f"- {w}\n"

        md += f"\n---\n**생성 시각**: {datetime.now().isoformat()}\n"
        return md

    def generate_weekly_trend(self) -> str:
        """주간 트렌드 분석 보고서를 생성합니다."""
        components = ["planner", "executor", "reviewer", "wiki", "router"]
        trends = {}
        for comp in components:
            trends[comp] = self.collector.get_component_confidence(comp, days=7)

        md = f"""# JARVIS 주간 신뢰도 트렌드
**기간**: 최근 7일
**생성일**: {datetime.now().strftime('%Y-%m-%d')}

## 컴포넌트별 추이
| 컴포넌트 | EMA | 평균 | 최소 | 최대 | 샘플 | 방향 |
|----------|-----|------|------|------|------|------|
"""
        for comp in components:
            info = trends.get(comp, {})
            ema = info.get("ema", 0)
            avg = info.get("average", 0)
            mn = info.get("min", 0)
            mx = info.get("max", 0)
            cnt = info.get("sample_count", 0)
            direction = info.get("direction", "unknown")
            direction_emoji = {"improving": "↑", "degrading": "↓", "stable": "→"}.get(direction, "?")
            md += f"| {comp} | {ema:.2f} | {avg:.2f} | {mn:.2f} | {mx:.2f} | {cnt} | {direction_emoji} {direction} |\n"

        # 프로바이더 분석
        provider_data = self.collector.get_provider_confidence(days=7)
        if provider_data:
            md += "\n## 프로바이더별 신뢰도\n"
            md += "| 프로바이더 | EMA | 평균 | 건강 |\n"
            md += "|-----------|-----|------|------|\n"
            for prov, info in provider_data.items():
                healthy = "✅" if info.get("is_healthy") else "🔴"
                md += f"| {prov} | {info.get('ema', 0):.2f} | {info.get('average', 0):.2f} | {healthy} |\n"

        md += f"\n---\n**생성 시각**: {datetime.now().isoformat()}\n"
        return md

    # ==================== 내부 메서드 ====================

    def _collect_trends(self, pipeline: PipelineConfidence) -> Dict[str, Any]:
        """현재 작업과 관련된 종적 트렌드를 수집합니다."""
        result = {}
        for step in pipeline.steps:
            comp = step.component.value
            info = self.collector.get_component_confidence(comp, days=7)
            result[comp] = {
                "ema": info.get("ema", 0),
                "direction": info.get("direction", "unknown"),
                "sample_count": info.get("sample_count", 0),
            }
        return result

    def _generate_recommendations(
        self, pipeline: PipelineConfidence, trends: Dict[str, Any]
    ) -> List[str]:
        """신뢰도 기반 시스템 개선 권장사항을 생성합니다."""
        recs = []

        for step in pipeline.steps:
            comp = step.component.value
            trend = trends.get(comp, {})

            # 재시도 과다
            if step.retries > 1:
                recs.append(
                    f"{comp}: 재시도 {step.retries}회 발생 → 프롬프트 개선 또는 모델 변경 권장"
                )

            # 응답 시간 초과
            if step.latency_ms > 5000:
                recs.append(
                    f"{comp}: 응답 {step.latency_ms}ms 소요 → 경량 모델 전환 또는 캐시 활용 권장"
                )

            # 종적 하락 감지
            if trend.get("direction") == "degrading":
                recs.append(
                    f"{comp}: 신뢰도 하락 추세 (EMA={trend.get('ema', 0):.2f}) → 파이프라인 점검 권장"
                )

            # 낮은 점수
            if step.score < 0.5:
                recs.append(
                    f"{comp}: 신뢰도 위험 수준 ({step.score:.2f}) → 즉시 원인 분석 필요"
                )

        if not recs:
            recs.append("현재 모든 컴포넌트가 정상 범위입니다.")

        return recs

    def _render_markdown(self, report: CompletionReport) -> str:
        """완료보고서를 마크다운으로 렌더링합니다."""
        md = f"""# JARVIS 완료보고서
**Task ID**: {report.task_id}
**목표**: {report.goal}
**전체 신뢰도**: {report.overall_score:.2f} ({report.stars})
**등급**: {report.level}
**소요 시간**: {report.duration_ms}ms
**프로바이더**: {report.provider_used or 'N/A'}

---

## 파이프라인 스코어카드
| 단계 | 점수 | 상태 | 소요시간 | 재시도 | 비고 |
|------|------|------|----------|--------|------|
"""
        for detail in report.step_details:
            md += (
                f"| {detail['component']} | {detail['score']:.2f} | {detail['status']} | "
                f"{detail['latency_ms']}ms | {detail['retries']} | {detail['reason']} |\n"
            )

        # 종적 트렌드
        if report.trends:
            md += "\n## 종적 트렌드 (최근 7일)\n"
            for comp, trend in report.trends.items():
                ema = trend.get("ema", 0)
                direction = trend.get("direction", "unknown")
                direction_emoji = {"improving": "↑", "degrading": "↓", "stable": "→"}.get(direction, "?")
                md += f"- **{comp}**: EMA {ema:.2f} ({direction_emoji} {direction})\n"

        # 권장사항
        if report.recommendations:
            md += "\n## 권장사항\n"
            for rec in report.recommendations:
                md += f"- {rec}\n"

        md += f"\n---\n**생성 시각**: {report.created_at}\n"
        return md

    def _save_to_vault(self, report: CompletionReport) -> None:
        """완료보고서를 AX_Vault에 마크다운 파일로 저장합니다."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"report_{timestamp}_{report.task_id}.md"
            filepath = AX_VAULT_AUDIT / filename

            filepath.write_text(report.report_md, encoding="utf-8")
            logger.info(f"📁 보고서 저장: {filepath}")
        except Exception as e:
            logger.warning(f"보고서 파일 저장 실패: {e}")


# 싱글톤
_reporter_instance = None


def get_completion_reporter() -> CompletionReporter:
    """CompletionReporter 싱글톤."""
    global _reporter_instance
    if not _reporter_instance:
        _reporter_instance = CompletionReporter()
    return _reporter_instance
