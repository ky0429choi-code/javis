"""
BaseSkill - 모든 Skill의 기본 클래스
"""

import logging
from typing import Dict, Any
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class BaseSkill(ABC):
    """모든 Skill의 기본 인터페이스"""
    
    name: str = "BaseSkill"
    description: str = "Base skill interface"
    version: str = "1.0"
    
    async def execute(self, task: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Skill 실행
        
        Args:
            task: 작업 정의
            {
                "id": 1,
                "title": "할 일",
                "description": "상세 설명",
                "parameters": {...}
            }
            
            context: 실행 컨텍스트
            {
                "user_preferences": {...},
                "project_context": {...},
                "previous_results": {...}
            }
        
        Returns:
            {
                "ok": True/False,
                "result": "결과",
                "metadata": {...}
            }
        """
        raise NotImplementedError("execute() must be implemented")
    
    async def validate_input(self, task: Dict[str, Any]) -> tuple[bool, str]:
        """
        입력 유효성 검사
        
        Returns:
            (valid: bool, error_message: str)
        """
        return True, ""
    
    async def estimate_duration(self, task: Dict[str, Any]) -> float:
        """예상 소요 시간 (초 단위)"""
        return 60.0
    
    def _create_result(self, ok: bool, result: Any = None, error: str = None, metadata: Dict = None) -> Dict[str, Any]:
        """표준 결과 객체 생성"""
        return {
            "ok": ok,
            "result": result,
            "error": error,
            "skill": self.name,
            "metadata": metadata or {}
        }
