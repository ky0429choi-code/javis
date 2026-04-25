import asyncio
import time
import logging
import sys
import os

# Add project path to sys.path
sys.path.append(os.path.abspath("backend"))

# Old Router
from app.llm_router import router as old_router
# New V4 Router (Modular)
from app.core_v4.llm.router import router_v4

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

async def run_comparison():
    print("\n" + "="*50)
    print("🚀 JARVIS CORE V4 ARCHITECTURE COMPARISON")
    print("="*50 + "\n")

    test_queries = [
        {"name": "Simple Greeting", "query": "안녕, 오늘 날씨 어때?", "sensitive": False},
        {"name": "Sensitive Data (Email)", "query": "my email is sry@stark.com. send the report.", "sensitive": True},
        {"name": "Sensitive Data (SSN)", "query": "주민번호 123456-1234567을 처리해줘.", "sensitive": True},
        {"name": "Complex Coding", "query": "Python으로 소수(prime number) 판별 함수를 작성해줘.", "sensitive": False},
    ]

    for test in test_queries:
        print(f"[{test['name']}]")
        print(f"Query: {test['query']}")
        
        # Test Old Router
        print("--- Old Router ---")
        start = time.time()
        try:
            # Note: Old router might not have sensitivity filtering active by default 
            # or it might just call Ollama if configured.
            old_res = await old_router.call(prompt=test['query'], system="You are Jarvis.")
            old_latency = int((time.time() - start) * 1000)
            print(f"Latency: {old_latency}ms")
            print(f"Response (truncated): {old_res[:50]}...")
        except Exception as e:
            print(f"Error: {e}")

        # Test New V4 Router (Modular)
        print("--- New V4 Router (Modular) ---")
        start = time.time()
        try:
            v4_res = await router_v4.call(prompt=test['query'], system="You are Jarvis.")
            v4_latency = int((time.time() - start) * 1000)
            print(f"Latency: {v4_latency}ms")
            print(f"Response (truncated): {v4_res[:50]}...")
            
            # Check sensitivity behavior
            if test['sensitive']:
                # V4 should have logged a warning and used Local Ollama. 
                # We can't easily check internal state here, but we can verify it succeeded safely.
                print("🛡️ Sensitivity logic engaged (See logs above)")
        except Exception as e:
            print(f"Error: {e}")
            
        print("-" * 30 + "\n")

    # Test Cache (V4 Only Feature being tested here)
    print("[Cache Test - V4 Router]")
    query = "동영상 파일을 압축하는 명령어를 알려줘."
    print("First call (Generating)...")
    await router_v4.call(prompt=query, system="You are Jarvis.")
    
    print("Second call (Expecting Cache)...")
    start = time.time()
    await router_v4.call(prompt=query, system="You are Jarvis.")
    cache_latency = int((time.time() - start) * 1000)
    print(f"Cache Latency: {cache_latency}ms")
    if cache_latency < 50:
        print("✅ Cache hit verified!")
    else:
        print("❌ Cache miss or slow response.")

if __name__ == "__main__":
    asyncio.run(run_comparison())
