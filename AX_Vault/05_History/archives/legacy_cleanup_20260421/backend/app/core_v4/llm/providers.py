import logging
import httpx
from typing import Optional
from app.utils.hybrid_settings import get_hybrid_settings

logger = logging.getLogger(__name__)
settings = get_hybrid_settings()

class BaseLLMProvider:
    """Interface for LLM Providers."""
    async def call(self, query: str, system_prompt: Optional[str] = None) -> str:
        raise NotImplementedError("Each provider must implement call()")

class OllamaProvider(BaseLLMProvider):
    """Local Ollama Provider (Free/Private)."""
    async def call(self, query: str, system_prompt: Optional[str] = None) -> str:
        try:
            # Reusing existing brain logic to avoid duplication
            from app.brains.base import OllamaBrain
            brain = OllamaBrain()
            return await brain.generate(query, system_prompt)
        except Exception as e:
            logger.error(f"Ollama call failed: {e}")
            raise

class GroqProvider(BaseLLMProvider):
    """Groq API Provider (High speed/Free tier)."""
    async def call(self, query: str, system_prompt: Optional[str] = None) -> str:
        if not settings.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not configured")
            
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": settings.GROQ_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt or ""},
                        {"role": "user", "content": query}
                    ],
                    "max_tokens": 1000,
                },
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

class ClaudeProvider(BaseLLMProvider):
    """Anthropic Claude Provider (Cost efficient)."""
    async def call(self, query: str, system_prompt: Optional[str] = None) -> str:
        if not settings.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY not configured")
            
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": settings.ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": settings.ANTHROPIC_MODEL,
                    "max_tokens": 1000,
                    "system": system_prompt or "",
                    "messages": [{"role": "user", "content": query}]
                },
                timeout=60.0
            )
            response.raise_for_status()
            data = response.json()
            return data["content"][0]["text"]

class HFProvider(BaseLLMProvider):
    """HuggingFace Inference API Provider."""
    async def call(self, query: str, system_prompt: Optional[str] = None) -> str:
        if not settings.HUGGINGFACE_API_KEY:
            raise ValueError("HUGGINGFACE_API_KEY not configured")
            
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api-inference.huggingface.co/models/{settings.HUGGINGFACE_MODEL}",
                headers={"Authorization": f"Bearer {settings.HUGGINGFACE_API_KEY}"},
                json={
                    "inputs": f"{system_prompt or ''}\n\nUser: {query}",
                    "parameters": {"max_new_tokens": 1000, "temperature": 0.7}
                },
                timeout=60.0
            )
            response.raise_for_status()
            data = response.json()
            return data[0]["generated_text"]
