import logging
import re
from typing import Set

logger = logging.getLogger(__name__)

class DataSensitivityFilter:
    """
    JARVIS Core 4.0 Data Sensitivity Filter.
    Ensures that sensitive information is processed locally (Ollama) and 
    not transmitted to external cloud APIs.
    """
    
    SENSITIVE_KEYWORDS: Set[str] = {
        # Personal/Org Info
        "직원", "사원", "이름", "주민등록", "주민번호", "사번",
        "조직도", "조직구도", "팀장", "관리자", "임원",
        
        # Financial
        "연봉", "급여", "월급", "보너스", "복리후생", "기본급",
        "예산", "비용", "계약금", "거래액", "수익", "손실",
        
        # Customers/Contracts
        "고객정보", "고객명", "고객사", "계약서", "고객사 기밀",
        "거래처", "중요고객", "전략고객",
        
        # Technical/Security
        "api키", "비밀번호", "암호", "인증키", "토큰",
        "개발자", "접속정보", "데이터베이스", "서버정보",
        
        # Strategy
        "기밀", "근무평가", "평가등급", "승진", "감급",
        "권고사직", "해고", "분쟁", "소송", "클레임",
    }
    
    SENSITIVE_PATTERNS = [
        r"\b\d{6}-\d{7}\b",                              # Social Security Number (KR)
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", # Email
        r"(sk|ak|sk|AIza)[a-zA-Z0-9_\-]{20,}",           # Potential API Keys
    ]

    async def is_sensitive(self, text: str) -> bool:
        """Evaluates if text contains sensitive information."""
        if not text:
            return False
        text_lower = text.lower()
        for keyword in self.SENSITIVE_KEYWORDS:
            if keyword in text_lower:
                logger.warning(f"🚨 Sensitivity Alert: Keyword '{keyword}' detected.")
                return True
        for pattern in self.SENSITIVE_PATTERNS:
            if re.search(pattern, text):
                logger.warning(f"🚨 Sensitivity Alert: Pattern matched.")
                return True
        return False

sensitivity_filter = DataSensitivityFilter()
