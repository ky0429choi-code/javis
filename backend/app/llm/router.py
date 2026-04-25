import logging
import asyncio
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
    JARVIS Unified LLM Router Core 4.0 (Confidence-Instrumented).
    Fixes:
    - B2: Race Condition (VRAM Lock)
    - B5: Model Key Mapping Errors
    New:
    - 종적 신뢰도 기반 동적 프로바이더 우선순위
    - 호출 성공/실패를 confidence_collector에 자동 기록
    """
    _vram_lock = asyncio.Lock()  # FIX B2: Mutual exclusion for local inference

    def __init__(self):
        self.providers = {
            "local_ollama": OllamaProvider(),
            "groq": GroqProvider(),
            "claude_haiku": ClaudeProvider(),
            "huggingface": HFProvider()
        }
        self.initialized = False
        self._last_provider = None  # 마지막으로 사용된 프로바이더 추적

    async def _ensure_init(self):
        if not self.initialized:
            await cache_manager.init()
            self.initialized = True

    async def call(self, 
                   prompt: str, 
                   system: str = None, 
                   task_type: str = "immediate",
                   model_key: Optional[str] = None) -> str:
        """
        Hardened call entry point with confidence tracking.
        """
        await self._ensure_init()
        start_time = time.time()
        
        # 1. Sensitivity Filter (설계 원칙: 민감 데이터는 Cloud로 절대 자동 폴백 안 함)
        is_sensitive = await sensitivity_filter.is_sensitive(f"{prompt}|{system or ''}")
        if is_sensitive:
            logger.info("🛡️ Sensitive data detected → Local only.")
            try:
                result = await self._call_with_lock_if_local("local_ollama", prompt, system)
                self._record_call("local_ollama", True, start_time)
                return result
            except Exception:
                # Ollama 다운 → HITL 위임 (Cloud 폴백 금지)
                logger.warning("🛡️ Ollama down + sensitive data → HITL delegation")
                return (
                    "⚠️ 민감 데이터가 감지되었으나 로컬 엔진이 오프라인입니다. "
                    "보안 정책상 클라우드로 전송할 수 없습니다. "
                    "/recover 명령어로 로컬 엔진을 재시작하거나, 민감 정보를 제거 후 재시도해 주세요."
                )

        # 2. Cache Check
        cached = await cache_manager.get(prompt, system)
        if cached:
            return cached

        # 3. Model Key Logic (FIX B5)
        target_provider = self._map_key_to_provider(model_key) if model_key else None
        
        if target_provider:
            try:
                result = await self._call_with_lock_if_local(target_provider, prompt, system)
                self._record_call(target_provider, True, start_time)
                return result
            except Exception as e:
                self._record_call(target_provider, False, start_time, str(e))
                logger.warning(f"Target provider {target_provider} failed, falling back to hybrid.")

        # 4. Hybrid Routing Logic (종적 신뢰도 기반 동적 우선순위)
        from app.core.hitl.gate2 import gate2, CostDecision
        priority_list = self._get_dynamic_priority(task_type)
        
        for provider_key in priority_list:
            # Gate 2: Cloud 비용 체크 (로컬은 자동 통과)
            if provider_key != "local_ollama":
                g2 = gate2.evaluate(provider_key)
                if g2.decision == CostDecision.HOLD:
                    logger.warning(f"Gate2: Skipping {provider_key} (cost ${g2.estimated_cost:.4f})")
                    continue

            try:
                response = await self._call_with_lock_if_local(provider_key, prompt, system)
                latency = int((time.time() - start_time) * 1000)
                logger.info(f"✅ V4 Success: {provider_key} ({latency}ms)")
                await cache_manager.set(prompt, response, system)
                self._record_call(provider_key, True, start_time)
                return response
            except Exception as e:
                self._record_call(provider_key, False, start_time, str(e))
                logger.warning(f"⚠️ Provider {provider_key} failed: {e}")
                continue
        
        return "❌ 모든 AI 엔진이 응답하지 않습니다."


    def _get_dynamic_priority(self, task_type: str) -> list:
        """종적 신뢰도 기반 동적 프로바이더 우선순위.

        충분한 데이터가 있으면 EMA 기반 정렬, 없으면 기본 설정값 사용.
        """
        try:
            from app.core.confidence_collector import get_confidence_collector
            collector = get_confidence_collector()
            dynamic = collector.get_dynamic_provider_priority(task_type)
            if dynamic and len(dynamic) > 1:
                logger.debug(f"📊 동적 라우팅: {dynamic}")
                return dynamic
        except Exception as e:
            logger.debug(f"동적 라우팅 fallback (데이터 부족): {e}")

        # 기본값
        return settings.get_routing_priority(task_type)

    def _record_call(self, provider: str, success: bool, start_time: float, error: str = None):
        """프로바이더 호출 결과를 종적 신뢰도 시스템에 기록."""
        self._last_provider = provider
        latency_ms = int((time.time() - start_time) * 1000)

        try:
            from app.core.confidence_collector import get_confidence_collector
            collector = get_confidence_collector()
            collector.record_step(
                task_id="__router__",
                component="router",
                success=success,
                latency_ms=latency_ms,
                provider=provider,
                reason=error or "ok",
            )
        except Exception:
            pass  # 신뢰도 기록 실패가 라우팅을 막아서는 안 됨

    def _map_key_to_provider(self, key: str) -> Optional[str]:
        """FIX B5: Normalizes model keys to provider keys."""
        mapping = {
            "qwen": "local_ollama",
            "gemma": "local_ollama",
            "mistral": "groq",
            "claude": "claude_haiku",
            "gpt": "groq" # Placeholder or fallback to best available
        }
        return mapping.get(key.lower())

    async def _call_with_lock_if_local(self, key: str, prompt: str, system: Optional[str]) -> str:
        """FIX B2: Protects VRAM from concurrent local calls."""
        if key == "local_ollama":
            async with self._vram_lock:
                return await self.providers["local_ollama"].call(prompt, system)
        
        actual_key = "claude_haiku" if "claude" in key else key
        provider = self.providers.get(actual_key)
        if not provider:
            raise ValueError(f"Unknown provider: {key}")
        return await provider.call(prompt, system)


# Global Instance
router = SmartRouterV4()
