"""
Skill Registry - Skill 관리 및 실행
"""

import logging
from typing import Dict, Any, Optional
from app.harness.skills.base_skill import BaseSkill

logger = logging.getLogger(__name__)


class SkillRegistry:
    """Skill 등록 및 관리"""
    
    _instance = None
    
    def __new__(cls):
        if not cls._instance:
            cls._instance = super(SkillRegistry, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.skills: Dict[str, BaseSkill] = {}
        self._register_builtin_skills()
        self._initialized = True
        logger.info("SkillRegistry initialized with built-in skills")
    
    def _register_builtin_skills(self) -> None:
        """빌트인 스킬 등록"""
        from app.harness.skills.file_skill import FileSkill
        from app.harness.skills.backup_skill import BackupSkill
        from app.harness.skills.diag_skill import DiagnosticSkill
        from app.harness.skills.advanced.code_gen_skill import CodeGenSkill
        from app.harness.skills.advanced.search_skill import SearchSkill
        from app.harness.skills.advanced.memory_skill import MemorySkill
        
        self.register(FileSkill())
        self.register(BackupSkill())
        self.register(DiagnosticSkill())
        self.register(CodeGenSkill())
        self.register(SearchSkill())
        self.register(MemorySkill())
    
    def register(self, skill: BaseSkill) -> None:
        """Skill 등록"""
        self.skills[skill.name] = skill
        logger.info(f"Skill registered: {skill.name}")
    
    async def get_skill(self, name: str) -> Optional[BaseSkill]:
        """Skill 조회"""
        skill = self.skills.get(name)
        if not skill:
            logger.warning(f"Skill not found: {name}")
        return skill
    
    async def execute(self, skill_name: str, task: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Skill 실행"""
        skill = await self.get_skill(skill_name)
        
        if not skill:
            return {
                "ok": False,
                "error": f"Skill not found: {skill_name}",
                "skill": skill_name
            }
        
        try:
            # 입력 검증
            is_valid, error_msg = await skill.validate_input(task)
            if not is_valid:
                return {
                    "ok": False,
                    "error": f"Validation failed: {error_msg}",
                    "skill": skill_name
                }
            
            # Skill 실행
            result = await skill.execute(task, context or {})
            return result
            
        except Exception as e:
            logger.error(f"Skill execution error ({skill_name}): {e}")
            return {
                "ok": False,
                "error": str(e),
                "skill": skill_name
            }
    
    def list_skills(self) -> list:
        """등록된 모든 Skill 목록"""
        return list(self.skills.keys())
    
    def get_skill_info(self, name: str) -> Dict[str, Any]:
        """Skill 정보 조회"""
        skill = self.skills.get(name)
        if not skill:
            return {"error": f"Skill not found: {name}"}
        
        return {
            "name": skill.name,
            "description": skill.description,
            "version": skill.version
        }


# 싱글톤 인스턴스
skill_registry = SkillRegistry()
