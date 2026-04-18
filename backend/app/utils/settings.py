from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "Jarvis Agent Office vNext"
    app_env: str = "local"
    app_shared_key: str = "AIN_PAPA_SHARED_KEY"
    intelligence_engine_url: str = "http://localhost:11434"
    intelligence_engine_chat_path: str = "/api/chat"
    jarvis_model: str = "JARVIS"
    gpt_oss_model: str = "gpt-oss:latest"
    gemma_model: str = "gemma3:4b"
    qwen_model: str = "qwen2.5-coder:latest"
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
