"""
성능 모니터링 및 통계 시스템
실시간 대시보드용 메트릭 수집
"""

import time
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, List
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class RequestMetric:
    """요청 메트릭"""
    timestamp: datetime
    request_id: str
    query: str
    response_time_ms: int
    provider: str
    cached: bool
    cost: float
    error: bool = False
    error_message: str = None


class MetricsCollector:
    """성능 메트릭 수집"""
    
    def __init__(self, db_path: str = "metrics.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """메트릭 데이터베이스 초기화"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                request_id TEXT UNIQUE,
                query TEXT,
                response_time_ms INTEGER,
                provider TEXT,
                cached BOOLEAN,
                cost REAL,
                error BOOLEAN,
                error_message TEXT
            )
        """)
        
        # 인덱스 생성
        conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON metrics(timestamp)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_provider ON metrics(provider)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_cached ON metrics(cached)")
        
        conn.commit()
        conn.close()
        logger.info("✅ 메트릭 데이터베이스 준비됨")
    
    def record(self, metric: RequestMetric):
        """메트릭 기록"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("""
                INSERT INTO metrics 
                (timestamp, request_id, query, response_time_ms, provider, cached, cost, error, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metric.timestamp,
                metric.request_id,
                metric.query[:100],  # 쿼리 길이 제한
                metric.response_time_ms,
                metric.provider,
                metric.cached,
                metric.cost,
                metric.error,
                metric.error_message
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning(f"메트릭 기록 실패: {e}")
    
    # ==================== 통계 ====================
    
    def get_stats_last_hour(self) -> Dict[str, Any]:
        """최근 1시간 통계"""
        return self._get_stats_by_time(hours=1)
    
    def get_stats_last_day(self) -> Dict[str, Any]:
        """최근 24시간 통계"""
        return self._get_stats_by_time(hours=24)
    
    def get_stats_last_week(self) -> Dict[str, Any]:
        """최근 7일 통계"""
        return self._get_stats_by_time(days=7)
    
    def _get_stats_by_time(self, hours: int = None, days: int = None) -> Dict[str, Any]:
        """시간별 통계"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 시간 범위 계산
            if hours:
                time_filter = f"datetime('now', '-{hours} hours')"
                period = f"최근 {hours}시간"
            elif days:
                time_filter = f"datetime('now', '-{days} days')"
                period = f"최근 {days}일"
            else:
                time_filter = "datetime('now', '-1 hour')"
                period = "최근 1시간"
            
            # 전체 통계
            cursor.execute(f"""
                SELECT 
                    COUNT(*) as total_requests,
                    AVG(response_time_ms) as avg_response_time,
                    MIN(response_time_ms) as min_response_time,
                    MAX(response_time_ms) as max_response_time,
                    SUM(CASE WHEN cached THEN 1 ELSE 0 END) as cached_hits,
                    SUM(CASE WHEN error THEN 1 ELSE 0 END) as errors,
                    SUM(cost) as total_cost
                FROM metrics
                WHERE timestamp > {time_filter}
            """)
            
            stats = cursor.fetchone()
            
            total_requests = stats[0] or 0
            avg_response_time = stats[1] or 0
            cached_hits = stats[4] or 0
            errors = stats[5] or 0
            total_cost = stats[6] or 0
            
            # 캐시 히트율
            cache_hit_rate = (cached_hits / total_requests * 100) if total_requests > 0 else 0
            
            # 에러율
            error_rate = (errors / total_requests * 100) if total_requests > 0 else 0
            
            # 프로바이더별 분석
            cursor.execute(f"""
                SELECT 
                    provider,
                    COUNT(*) as count,
                    AVG(response_time_ms) as avg_time,
                    SUM(cost) as total_cost,
                    SUM(CASE WHEN cached THEN 1 ELSE 0 END) as cached_count
                FROM metrics
                WHERE timestamp > {time_filter}
                GROUP BY provider
                ORDER BY count DESC
            """)
            
            by_provider = []
            for row in cursor.fetchall():
                by_provider.append({
                    "provider": row[0],
                    "count": row[1],
                    "avg_response_time_ms": int(row[2] or 0),
                    "total_cost": float(row[3] or 0),
                    "cached_count": row[4] or 0,
                })
            
            conn.close()
            
            return {
                "period": period,
                "total_requests": total_requests,
                "avg_response_time_ms": int(avg_response_time),
                "min_response_time_ms": int(stats[2] or 0),
                "max_response_time_ms": int(stats[3] or 0),
                "cache_hit_rate_percent": round(cache_hit_rate, 2),
                "total_cached_hits": cached_hits,
                "error_rate_percent": round(error_rate, 2),
                "total_errors": errors,
                "total_cost_usd": round(total_cost, 4),
                "by_provider": by_provider,
            }
        except Exception as e:
            logger.warning(f"통계 조회 실패: {e}")
            return {}
    
    # ==================== 성능 향상도 ====================
    
    def get_performance_improvement(self) -> Dict[str, Any]:
        """성능 향상도 계산"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 캐시 적중 시 성능
            cursor.execute("""
                SELECT AVG(response_time_ms) FROM metrics
                WHERE cached = 1
            """)
            cache_hit_time = cursor.fetchone()[0] or 0
            
            # 캐시 미적중 시 성능
            cursor.execute("""
                SELECT AVG(response_time_ms) FROM metrics
                WHERE cached = 0
            """)
            cache_miss_time = cursor.fetchone()[0] or 0
            
            # 프로바이더별 평균 시간
            cursor.execute("""
                SELECT provider, AVG(response_time_ms)
                FROM metrics
                GROUP BY provider
                ORDER BY AVG(response_time_ms) ASC
            """)
            provider_times = dict(cursor.fetchall())
            
            # 캐시 히트율
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN cached THEN 1 ELSE 0 END) as cached
                FROM metrics
                WHERE timestamp > datetime('now', '-7 days')
            """)
            total, cached = cursor.fetchone()
            cache_hit_rate = (cached / total * 100) if total > 0 else 0
            
            # 총 비용 절감
            cursor.execute("""
                SELECT SUM(cost) FROM metrics
                WHERE timestamp > datetime('now', '-30 days')
            """)
            total_cost_30d = cursor.fetchone()[0] or 0
            
            conn.close()
            
            # 계산
            improvement_factor = (cache_miss_time / cache_hit_time) if cache_hit_time > 0 else 1
            
            return {
                "cache_hit_time_ms": int(cache_hit_time),
                "cache_miss_time_ms": int(cache_miss_time),
                "improvement_factor": round(improvement_factor, 1),  # 몇 배 빠른지
                "cache_hit_rate_7d_percent": round(cache_hit_rate, 2),
                "total_cost_30d": round(total_cost_30d, 2),
                "monthly_cost_estimate": round(total_cost_30d, 2),
                "provider_times": provider_times,
            }
        except Exception as e:
            logger.warning(f"성능 분석 실패: {e}")
            return {}
    
    # ==================== 대시보드용 데이터 ====================
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """실시간 대시보드 데이터"""
        return {
            "last_1h": self.get_stats_last_hour(),
            "last_24h": self.get_stats_last_day(),
            "last_7d": self.get_stats_last_week(),
            "performance": self.get_performance_improvement(),
        }
    
    # ==================== 정리 ====================
    
    def cleanup_old_metrics(self, retention_days: int = 90):
        """오래된 메트릭 정리"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                DELETE FROM metrics
                WHERE timestamp < datetime('now', '-' || ? || ' days')
            """, (retention_days,))
            
            deleted = cursor.rowcount
            conn.commit()
            conn.close()
            
            logger.info(f"🗑️ {deleted}개 오래된 메트릭 정리됨")
            return deleted
        except Exception as e:
            logger.warning(f"메트릭 정리 실패: {e}")
            return 0


# 싱글톤
_collector_instance = None


def get_metrics_collector() -> MetricsCollector:
    """MetricsCollector 싱글톤"""
    global _collector_instance
    if not _collector_instance:
        _collector_instance = MetricsCollector()
    return _collector_instance
