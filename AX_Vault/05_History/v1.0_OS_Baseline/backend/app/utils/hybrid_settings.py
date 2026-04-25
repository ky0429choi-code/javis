"""
통합 설정 관리 - 하이브리드 리소스 활용
"""

import os
from typing import Optional, List
from pydantic_settings import BaseSettings, SettingsConfigDict
import logging

logger = logging.getLogger(__name__)


class HybridSettings(BaseSettings):
    """JARVIS 하이브리드 모드 설정"""
    model_config = SettingsConfigDict(
        env_file=".env.hybrid",
        case_sensitive=True,
        extra='ignore'
    )
    
    # ==================== LLM 라우팅 ====================
    LLM_MODE: str = "hybrid"  # local | cloud | hybrid
    
    # 로컬 Ollama
    LOCAL_OLLAMA_URL: str = "http://localhost:11434"
    LOCAL_OLLAMA_MODEL: str = "jarvis"
    OLLAMA_KEEP_ALIVE: str = "5m"
    
    # 무료 LLM APIs
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "mixtral-8x7b-32768"
    
    HUGGINGFACE_API_KEY: Optional[str] = None
    HUGGINGFACE_MODEL: str = "mistralai/Mistral-7B-Instruct-v0.1"
    
    ANTHROPIC_API_KEY: Optional[str] = None
    ANTHROPIC_MODEL: str = "claude-3-haiku-20240307"
    
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_BATCH_MODE: bool = True
    
    # ==================== 캐시 설정 ====================
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_DB: int = 0
    REDIS_TTL: int = 3600  # 1시간
    
    SQLITE_CACHE_DB: str = "cache.db"
    SQLITE_CACHE_RETENTION_DAYS: int = 30
    
    CACHE_ENABLE: bool = True
    CACHE_L1_TTL: int = 3600  # Redis
    CACHE_L2_TTL: int = 2592000  # SQLite (30일)
    
    # ==================== 우선순위 ====================
    PRIORITY_IMMEDIATE: str = "local_ollama,groq,huggingface"
    PRIORITY_COMPLEX: str = "claude_haiku,groq,openai_batch"
    PRIORITY_BULK: str = "openai_batch,local_queue"
    
    # ==================== 모니터링 ====================
    LOG_RESPONSE_TIME: bool = True
    LOG_RESPONSE_TIME_THRESHOLD_MS: int = 2000
    
    TRACK_COSTS: bool = True
    MONTHLY_BUDGET: float = 5.0
    
    # ==================== 클라우드 저장소 ====================
    SUPABASE_URL: Optional[str] = None
    SUPABASE_KEY: Optional[str] = None
    
    FIREBASE_PROJECT_ID: Optional[str] = None
    FIREBASE_API_KEY: Optional[str] = None
    
    # ==================== 배치 처리 ====================
    TASK_QUEUE_ENABLE: bool = True
    TASK_QUEUE_MAX_WORKERS: int = 4
    
    BATCH_JOB_MAX_ITEMS: int = 1000
    BATCH_JOB_TIMEOUT_HOURS: int = 24
    
    # ==================== 통계 ====================
    COLLECT_STATS: bool = True
    STATS_INTERVAL_SECONDS: int = 60
    SAVE_METRICS_TO_DB: bool = True
    METRICS_RETENTION_DAYS: int = 90
    
    # ==================== 경고 ====================
    ALERT_HIGH_LATENCY_MS: int = 5000
    ALERT_ERROR_RATE_PERCENT: int = 10
    ALERT_COST_EXCEED_PERCENT: int = 80
    
    # ==================== 기본 설정 ====================
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    LOG_API_CALLS: bool = True
    MOCK_MODE: bool = False
    
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    
    RAILWAY_ENVIRONMENT_NAME: str = "development"
    RAILWAY_LINK: Optional[str] = None
    
    # ==================== 보안 ====================
    VALIDATE_API_KEYS_ON_STARTUP: bool = True
    SANITIZE_LOGS: bool = True
    MASK_API_KEYS: bool = True
    
    
    # ==================== 검증 메서드 ====================
    
    def validate_llm_providers(self) -> dict:
        """사용 가능한 LLM 프로바이더 검증"""
        available = {}
        
        # 로컬 Ollama
        available["local_ollama"] = {
            "status": "available",
            "model": self.LOCAL_OLLAMA_MODEL,
            "url": self.LOCAL_OLLAMA_URL,
            "cost": 0
        }
        
        # Groq
        available["groq"] = {
            "status": "available" if self.GROQ_API_KEY else "not_configured",
            "model": self.GROQ_MODEL,
            "cost": 0  # 무료
        }
        
        # HuggingFace
        available["huggingface"] = {
            "status": "available" if self.HUGGINGFACE_API_KEY else "not_configured",
            "model": self.HUGGINGFACE_MODEL,
            "cost": 0  # 무료
        }
        
        # Claude (가장 저렴)
        available["claude"] = {
            "status": "available" if self.ANTHROPIC_API_KEY else "not_configured",
            "model": self.ANTHROPIC_MODEL,
            "cost": 0.00025  # $0.25 per M input tokens
        }
        
        # OpenAI Batch
        available["openai_batch"] = {
            "status": "available" if self.OPENAI_API_KEY else "not_configured",
            "cost": 0.00015  # 배치 모드 50% 할인
        }
        
        return available
    
    def validate_storage_providers(self) -> dict:
        """클라우드 저장소 검증"""
        available = {}
        
        available["supabase"] = {
            "status": "available" if (self.SUPABASE_URL and self.SUPABASE_KEY) else "not_configured",
            "free_tier": "500MB"
        }
        
        available["firebase"] = {
            "status": "available" if self.FIREBASE_PROJECT_ID else "not_configured",
            "free_tier": "1GB"
        }
        
        available["sqlite"] = {
            "status": "available",
            "path": self.SQLITE_CACHE_DB,
            "retention_days": self.SQLITE_CACHE_RETENTION_DAYS
        }
        
        return available
    
    def get_routing_priority(self, task_type: str) -> List[str]:
        """작업 유형별 라우팅 우선순위"""
        if task_type == "immediate":
            return self.PRIORITY_IMMEDIATE.split(",")
        elif task_type == "complex":
            return self.PRIORITY_COMPLEX.split(",")
        elif task_type == "bulk":
            return self.PRIORITY_BULK.split(",")
        else:
            return self.PRIORITY_IMMEDIATE.split(",")
    
    def check_budget(self, current_cost: float) -> bool:
        """월 예산 확인"""
        if current_cost >= self.MONTHLY_BUDGET * (self.ALERT_COST_EXCEED_PERCENT / 100):
            logger.warning(f"⚠️ 월 예산 경고: ${current_cost:.2f}/${self.MONTHLY_BUDGET:.2f}")
            return False
        return True
    
    def get_summary(self) -> dict:
        """설정 요약"""
        return {
            "mode": self.LLM_MODE,
            "llm_providers": self.validate_llm_providers(),
            "storage_providers": self.validate_storage_providers(),
            "cache_enabled": self.CACHE_ENABLE,
            "redis_ttl": self.REDIS_TTL,
            "sqlite_retention_days": self.SQLITE_CACHE_RETENTION_DAYS,
            "monthly_budget": self.MONTHLY_BUDGET,
            "track_costs": self.TRACK_COSTS,
        }


# 싱글톤
_settings_instance = None


def get_hybrid_settings() -> HybridSettings:
    """HybridSettings 싱글톤"""
    global _settings_instance
    if not _settings_instance:
        _settings_instance = HybridSettings()
        logger.info("✅ 하이브리드 설정 로드됨")
        
        # 설정 검증
        try:
            summary = _settings_instance.get_summary()
            logger.info(f"📊 LLM 모드: {_settings_instance.LLM_MODE}")
            logger.info(f"📊 캐시: {'활성화' if _settings_instance.CACHE_ENABLE else '비활성화'}")
            logger.info(f"📊 예산 추적: {'활성화' if _settings_instance.TRACK_COSTS else '비활성화'}")
        except Exception as e:
            logger.error(f"❌ 설정 검증 실패: {e}")
    
    return _settings_instance


# 초기화 시 자동 설정 검증
if not os.getenv("SKIP_SETTINGS_VALIDATION"):
    try:
        settings = get_hybrid_settings()
    except Exception as e:
        logger.error(f"설정 초기화 실패: {e}")
