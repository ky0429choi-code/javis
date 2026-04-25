"""
멀티레이어 캐시 시스템 - Redis + SQLite
로컬 성능 극대화: 반복되는 응답은 0.01초 내 반환
"""

import json
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from redis import asyncio as aioredis

logger = logging.getLogger(__name__)


class CacheLayer:
    """
    2단계 캐시 시스템:
    - L1: Redis (메모리, 1시간, 1ms)
    - L2: SQLite (디스크, 30일, 10ms)
    """
    
    def __init__(self, sqlite_path: str = "cache.db"):
        self.sqlite_path = sqlite_path
        self.redis: Optional[aioredis.Redis] = None
        self._init_sqlite()
    
    def _init_sqlite(self):
        """SQLite 테이블 초기화"""
        conn = sqlite3.connect(self.sqlite_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                id INTEGER PRIMARY KEY,
                key TEXT UNIQUE NOT NULL,
                value TEXT NOT NULL,
                category TEXT,  -- 'query' | 'code' | 'analysis' | 'bulk'
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                access_count INTEGER DEFAULT 1,
                cost REAL DEFAULT 0
            )
        """)
        
        # 만료된 항목 자동 정리용 인덱스
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_created_at ON cache(created_at)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_key ON cache(key)
        """)
        
        conn.commit()
        conn.close()
        logger.info("✅ SQLite 캐시 테이블 준비됨")
    
    async def init_redis(self):
        """Redis 연결"""
        try:
            self.redis = aioredis.from_url('redis://localhost')
            logger.info("✅ Redis 연결됨")
        except Exception as e:
            logger.warning(f"⚠️ Redis 미연결: {e}")
            self.redis = None
    
    # ==================== L1: Redis 캐시 ====================
    
    async def get_from_redis(self, key: str) -> Optional[str]:
        """Redis에서 조회 (1ms)"""
        if not self.redis:
            return None
        
        try:
            value = await self.redis.get(f"cache:{key}")
            if value:
                logger.debug(f"💾 L1(Redis) 히트: {key[:30]}...")
                return value.decode() if isinstance(value, bytes) else value
        except Exception as e:
            logger.warning(f"Redis 조회 실패: {e}")
        
        return None
    
    async def set_to_redis(self, key: str, value: str, ttl: int = 3600):
        """Redis에 저장 (1시간 TTL)"""
        if not self.redis:
            return
        
        try:
            await self.redis.set(f"cache:{key}", value, ex=ttl)
            logger.debug(f"🔄 L1(Redis) 저장: {key[:30]}... (TTL: {ttl}s)")
        except Exception as e:
            logger.warning(f"Redis 저장 실패: {e}")
    
    # ==================== L2: SQLite 캐시 ====================
    
    def get_from_sqlite(self, key: str) -> Optional[str]:
        """SQLite에서 조회 (10ms)"""
        try:
            conn = sqlite3.connect(self.sqlite_path)
            cursor = conn.cursor()
            
            # 30일 이내 항목만
            cursor.execute("""
                SELECT value, access_count FROM cache 
                WHERE key = ? AND created_at > datetime('now', '-30 days')
            """, (key,))
            
            result = cursor.fetchone()
            if result:
                value, access_count = result
                
                # 접근 횟수 업데이트
                cursor.execute("""
                    UPDATE cache SET accessed_at = CURRENT_TIMESTAMP, access_count = ?
                    WHERE key = ?
                """, (access_count + 1, key))
                conn.commit()
                
                logger.debug(f"💾 L2(SQLite) 히트: {key[:30]}... (접근: {access_count + 1}회)")
                return value
            
            conn.close()
        except Exception as e:
            logger.warning(f"SQLite 조회 실패: {e}")
        
        return None
    
    def set_to_sqlite(self, key: str, value: str, category: str = "query", cost: float = 0):
        """SQLite에 저장"""
        try:
            conn = sqlite3.connect(self.sqlite_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO cache (key, value, category, cost)
                VALUES (?, ?, ?, ?)
            """, (key, value, category, cost))
            
            conn.commit()
            conn.close()
            logger.debug(f"🔄 L2(SQLite) 저장: {key[:30]}... (카테고리: {category})")
        except Exception as e:
            logger.warning(f"SQLite 저장 실패: {e}")
    
    # ==================== 통합 인터페이스 ====================
    
    async def get(self, key: str) -> Optional[str]:
        """
        L1(Redis) → L2(SQLite) 순서로 조회
        """
        # L1: Redis
        result = await self.get_from_redis(key)
        if result:
            return result
        
        # L2: SQLite
        result = self.get_from_sqlite(key)
        if result:
            # SQLite에서 찾은 항목을 Redis에 프로모션 (1시간)
            await self.set_to_redis(key, result, ttl=3600)
            return result
        
        return None
    
    async def set(self, key: str, value: str, category: str = "query", cost: float = 0, redis_ttl: int = 3600):
        """
        L1(Redis) + L2(SQLite) 모두에 저장
        """
        # L1: Redis (1시간)
        await self.set_to_redis(key, value, ttl=redis_ttl)
        
        # L2: SQLite (30일)
        self.set_to_sqlite(key, value, category, cost)
    
    # ==================== 캐시 관리 ====================
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """캐시 통계"""
        try:
            conn = sqlite3.connect(self.sqlite_path)
            cursor = conn.cursor()
            
            # 전체 항목 수
            cursor.execute("SELECT COUNT(*) FROM cache")
            total_items = cursor.fetchone()[0]
            
            # 카테고리별 분류
            cursor.execute("""
                SELECT category, COUNT(*) as count, SUM(cost) as total_cost
                FROM cache GROUP BY category
            """)
            by_category = dict(cursor.fetchall())
            
            # 전체 비용
            cursor.execute("SELECT SUM(cost) FROM cache")
            total_cost = cursor.fetchone()[0] or 0
            
            # 가장 많이 접근한 항목
            cursor.execute("""
                SELECT key, access_count, cost FROM cache 
                ORDER BY access_count DESC LIMIT 5
            """)
            top_accessed = [
                {"key": row[0], "count": row[1], "cost": row[2]}
                for row in cursor.fetchall()
            ]
            
            conn.close()
            
            return {
                "total_items": total_items,
                "by_category": by_category,
                "total_cost": float(total_cost),
                "top_accessed": top_accessed,
            }
        except Exception as e:
            logger.warning(f"통계 조회 실패: {e}")
            return {}
    
    def cleanup_old_cache(self, days: int = 30):
        """오래된 캐시 정리 (30일 이상)"""
        try:
            conn = sqlite3.connect(self.sqlite_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                DELETE FROM cache 
                WHERE created_at < datetime('now', '-' || ? || ' days')
            """, (days,))
            
            deleted = cursor.rowcount
            conn.commit()
            conn.close()
            
            logger.info(f"🗑️ {deleted}개 오래된 캐시 정리됨")
            return deleted
        except Exception as e:
            logger.warning(f"캐시 정리 실패: {e}")
            return 0
    
    def export_cache(self, output_file: str = "cache_export.json"):
        """캐시 내보내기 (백업)"""
        try:
            conn = sqlite3.connect(self.sqlite_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM cache ORDER BY accessed_at DESC")
            rows = [dict(row) for row in cursor.fetchall()]
            
            # datetime 직렬화
            for row in rows:
                row['created_at'] = str(row['created_at'])
                row['accessed_at'] = str(row['accessed_at'])
            
            with open(output_file, 'w') as f:
                json.dump(rows, f, indent=2, ensure_ascii=False)
            
            conn.close()
            logger.info(f"✅ {len(rows)}개 캐시 항목 내보냄: {output_file}")
            return len(rows)
        except Exception as e:
            logger.warning(f"캐시 내보내기 실패: {e}")
            return 0


# 싱글톤
_cache_instance = None


async def get_cache_layer() -> CacheLayer:
    """CacheLayer 싱글톤 인스턴스"""
    global _cache_instance
    if not _cache_instance:
        _cache_instance = CacheLayer()
        await _cache_instance.init_redis()
    return _cache_instance
