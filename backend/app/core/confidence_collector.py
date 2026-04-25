"""
JARVIS 종적 신뢰도 수집 엔진.
파이프라인 각 단계에서 신뢰도를 수집하고 SQLite에 저장합니다.
EMA(지수이동평균) 기반 종적 트렌드 분석을 제공합니다.
"""

import logging
import sqlite3
import json
import math
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path

from app.utils.settings import get_settings

logger = logging.getLogger(__name__)

# 신뢰도 계산 상수
RETRY_PENALTY = 0.08         # 재시도 1회당 8% 감점
LATENCY_THRESHOLD_MS = 5000  # 5초 초과 시 감점 시작
LATENCY_PENALTY_RATE = 0.02  # 초과 1초당 2% 감점
EMA_ALPHA = 0.3              # EMA 가중치 (최신 데이터 30% 반영)
ANOMALY_SIGMA = 2.0          # 이상탐지 시그마 임계값
MIN_PROVIDER_CONFIDENCE = 0.5  # 프로바이더 자동 비활성화 임계값


class ConfidenceCollector:
    """종적 신뢰도 수집기 (싱글톤)."""

    def __init__(self):
        settings = get_settings()
        self.db_path = Path(__file__).resolve().parents[3] / settings.sqlite_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def _connect(self):
        return sqlite3.connect(self.db_path)

    # ==================== 기록 ====================

    def record_step(
        self,
        task_id: str,
        component: str,
        success: bool,
        latency_ms: int = 0,
        retries: int = 0,
        provider: str = None,
        reason: str = "",
        metadata: Dict[str, Any] = None,
    ) -> float:
        """개별 스텝의 신뢰도를 계산하고 기록합니다."""
        score = self._calculate_step_score(success, latency_ms, retries)

        try:
            with self._connect() as con:
                con.execute(
                    "INSERT INTO confidence_log "
                    "(task_id, component, score, reason, latency_ms, retries, provider, metadata) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        task_id,
                        component,
                        round(score, 4),
                        reason,
                        latency_ms,
                        retries,
                        provider,
                        json.dumps(metadata or {}, ensure_ascii=False),
                    ),
                )
                con.commit()
        except Exception as e:
            logger.warning(f"신뢰도 기록 실패 ({component}): {e}")

        logger.info(
            f"📊 Confidence [{component}]: {score:.2f} "
            f"(latency={latency_ms}ms, retries={retries}, provider={provider})"
        )
        return score

    def record_completion(
        self,
        task_id: str,
        goal: str,
        overall_score: float,
        pipeline_scores: Dict[str, float],
        provider_used: str = None,
        duration_ms: int = 0,
        report_md: str = "",
    ) -> None:
        """완료보고서를 DB에 저장합니다."""
        try:
            with self._connect() as con:
                con.execute(
                    "INSERT OR REPLACE INTO completion_reports "
                    "(task_id, goal, overall_score, pipeline_scores, provider_used, duration_ms, report_md) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        task_id,
                        goal,
                        round(overall_score, 4),
                        json.dumps(pipeline_scores, ensure_ascii=False),
                        provider_used,
                        duration_ms,
                        report_md,
                    ),
                )
                con.commit()
            logger.info(f"📋 완료보고서 저장됨: {task_id} (score={overall_score:.2f})")
        except Exception as e:
            logger.warning(f"완료보고서 저장 실패: {e}")

    # ==================== 신뢰도 계산 ====================

    def _calculate_step_score(
        self, success: bool, latency_ms: int = 0, retries: int = 0
    ) -> float:
        """스텝 신뢰도 점수를 계산합니다.

        공식: base * (1 - retry_penalty) * latency_factor
        """
        if not success:
            return max(0.1, 0.3 - retries * 0.05)

        base = 1.0

        # 재시도 감점
        retry_factor = max(0.0, 1.0 - retries * RETRY_PENALTY)

        # 응답 시간 감점
        latency_factor = 1.0
        if latency_ms > LATENCY_THRESHOLD_MS:
            excess_seconds = (latency_ms - LATENCY_THRESHOLD_MS) / 1000.0
            latency_factor = max(0.5, 1.0 - excess_seconds * LATENCY_PENALTY_RATE)

        score = base * retry_factor * latency_factor
        return round(min(1.0, max(0.0, score)), 4)

    # ==================== 종적 분석 ====================

    def get_component_confidence(
        self, component: str, days: int = 7
    ) -> Dict[str, Any]:
        """특정 컴포넌트의 종적 신뢰도 (EMA 기반)."""
        try:
            with self._connect() as con:
                cursor = con.cursor()
                cursor.execute(
                    "SELECT score, created_at FROM confidence_log "
                    "WHERE component = ? AND created_at > datetime('now', ?) "
                    "ORDER BY created_at ASC",
                    (component, f"-{days} days"),
                )
                rows = cursor.fetchall()

            if not rows:
                return {
                    "component": component,
                    "ema": 0.0,
                    "sample_count": 0,
                    "direction": "unknown",
                    "data_points": [],
                }

            # EMA 계산
            scores = [r[0] for r in rows]
            ema = self._calculate_ema(scores)

            # 방향 판단 (전반부 vs 후반부 평균 비교)
            mid = len(scores) // 2
            if mid > 0:
                first_half = sum(scores[:mid]) / mid
                second_half = sum(scores[mid:]) / (len(scores) - mid)
                diff = second_half - first_half
                if diff > 0.03:
                    direction = "improving"
                elif diff < -0.03:
                    direction = "degrading"
                else:
                    direction = "stable"
            else:
                direction = "stable"

            data_points = [
                {"score": r[0], "timestamp": r[1]} for r in rows[-20:]
            ]

            return {
                "component": component,
                "ema": round(ema, 4),
                "average": round(sum(scores) / len(scores), 4),
                "min": round(min(scores), 4),
                "max": round(max(scores), 4),
                "sample_count": len(scores),
                "direction": direction,
                "data_points": data_points,
            }
        except Exception as e:
            logger.warning(f"종적 분석 실패 ({component}): {e}")
            return {"component": component, "ema": 0.0, "sample_count": 0}

    def get_provider_confidence(
        self, provider: str = None, days: int = 7
    ) -> Dict[str, Any]:
        """프로바이더별 종적 신뢰도."""
        try:
            with self._connect() as con:
                cursor = con.cursor()

                if provider:
                    cursor.execute(
                        "SELECT provider, score FROM confidence_log "
                        "WHERE provider = ? AND created_at > datetime('now', ?) "
                        "ORDER BY created_at ASC",
                        (provider, f"-{days} days"),
                    )
                else:
                    cursor.execute(
                        "SELECT provider, score FROM confidence_log "
                        "WHERE provider IS NOT NULL AND created_at > datetime('now', ?) "
                        "ORDER BY created_at ASC",
                        (f"-{days} days",),
                    )

                rows = cursor.fetchall()

            if not rows:
                return {}

            # 프로바이더별 그룹화
            by_provider: Dict[str, List[float]] = {}
            for prov, score in rows:
                if prov:
                    by_provider.setdefault(prov, []).append(score)

            result = {}
            for prov, scores in by_provider.items():
                ema = self._calculate_ema(scores)
                result[prov] = {
                    "ema": round(ema, 4),
                    "average": round(sum(scores) / len(scores), 4),
                    "sample_count": len(scores),
                    "is_healthy": ema >= MIN_PROVIDER_CONFIDENCE,
                }

            return result
        except Exception as e:
            logger.warning(f"프로바이더 신뢰도 조회 실패: {e}")
            return {}

    def get_system_summary(self, days: int = 7) -> Dict[str, Any]:
        """전체 시스템 신뢰도 요약."""
        components = ["planner", "executor", "reviewer", "wiki", "router"]
        component_scores = {}
        warnings = []

        for comp in components:
            info = self.get_component_confidence(comp, days)
            ema = info.get("ema", 0.0)
            component_scores[comp] = ema

            if info.get("direction") == "degrading":
                warnings.append(f"{comp} 신뢰도 하락 중 ({ema:.2f})")
            if 0 < ema < MIN_PROVIDER_CONFIDENCE:
                warnings.append(f"⚠️ {comp} 신뢰도 위험 수준 ({ema:.2f})")

        # 전체 점수
        valid_scores = [s for s in component_scores.values() if s > 0]
        overall = sum(valid_scores) / len(valid_scores) if valid_scores else 0.0

        # 성공률
        try:
            with self._connect() as con:
                cursor = con.cursor()
                cursor.execute(
                    "SELECT COUNT(*), SUM(CASE WHEN score >= 0.5 THEN 1 ELSE 0 END) "
                    "FROM confidence_log WHERE created_at > datetime('now', ?)",
                    (f"-{days} days",),
                )
                total, successes = cursor.fetchone()
                success_rate = (successes / total * 100) if total else 0.0
        except Exception:
            total = 0
            success_rate = 0.0

        # 프로바이더 신뢰도
        provider_scores = self.get_provider_confidence(days=days)

        # 헬스 판정
        if overall >= 0.8:
            health = "excellent"
        elif overall >= 0.6:
            health = "good"
        elif overall >= 0.4:
            health = "degraded"
        elif overall > 0:
            health = "critical"
        else:
            health = "unknown"

        return {
            "overall_health": health,
            "overall_score": round(overall, 4),
            "component_scores": component_scores,
            "provider_scores": {k: v.get("ema", 0) for k, v in provider_scores.items()},
            "total_tasks": total or 0,
            "success_rate": round(success_rate, 2),
            "warnings": warnings,
            "last_updated": datetime.now().isoformat(),
        }

    def detect_anomaly(self, component: str, current_score: float, days: int = 7) -> Optional[str]:
        """신뢰도 급락 이상탐지 (시그마 기반)."""
        try:
            with self._connect() as con:
                cursor = con.cursor()
                cursor.execute(
                    "SELECT score FROM confidence_log "
                    "WHERE component = ? AND created_at > datetime('now', ?) ",
                    (component, f"-{days} days"),
                )
                rows = cursor.fetchall()

            if len(rows) < 5:
                return None

            scores = [r[0] for r in rows]
            mean = sum(scores) / len(scores)
            variance = sum((s - mean) ** 2 for s in scores) / len(scores)
            std = math.sqrt(variance) if variance > 0 else 0.01

            if current_score < mean - ANOMALY_SIGMA * std:
                msg = (
                    f"🚨 {component} 신뢰도 급락 감지: "
                    f"현재={current_score:.2f}, 평균={mean:.2f}, 편차={std:.2f}"
                )
                logger.warning(msg)
                return msg

            return None
        except Exception as e:
            logger.warning(f"이상탐지 실패: {e}")
            return None

    def get_completion_reports(self, limit: int = 10) -> List[Dict[str, Any]]:
        """최근 완료보고서 목록 조회."""
        try:
            with self._connect() as con:
                cursor = con.cursor()
                cursor.execute(
                    "SELECT task_id, goal, overall_score, pipeline_scores, "
                    "provider_used, duration_ms, created_at "
                    "FROM completion_reports ORDER BY id DESC LIMIT ?",
                    (limit,),
                )
                rows = cursor.fetchall()

            return [
                {
                    "task_id": r[0],
                    "goal": r[1],
                    "overall_score": r[2],
                    "pipeline_scores": json.loads(r[3]) if r[3] else {},
                    "provider_used": r[4],
                    "duration_ms": r[5],
                    "created_at": r[6],
                }
                for r in rows
            ]
        except Exception as e:
            logger.warning(f"보고서 목록 조회 실패: {e}")
            return []

    def get_report_by_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """특정 작업의 완료보고서 조회 (마크다운 포함)."""
        try:
            with self._connect() as con:
                cursor = con.cursor()
                cursor.execute(
                    "SELECT task_id, goal, overall_score, pipeline_scores, "
                    "provider_used, duration_ms, report_md, created_at "
                    "FROM completion_reports WHERE task_id = ?",
                    (task_id,),
                )
                r = cursor.fetchone()

            if not r:
                return None

            return {
                "task_id": r[0],
                "goal": r[1],
                "overall_score": r[2],
                "pipeline_scores": json.loads(r[3]) if r[3] else {},
                "provider_used": r[4],
                "duration_ms": r[5],
                "report_md": r[6],
                "created_at": r[7],
            }
        except Exception as e:
            logger.warning(f"보고서 조회 실패: {e}")
            return None

    # ==================== EMA 계산 ====================

    @staticmethod
    def _calculate_ema(scores: List[float]) -> float:
        """지수이동평균(EMA) 계산."""
        if not scores:
            return 0.0

        ema = scores[0]
        for s in scores[1:]:
            ema = EMA_ALPHA * s + (1 - EMA_ALPHA) * ema

        return ema

    def get_dynamic_provider_priority(self, task_type: str = "immediate") -> List[str]:
        """종적 신뢰도 기반 동적 프로바이더 우선순위."""
        provider_data = self.get_provider_confidence(days=14)

        if not provider_data:
            # 데이터 없으면 기본 순서
            return ["local_ollama", "groq", "claude_haiku", "huggingface"]

        # EMA 기준 정렬 (건강한 프로바이더만)
        healthy = [
            (prov, info["ema"])
            for prov, info in provider_data.items()
            if info.get("is_healthy", True)
        ]
        healthy.sort(key=lambda x: x[1], reverse=True)

        priority = [p[0] for p in healthy]

        # 비활성 프로바이더 제외 로그
        disabled = [
            prov
            for prov, info in provider_data.items()
            if not info.get("is_healthy", True)
        ]
        if disabled:
            logger.warning(f"⚠️ 신뢰도 부족으로 비활성: {disabled}")

        return priority if priority else ["local_ollama"]


# 싱글톤
_collector_instance = None


def get_confidence_collector() -> ConfidenceCollector:
    """ConfidenceCollector 싱글톤."""
    global _collector_instance
    if not _collector_instance:
        _collector_instance = ConfidenceCollector()
    return _collector_instance
