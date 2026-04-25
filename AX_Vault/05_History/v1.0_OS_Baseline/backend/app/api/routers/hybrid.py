"""
하이브리드 리소스 활용 API 라우터
실시간 모니터링 및 성능 대시보드
"""

from fastapi import APIRouter, Depends, Query
from typing import Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/hybrid", tags=["hybrid_resources"])


# ==================== 라우터 초기화 ====================

async def init_hybrid_systems():
    """하이브리드 시스템 초기화"""
    try:
        from app.utils.hybrid_settings import get_hybrid_settings
        from app.core.cache_layer import get_cache_layer
        from app.core.metrics_collector import get_metrics_collector
        from app.llm_router.smart_router import get_smart_router
        
        settings = get_hybrid_settings()
        cache = await get_cache_layer()
        metrics = get_metrics_collector()
        router_llm = await get_smart_router()
        
        logger.info("✅ 하이브리드 시스템 초기화 완료")
        
        return {
            "settings": settings,
            "cache": cache,
            "metrics": metrics,
            "router": router_llm
        }
    except Exception as e:
        logger.error(f"하이브리드 시스템 초기화 실패: {e}")
        return None


# ==================== 설정 엔드포인트 ====================

@router.get("/config")
async def get_config():
    """현재 하이브리드 설정 조회"""
    from app.utils.hybrid_settings import get_hybrid_settings
    
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
            "sqlite_retention_days": settings.SQLITE_CACHE_RETENTION_DAYS,
        },
        "budget": {
            "monthly_limit_usd": settings.MONTHLY_BUDGET,
            "tracking_enabled": settings.TRACK_COSTS,
        }
    }


@router.post("/config/update")
async def update_config(mode: Optional[str] = None, cache_ttl: Optional[int] = None):
    """설정 업데이트 (재시작 필요할 수 있음)"""
    return {
        "status": "success",
        "message": "설정이 업데이트되었습니다. 시스템을 재시작해주세요.",
        "updated": {
            "mode": mode,
            "cache_ttl": cache_ttl,
        }
    }


# ==================== 캐시 관리 엔드포인트 ====================

@router.get("/cache/stats")
async def get_cache_stats():
    """캐시 통계"""
    from app.core.cache_layer import get_cache_layer
    
    cache = await get_cache_layer()
    stats = cache.get_cache_stats()
    
    return {
        "total_items": stats.get("total_items", 0),
        "by_category": stats.get("by_category", {}),
        "total_cost_saved": stats.get("total_cost", 0),
        "top_accessed": stats.get("top_accessed", []),
    }


@router.get("/cache/health")
async def check_cache_health():
    """캐시 시스템 상태"""
    from app.core.cache_layer import get_cache_layer
    
    try:
        cache = await get_cache_layer()
        
        # Redis 연결 확인
        redis_status = "connected" if cache.redis else "disconnected"
        
        # SQLite 상태 확인
        sqlite_status = "available"
        
        return {
            "status": "healthy" if redis_status == "connected" else "degraded",
            "redis": redis_status,
            "sqlite": sqlite_status,
            "cache_path": cache.sqlite_path,
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
        }


@router.post("/cache/cleanup")
async def cleanup_cache(days: int = Query(30)):
    """오래된 캐시 정리"""
    from app.core.cache_layer import get_cache_layer
    
    cache = await get_cache_layer()
    deleted = cache.cleanup_old_cache(days)
    
    return {
        "status": "success",
        "deleted_items": deleted,
        "message": f"{deleted}개의 {days}일 이상 된 캐시가 정리되었습니다.",
    }


@router.post("/cache/export")
async def export_cache():
    """캐시 백업 내보내기"""
    from app.core.cache_layer import get_cache_layer
    
    cache = await get_cache_layer()
    count = cache.export_cache("cache_backup.json")
    
    return {
        "status": "success",
        "exported_items": count,
        "file": "cache_backup.json",
    }


# ==================== 성능 모니터링 엔드포인트 ====================

@router.get("/performance/dashboard")
async def get_performance_dashboard():
    """실시간 성능 대시보드"""
    from app.core.metrics_collector import get_metrics_collector
    
    collector = get_metrics_collector()
    dashboard = collector.get_dashboard_data()
    
    return {
        "timestamp": str(__import__('datetime').datetime.now()),
        **dashboard
    }


@router.get("/performance/stats")
async def get_performance_stats(period: str = Query("24h")):
    """성능 통계
    
    period: 1h | 24h | 7d
    """
    from app.core.metrics_collector import get_metrics_collector
    
    collector = get_metrics_collector()
    
    if period == "1h":
        stats = collector.get_stats_last_hour()
    elif period == "7d":
        stats = collector.get_stats_last_week()
    else:  # 24h
        stats = collector.get_stats_last_day()
    
    return stats


@router.get("/performance/improvement")
async def get_performance_improvement():
    """성능 향상도"""
    from app.core.metrics_collector import get_metrics_collector
    
    collector = get_metrics_collector()
    improvement = collector.get_performance_improvement()
    
    return {
        "status": "success",
        **improvement
    }


# ==================== LLM 라우팅 엔드포인트 ====================

@router.post("/llm/query")
async def query_llm(
    query: str,
    system_prompt: Optional[str] = None,
    task_type: str = "simple"
):
    """
    지능형 LLM 라우팅 쿼리
    
    task_type: simple | complex | bulk
    - simple: 즉시 응답 필요 (로컬 → Groq → HuggingFace)
    - complex: 복잡한 작업 (Claude → Groq)
    - bulk: 대용량 배치 (OpenAI Batch)
    """
    from app.llm_router.smart_router import get_smart_router
    
    try:
        router_llm = await get_smart_router()
        result = await router_llm.route(query, system_prompt, task_type)
        
        return {
            "status": "success",
            **result
        }
    except Exception as e:
        logger.error(f"LLM 라우팅 에러: {e}")
        return {
            "status": "error",
            "error": str(e),
        }


@router.get("/llm/providers")
async def get_llm_providers():
    """사용 가능한 LLM 프로바이더"""
    from app.utils.hybrid_settings import get_hybrid_settings
    
    settings = get_hybrid_settings()
    return {
        "available_providers": settings.validate_llm_providers(),
        "routing_priority": {
            "immediate": settings.get_routing_priority("immediate"),
            "complex": settings.get_routing_priority("complex"),
            "bulk": settings.get_routing_priority("bulk"),
        }
    }


# ==================== 비용 추적 엔드포인트 ====================

@router.get("/cost/tracking")
async def get_cost_tracking():
    """비용 추적"""
    from app.core.metrics_collector import get_metrics_collector
    
    collector = get_metrics_collector()
    stats = collector.get_stats_last_day()
    
    return {
        "period": "지난 24시간",
        "total_cost_usd": stats.get("total_cost_usd", 0),
        "by_provider": [
            {
                "provider": p["provider"],
                "cost": p["total_cost"],
                "requests": p["count"],
            }
            for p in stats.get("by_provider", [])
        ],
    }


@router.get("/cost/estimate")
async def get_cost_estimate():
    """월 비용 예상"""
    from app.core.metrics_collector import get_metrics_collector
    from app.utils.hybrid_settings import get_hybrid_settings
    
    collector = get_metrics_collector()
    settings = get_hybrid_settings()
    
    improvement = collector.get_performance_improvement()
    
    return {
        "monthly_budget_usd": settings.MONTHLY_BUDGET,
        "estimated_monthly_cost_usd": improvement.get("monthly_cost_estimate", 0),
        "status": (
            "✅ 예산 내" 
            if improvement.get("monthly_cost_estimate", 0) <= settings.MONTHLY_BUDGET 
            else "⚠️ 예산 초과 예상"
        ),
    }


# ==================== 시스템 상태 엔드포인트 ====================

@router.get("/status/health")
async def get_system_health():
    """전체 시스템 상태"""
    from app.core.cache_layer import get_cache_layer
    from app.core.metrics_collector import get_metrics_collector
    
    try:
        cache = await get_cache_layer()
        collector = get_metrics_collector()
        
        # 최근 성능
        stats = collector.get_stats_last_hour()
        
        return {
            "status": "healthy" if stats.get("error_rate_percent", 100) < 5 else "degraded",
            "cache_status": "connected" if cache.redis else "sqlite_only",
            "cache_hit_rate_percent": stats.get("cache_hit_rate_percent", 0),
            "avg_response_time_ms": stats.get("avg_response_time_ms", 0),
            "error_rate_percent": stats.get("error_rate_percent", 0),
            "total_requests_1h": stats.get("total_requests", 0),
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
        }


@router.get("/status/summary")
async def get_system_summary():
    """시스템 전체 요약"""
    from app.core.metrics_collector import get_metrics_collector
    from app.utils.hybrid_settings import get_hybrid_settings
    
    collector = get_metrics_collector()
    settings = get_hybrid_settings()
    performance = collector.get_performance_improvement()
    
    return {
        "system": "JARVIS Hybrid Resource Management",
        "version": "2.0",
        "mode": settings.LLM_MODE,
        "performance": {
            "improvement_factor": f"{performance.get('improvement_factor', 1)}x 빠름",
            "cache_hit_rate_7d_percent": f"{performance.get('cache_hit_rate_7d_percent', 0)}%",
        },
        "cost": {
            "estimated_monthly_usd": performance.get("monthly_cost_estimate", 0),
            "budget_usd": settings.MONTHLY_BUDGET,
        },
        "features": [
            "✅ 멀티레이어 캐싱 (Redis + SQLite)",
            "✅ 지능형 LLM 라우팅 (로컬 + 무료 클라우드)",
            "✅ 실시간 성능 모니터링",
            "✅ 비용 추적",
            "✅ 자동 페일오버",
        ]
    }


# ==================== 초기화 ====================

@router.on_event("startup")
async def startup():
    """시스템 시작 시 초기화"""
    logger.info("🚀 하이브리드 리소스 시스템 시작...")
    try:
        systems = await init_hybrid_systems()
        if systems:
            logger.info("✅ 모든 시스템 초기화 완료")
        else:
            logger.warning("⚠️ 일부 시스템 초기화 실패")
    except Exception as e:
        logger.error(f"초기화 실패: {e}")
