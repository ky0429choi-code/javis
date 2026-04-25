import logging
import httpx
from typing import Optional
from app.utils.settings import get_settings
from app.utils.hybrid_settings import get_hybrid_settings

logger = logging.getLogger(__name__)
settings = get_settings()
h_settings = get_hybrid_settings()


class BaseLLMProvider:
    """Interface for LLM Providers."""
    async def call(self, query: str, system_prompt: Optional[str] = None) -> str:
        raise NotImplementedError("Each provider must implement call()")


class OllamaProvider(BaseLLMProvider):
    """Local Ollama Provider (Free/Private) — 선택적 사용."""

    async def call(self, query: str, system_prompt: Optional[str] = None) -> str:
        """Ollama API 직접 호출 (brains/base.py 의존성 제거)."""
        url = f"{settings.intelligence_engine_url}/api/chat"
        payload = {
            "model": settings.jarvis_model,
            "messages": [
                {"role": "system", "content": system_prompt or ""},
                {"role": "user", "content": query},
            ],
            "stream": False,
        }
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                return data["message"]["content"]
        except httpx.ConnectError:
            raise ConnectionError(
                f"Ollama 서버에 연결할 수 없습니다 ({settings.intelligence_engine_url}). "
                "클라우드 모드로 전환합니다."
            )
        except Exception as e:
            logger.error(f"Ollama call failed: {e}")
            raise


class GroqProvider(BaseLLMProvider):
    """Groq API Provider (High speed / Free tier)."""

    async def call(self, query: str, system_prompt: Optional[str] = None) -> str:
        if not h_settings.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not configured")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {h_settings.GROQ_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": h_settings.GROQ_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt or ""},
                        {"role": "user", "content": query},
                    ],
                    "max_tokens": 1000,
                },
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]


class ClaudeProvider(BaseLLMProvider):
    """Anthropic Claude Provider."""

    async def call(self, query: str, system_prompt: Optional[str] = None) -> str:
        if not h_settings.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY not configured")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": h_settings.ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": h_settings.ANTHROPIC_MODEL,
                    "max_tokens": 1000,
                    "system": system_prompt or "",
                    "messages": [{"role": "user", "content": query}],
                },
                timeout=60.0,
            )
            response.raise_for_status()
            data = response.json()
            return data["content"][0]["text"]


class HFProvider(BaseLLMProvider):
    """HuggingFace Inference API Provider."""

    async def call(self, query: str, system_prompt: Optional[str] = None) -> str:
        if not h_settings.HUGGINGFACE_API_KEY:
            raise ValueError("HUGGINGFACE_API_KEY not configured")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api-inference.huggingface.co/models/{h_settings.HUGGINGFACE_MODEL}",
                headers={"Authorization": f"Bearer {h_settings.HUGGINGFACE_API_KEY}"},
                json={
                    "inputs": f"{system_prompt or ''}\n\nUser: {query}",
                    "parameters": {"max_new_tokens": 1000, "temperature": 0.7},
                },
                timeout=60.0,
            )
            response.raise_for_status()
            data = response.json()
            return data[0]["generated_text"]
