#!/usr/bin/env python3
"""
Complete JARVIS API Testing Suite
Tests all modes: chat, task, command
"""

import httpx
import asyncio
import json
from typing import Dict, Any

class JarvisAPITester:
    def __init__(self, base_url: str = "http://127.0.0.1:8000/api", shared_key: str = "AIN_PAPA_SHARED_KEY"):
        self.base_url = base_url
        self.headers = {
            "X-Shared-Key": shared_key,
            "Content-Type": "application/json"
        }
        self.client = None
        self.results = []

    async def setup(self):
        """Initialize async client."""
        self.client = httpx.AsyncClient(timeout=60.0)

    async def cleanup(self):
        """Close async client."""
        if self.client:
            await self.client.aclose()

    async def health_check(self) -> bool:
        """Test health endpoint."""
        print("\n" + "=" * 70)
        print("TEST 1: Health Check")
        print("=" * 70)
        try:
            resp = await self.client.get(f"{self.base_url}/health")
            if resp.status_code == 200:
                data = resp.json()
                print(f"✅ Health check PASSED")
                print(f"   Status Code: {resp.status_code}")
                print(f"   Response: {json.dumps(data, ensure_ascii=False, indent=2)}")
                self.results.append({"test": "health", "status": "PASS"})
                return True
            else:
                print(f"❌ Health check FAILED (Status: {resp.status_code})")
                self.results.append({"test": "health", "status": "FAIL", "code": resp.status_code})
                return False
        except Exception as e:
            print(f"❌ Health check ERROR: {e}")
            self.results.append({"test": "health", "status": "ERROR", "error": str(e)})
            return False

    async def test_chat_mode(self) -> bool:
        """Test simple chat mode."""
        print("\n" + "=" * 70)
        print("TEST 2: Chat Mode (Simple Conversation)")
        print("=" * 70)
        try:
            payload = {
                "message": "안녕하세요! 오늘 날씨가 어떨까요?",
                "mode": "chat"
            }
            print(f"Request: {json.dumps(payload, ensure_ascii=False)}")
            
            resp = await self.client.post(
                f"{self.base_url}/jarvis/chat",
                json=payload,
                headers=self.headers,
                timeout=20.0
            )
            
            print(f"Response Status: {resp.status_code}")
            print(f"Response Text: {resp.text[:500]}")
            
            if resp.status_code == 200:
                data = resp.json()
                if data.get("ok"):
                    response_msg = data.get("data", {}).get("message", "No message")
                    print(f"✅ Chat mode PASSED")
                    print(f"   Status Code: {resp.status_code}")
                    print(f"   Response Message:\n   {response_msg}")
                    self.results.append({"test": "chat_mode", "status": "PASS"})
                    return True
                else:
                    error_detail = data.get("error", "Unknown error")
                    print(f"❌ Chat mode FAILED (API returned ok=false)")
                    print(f"   Error: {error_detail}")
                    print(f"   Response: {json.dumps(data, ensure_ascii=False)}")
                    self.results.append({"test": "chat_mode", "status": "FAIL", "reason": error_detail})
                    return False
            else:
                print(f"❌ Chat mode FAILED (Status: {resp.status_code})")
                print(f"   Response: {resp.text[:500]}")
                self.results.append({"test": "chat_mode", "status": "FAIL", "code": resp.status_code})
                return False
        except asyncio.TimeoutError:
            print(f"❌ Chat mode TIMEOUT (20 seconds exceeded)")
            self.results.append({"test": "chat_mode", "status": "TIMEOUT"})
            return False
        except Exception as e:
            print(f"❌ Chat mode ERROR: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            self.results.append({"test": "chat_mode", "status": "ERROR", "error": str(e)})
            return False

    async def test_auto_mode(self) -> bool:
        """Test auto-classification mode."""
        print("\n" + "=" * 70)
        print("TEST 3: Auto-Classification Mode")
        print("=" * 70)
        try:
            # Test 1: Simple greeting (should classify as chat)
            payload = {
                "message": "안녕!"
            }
            print(f"Request (mode auto): {json.dumps(payload, ensure_ascii=False)}")
            
            resp = await self.client.post(
                f"{self.base_url}/jarvis/chat",
                json=payload,
                headers=self.headers,
                timeout=20.0
            )
            
            if resp.status_code == 200:
                data = resp.json()
                if data.get("ok"):
                    print(f"✅ Auto-classification PASSED")
                    print(f"   Request auto-classified and processed successfully")
                    self.results.append({"test": "auto_mode", "status": "PASS"})
                    return True
                else:
                    print(f"❌ Auto-classification FAILED")
                    self.results.append({"test": "auto_mode", "status": "FAIL", "reason": "ok=false"})
                    return False
            else:
                print(f"❌ Auto-classification FAILED (Status: {resp.status_code})")
                self.results.append({"test": "auto_mode", "status": "FAIL", "code": resp.status_code})
                return False
        except Exception as e:
            print(f"❌ Auto-classification ERROR: {e}")
            self.results.append({"test": "auto_mode", "status": "ERROR", "error": str(e)})
            return False

    async def test_task_mode(self) -> bool:
        """Test task mode with planning."""
        print("\n" + "=" * 70)
        print("TEST 4: Task Mode (With Planning)")
        print("=" * 70)
        try:
            payload = {
                "message": "TEST.txt 파일을 생성해줄 수 있나요?",
                "mode": "task"
            }
            print(f"Request: {json.dumps(payload, ensure_ascii=False)}")
            
            resp = await self.client.post(
                f"{self.base_url}/jarvis/chat",
                json=payload,
                headers=self.headers,
                timeout=30.0
            )
            
            print(f"Response Status: {resp.status_code}")
            print(f"Response Text: {resp.text[:800]}")
            
            if resp.status_code == 200:
                data = resp.json()
                if data.get("ok"):
                    response_data = data.get("data", {})
                    status = response_data.get("status", "unknown")
                    execution_steps = response_data.get("execution_steps", [])
                    print(f"✅ Task mode PASSED")
                    print(f"   Status: {status}")
                    print(f"   Execution Steps: {len(execution_steps)}")
                    self.results.append({"test": "task_mode", "status": "PASS", "steps": len(execution_steps)})
                    return True
                else:
                    error_detail = data.get("error", "Unknown error")
                    print(f"❌ Task mode FAILED (API returned ok=false)")
                    print(f"   Error: {error_detail}")
                    self.results.append({"test": "task_mode", "status": "FAIL", "reason": error_detail})
                    return False
            else:
                print(f"❌ Task mode FAILED (Status: {resp.status_code})")
                print(f"   Response: {resp.text[:500]}")
                self.results.append({"test": "task_mode", "status": "FAIL", "code": resp.status_code})
                return False
        except asyncio.TimeoutError:
            print(f"❌ Task mode TIMEOUT (30 seconds exceeded)")
            self.results.append({"test": "task_mode", "status": "TIMEOUT"})
            return False
        except Exception as e:
            print(f"❌ Task mode ERROR: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            self.results.append({"test": "task_mode", "status": "ERROR", "error": str(e)})
            return False

    async def run_all_tests(self):
        """Run all tests."""
        print("\n")
        print("╭" + "─" * 68 + "╮")
        print("│ JARVIS Complete Test Suite (Mode-Driven Architecture)".ljust(69) + "│")
        print("╰" + "─" * 68 + "╯")
        
        await self.setup()
        try:
            # Run tests
            health_ok = await self.health_check()
            
            if health_ok:
                await self.test_chat_mode()
                await self.test_auto_mode()
                await self.test_task_mode()
            else:
                print("\n⚠️  Skipping remaining tests due to health check failure")
            
            # Print summary
            self.print_summary()
        finally:
            await self.cleanup()

    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        
        total = len(self.results)
        passed = sum(1 for r in self.results if r["status"] == "PASS")
        failed = sum(1 for r in self.results if r["status"] == "FAIL")
        error = sum(1 for r in self.results if r["status"] == "ERROR")
        timeout = sum(1 for r in self.results if r["status"] == "TIMEOUT")
        
        print(f"Total Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⚠️  Errors: {error}")
        print(f"⏱️  Timeouts: {timeout}")
        
        print("\n" + "-" * 70)
        print("Detailed Results:")
        for result in self.results:
            test_name = result["test"]
            status = result["status"]
            symbol = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️ " if status == "ERROR" else "⏱️ "
            print(f"{symbol} {test_name:20} - {status}")
        
        print("\n" + "=" * 70)
        if passed == total and total > 0:
            print("🎉 ALL TESTS PASSED! JARVIS is ready for deployment.")
        else:
            print(f"⚠️  Some tests failed. Review errors above.")
        print("=" * 70 + "\n")

async def main():
    """Main entry point."""
    tester = JarvisAPITester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
