import asyncio
from app.core.conductor import conductor

async def test_conductor():
    print("--- Testing Chat ---")
    res = await conductor.chat("안녕하세요 자비스. 새로운 보고서 생성을 요청할게요.")
    print(f"Chat Response: {res['message'][:100]}...")
    
    print("\n--- Testing File Action Request ---")
    req = conductor.request_file_action(
        action_type="create_file",
        target_path="./test_output.txt",
        reason="테스트 파일 생성",
        content="Hello from ported JARVIS Core!"
    )
    print(f"Request Created: {req['request_id']} Status: {req['status']}")
    
    print("\n--- Testing Approval Resolution ---")
    resolved = conductor.resolve_approval(req['request_id'], "approve")
    print(f"Resolution Result: {resolved['status']}")
    if 'execution_result' in resolved:
        print(f"Execution Output: {resolved['execution_result']}")

if __name__ == "__main__":
    asyncio.run(test_conductor())
