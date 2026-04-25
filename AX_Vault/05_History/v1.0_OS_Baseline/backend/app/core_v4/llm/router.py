import logging
import time
from typing import Dict, Any, Optional
from .sensitivity import sensitivity_filter
from .cache import cache_manager
from .providers import OllamaProvider, GroqProvider, ClaudeProvider, HFProvider
from app.utils.hybrid_settings import get_hybrid_settings

logger = logging.getLogger(__name__)
settings = get_hybrid_settings()

class SmartRouterV4:
    """
    Unified JARVIS LLM Router V4.
    Highly modular, secure, and cost-efficient.
    """
    def __init__(self):
        self.providers = {
            "local_ollama": OllamaProvider(),
            "groq": GroqProvider(),
            "claude_haiku": ClaudeProvider(),
            "huggingface": HFProvider()
        }
        self.initialized = False

    async def _ensure_init(self):
        if not self.initialized:
            await cache_manager.init()
            self.initialized = True

    async def call(self, 
                   prompt: str, 
                   system: str = None, 
                   task_type: str = "immediate") -> str:
        """
        Main entry point for LLM calls.
        """
        await self._ensure_init()
        start_time = time.time()
        
        # 1. Sensitivity Filter (Security First)
        is_sensitive = await sensitivity_filter.is_sensitive(f"{prompt}|{system or ''}")
        
        if is_sensitive:
            logger.info("🛡️ Sensitive data detected. routing to Local Ollama ONLY.")
            return await self._call_provider("local_ollama", prompt, system)

        # 2. Cache Check (Efficiency)
        cached = await cache_manager.get(prompt, system)
        if cached:
            return cached

        # 3. Routing Logic (Hybrid)
        priority_list = settings.get_routing_priority(task_type)
        
        response = None
        used_provider = None
        
        for provider_key in priority_list:
            try:
                logger.info(f"🔄 Attempting {provider_key} for {task_type} task...")
                response = await self._call_provider(provider_key, prompt, system)
                used_provider = provider_key
                break
            except Exception as e:
                logger.warning(f"⚠️ Provider {provider_key} failed: {e}")
                continue
        
        if not response:
            logger.error("❌ All LLM providers failed.")
            return "❌ AI 엔진을 사용할 수 없습니다."

        # 4. Success handling (Cache & Log)
        latency = int((time.time() - start_time) * 1000)
        logger.info(f"✅ V4 Response via {used_provider} in {latency}ms")
        
        await cache_manager.set(prompt, response, system)
        
        return response

    async def _call_provider(self, key: str, prompt: str, system: Optional[str]) -> str:
        """Helper to invoke a provider by key."""
        # Simple mapping for Anthropic name variations
        actual_key = "claude_haiku" if "claude" in key else key
        provider = self.providers.get(actual_key)
        
        if not provider:
            # Fallback to Local Ollama if provider unknown
            logger.warning(f"Unknown provider {key}, falling back to local_ollama")
            return await self.providers["local_ollama"].call(prompt, system)
            
        return await provider.call(prompt, system)

# Singleton instance
router_v4 = SmartRouterV4()
