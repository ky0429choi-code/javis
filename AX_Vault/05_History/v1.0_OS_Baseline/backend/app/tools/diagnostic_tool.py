import logging
import time
from typing import Dict, Any
from app.core.cache_layer import get_cache_layer
from app.core.metrics_collector import get_metrics_collector
from app.utils.hybrid_settings import get_hybrid_settings

logger = logging.getLogger(__name__)

class DiagnosticTool:
    """
    JARVIS System Diagnostic Tool.
    Collects real-time evidence of system health and performance.
    """
    def __init__(self):
        self.settings = get_hybrid_settings()

    async def run_diagnostic(self) -> Dict[str, Any]:
        """
        Runs a full system diagnostic and returns grounded evidence.
        """
        logger.info("DiagnosticTool: Starting system-wide health check...")
        
        # 1. Cache Layer Check
        cache_status = "unknown"
        redis_info = "disconnected"
        sqlite_count = 0
        try:
            cache = await get_cache_layer()
            if cache.redis:
                # Basic ping/test
                await cache.redis.ping()
                redis_info = "connected"
            
            stats = cache.get_cache_stats()
            sqlite_count = stats.get("total_items", 0)
            cache_status = "healthy" if redis_info == "connected" else "degraded (sqlite only)"
        except Exception as e:
            logger.error(f"DiagnosticTool: Cache check failed: {e}")
            cache_status = f"error: {str(e)}"

        # 2. Metrics Check
        latency_info = {}
        try:
            collector = get_metrics_collector()
            perf = collector.get_performance_improvement()
            latency_info = {
                "avg_cache_hit_ms": perf.get("cache_hit_time_ms", 0),
                "avg_cache_miss_ms": perf.get("cache_miss_time_ms", 0),
                "improvement_factor": perf.get("improvement_factor", 1.0)
            }
        except Exception as e:
            logger.error(f"DiagnosticTool: Metrics check failed: {e}")

        # 3. Environment & LLM Mode
        llm_mode = self.settings.LLM_MODE
        
        return {
            "status": "online",
            "cache": {
                "overall": cache_status,
                "redis": redis_info,
                "sqlite_items": sqlite_count
            },
            "performance": latency_info,
            "llm_mode": llm_mode,
            "timestamp": time.time()
        }

diagnostic_tool = DiagnosticTool()
