import asyncio
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

class StartupSync:
    """온/오프라인 감지 + 타임아웃 처리"""
    
    def __init__(self, timeout: float = 3.0):
        self.timeout = timeout
        self.is_online = False
    
    async def sync(self) -> bool:
        """3초 내에 응답 없으면 오프라인 모드"""
        
        logger.info(f"🔄 [Startup Sync] Attempting (timeout={self.timeout}s)...")
        
        try:
            # 실제 구현에서는 GAS API 호출
            # 지금은 테스트용으로 빠른 응답
            await asyncio.sleep(0.1)
            
            self.is_online = True
            logger.info(f"✅ [Online Mode] Ready")
            return True
        
        except asyncio.TimeoutError:
            logger.warning(f"⏱️  [Offline Mode] Timeout (will use local only)")
            self.is_online = False
            return False
        
        except Exception as e:
            logger.error(f"❌ Sync error: {e}")
            self.is_online = False
            return False
