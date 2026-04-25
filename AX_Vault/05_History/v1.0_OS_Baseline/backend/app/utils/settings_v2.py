from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "Jarvis Agent Office"
    app_env: str = "local"  # local, staging, production
    app_shared_key: str = "AIN_PAPA_SHARED_KEY"
    
    # ==================== LLM 모드 설정 ====================
    # 실패 시 우선순위: 로컬 > 클라우드 > 오프라인
    llm_mode: str = "hybrid"  # "local" | "cloud" | "hybrid" | "offline"
    
    # ==================== 로컬 Ollama 설정 ====================
    local_ollama_url: str = "http://localhost:11434"
    local_model: str = "jarvis"
    local_chat_path: str = "/api/chat"
    
    # Ollama 연결 타임아웃 (초)
    ollama_timeout: int = 60
    ollama_retry_attempts: int = 3
    ollama_retry_delay: int = 3
    
    # ==================== 클라우드 API 설정 ====================
    cloud_provider: str = "openai"  # "openai" | "anthropic" | "vertex"
    
    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4-mini"
    openai_base_url: str = "https://api.openai.com/v1"
    
    # Anthropic (Claude)
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-3-haiku-20240307"
    
    # Google Vertex AI
    gemini_api_key: str = ""
    vertex_model: str = "gemini-2.0-flash"
    
    # ==================== 레거시 설정 (호환성) ====================
    # 아래는 이전 코드와의 호환성을 위해 유지
    intelligence_engine_url: str = "http://localhost:11434"
    intelligence_engine_chat_path: str = "/api/chat"
    jarvis_model: str = "JARVIS"
    gpt_oss_model: str = "gpt-oss:latest"
    gemma_model: str = "gemma3:4b"
    qwen_model: str = "qwen2.5-coder:latest"
    use_external_api: bool = False
    
    # ==================== 데이터베이스 ====================
    sqlite_path: str = "../data/jarvis.db"
    
    # ==================== 보관함 ====================
    ax_vault_path: str = "../AX_Vault"
    
    # ==================== 로깅 ====================
    log_level: str = "INFO"
    debug_mode: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

@lru_cache
def get_settings() -> Settings:
    return Settings()
