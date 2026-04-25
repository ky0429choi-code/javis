"""
하이브리드 시스템 통합 예제
기존 Chat 엔드포인트에 SmartRouter 통합
"""

import asyncio
import uuid
from datetime import datetime
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class ChatWithHybridRouter:
    """
    기존 Chat 시스템에 SmartRouter 통합
    
    사용 예:
    ```python
    chat = ChatWithHybridRouter()
    result = await chat.chat("Python 코드 작성해줘")
    ```
    """
    
    def __init__(self):
        self.router = None
        self.cache = None
        self.metrics = None
        self._initialized = False
    
    async def init(self):
        """초기화"""
        if self._initialized:
            return
        
        try:
            from app.llm_router.smart_router import get_smart_router
            from app.core.cache_layer import get_cache_layer
            from app.core.metrics_collector import get_metrics_collector, RequestMetric
            
            self.router = await get_smart_router()
            self.cache = await get_cache_layer()
            self.metrics = get_metrics_collector()
            self.RequestMetric = RequestMetric
            
            self._initialized = True
            logger.info("✅ ChatWithHybridRouter 초기화 완료")
        except Exception as e:
            logger.error(f"초기화 실패: {e}")
    
    async def chat(self, 
                   message: str, 
                   system_prompt: Optional[str] = None,
                   user_id: Optional[str] = None) -> dict:
        """
        메시지 처리 (SmartRouter 사용)
        
        Args:
            message: 사용자 메시지
            system_prompt: 시스템 프롬프트
            user_id: 사용자 ID (추적용)
        
        Returns:
            {
                "response": "...",
                "provider": "local_ollama|groq|claude|...",
                "time_ms": 123,
                "cached": False,
                "cost": 0.001,
            }
        """
        await self.init()
        
        request_id = str(uuid.uuid4())
        user_id = user_id or "anonymous"
        
        logger.info(f"📨 [{user_id}] {message[:50]}... (ID: {request_id})")
        
        try:
            # SmartRouter로 처리
            result = await self.router.route(
                message,
                system_prompt=system_prompt,
                task_type=self._classify_task(message)
            )
            
            # 메트릭 기록
            if self.metrics:
                self.metrics.record(self.RequestMetric(
                    timestamp=datetime.now(),
                    request_id=request_id,
                    query=message,
                    response_time_ms=result.get("time_ms", 0),
                    provider=result.get("provider", "unknown"),
                    cached=result.get("cached", False),
                    cost=result.get("cost", 0),
                    error=not result.get("ok", False),
                    error_message=result.get("error") if not result.get("ok") else None,
                ))
            
            logger.info(f"✅ 응답 ({result['provider']}, {result['time_ms']}ms)")
            
            return {
                **result,
                "user_id": user_id,
                "request_id": request_id,
            }
        
        except Exception as e:
            logger.error(f"❌ 채팅 처리 실패: {e}")
            
            # 오류 메트릭 기록
            if self.metrics:
                self.metrics.record(self.RequestMetric(
                    timestamp=datetime.now(),
                    request_id=request_id,
                    query=message,
                    response_time_ms=0,
                    provider="error",
                    cached=False,
                    cost=0,
                    error=True,
                    error_message=str(e),
                ))
            
            return {
                "ok": False,
                "error": str(e),
                "provider": None,
                "time_ms": 0,
                "cost": 0,
                "user_id": user_id,
                "request_id": request_id,
            }
    
    def _classify_task(self, message: str) -> str:
        """
        메시지에서 작업 유형 판단
        
        simple: 짧고 단순한 질문
        complex: 코드 생성, 분석, 긴 응답 필요
        bulk: 대량 데이터 처리
        """
        keywords_complex = [
            "코드", "code", "작성", "write", "생성", "generate",
            "분석", "analysis", "보고서", "report", "차트", "chart",
            "리뷰", "review", "설계", "design", "계획", "plan",
        ]
        
        keywords_bulk = [
            "1000", "백개", "여러개", "대량", "배치", "batch",
            "일괄", "전체", "모든", "수천", "수만",
        ]
        
        message_lower = message.lower()
        
        # 대량 작업 우선 확인
        if any(kw in message_lower for kw in keywords_bulk):
            return "bulk"
        
        # 복잡한 작업 확인
        if any(kw in message_lower for kw in keywords_complex):
            return "complex"
        
        # 기본값: 즉시 응답
        return "simple"
    
    async def get_user_stats(self, user_id: str) -> dict:
        """사용자 통계"""
        if not self.metrics:
            return {}
        
        # 메트릭 데이터베이스에서 사용자별 통계 조회
        # (implement as needed)
        return {
            "user_id": user_id,
            "message": "통계 조회 구현 필요",
        }


# 싱글톤 인스턴스
_chat_instance = None


async def get_chat_with_hybrid() -> ChatWithHybridRouter:
    """ChatWithHybridRouter 싱글톤"""
    global _chat_instance
    if not _chat_instance:
        _chat_instance = ChatWithHybridRouter()
        await _chat_instance.init()
    return _chat_instance


# ==================== FastAPI 라우터 통합 예제 ====================

async def chat_endpoint_example(message: str) -> dict:
    """
    기존 /api/chat 엔드포인트 개선판
    
    사용:
    ```
    POST /api/chat/hybrid
    body: {"message": "안녕하세요"}
    ```
    """
    chat = await get_chat_with_hybrid()
    return await chat.chat(message)
