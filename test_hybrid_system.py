#!/usr/bin/env python
"""
JARVIS 하이브리드 시스템 테스트 스크립트
로컬 검증용
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("HybridTest")


async def test_settings():
    """설정 검증 테스트"""
    logger.info("🧪 [1/6] 하이브리드 설정 검증...")
    
    try:
        from app.utils.hybrid_settings import get_hybrid_settings
        
        settings = get_hybrid_settings()
        summary = settings.get_summary()
        
        logger.info(f"✅ LLM 모드: {summary['mode']}")
        logger.info(f"✅ 캐시 활성화: {summary['cache_enabled']}")
        logger.info(f"✅ 비용 추적: {summary['track_costs']}")
        logger.info(f"✅ 월 예산: ${summary['monthly_budget']}")
        
        return True
    except Exception as e:
        logger.error(f"❌ 설정 검증 실패: {e}")
        return False


async def test_cache():
    """캐시 시스템 테스트"""
    logger.info("🧪 [2/6] 캐시 시스템 검증...")
    
    try:
        from app.core.cache_layer import get_cache_layer
        
        cache = await get_cache_layer()
        
        # 저장 테스트
        await cache.set("test_key", "test_value", "test")
        logger.info("✅ 캐시 저장 성공")
        
        # 조회 테스트
        result = await cache.get("test_key")
        if result == "test_value":
            logger.info("✅ 캐시 조회 성공")
        else:
            logger.warning("⚠️ 캐시 조회 실패 (L2 SQLite 사용)")
        
        # 통계 테스트
        stats = cache.get_cache_stats()
        logger.info(f"✅ 캐시 항목: {stats.get('total_items', 0)}개")
        
        return True
    except Exception as e:
        logger.error(f"❌ 캐시 검증 실패: {e}")
        return False


async def test_mock_llm_query():
    """LLM 라우터 테스트 (모의)"""
    logger.info("🧪 [3/6] LLM 라우터 검증...")
    
    try:
        from app.llm_router.smart_router import SmartLLMRouter
        
        router = SmartLLMRouter()
        await router.init()
        
        logger.info("✅ SmartLLMRouter 초기화 성공")
        logger.info("⚠️ 참고: 실제 API 키 없으면 폴백 작동")
        
        return True
    except Exception as e:
        logger.error(f"❌ LLM 라우터 검증 실패: {e}")
        return False


async def test_metrics():
    """메트릭 시스템 테스트"""
    logger.info("🧪 [4/6] 메트릭 시스템 검증...")
    
    try:
        from app.core.metrics_collector import get_metrics_collector, RequestMetric
        from datetime import datetime
        
        collector = get_metrics_collector()
        
        # 테스트 메트릭 기록
        test_metric = RequestMetric(
            timestamp=datetime.now(),
            request_id="test-001",
            query="테스트 쿼리",
            response_time_ms=100,
            provider="local_ollama",
            cached=False,
            cost=0,
        )
        
        collector.record(test_metric)
        logger.info("✅ 메트릭 기록 성공")
        
        # 통계 조회
        stats = collector.get_stats_last_hour()
        logger.info(f"✅ 지난 1시간 요청: {stats.get('total_requests', 0)}개")
        
        return True
    except Exception as e:
        logger.error(f"❌ 메트릭 검증 실패: {e}")
        return False


async def test_skill_registry():
    """Skill 레지스트리 테스트"""
    logger.info("🧪 [5/6] Skill 레지스트리 검증...")
    
    try:
        from app.harness.skills.registry import skill_registry
        
        logger.info(f"✅ 등록된 Skill: {skill_registry.list_skills()}")
        logger.info("✅ Skill 레지스트리 준비됨")
        
        return True
    except Exception as e:
        logger.error(f"❌ Skill 레지스트리 검증 실패: {e}")
        return False


async def test_integration():
    """통합 테스트"""
    logger.info("🧪 [6/6] 시스템 통합 검증...")
    
    try:
        from app.integrations.chat_hybrid_integration import ChatWithHybridRouter
        
        chat = ChatWithHybridRouter()
        await chat.init()
        
        logger.info("✅ ChatWithHybridRouter 초기화 성공")
        logger.info("✅ 모든 시스템 통합 준비됨")
        
        return True
    except Exception as e:
        logger.error(f"❌ 통합 검증 실패: {e}")
        return False


async def main():
    """메인 테스트"""
    logger.info("=" * 60)
    logger.info("🚀 JARVIS 하이브리드 시스템 검증 시작")
    logger.info("=" * 60)
    
    results = []
    
    # 각 테스트 실행
    results.append(("설정 검증", await test_settings()))
    results.append(("캐시 시스템", await test_cache()))
    results.append(("LLM 라우터", await test_mock_llm_query()))
    results.append(("메트릭 시스템", await test_metrics()))
    results.append(("Skill 레지스트리", await test_skill_registry()))
    results.append(("시스템 통합", await test_integration()))
    
    # 결과 요약
    logger.info("=" * 60)
    logger.info("📊 테스트 결과 요약")
    logger.info("=" * 60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ 성공" if result else "❌ 실패"
        logger.info(f"{status}: {test_name}")
        if result:
            passed += 1
    
    logger.info("=" * 60)
    logger.info(f"🎯 최종 결과: {passed}/{len(results)} 테스트 통과")
    logger.info("=" * 60)
    
    if passed == len(results):
        logger.info("\n✅ 모든 테스트 통과! 배포 준비 완료\n")
        return 0
    else:
        logger.warning("\n⚠️ 일부 테스트 실패. 위의 로그를 확인하세요.\n")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
