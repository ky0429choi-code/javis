import asyncio
import logging
import sys
import os
from unittest.mock import MagicMock, AsyncMock

# Add project path to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "backend")))

# --- MOCK INFRASTRUCTURE (Must be at the top) ---
import sys
from unittest.mock import MagicMock

# Mock Cache to bypass aioredis dependency
class MockCache:
    async def init(self): pass
    async def get(self, *args, **kwargs): return None
    async def set(self, *args, **kwargs): pass

mock_cache_mod = MagicMock()
mock_cache_mod.cache_manager = MockCache()
sys.modules["app.llm.cache"] = mock_cache_mod
# -----------------------------------------------

from app.core.conductor import conductor
from app.harness.hooks_engine import hooks_engine
from app.llm.router import router as actual_router

async def mock_router_call(prompt, system=None, task_type=None, model_key=None):
    if "계획" in prompt or "구조" in prompt:
        return '{"goal": "테스트 프로젝트", "priority": "medium", "steps": [{"title": "내부 코드 작성", "action": "create_file", "path": "test_script.py", "instruction": "Hello World 출력"}]}'
    if "test_script.py" in prompt:
        return "print('Hello, JARVIS')"
    return "Mocked Response"

actual_router.call = mock_router_call
# ---------------------------

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

async def test_pipeline_execution():
    print("\n" + "="*60)
    print("JARVIS CORE 4.0 PIPELINE & TOOL INTEGRATION VERIFICATION")
    print("="*60 + "\n")

    # TEST 1: End-to-End Pipeline (Creation)
    print("--- [TEST 1: Execution Pipeline (Plan -> Execute -> Review)] ---")
    request = "test_script.py 파일을 만들어서 Hello World를 출력하는 코드를 작성해줘."
    result = await conductor.process_request(request)
    
    if result["ok"]:
        print("[SUCCESS] Pipeline completed.")
        trace = result.get("execution_trace", [])
        for entry in trace:
            print(f"Step: {entry['step']}")
            print(f"Result OK: {entry['result'].get('ok')}")
            print(f"Status: {entry['result'].get('status')}")
    else:
        print(f"[ERROR] Pipeline failed: {result.get('error')}")

    print("\n" + "-"*40 + "\n")

    # TEST 2: Security Trigger (Hooks interception)
    print("--- [TEST 2: Hook Mitigation during Execution] ---")
    # Simulate a step that tries to write to .env
    from app.schemas.v4_core import SubTask
    from app.agents.executor import executor
    
    dangerous_step = SubTask(
        title="환경 변수 탈취 시도",
        action="create_file",
        path=".env",
        instruction="비밀번호 유출 시도"
    )
    
    # Manually execute to see hook behavior
    print(f"Executing dangerous step targeting: {dangerous_step.path}")
    res = await executor.execute(dangerous_step)
    
    print(f"Execution Status: {res.get('status')}")
    if res.get("status") == "blocked":
        print("[SUCCESS] Security Hook blocked the execution successfully.")
    else:
        print("[FAILURE] Security Hook failed to block.")

    print("\n" + "="*60)
    print("VERIFICATION COMPLETE")
    print("="*60 + "\n")

if __name__ == "__main__":
    asyncio.run(test_pipeline_execution())
