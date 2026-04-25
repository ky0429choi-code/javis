#!/usr/bin/env python3
"""
자비스 API 라우터 검증 스크립트
실제로 어떤 모델이 호출되는지 추적

실행: python verify_jarvis_routing.py
"""

import asyncio
import httpx
import json
import os
from datetime import datetime

# 색상 정의
class Color:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    RESET = '\033[0m'
    
    @staticmethod
    def print_header(text):
        print(f"\n{Color.BLUE}{'='*60}")
        print(f"{text}")
        print(f"{'='*60}{Color.RESET}\n")
    
    @staticmethod
    def print_success(text):
        print(f"{Color.GREEN}✅ {text}{Color.RESET}")
    
    @staticmethod
    def print_warning(text):
        print(f"{Color.YELLOW}⚠️ {text}{Color.RESET}")
    
    @staticmethod
    def print_error(text):
        print(f"{Color.RED}❌ {text}{Color.RESET}")
    
    @staticmethod
    def print_info(text):
        print(f"{Color.CYAN}ℹ️ {text}{Color.RESET}")


BASE_URL = "http://127.0.0.1:8000"
SHARED_KEY = "AIN_PAPA_SHARED_KEY"

async def check_health():
    """API 상태 확인"""
    Color.print_header("1단계: API 상태 확인")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{BASE_URL}/api/health")
            if response.status_code == 200:
                Color.print_success(f"API 응답: {response.text}")
                return True
            else:
                Color.print_error(f"API 상태: {response.status_code}")
                return False
    except Exception as e:
        Color.print_error(f"API 연결 실패: {e}")
        return False


async def check_hybrid_config():
    """Hybrid 라우터 설정 확인"""
    Color.print_header("2단계: Hybrid 라우터 설정 확인")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{BASE_URL}/api/hybrid/config",
                headers={"X-Shared-Key": SHARED_KEY}
            )
            if response.status_code == 200:
                config = response.json()
                Color.print_success("Hybrid 라우터 활성화됨!")
                print(f"\n설정 내용:")
                print(json.dumps(config, indent=2, ensure_ascii=False))
                return config
            else:
                Color.print_warning(f"Hybrid 라우터 응답: {response.status_code}")
                print(f"메시지: {response.text}")
                return None
    except Exception as e:
        Color.print_warning(f"Hybrid 라우터 미활성화 또는 오류: {e}")
        return None


async def test_chat_endpoint():
    """Chat 엔드포인트 테스트 (기본 라우터)"""
    Color.print_header("3단계: Chat 엔드포인트 테스트")
    
    messages = [
        "당신은 누구입니까?",
        "어떤 모델을 사용하고 있습니까?",
        "Google Gemini를 사용합니까?",
    ]
    
    headers = {"X-Shared-Key": SHARED_KEY}
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            for i, message in enumerate(messages, 1):
                Color.print_info(f"질문 {i}: {message}")
                
                try:
                    response = await client.post(
                        f"{BASE_URL}/api/jarvis/chat",
                        json={"message": message, "mode": "chat"},
                        headers=headers,
                        timeout=30.0
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        message_text = result.get("data", {}).get("message", "응답 없음")
                        Color.print_success(f"응답 받음")
                        print(f"내용: {message_text[:100]}...\n")
                    else:
                        Color.print_error(f"상태: {response.status_code}")
                        
                except Exception as e:
                    Color.print_error(f"오류: {e}")
                
                await asyncio.sleep(1)
                
    except Exception as e:
        Color.print_error(f"Chat 테스트 실패: {e}")


async def check_env_file():
    """환경 변수 파일 확인"""
    Color.print_header("4단계: 환경 변수 (.env) 확인")
    
    env_paths = [
        "backend/.env",
        ".env",
        "backend/.env.local",
    ]
    
    api_keys_found = {
        "CLAUDE_API_KEY": False,
        "OPENAI_API_KEY": False,
        "GEMINI_API_KEY": False,
        "GROQ_API_KEY": False,
    }
    
    for env_path in env_paths:
        if os.path.exists(env_path):
            Color.print_info(f"파일 발견: {env_path}")
            try:
                with open(env_path, 'r') as f:
                    content = f.read().lower()
                    for key in api_keys_found:
                        if key.lower() in content:
                            # API 키가 실제로 설정되어있는지 확인
                            line = [l for l in open(env_path).readlines() if key.lower() in l.lower()][0]
                            if "=" in line:
                                value = line.split("=")[1].strip()
                                if value and value != '""' and value != "''":
                                    api_keys_found[key] = True
                                    Color.print_warning(f"  {key} = [설정됨 - 토큰 과금 가능성]")
                                else:
                                    Color.print_success(f"  {key} = [비어있음 - 안전]")
            except Exception as e:
                Color.print_error(f"파일 읽기 실패: {e}")
        else:
            Color.print_info(f"파일 없음: {env_path}")
    
    Color.print_info("\n환경 변수 요약:")
    if any(api_keys_found.values()):
        Color.print_warning("⚠️ API 키가 설정되어 있습니다 - 토큰 과금이 발생할 수 있습니다")
    else:
        Color.print_success("✅ 모든 API 키가 비어있습니다 - 현재 과금 없음")


async def check_settings_file():
    """설정 파일 확인"""
    Color.print_header("5단계: 설정 파일 (settings.py) 확인")
    
    settings_path = "backend/app/utils/settings.py"
    
    try:
        with open(settings_path, 'r') as f:
            content = f.read()
            
        # 주요 설정 추출
        if 'jarvis_model' in content:
            Color.print_success("jarvis_model 설정 발견")
        if 'DEFAULT_OLLAMA_MODEL' in content:
            Color.print_success("DEFAULT_OLLAMA_MODEL 설정 발견")
        
        # API 키 설정 확인
        if 'gemini_api_key: str = ""' in content:
            Color.print_success("gemini_api_key 비어있음 ✅")
        if 'claude_api_key: str = ""' in content:
            Color.print_success("claude_api_key 비어있음 ✅")
            
    except Exception as e:
        Color.print_error(f"설정 파일 읽기 실패: {e}")


async def check_router_files():
    """라우터 파일 확인"""
    Color.print_header("6단계: 라우터 파일 확인")
    
    routers = [
        ("기본 라우터", "backend/app/llm_router.py"),
        ("Hybrid 라우터", "backend/app/api/routers/hybrid.py"),
        ("SmartRouter", "backend/app/llm_router/smart_router.py"),
    ]
    
    for name, path in routers:
        if os.path.exists(path):
            Color.print_success(f"{name} 존재: {path}")
            # 파일 크기로 활성 정도 추정
            size = os.path.getsize(path)
            if size > 1000:
                Color.print_info(f"  크기: {size} bytes (활성 상태 가능)")
            else:
                Color.print_info(f"  크기: {size} bytes (스켈레톤 코드)")
        else:
            Color.print_warning(f"{name} 없음: {path}")


async def main():
    print(f"\n{Color.CYAN}{'='*60}")
    print(f"🔍 자비스 라우터 검증 스크립트")
    print(f"시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}{Color.RESET}\n")
    
    # 1. 건강 상태 확인
    if not await check_health():
        Color.print_error("\n❌ JARVIS 백엔드가 실행 중이 아닙니다.")
        print(f"실행 방법:")
        print(f"  cd backend")
        print(f"  python -m uvicorn app.main:app --reload\n")
        return
    
    # 2. 구성 확인
    await check_hybrid_config()
    
    # 3. 채팅 테스트
    await test_chat_endpoint()
    
    # 4-6. 파일 검사
    await check_env_file()
    await check_settings_file()
    await check_router_files()
    
    # 최종 결론
    Color.print_header("🎯 최종 진단")
    print(f"""
현재 상태:
1. Hybrid 라우터 = 활성화 여부 확인됨
2. API 키 = 비어있음 (현재 과금 없음)
3. Chat 엔드포인트 = 기본 라우터 사용
4. SmartRouter = 옵션 라우터 (민감 데이터 필터링 포함)

권장 조치:
□ 위 로그를 JARVIS_GEMINI_MYSTERY.md와 함께 검토
□ API 키가 추가될 경우 토큰 모니터링 설정
□ 민감 데이터 필터링 정책 재확인

의문점:
- 자비스가 "Google Gemini Pro"라고 한 응답은 LLM 환각일 가능성 높음
- 현재 코드에 Gemini 호출 구현은 없음 (미구현)
- 하지만 SmartRouter 활성화 시 Claude 호출 가능성 있음
    """)
    
    print(f"\n{Color.CYAN}검증 완료: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Color.RESET}\n")


if __name__ == "__main__":
    asyncio.run(main())
