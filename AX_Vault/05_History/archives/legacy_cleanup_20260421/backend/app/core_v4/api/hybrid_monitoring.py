from fastapi import APIRouter, Query
from typing import Optional
import logging
import datetime
from app.utils.hybrid_settings import get_hybrid_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v4/hybrid", tags=["v4_hybrid_monitoring"])

@router.get("/config")
async def get_config():
    """V4 Hybrid Configuration View."""
    settings = get_hybrid_settings()
    return {
        "mode": settings.LLM_MODE,
        "llm_providers": settings.validate_llm_providers(),
        "storage_providers": settings.validate_storage_providers(),
        "routing_priority": {
            "immediate": settings.get_routing_priority("immediate"),
            "complex": settings.get_routing_priority("complex"),
            "bulk": settings.get_routing_priority("bulk"),
        },
        "cache": {
            "enabled": settings.CACHE_ENABLE,
            "redis_ttl_seconds": settings.REDIS_TTL,
        },
        "budget": {
            "monthly_limit_usd": settings.MONTHLY_BUDGET,
            "tracking_enabled": settings.TRACK_COSTS,
        }
    }

@router.get("/performance/dashboard")
async def get_performance_dashboard():
    """V4 Performance Dashboard."""
    try:
        from app.core.metrics_collector import get_metrics_collector
        collector = get_metrics_collector()
        dashboard = collector.get_dashboard_data()
        
        return {
            "timestamp": str(datetime.datetime.now()),
            "status": "active",
            **dashboard
        }
    except Exception as e:
        logger.error(f"Failed to load metrics: {e}")
        return {"status": "degraded", "error": str(e)}

@router.get("/cache/health")
async def check_cache_health():
    """V4 Cache Health Check."""
    from app.core_v4.llm.cache import cache_manager
    await cache_manager.init()
    
    return {
        "l1_redis": "connected" if cache_manager.redis else "disconnected",
        "initialized": cache_manager.initialized
    }
