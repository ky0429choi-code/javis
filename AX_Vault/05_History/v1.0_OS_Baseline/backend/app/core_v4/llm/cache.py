import logging
import json
import hashlib
from typing import Optional
from redis import asyncio as aioredis
from app.utils.hybrid_settings import get_hybrid_settings

logger = logging.getLogger(__name__)
settings = get_hybrid_settings()

class CacheManager:
    """
    JARVIS Multi-layer Cache Manager (Redis L1 + SQLite L2).
    """
    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None
        self.initialized = False

    async def init(self):
        """Initialize connections."""
        if self.initialized:
            return
            
        try:
            if settings.CACHE_ENABLE:
                self.redis = aioredis.from_url(settings.REDIS_URL)
                logger.info("✅ Redis L1 Cache connected")
        except Exception as e:
            logger.warning(f"⚠️ Redis connection failed: {e}. Falling back to No-L1.")
            self.redis = None
            
        self.initialized = True

    def _get_key(self, query: str, system_prompt: Optional[str]) -> str:
        """Generate a versioned cache key."""
        # Using hash to keep keys short and handle long queries
        raw_key = f"{query}|{system_prompt or ''}|v{settings.LOCAL_OLLAMA_MODEL}"
        return f"jarvis:v4:cache:{hashlib.md5(raw_key.encode()).hexdigest()}"

    async def get(self, query: str, system_prompt: Optional[str] = None) -> Optional[str]:
        """Retrieve from cache."""
        if not settings.CACHE_ENABLE or not self.initialized:
            return None
            
        key = self._get_key(query, system_prompt)
        
        # 1. Try Redis (L1)
        if self.redis:
            try:
                cached = await self.redis.get(key)
                if cached:
                    logger.debug("💾 L1 Cache Hit")
                    return cached.decode() if isinstance(cached, bytes) else cached
            except Exception as e:
                logger.warning(f"L1 Cache get error: {e}")
                
        # 2. SQLite (L2) placeholder - could be implemented via a dedicated DAO
        return None

    async def set(self, query: str, response: str, system_prompt: Optional[str] = None, ttl: int = 3600):
        """Store in cache."""
        if not settings.CACHE_ENABLE or not self.initialized:
            return
            
        key = self._get_key(query, system_prompt)
        
        if self.redis:
            try:
                await self.redis.set(key, response, ex=ttl)
                logger.debug(f"💾 L1 Cache stored (TTL={ttl}s)")
            except Exception as e:
                logger.warning(f"L1 Cache set error: {e}")

cache_manager = CacheManager()
