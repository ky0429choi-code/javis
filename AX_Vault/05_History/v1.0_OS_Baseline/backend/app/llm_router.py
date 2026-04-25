import asyncio
import logging
import httpx
from typing import Optional, Dict, Any
from app.utils.settings import get_settings
from app.brains.qwen_brain import QwenBrain
from app.brains.gemma_brain import GemmaBrain
from app.brains.gpt_oss_brain import GptOssBrain

logger = logging.getLogger(__name__)
settings = get_settings()

class LLMRouter:
    _instance = None
    _lock = asyncio.Lock()
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(LLMRouter, cls).__new__(cls)
            cls._instance._init_brains()
        return cls._instance

    def _init_brains(self):
        self.brains = {
            "qwen": QwenBrain(),
            "gemma": GemmaBrain(),
            "gpt_oss": GptOssBrain(),
        }
        # 'JARVIS' is the primary identity, currently mapped to gpt_oss in settings
        self.primary_brain_key = "gpt_oss" 

    async def call(self, prompt: str, system: str, model_key: Optional[str] = None, format: Optional[str] = None) -> str:
        """
        Unified entry point for LLM calls with sequential queuing for local VRAM protection.
        """
        if settings.use_external_api:
            return await self._call_external(prompt, system, model_key)
        
        # Sequential execution for local models to prevent OOM
        async with self._lock:
            retries = 3
            for attempt in range(retries):
                try:
                    logger.info(f"LLM Router: Queuing request (Attempt {attempt+1}/{retries})...")
                    async with httpx.AsyncClient(timeout=60.0) as client:
                        response = await client.post(
                            f"{settings.intelligence_engine_url}/api/chat",
                            json={
                                "model": settings.jarvis_model,
                                "messages": [
                                    {"role": "system", "content": system},
                                    {"role": "user", "content": prompt}
                                ],
                                "stream": False
                            }
                        )
                        response.raise_for_status()
                        result = response.json()
                        return result["message"]["content"]
                except (httpx.ConnectError, httpx.ReadTimeout, httpx.HTTPStatusError) as e:
                    logger.warning(f"LLM Router Connection Error (Attempt {attempt+1}): {e}")
                    if attempt < retries - 1:
                        await asyncio.sleep(3) # Wait before retry
                    else:
                        return f"❌ [LLM_ERROR] 모델과 통신할 수 없습니다. Ollama 상태를 확인해 주세요: {str(e)}"
                except Exception as e:
                    logger.error(f"LLM Router Unexpected Error: {e}")
                    return f"❌ [SYSTEM_ERROR] 내부 처리 중 오류가 발생했습니다: {str(e)}"

    async def _call_external(self, prompt: str, system: str, model_key: Optional[str]) -> str:
        """
        Logic for calling external APIs (OpenAI, Claude, etc.)
        """
        # Placeholder for external API integration
        # In a real implementation, we would use openai or anthropic libraries here
        logger.info("LLM Router: Calling external API (Not fully implemented yet)")
        return "External API response placeholder"

router = LLMRouter()
