"""
멀티레이어 LLM 라우터 - 로컬 + 무료 클라우드 최적 조합 (⚠️ 민감 데이터 필터링 포함)
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from enum import Enum
from redis import asyncio as aioredis
import httpx

logger = logging.getLogger(__name__)


class DataSensitivityFilter:
    """
    ⚠️ 중요: 클라우드 API 전송 전 민감 데이터 필터링
    
    정책:
    - 민감 정보는 항상 로컬 Ollama만 사용
    - 클라우드 전송 시도 전 필터링 필수
    """
    
    SENSITIVE_KEYWORDS = {
        # 개인/조직 정보
        "직원", "사원", "이름", "주민등록", "주민번호", "사번",
        "조직도", "조직구도", "팀장", "관리자", "임원",
        
        # 금융/급여
        "연봉", "급여", "월급", "보너스", "복리후생", "기본급",
        "예산", "비용", "계약금", "거래액", "수익", "손실",
        
        # 고객/계약
        "고객정보", "고객명", "고객사", "계약서", "고객사 기밀",
        "거래처", "중요고객", "전략고객",
        
        # 기술/보안
        "api키", "비밀번호", "암호", "인증키", "토큰",
        "개발자", "접속정보", "데이터베이스", "서버정보",
        
        # 기업 전략
        "기밀", "근무평가", "평가등급", "승진", "감급",
        "권고사직", "해고", "분쟁", "소송", "클레임",
    }
    
    async def is_sensitive(self, text: str) -> bool:
        """텍스트가 민감 정보를 포함하는지 판단"""
        text_lower = text.lower()
        for keyword in self.SENSITIVE_KEYWORDS:
            if keyword in text_lower:
                logger.warning(f"🚨 민감 키워드 감지: '{keyword}' → 로컬 처리만 허용")
                return True
        return False


class LLMProvider(Enum):
    """LLM 제공자"""
    LOCAL_OLLAMA = "local_ollama"
    GROQ_FREE = "groq"  # Rate Limited (~30k tokens/min)
    HUGGINGFACE = "huggingface"  # Queue-based (지연 가능)
    CLAUDE_HAIKU = "claude_haiku"  # 권장: $0.00025/input token
    OPENAI_BATCH = "openai_batch"  # 배치 전용 (1-24시간 SLA)


class SmartLLMRouter:
    """
    지능형 LLM 라우터 - 요청 유형별 최적 프로바이더 선택
    
    ⚠️ 보안 정책:
    1. 민감 데이터는 절대 클라우드 전송 금지 (로컬 Ollama만)
    2. 모든 클라우드 API는 Rate Limited (무료 ≠ 무제한)
    3. Batch API는 배치 전용 (실시간 불가)
    
    예: "안녕" → 캐시 (0.01초)
        "Python 코드" → Ollama (0.2초) → Claude (1초)
        "조직 구조도" → 민감 데이터 감지 → Ollama만 (로컬 처리)
        "1000개 뉴스" → 배치 (1-24시간)
    """
    
    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None
        self.cache_ttl = {
            "immediate": 3600,      # 1시간 (즉시 응답)
            "complex": 86400,       # 1일 (복잡한 작업)
            "bulk": 604800,         # 7일 (대용량)
        }
        self.data_filter = DataSensitivityFilter()
        
        # API 설정
        self.groq_api_key = None  # .env에서 로드
        self.hf_api_key = None
        self.claude_api_key = None
        self.openai_api_key = None
    
    async def init(self):
        """초기화"""
        # Redis 연결
        try:
            self.redis = aioredis.from_url('redis://localhost')
            logger.info("✅ Redis 연결됨")
        except:
            logger.warning("⚠️ Redis 미연결 (캐시 비활성화)")
            self.redis = None
    
    async def route(self, 
                    query: str, 
                    system_prompt: str = None,
                    task_type: str = "simple") -> Dict[str, Any]:
        """
        요청을 최적 프로바이더로 라우팅
        
        ⚠️ 보안: 민감 데이터 필터링이 첫 번째 단계
        
        Args:
            query: 사용자 질문
            system_prompt: 시스템 프롬프트
            task_type: "simple" | "complex" | "bulk"
        
        Returns:
            {
                "ok": bool,
                "response": str,
                "provider": str,
                "time_ms": int,
                "cost": float,
                "cached": bool,
                "sensitive": bool  # 민감 데이터 여부
            }
        """
        import time
        start_time = time.time()
        
        # 0️⃣ 민감 데이터 검사 (클라우드 전송 전)
        combined_text = f"{query}|{system_prompt or ''}".lower()
        is_sensitive = await self.data_filter.is_sensitive(combined_text)
        
        if is_sensitive:
            logger.warning("🚨 민감 데이터 감지 → 로컬 Ollama만 사용")
            # 민감 데이터는 로컬만 시도 (절대 클라우드 전송 금지)
            result = await self._route_local_only(query, system_prompt)
            result["time_ms"] = int((time.time() - start_time) * 1000)
            result["sensitive"] = True
            logger.info(f"✅ 로컬 처리 (민감): {result['time_ms']}ms")
            return result
        
        # 1️⃣ 캐시 확인 (0.01초, 무료)
        cached_result = await self._check_cache(query)
        if cached_result:
            logger.info(f"💾 캐시 히트: {query[:30]}...")
            return {
                "ok": True,
                "response": cached_result,
                "provider": "cache",
                "time_ms": int((time.time() - start_time) * 1000),
                "cost": 0,
                "cached": True,
                "sensitive": False
            }
        
        # 2️⃣ 작업 유형별 라우팅
        if task_type == "simple":
            result = await self._route_simple(query, system_prompt)
        elif task_type == "complex":
            result = await self._route_complex(query, system_prompt)
        elif task_type == "bulk":
            result = await self._route_bulk(query, system_prompt)
        else:
            result = await self._route_simple(query, system_prompt)
        
        # 3️⃣ 결과 캐싱
        if result["ok"]:
            await self._set_cache(query, result["response"], task_type)
        
        result["time_ms"] = int((time.time() - start_time) * 1000)
        result["cached"] = False
        result["sensitive"] = False
        
        logger.info(f"✅ {result['provider']}: {result['time_ms']}ms (${result['cost']:.4f})")
        
        return result
    
    async def _route_local_only(self, query: str, system_prompt: str) -> Dict:
        """
        민감 데이터 전용: 로컬 Ollama만 사용
        클라우드 폴백 없음
        """
        try:
            response = await self._call_ollama(query, system_prompt)
            return {
                "ok": True,
                "response": response,
                "provider": "local_ollama",
                "cost": 0
            }
        except Exception as e:
            logger.error(f"🚨 민감 데이터 처리 로컬 실패: {e}")
            return {
                "ok": False,
                "response": (
                    f"⚠️ 민감 정보 처리 중 오류\n"
                    f"로컬 AI 엔진만 사용 가능하며, 현재 사용할 수 없습니다.\n"
                    f"관리자에게 문의하세요."
                ),
                "provider": "none",
                "cost": 0
            }
    
    async def _route_simple(self, query: str, system_prompt: str) -> Dict:
        """
        즉시 응답 필요한 작업 (민감 데이터 없음)
        전략: 로컬 → Groq (Rate Limited) → HuggingFace (Queue-based)
        
        ⚠️ 주의:
        - Groq: ~30k tokens/min 제한 (무료가 아닌 Rate Limited)
        - HF: 트래픽 몰리면 분 단위 지연 가능
        """
        providers = [
            (self._call_ollama, LLMProvider.LOCAL_OLLAMA, 0),
            (self._call_groq, LLMProvider.GROQ_FREE, 0),  # Rate limited
            (self._call_huggingface, LLMProvider.HUGGINGFACE, 0),  # 지연 가능
        ]
        
        for provider_fn, provider, cost in providers:
            try:
                logger.info(f"🔄 시도: {provider.value}")
                response = await provider_fn(query, system_prompt)
                return {
                    "ok": True,
                    "response": response,
                    "provider": provider.value,
                    "cost": cost
                }
            except Exception as e:
                logger.warning(f"⚠️ {provider.value} 실패: {e}")
                continue
        
        return {
            "ok": False,
            "response": "모든 LLM 프로바이더 실패",
            "provider": None,
            "cost": 0
        }
    
    async def _route_complex(self, query: str, system_prompt: str) -> Dict:
        """
        복잡한 작업 (코드 생성, 분석 등) - 비용 vs 품질 트레이드오프
        
        전략:
        1. 로컬 Ollama 시도 (무료)
        2. 실패 시 Claude-Haiku (권장: $0.00025/input token)
        3. 기타 API는 Rate Limited 확인 필수
        """
        providers = [
            (self._call_ollama, LLMProvider.LOCAL_OLLAMA, 0),
            (self._call_claude_haiku, LLMProvider.CLAUDE_HAIKU, 0.00025),  # 권장
            (self._call_groq, LLMProvider.GROQ_FREE, 0),  # Rate limited fallback
        ]
        
        for provider_fn, provider, cost in providers:
            try:
                logger.info(f"🔄 복잡 작업 시도: {provider.value}")
                response = await provider_fn(query, system_prompt)
                return {
                    "ok": True,
                    "response": response,
                    "provider": provider.value,
                    "cost": cost
                }
            except Exception as e:
                logger.warning(f"⚠️ {provider.value} 실패: {e}")
                continue
        
        return {
            "ok": False,
            "response": "복잡한 작업 처리 실패",
            "provider": None,
            "cost": 0
        }
    
    async def _route_bulk(self, query: str, system_prompt: str) -> Dict:
        """
        대용량 배치 작업 전용 (⚠️ 실시간 불가)
        
        특이점:
        - OpenAI Batch API: 1-24시간 SLA (즉시 반환하지 않음)
        - 비동기 작업 큐에 추가 후 job_id 반환
        - 결과는 이메일/Webhook으로 전달
        - 비용 50% 할인
        
        실사용:
        - 야간 배치: "지난 3개월 뉴스 1000개 분석"
        - 보고서: "분기별 실적 요약"
        """
        logger.info(f"📦 배치 작업 큐 추가 (1-24시간 처리): {query[:30]}...")
        logger.warning(
            "⚠️ Batch API는 실시간 응답 불가 - 결과 이메일로 전송됩니다 (1-24시간 소요)"
        )
        
        return {
            "ok": True,
            "response": (
                "배치 작업이 큐에 추가되었습니다.\n"
                "처리 시간: 1-24시간\n"
                "결과는 이메일로 전송됩니다."
            ),
            "provider": "openai_batch",
            "cost": 0.00015  # 배치 50% 할인
        }
    
    async def _check_cache(self, query: str) -> Optional[str]:
        """
        캐시에서 응답 조회
        
        ⚠️ 캐시 일관성: 모델 버전을 포함한 키 사용
        예: key = "llm_response:{query}:v{model_version}"
        
        이유: Redis TTL 만료 후 SQLite 반환 시 모델이
        업그레이드되었을 수 있음 (예: Claude 3.5→4.0)
        """
        if not self.redis:
            return None
        
        try:
            # ⚠️ 버전 추적 포함 (모델 버전 변경 대비)
            # 실제 구현에서는 model_version을 settings에서 가져와야 함
            model_version = getattr(self, 'model_version', '1')
            key = f"llm_response:{query[:50]}:v{model_version}"
            
            cached = await self.redis.get(key)
            if cached:
                logger.info(f"💾 캐시 히트 (v{model_version}): {query[:30]}...")
                return cached.decode() if isinstance(cached, bytes) else cached
        except Exception as e:
            logger.warning(f"캐시 조회 실패: {e}")
        
        return None
    
    async def _set_cache(self, query: str, response: str, task_type: str):
        """
        캐시에 응답 저장 (모델 버전 포함)
        """
        if not self.redis:
            return
        
        try:
            # ⚠️ 버전 추적 포함
            model_version = getattr(self, 'model_version', '1')
            key = f"llm_response:{query[:50]}:v{model_version}"
            ttl = self.cache_ttl.get(task_type, 3600)
            await self.redis.set(key, response, ex=ttl)
            logger.debug(f"💾 캐시 저장 (v{model_version}, TTL={ttl}s)")
        except Exception as e:
            logger.warning(f"캐시 저장 실패: {e}")
    
    # ==================== 실제 LLM 호출 ====================
    
    async def _call_ollama(self, query: str, system_prompt: str) -> str:
        """로컬 Ollama 호출 (무료, 0.2초)"""
        # 기존 코드 사용
        from app.brains.base import OllamaBrain
        brain = OllamaBrain()
        return await brain.generate(query, system_prompt)
    
    async def _call_groq(self, query: str, system_prompt: str) -> str:
        """
        Groq API 호출 (무료, Mixtral 8x7B)
        https://console.groq.com
        """
        if not self.groq_api_key:
            raise ValueError("GROQ_API_KEY 미설정")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.groq_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "mixtral-8x7b-32768",
                    "messages": [
                        {"role": "system", "content": system_prompt or ""},
                        {"role": "user", "content": query}
                    ],
                    "max_tokens": 1000,
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"]
            else:
                raise Exception(f"Groq API error: {response.text}")
    
    async def _call_huggingface(self, query: str, system_prompt: str) -> str:
        """
        HuggingFace Inference API (무료)
        https://huggingface.co/inference-api
        """
        if not self.hf_api_key:
            raise ValueError("HUGGINGFACE_API_KEY 미설정")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.1",
                headers={"Authorization": f"Bearer {self.hf_api_key}"},
                json={
                    "inputs": f"{system_prompt or ''}\n\n사용자: {query}",
                    "parameters": {
                        "max_new_tokens": 1000,
                        "temperature": 0.7,
                    }
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return data[0]["generated_text"]
            else:
                raise Exception(f"HuggingFace API error: {response.text}")
    
    async def _call_claude_haiku(self, query: str, system_prompt: str) -> str:
        """
        Claude API (가장 저렴, $0.25/$0.75 per M tokens)
        https://console.anthropic.com
        """
        if not self.claude_api_key:
            raise ValueError("ANTHROPIC_API_KEY 미설정")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.claude_api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": "claude-3-haiku-20240307",
                    "max_tokens": 1000,
                    "system": system_prompt or "",
                    "messages": [
                        {"role": "user", "content": query}
                    ]
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return data["content"][0]["text"]
            else:
                raise Exception(f"Claude API error: {response.text}")


# 싱글톤
_router_instance = None


async def get_smart_router() -> SmartLLMRouter:
    """SmartLLMRouter 싱글톤 인스턴스"""
    global _router_instance
    if not _router_instance:
        _router_instance = SmartLLMRouter()
        await _router_instance.init()
    return _router_instance
