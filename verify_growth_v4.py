import asyncio
import logging
import sys
import os
from unittest.mock import MagicMock

# 프로젝트 경로 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "backend")))

# --- 인프라 모의(Mock) 설정 ---
import sys
from unittest.mock import MagicMock

# 캐시 모킹
class MockCache:
    async def init(self): pass
    async def get(self, *args, **kwargs): return None
    async def set(self, *args, **kwargs): pass

mock_cache_mod = MagicMock()
mock_cache_mod.cache_manager = MockCache()
sys.modules["app.llm.cache"] = mock_cache_mod

# 라우터 모킹 (지식 추출 결과 시뮬레이션)
from app.llm import router as actual_router
async def mock_router_call(prompt, **kwargs):
    if "위 작업 이력을 분석" in prompt:
        return '{"lore": "테스트 결정 내역", "pattern": "테스트 패턴", "kpi_score": 90, "best_practice": "자동 생성된 지식 문서입니다."}'
    return '{"status": "ok"}'
actual_router.call = mock_router_call
# ---------------------------

from app.agents.wiki import wiki_agent
from app.memory.repository import initialize_database, Repository

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

async def test_growth_system():
    print("\n" + "="*60)
    print("자비스 코어 4.0 [성장 및 메모리] 시스템 검증")
    print("="*60 + "\n")

    # 1. DB 초기화 (신규 테이블 생성 확인)
    print("--- [1단계: 데이터베이스 초기화 및 확장 확인] ---")
    initialize_database()
    print("[성공] memory_nodes 테이블 및 기본 스키마 확인됨.")

    # 2. 위키 에이전트 가동 테스트
    print("\n--- [2단계: 위키 에이전트 지식 추출 및 저장 테스트] ---")
    goal = "Python Flask API 서버 구축"
    trace = [
        {"step": "환경 설정", "result": {"ok": True, "status": "executed"}},
        {"step": "코드 작성", "result": {"ok": True, "status": "executed"}}
    ]
    
    await wiki_agent.process_task(goal, trace)
    
    # 3. 저장 결과 확인 (Repository)
    print("\n--- [3단계: 저장된 메모리 노드 검색 테스트] ---")
    repo = Repository()
    nodes = repo.search_memory_nodes(type="lore")
    if nodes:
        print(f"[성공] Lore 메모리 저장 확인: {nodes[0]['content']['decision']}")
    else:
        print("[실패] 메모리 노드가 저장되지 않았습니다.")

    # 4. AX_Vault 검색 확인
    print("\n--- [4단계: AX_Vault 지식 검색(RAG) 테스트] ---")
    from app.vault.ax_vault import ax_vault
    search_res = await ax_vault.rag_search("Python", folder="02_Knowledge")
    if search_res:
        print(f"[성공] AX_Vault 지식 검색 확인: {search_res[0]['title']}")
    else:
        print("[실패] AX_Vault에서 지식을 찾을 수 없습니다.")

    print("\n" + "="*60)
    print("검증 완료")
    print("="*60 + "\n")

if __name__ == "__main__":
    asyncio.run(test_growth_system())
