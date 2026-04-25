from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    app_name: str = "Jarvis Agent Office vNext"
    app_env: str = "local"
    app_shared_key: str = "AIN_PAPA_SHARED_KEY"
    intelligence_engine_url: str = "http://localhost:11434"
    intelligence_engine_chat_path: str = "/api/chat"
    
    # 🟢 기본 Ollama 모델
    DEFAULT_OLLAMA_MODEL: str = "qwen2.5-coder:latest"  # 한글 이해 95%+
    
    # ✅ JARVIS 커스텀 모델 (Gemma3 기반)
    # 사장님의 진정한 비서 JARVIS
    # - 베이스: Gemma3 (Google)
    # - 크기: 3.3GB
    # - 특징: 구어체 한국어, 존댓말, 최고 수준의 예우
    jarvis_model: str = "JARVIS"  # Ollama에 등록된 커스텀 모델
    
    # 대체 모델들
    gpt_oss_model: str = "gpt-oss:latest"
    gemma_model: str = "gemma3:4b"
    qwen_model: str = "qwen2.5-coder:latest"  # Qwen 지정 (권장)
    
    # ⏰ 타임존 설정 (시간 기능용)
    timezone: str = os.getenv("TIMEZONE", "Asia/Seoul")
    
    # 폴백 모델 순서
    FALLBACK_OLLAMA_MODELS: list = [
        "dolphin-mistral:latest",      # 코드 생성 우수
        "neural-chat-7b:latest",       # 균형
    ]
    
    # 데이터베이스
    sqlite_path: str = "../data/jarvis.db"
    
    # AI Core 4.0 Settings
    use_external_api: bool = False
    openai_api_key: str = ""
    claude_api_key: str = ""
    gemini_api_key: str = ""
    
    # Vault Paths
    ax_vault_path: str = "../AX_Vault"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

@lru_cache
def get_settings() -> Settings:
    return Settings()
