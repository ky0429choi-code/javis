"""
동적 API 라우터 - 공식 무료/저비용 API 조합
가격 변동 및 정책 변경에 강한 자동 페일오버 시스템
"""

import asyncio
import logging
import httpx
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class APIProvider(Enum):
    """공식 API 제공자 (웹 자동화 제외)"""
    LOCAL_OLLAMA = "ollama"           # 로컬 (무제한, 무료)
    GROQ = "groq"                     # 무료 (Rate Limited: 30k tokens/min)
    HUGGINGFACE = "huggingface"       # 무료 (Queue 기반)
    TOGETHER_AI = "together_ai"       # $5/월 크레딧
    CLAUDE_API = "claude_api"         # 공식 API (저비용)


class PricingPolicy:
    """API 비용 정책 (변동 감시)"""
    
    def __init__(self):
        self.last_check = {}
        self.policies = {
            APIProvider.LOCAL_OLLAMA: {
                "cost_per_1k_tokens": 0,
                "rate_limit": None,
                "monthly_quota": None,
            },
            APIProvider.GROQ: {
                "cost_per_1k_tokens": 0,
                "rate_limit": "30000 tokens/min",  # ← 변경 감지 대상
                "monthly_quota": None,
            },
            APIProvider.HUGGINGFACE: {
                "cost_per_1k_tokens": 0,
                "rate_limit": "Queue based",
                "monthly_quota": None,
            },
            APIProvider.TOGETHER_AI: {
                "cost_per_1k_tokens": 0,
                "rate_limit": "$5/month credit",  # ← 변경 감지 대상
                "monthly_quota": 5.0,
            },
            APIProvider.CLAUDE_API: {
                "cost_per_1k_tokens": 0.25,  # ← 변경 감지 대상
                "rate_limit": None,
                "monthly_quota": None,
            },
        }
    
    async def check_for_changes(self) -> List[str]:
        """정책 변경 감지"""
        changes = []
        
        for provider, policy in self.policies.items():
            try:
                # 각 API 공식 문서 또는 상태 엔드포인트 체크
                new_policy = await self._fetch_current_policy(provider)
                
                if new_policy != policy:
                    change_msg = self._describe_change(provider, policy, new_policy)
                    changes.append(change_msg)
                    self.policies[provider] = new_policy
                    logger.warning(f"🔴 정책 변경 감지: {change_msg}")
                    
            except Exception as e:
                logger.debug(f"정책 확인 실패 {provider.value}: {e}")
        
        return changes
    
    async def _fetch_current_policy(self, provider: APIProvider) -> Dict:
        """현재 정책 조회 (공식 소스에서)"""
        # 실제 구현에서는 각 API의 공식 Docs/API 확인
        # 여기서는 캐시된 정책 반환
        return self.policies[provider]
    
    def _describe_change(self, provider: APIProvider, old: Dict, new: Dict) -> str:
        """변경사항 설명"""
        changes = []
        for key in old:
            if old[key] != new.get(key):
                changes.append(f"{key}: {old[key]} → {new.get(key)}")
        return f"{provider.value}: " + ", ".join(changes)


class DynamicAPIRouter:
    """
    동적 API 라우터
    
    기능:
    1. 공식 무료 API 자동 조합 (웹 자동화 없음)
    2. 가격/정책 변동 감지
    3. 자동 페일오버 (한 곳 실패 시 다음 API)
    4. 비용 추적
    """
    
    def __init__(self):
        self.pricing = PricingPolicy()
        self.monthly_cost = 0.0
        self.call_count = {}
        self.last_alert = {}
        
        # API 키 (환경변수에서 로드)
        self.groq_key = None
        self.hf_key = None
        self.together_key = None
        self.claude_key = None
        
        # 공식 API 폴백 순서
        self.provider_chain: List[Tuple[APIProvider, float, str]] = [
            (APIProvider.LOCAL_OLLAMA, 0, "로컬 메모리"),
            (APIProvider.GROQ, 0, "30k tokens/min"),
            (APIProvider.HUGGINGFACE, 0, "Queue 기반"),
            (APIProvider.TOGETHER_AI, 0, "$5/월"),
            (APIProvider.CLAUDE_API, 0.00025, "공식 API"),
        ]
    
    async def route(self, 
                    query: str,
                    system_prompt: str = None,
                    max_tokens: int = 1000) -> Dict[str, Any]:
        """
        쿼리를 최적의 가용 API로 라우팅
        
        Returns:
            {
                "ok": bool,
                "response": str,
                "provider": str,
                "cost": float,
                "time_ms": int,
                "retry_count": int
            }
        """
        import time
        start_time = time.time()
        
        retry_count = 0
        
        # 각 제공자 순서대로 시도
        for provider, cost, limit_desc in self.provider_chain:
            retry_count += 1
            
            try:
                logger.info(f"🔄 시도: {provider.value} ({limit_desc})")
                
                # 1단계: 가용성 확인
                is_available = await self._check_availability(provider)
                if not is_available:
                    logger.warning(f"⏭️ {provider.value}: 사용 불가 → 다음 것 시도")
                    continue
                
                # 2단계: 비용 확인 (예산 내인지)
                if cost > 0 and not self._budget_ok(cost):
                    logger.warning(f"💰 {provider.value}: 예산 부족 → 다음 것 시도")
                    continue
                
                # 3단계: 공식 API 호출 (웹 자동화 없음)
                response = await self._call_official_api(
                    provider, query, system_prompt, max_tokens
                )
                
                # 4단계: 비용 기록
                self.monthly_cost += cost
                self.call_count[provider.value] = self.call_count.get(provider.value, 0) + 1
                
                elapsed_ms = int((time.time() - start_time) * 1000)
                logger.info(
                    f"✅ {provider.value}: 성공 "
                    f"({elapsed_ms}ms, 비용 ${cost:.6f})"
                )
                
                return {
                    "ok": True,
                    "response": response,
                    "provider": provider.value,
                    "cost": cost,
                    "time_ms": elapsed_ms,
                    "retry_count": retry_count,
                }
                
            except Exception as e:
                logger.warning(f"⚠️ {provider.value} 실패: {str(e)}")
                continue
        
        # 모든 API 실패
        logger.error("❌ 모든 외부 API 실패")
        elapsed_ms = int((time.time() - start_time) * 1000)
        
        return {
            "ok": False,
            "response": "⚠️ 모든 AI 엔진 실패 (나중에 다시 시도)",
            "provider": None,
            "cost": 0,
            "time_ms": elapsed_ms,
            "retry_count": retry_count,
        }
    
    async def _check_availability(self, provider: APIProvider) -> bool:
        """API 가용성 확인"""
        
        if provider == APIProvider.LOCAL_OLLAMA:
            # 로컬 상태 확인
            try:
                async with httpx.AsyncClient(timeout=2) as client:
                    response = await client.get("http://localhost:11434/api/tags")
                    return response.status_code == 200
            except:
                return False
        
        elif provider == APIProvider.GROQ:
            return self.groq_key is not None
        
        elif provider == APIProvider.HUGGINGFACE:
            return self.hf_key is not None
        
        elif provider == APIProvider.TOGETHER_AI:
            return self.together_key is not None
        
        elif provider == APIProvider.CLAUDE_API:
            return self.claude_key is not None
        
        return False
    
    def _budget_ok(self, cost: float) -> bool:
        """예산 내인지 확인"""
        MONTHLY_BUDGET = 50.0  # 설정에서 가져오기
        return self.monthly_cost + cost <= MONTHLY_BUDGET
    
    async def _call_official_api(self,
                                 provider: APIProvider,
                                 query: str,
                                 system_prompt: str = None,
                                 max_tokens: int = 1000) -> str:
        """
        공식 API 호출 (웹 자동화 절대 금지)
        """
        
        if provider == APIProvider.LOCAL_OLLAMA:
            return await self._call_ollama(query, system_prompt)
        
        elif provider == APIProvider.GROQ:
            return await self._call_groq(query, system_prompt, max_tokens)
        
        elif provider == APIProvider.HUGGINGFACE:
            return await self._call_huggingface(query, system_prompt)
        
        elif provider == APIProvider.TOGETHER_AI:
            return await self._call_together(query, system_prompt, max_tokens)
        
        elif provider == APIProvider.CLAUDE_API:
            return await self._call_claude(query, system_prompt, max_tokens)
        
        else:
            raise ValueError(f"Unknown provider: {provider}")
    
    async def _call_ollama(self, query: str, system_prompt: str) -> str:
        """Ollama 공식 API (로컬)"""
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                "http://localhost:11434/api/chat",
                json={
                    "model": "mistral",  # 또는 설정된 모델
                    "messages": [
                        {"role": "system", "content": system_prompt or ""},
                        {"role": "user", "content": query},
                    ],
                    "stream": False,
                }
            )
            data = response.json()
            return data.get("message", {}).get("content", "")
    
    async def _call_groq(self, query: str, system_prompt: str, max_tokens: int) -> str:
        """Groq 공식 API (무료, Rate Limited)"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.groq_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "mixtral-8x7b-32768",
                    "messages": [
                        {"role": "system", "content": system_prompt or ""},
                        {"role": "user", "content": query},
                    ],
                    "max_tokens": max_tokens,
                }
            )
            data = response.json()
            return data["choices"][0]["message"]["content"]
    
    async def _call_huggingface(self, query: str, system_prompt: str) -> str:
        """HuggingFace 공식 API (무료)"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.1",
                headers={"Authorization": f"Bearer {self.hf_key}"},
                json={
                    "inputs": f"{system_prompt or ''}\n사용자: {query}",
                    "parameters": {"max_new_tokens": 1000},
                }
            )
            data = response.json()
            return data[0]["generated_text"] if data else ""
    
    async def _call_together(self, query: str, system_prompt: str, max_tokens: int) -> str:
        """Together AI 공식 API ($5/월 크레딧)"""
        import together
        
        together.api_key = self.together_key
        response = together.Complete.create(
            prompt=f"{system_prompt or ''}\n사용자: {query}",
            model="togethercomputer/mistral-7b-instruct",
            max_tokens=max_tokens,
            temperature=0.7,
        )
        return response["output"]["choices"][0]["text"]
    
    async def _call_claude(self, query: str, system_prompt: str, max_tokens: int) -> str:
        """Claude 공식 API (저비용)"""
        from anthropic import Anthropic
        
        client = Anthropic(api_key=self.claude_key)
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=max_tokens,
            system=system_prompt or "",
            messages=[{"role": "user", "content": query}]
        )
        return response.content[0].text
    
    async def monitor_policies(self):
        """
        정책 변경 모니터링 (매일 04:00 실행)
        
        감시 항목:
        - Groq Rate Limit 변경
        - Claude 가격 변경
        - Together AI 크레딧 정책 변경
        """
        logger.info("🔍 API 정책 모니터링 시작...")
        
        changes = await self.pricing.check_for_changes()
        
        if changes:
            alert_msg = "🚨 API 정책 변경 감지!\n\n" + "\n".join(changes)
            logger.warning(alert_msg)
            await self._send_admin_alert(alert_msg)
    
    async def _send_admin_alert(self, message: str):
        """관리자에게 알림 (email/slack/etc)"""
        # 실제 구현에서는 email 또는 slack webhook 사용
        logger.info(f"📧 관리자 알림: {message}")
    
    def get_stats(self) -> Dict[str, Any]:
        """현재 통계"""
        return {
            "monthly_cost": self.monthly_cost,
            "call_counts": self.call_count,
            "providers_available": [
                p.value for p, _, _ in self.provider_chain
                if asyncio.run(self._check_availability(p))
            ],
        }


# 싱글톤 인스턴스
_router_instance: Optional[DynamicAPIRouter] = None


async def get_dynamic_router() -> DynamicAPIRouter:
    """동적 라우터 싱글톤"""
    global _router_instance
    if not _router_instance:
        _router_instance = DynamicAPIRouter()
    return _router_instance
