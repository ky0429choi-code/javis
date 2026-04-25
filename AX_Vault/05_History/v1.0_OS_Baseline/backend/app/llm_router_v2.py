"""
JARVIS LLM Router v2.0 - 하이브리드 모드 지원
로컬 Ollama + 클라우드 API (OpenAI/Anthropic/Vertex) 통합
"""

import asyncio
import logging
import httpx
import json
from typing import Optional, Dict, Any
from app.utils.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class LocalOllamaConnector:
    """로컬 Ollama 연결"""
    
    async def call(self, prompt: str, system: str) -> Optional[str]:
        """
        Ollama API 호출
        :return: 응답 또는 None (실패 시)
        """
        try:
            url = f"{settings.intelligence_engine_url}/api/chat"
            payload = {
                "model": settings.jarvis_model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt}
                ],
                "stream": False
            }
            
            logger.debug(f"🔵 Local Ollama: {url}")
            
            async with httpx.AsyncClient(timeout=settings.ollama_timeout) as client:
                response = await client.post(url, json=payload)
                
                if response.status_code == 200:
                    result = response.json()
                    message = result.get("message", {}).get("content", "")
                    logger.info("✅ Local Ollama: 성공")
                    return message
                else:
                    logger.warning(f"❌ Local Ollama: HTTP {response.status_code}")
                    return None
                    
        except httpx.ConnectError as e:
            logger.warning(f"❌ Local Ollama: 연결 실패 - {str(e)}")
            return None
        except httpx.TimeoutException as e:
            logger.warning(f"❌ Local Ollama: 타임아웃 - {str(e)}")
            return None
        except Exception as e:
            logger.error(f"❌ Local Ollama: 예상 외 오류 - {str(e)}")
            return None


class CloudAPIConnector:
    """클라우드 API 연결 (OpenAI, Anthropic, Vertex)"""
    
    async def call(self, prompt: str, system: str, provider: Optional[str] = None) -> Optional[str]:
        """
        클라우드 API 호출
        :param provider: "openai" | "anthropic" | "vertex" | None (자동 선택)
        :return: 응답 또는 None (실패 시)
        """
        provider = provider or settings.cloud_provider
        
        if provider == "openai":
            return await self._call_openai(prompt, system)
        elif provider == "anthropic":
            return await self._call_anthropic(prompt, system)
        elif provider == "vertex":
            return await self._call_vertex(prompt, system)
        else:
            logger.error(f"Unknown cloud provider: {provider}")
            return None
    
    async def _call_openai(self, prompt: str, system: str) -> Optional[str]:
        """OpenAI API 호출"""
        if not settings.openai_api_key:
            logger.warning("⚠️ OpenAI API Key 설정 안 됨")
            return None
        
        try:
            logger.info("🟢 OpenAI API: 호출 시작")
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{settings.openai_base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                    json={
                        "model": settings.openai_model,
                        "messages": [
                            {"role": "system", "content": system},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.7
                    },
                    timeout=60.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    message = result["choices"][0]["message"]["content"]
                    logger.info("✅ OpenAI: 성공")
                    return message
                else:
                    logger.warning(f"❌ OpenAI: HTTP {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ OpenAI: {str(e)}")
            return None
    
    async def _call_anthropic(self, prompt: str, system: str) -> Optional[str]:
        """Anthropic (Claude) API 호출"""
        if not settings.anthropic_api_key:
            logger.warning("⚠️ Anthropic API Key 설정 안 됨")
            return None
        
        try:
            logger.info("🟣 Anthropic: 호출 시작")
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": settings.anthropic_api_key,
                        "anthropic-version": "2023-06-01"
                    },
                    json={
                        "model": settings.anthropic_model,
                        "max_tokens": 1024,
                        "system": system,
                        "messages": [{"role": "user", "content": prompt}]
                    },
                    timeout=60.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    message = result["content"][0]["text"]
                    logger.info("✅ Anthropic: 성공")
                    return message
                else:
                    logger.warning(f"❌ Anthropic: HTTP {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Anthropic: {str(e)}")
            return None
    
    async def _call_vertex(self, prompt: str, system: str) -> Optional[str]:
        """Google Vertex AI (Gemini) 호출"""
        # Vertex AI는 인증이 복잡하므로 나중에 구현
        logger.warning("⚠️ Vertex AI: 아직 미구현")
        return None


class DataSensitivityFilter:
    """
    민감 데이터 필터링 (⚠️ 중요: 클라우드 전송 전 필터링)
    
    정책: 민감 정보는 절대 외부 API로 전송하지 않음
    """
    
    # 한국어 민감 키워드
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
        "API키", "비밀번호", "암호", "인증키", "토큰",
        "개발자", "접속정보", "데이터베이스", "서버정보",
        
        # 기업 전략
        "기밀", "근무평가", "평가등급", "승진", "감급",
        "권고사직", "해고", "분쟁", "소송", "클레임",
    }
    
    async def is_sensitive(self, text: str) -> bool:
        """텍스트가 민감 정보 포함 여부 판단"""
        text_lower = text.lower()
        for keyword in self.SENSITIVE_KEYWORDS:
            if keyword in text_lower:
                logger.warning(f"🚨 민감 키워드 감지: '{keyword}'")
                return True
        return False
    
    async def should_use_local_only(self, prompt: str, system: str) -> bool:
        """로컬 전용 처리 필요 여부 판단"""
        combined_text = f"{prompt}|{system}".lower()
        return await self.is_sensitive(combined_text)


class LLMRouter:
    """
    JARVIS LLM Router v2.0
    로컬 Ollama와 클라우드 API를 지능적으로 라우팅
    
    ⚠️ 보안 정책:
    - 민감 데이터는 항상 로컬 Ollama만 사용
    - 클라우드 폴백 전에 데이터 필터링 수행
    """
    
    _instance = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if not cls._instance:
            cls._instance = super(LLMRouter, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self.local_connector = LocalOllamaConnector()
        self.cloud_connector = CloudAPIConnector()
        self.data_filter = DataSensitivityFilter()
        self._initialized = True
    
    async def call(self, prompt: str, system: str) -> str:
        """
        하이브리드 LLM 호출
        
        모드별 동작:
        - "local": 로컬 Ollama만 시도
        - "cloud": 클라우드 API만 사용
        - "hybrid": 로컬 시도 → 실패 시 클라우드
        - "offline": 오프라인 응답만
        """
        mode = settings.llm_mode
        
        if mode == "offline":
            return self._offline_response(prompt)
        
        if mode == "local":
            return await self._call_local_with_retry(prompt, system)
        
        if mode == "cloud":
            return await self._call_cloud_with_retry(prompt, system)
        
        if mode == "hybrid":
            return await self._call_hybrid(prompt, system)
        
        logger.error(f"Unknown LLM mode: {mode}")
        return self._offline_response(prompt)
    
    async def _call_local_with_retry(self, prompt: str, system: str) -> str:
        """로컬 Ollama 재시도 로직"""
        for attempt in range(settings.ollama_retry_attempts):
            logger.info(f"📡 Local attempt {attempt + 1}/{settings.ollama_retry_attempts}")
            
            result = await self.local_connector.call(prompt, system)
            if result:
                return result
            
            if attempt < settings.ollama_retry_attempts - 1:
                await asyncio.sleep(settings.ollama_retry_delay)
        
        return "❌ 로컬 AI 엔진(Ollama)과 연결할 수 없습니다."
    
    async def _call_cloud_with_retry(self, prompt: str, system: str) -> str:
        """클라우드 API 재시도 로직"""
        result = await self.cloud_connector.call(prompt, system)
        if result:
            return result
        
        return "❌ 클라우드 AI 서비스를 사용할 수 없습니다. API 키를 확인하세요."
    
    async def _call_hybrid(self, prompt: str, system: str) -> str:
        """
        하이브리드: 로컬 시도 → 실패 시 클라우드 (⚠️ 민감 데이터 필터링 적용)
        
        보안 정책:
        1. 로컬 시도 (모든 데이터 허용)
        2. 로컬 실패 + 민감 데이터 없음 → 클라우드 시도
        3. 로컬 실패 + 민감 데이터 있음 → 로컬 재시도 또는 에러 반환 (절대 클라우드 전송 금지)
        """
        logger.info("🔄 Hybrid mode: 로컬 시도")
        
        # 스텝 1: 로컬 시도 (재시도 포함)
        for attempt in range(settings.ollama_retry_attempts):
            logger.info(f"📡 Local attempt {attempt + 1}/{settings.ollama_retry_attempts}")
            
            result = await self.local_connector.call(prompt, system)
            if result:
                logger.info("✅ Hybrid: 로컬 성공")
                return result
            
            if attempt < settings.ollama_retry_attempts - 1:
                await asyncio.sleep(settings.ollama_retry_delay)
        
        # 스텝 2: 로컬 실패 → 민감 데이터 검사
        logger.warning("⚠️ Hybrid: 로컬 실패")
        
        is_sensitive = await self.data_filter.should_use_local_only(prompt, system)
        
        if is_sensitive:
            logger.error("🚨 Hybrid: 민감 데이터 감지 → 클라우드 전송 차단")
            return (
                "⚠️ 민감 정보가 포함된 요청입니다.\n"
                "로컬 AI 엔진을 사용해야 하지만 현재 사용 불가입니다.\n"
                "나중에 다시 시도해주세요 (외부 API로 전송 불가)."
            )
        
        # 스텝 3: 민감 데이터 없으면 클라우드 폴백
        logger.info("ℹ️ Hybrid: 민감 데이터 없음 → 클라우드로 폴백 시도")
        
        result = await self.cloud_connector.call(prompt, system)
        if result:
            logger.info("✅ Hybrid: 클라우드 성공")
            return result
        
        # 모두 실패
        logger.error("❌ Hybrid: 모든 AI 엔진 실패")
        return "❌ AI 엔진을 사용할 수 없습니다. 나중에 다시 시도해주세요."
    
    def _offline_response(self, prompt: str) -> str:
        """오프라인 응답"""
        logger.warning("⚠️ Offline mode: AI 엔진 사용 불가")
        return "💤 오프라인 모드에서는 AI 엔진을 사용할 수 없습니다."


# 싱글톤 인스턴스
router = LLMRouter()


# ==================== 테스트 및 유틸리티 ====================

async def test_local_connection() -> bool:
    """로컬 Ollama 연결 테스트"""
    connector = LocalOllamaConnector()
    result = await connector.call("테스트", "You are JARVIS.")
    return result is not None


async def test_cloud_connection(provider: str = "openai") -> bool:
    """클라우드 API 연결 테스트"""
    connector = CloudAPIConnector()
    result = await connector.call("테스트", "You are JARVIS.", provider)
    return result is not None


async def test_all_connections() -> Dict[str, bool]:
    """모든 연결 상태 테스트"""
    return {
        "local": await test_local_connection(),
        "openai": await test_cloud_connection("openai"),
        "anthropic": await test_cloud_connection("anthropic"),
    }
