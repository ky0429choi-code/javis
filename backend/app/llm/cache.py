"""
JARVIS 캐시 관리자 — Redis 선택적 (Ollama 독립).
Redis가 없으면 SQLite 기반 L2 캐시만 사용합니다.
"""

import logging
import json
import hashlib
import sqlite3
from typing import Optional
from pathlib import Path
from app.utils.hybrid_settings import get_hybrid_settings

logger = logging.getLogger(__name__)
settings = get_hybrid_settings()

# Redis를 선택적으로 임포트 (없어도 동작)
try:
    from redis import asyncio as aioredis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False
    logger.info("📦 Redis 패키지 미설치 — SQLite L2 캐시만 사용합니다.")


class CacheManager:
    """
    JARVIS Multi-layer Cache Manager.
    - L1: Redis (선택적 — 패키지 미설치 시 자동 스킵)
    - L2: SQLite (기본 — 항상 사용 가능)
    """

    def __init__(self):
        self.redis = None
        self.initialized = False
        self._db_path = Path(__file__).resolve().parents[2] / "data" / "cache.db"

    async def init(self):
        """초기화 — Redis 없이도 동작."""
        if self.initialized:
            return

        # L1: Redis (선택적)
        if HAS_REDIS and settings.CACHE_ENABLE:
            try:
                self.redis = aioredis.from_url(settings.REDIS_URL)
                await self.redis.ping()
                logger.info("✅ Redis L1 캐시 연결됨")
            except Exception as e:
                logger.info(f"📦 Redis 미사용 (L2 SQLite로 동작): {e}")
                self.redis = None

        # L2: SQLite (항상 사용 가능)
        self._init_sqlite()

        self.initialized = True

    def _init_sqlite(self):
        """SQLite L2 캐시 테이블 초기화."""
        try:
            self._db_path.parent.mkdir(parents=True, exist_ok=True)
            with sqlite3.connect(self._db_path) as con:
                con.execute(
                    "CREATE TABLE IF NOT EXISTS llm_cache ("
                    "key TEXT PRIMARY KEY, "
                    "value TEXT NOT NULL, "
                    "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
                )
                con.commit()
        except Exception as e:
            logger.warning(f"L2 캐시 초기화 실패: {e}")

    def _get_key(self, query: str, system_prompt: Optional[str]) -> str:
        """버전 키 생성."""
        raw_key = f"{query}|{system_prompt or ''}|v{settings.LOCAL_OLLAMA_MODEL}"
        return f"jarvis:v4:cache:{hashlib.md5(raw_key.encode()).hexdigest()}"

    async def get(self, query: str, system_prompt: Optional[str] = None) -> Optional[str]:
        """캐시 조회 (L1 Redis → L2 SQLite)."""
        if not settings.CACHE_ENABLE or not self.initialized:
            return None

        key = self._get_key(query, system_prompt)

        # L1: Redis
        if self.redis:
            try:
                cached = await self.redis.get(key)
                if cached:
                    logger.debug("💾 L1 Cache Hit (Redis)")
                    return cached.decode() if isinstance(cached, bytes) else cached
            except Exception as e:
                logger.debug(f"L1 miss: {e}")

        # L2: SQLite
        try:
            with sqlite3.connect(self._db_path) as con:
                cursor = con.execute(
                    "SELECT value FROM llm_cache WHERE key = ?", (key,)
                )
                row = cursor.fetchone()
                if row:
                    logger.debug("💾 L2 Cache Hit (SQLite)")
                    return row[0]
        except Exception:
            pass

        return None

    async def set(
        self, query: str, response: str, system_prompt: Optional[str] = None, ttl: int = 3600
    ):
        """캐시 저장 (L1 + L2)."""
        if not settings.CACHE_ENABLE or not self.initialized:
            return

        key = self._get_key(query, system_prompt)

        # L1: Redis
        if self.redis:
            try:
                await self.redis.set(key, response, ex=ttl)
                logger.debug(f"💾 L1 Cache stored (TTL={ttl}s)")
            except Exception as e:
                logger.debug(f"L1 store fail: {e}")

        # L2: SQLite
        try:
            with sqlite3.connect(self._db_path) as con:
                con.execute(
                    "INSERT OR REPLACE INTO llm_cache (key, value) VALUES (?, ?)",
                    (key, response),
                )
                con.commit()
        except Exception:
            pass


cache_manager = CacheManager()
