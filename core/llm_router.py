"""
JARVIS v5  LLM Router

역할: model_key  실제 모델명 매핑 후 Ollama /api/chat 호출.
      순차 lock + 지수 백오프 재시도 포함.

수정 이력 (rebuild patch):
  - model_key를 실제 Ollama 모델명으로 매핑
  - /api/generate > /api/chat 엔드포인트로 전환
  - asyncio.Lock으로 순차 실행 보장
  - 재시도 강화: max_retries + 지수 백오프
  - 모델 없음 > 설치된 fallback 모델로 자동 대체
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
#  기본 설정
# ──────────────────────────────────────────────

OLLAMA_BASE = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
MAX_RETRIES  = int(os.getenv("LLM_MAX_RETRIES", "3"))
TIMEOUT_SEC  = float(os.getenv("LLM_TIMEOUT", "120"))

_DEFAULT_MODEL_MAP: Dict[str, str] = {
    "jarvis":   os.getenv("JARVIS_MODEL",   "qwen2.5:14b"),
    "planner":  os.getenv("PLANNER_MODEL",  "qwen2.5:14b"),
    "gpt_oss":  os.getenv("GPT_OSS_MODEL",  "qwen2.5:14b"),
    "qwen":     os.getenv("QWEN_MODEL",     "qwen2.5:14b"),
    "fast":     os.getenv("FAST_MODEL",     "qwen2.5:14b"),
}


class LLMRouter:
    """
    model_key를 실제 Ollama 모델명으로 변환해 /api/chat을 호출한다.
    동시 호출을 막기 위해 asyncio.Lock을 사용한다.
    """

    def __init__(
        self,
        model_map: Optional[Dict[str, str]] = None,
        max_retries: int = MAX_RETRIES,
        timeout: float = TIMEOUT_SEC,
    ) -> None:
        self._model_map = model_map or dict(_DEFAULT_MODEL_MAP)
        self._max_retries = max_retries
        self._timeout = timeout
        self._lock = asyncio.Lock()
        self._available_models: List[str] = []

    async def complete(
        self,
        model_key: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> str:
        model_name = self._resolve_model(model_key)
        payload = {
            "model": model_name,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        async with self._lock:
            return await self._call_with_retry(payload)

    async def refresh_available_models(self) -> List[str]:
        """Ollama에서 설치된 모델 목록을 갱신한다"""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"{OLLAMA_BASE}/api/tags")
                resp.raise_for_status()
                data = resp.json()
                self._available_models = [
                    m["name"] for m in data.get("models", [])
                ]
                logger.info(
                    "Available models: %s", self._available_models
                )
        except Exception as exc:
            logger.warning("Could not refresh model list: %s", exc)
        return self._available_models

    def _resolve_model(self, model_key: str) -> str:
        name = self._model_map.get(model_key, model_key)

        if self._available_models and name not in self._available_models:
            fallback = self._available_models[0]
            logger.warning(
                "Model '%s' not available; falling back to '%s'",
                name, fallback,
            )
            return fallback

        return name

    async def _call_with_retry(self, payload: dict) -> str:
        last_exc: Optional[Exception] = None

        for attempt in range(1, self._max_retries + 2):
            try:
                async with httpx.AsyncClient(timeout=self._timeout) as client:
                    resp = await client.post(
                        f"{OLLAMA_BASE}/api/chat",
                        json=payload,
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    return data["message"]["content"]

            except (httpx.HTTPStatusError, httpx.RequestError, KeyError) as exc:
                last_exc = exc
                if attempt <= self._max_retries:
                    wait = 2 ** (attempt - 1)
                    logger.warning(
                        "LLM call attempt %d/%d failed (%s), retry in %ds",
                        attempt, self._max_retries + 1, exc, wait,
                    )
                    await asyncio.sleep(wait)

        raise RuntimeError(
            f"LLM call failed after {self._max_retries + 1} attempts: {last_exc}"
        )

    def complete_sync(
        self,
        model_key: str,
        messages: List[Dict[str, str]],
        **kwargs,
    ) -> str:
        return asyncio.get_event_loop().run_until_complete(
            self.complete(model_key, messages, **kwargs)
        )
