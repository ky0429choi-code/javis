#!/usr/bin/env python
"""
JARVIS v5 시스템 검증 스크립트
패치 적용 및 모듈 구조 확인
"""
import os
import sys
import asyncio

# 루트 경로 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_imports():
    """모든 모듈이 제대로 import되는지 확인"""
    print("[테스트] 모듈 구조 확인 중...")
    try:
        from core.planner import Planner
        print("  ✅ core.planner 로드됨")
        
        from core.orchestrator import Orchestrator
        print("  ✅ core.orchestrator 로드됨")
        
        from core.llm_router import LLMRouter
        print("  ✅ core.llm_router 로드됨")
        
        from core.bootstrap import run_bootstrap
        print("  ✅ core.bootstrap 로드됨")
        
        from core.hooks import HookManager, HookMode
        print("  ✅ core.hooks 로드됨")
        
        from core.tool_registry import ToolRegistry
        print("  ✅ core.tool_registry 로드됨")
        
        from api.main import app
        print("  ✅ api.main (FastAPI 앱) 로드됨")
        
        return True
    except Exception as e:
        print(f"  ❌ 에러: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_planner():
    """Planner 동작 테스트"""
    print("\n[테스트] Planner 동작 확인...")
    try:
        from core.planner import Planner
        from core.llm_router import LLMRouter
        
        router = LLMRouter()
        planner = Planner(router)
        
        # 간단한 계획 생성 테스트 (LLM 없이 fallback)
        test_input = "테스트: 파일을 생성해줘"
        plan = planner.create_plan(test_input)
        
        print(f"  ✅ 계획 생성됨:")
        print(f"     - 목표: {plan.goal}")
        print(f"     - 단계 수: {len(plan.steps)}")
        if plan.steps:
            print(f"     - 첫 번째 단계: {plan.steps[0].action}")
        
        return True
    except Exception as e:
        print(f"  ❌ 에러: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_orchestrator():
    """Orchestrator 동작 테스트"""
    print("\n[테스트] Orchestrator 동작 확인...")
    try:
        from core.orchestrator import Orchestrator
        from core.planner import Plan, Step
        from core.tool_registry import ToolRegistry
        
        registry = ToolRegistry()
        orch = Orchestrator(registry)
        
        # 테스트 계획
        plan = Plan(
            goal="테스트 작업",
            steps=[
                Step(
                    id=1,
                    action="test_action",
                    tool=None,
                    args={"test": "value"},
                    depends_on=[]
                )
            ]
        )
        
        result = await orch.run(plan)
        print(f"  ✅ 오케스트레이션 동작됨:")
        print(f"     - 목표: {result.goal}")
        print(f"     - 단계 완료: {len(result.step_results)}")
        print(f"     - 성공 여부: {result.success}")
        
        return True
    except Exception as e:
        print(f"  ❌ 에러: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_fastapi_routes():
    """FastAPI 라우트 확인"""
    print("\n[테스트] FastAPI 라우트 확인...")
    try:
        from api.main import app
        
        routes = [
            {"path": route.path, "methods": route.methods}
            for route in app.routes
        ]
        
        print(f"  ✅ 등록된 라우트 {len(routes)}개:")
        for route in routes:
            if "/api" in route["path"]:
                print(f"     - {route['path']} {route['methods']}")
        
        return True
    except Exception as e:
        print(f"  ❌ 에러: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    print("=" * 60)
    print("JARVIS v5 시스템 검증")
    print("=" * 60)
    
    tests = [
        ("모듈 import", test_imports),
        ("Planner", test_planner),
        ("Orchestrator", test_orchestrator),
        ("FastAPI 라우트", test_fastapi_routes),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = await test_func()
            results.append((name, result))
        except Exception as e:
            print(f"  ❌ 테스트 실패: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 60)
    print("테스트 결과 요약")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 통과" if result else "❌ 실패"
        print(f"  {name}: {status}")
    
    print(f"\n총 {passed}/{total} 테스트 통과")
    
    if passed == total:
        print("\n🎉 모든 테스트 통과! 시스템이 정상 작동합니다.")
        print("\n다음 단계:")
        print("  1. 백엔드 실행: python -m uvicorn api.main:app --host 127.0.0.1 --port 8000")
        print("  2. 프론트엔드 실행: cd frontend && npm run dev")
        print("  3. 브라우저: http://localhost:5173")
    else:
        print("\n⚠️  일부 테스트 실패. 위의 에러 메시지를 확인하세요.")
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
