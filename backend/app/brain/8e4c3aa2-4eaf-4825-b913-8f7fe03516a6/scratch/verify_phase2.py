import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(os.getcwd()) / "backend"))

async def test_phase2_verification():
    print("--- Phase 2 Verification Starting ---")
    
    # 1. HybridSettings & providers.yaml Test
    from app.utils.hybrid_settings import get_hybrid_settings
    settings = get_hybrid_settings()
    print(f"Settings: LLM_MODE = {settings.LLM_MODE}")
    print(f"Settings: LOCAL_OLLAMA_MODEL = {settings.LOCAL_OLLAMA_MODEL}")
    
    # Check if YAML override worked (if we had specific value in YAML)
    # Our YAML has 'jarvis' as model name, same as default, so it's hard to tell without logging.
    # But we saw the log '✅ providers.yaml 설정 로드 완료' in the previous step.

    # 2. SkillRegistry Registration Test
    from app.harness.skills.registry import skill_registry
    skills = skill_registry.list_skills()
    print(f"Registry: Found {len(skills)} skills: {skills}")
    
    expected_skills = ["file_skill", "backup_skill", "diag_skill"]
    for s in expected_skills:
        if s in skills:
            print(f"  OK: {s} registered.")
        else:
            print(f"  FAIL: {s} NOT registered.")

    # 3. Executor + SkillRegistry Execution Test
    from app.schemas.v4_core import SubTask
    from app.agents.executor import executor
    
    # Test file create via SkillRegistry
    task = SubTask(
        id="test_v2_1",
        title="Create Test File via Skill",
        action="create_file",
        path="AX_Vault/test_phase2_skill.txt",
        instruction="Hello SkillRegistry!"
    )
    
    print("Executor: Testing execution via SkillRegistry...")
    # This will trigger Gate 1 as well
    res = await executor.execute(task)
    
    if res.get("ok"):
        print("  OK: Executor successfully executed file_skill.")
        print(f"  Tool Result: {res.get('tool_result')}")
    else:
        print(f"  FAIL: Executor failed execution. Result: {res}")

    print("--- Phase 2 Verification Completed ---")

if __name__ == "__main__":
    asyncio.run(test_phase2_verification())
