#!/usr/bin/env python3
"""
JARVIS 모델명 실제 사용 진단
Ollama에서 실제로 어떤 모델이 사용되는지 추적
"""

import subprocess
import httpx
import os
import sys

class Color:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

print(f"\n{Color.BLUE}{'='*60}")
print("🔍 JARVIS 모델명 실제 사용 진단")
print(f"{'='*60}{Color.RESET}\n")

# 1️⃣ 환경 변수 확인
print(f"{Color.BLUE}1️⃣ 환경 변수 확인:{Color.RESET}")
jarvis_model_env = os.getenv("JARVIS_MODEL", None)
if jarvis_model_env:
    print(f"   ✅ JARVIS_MODEL = {jarvis_model_env}")
else:
    print(f"   ℹ️ JARVIS_MODEL 설정 안 됨 (backend/.env 사용)")

ollama_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
print(f"   Ollama URL = {ollama_url}\n")

# 2️⃣ 설정 파일 확인
print(f"{Color.BLUE}2️⃣ 설정 파일 확인:{Color.RESET}")
settings_path = "backend/app/utils/settings.py"
if os.path.exists(settings_path):
    with open(settings_path, 'r') as f:
        for line in f:
            if 'jarvis_model' in line.lower():
                print(f"   {line.strip()}")
else:
    print(f"   ❌ {settings_path} 없음")

# 3️⃣ Ollama 설치된 모델 목록
print(f"\n{Color.BLUE}3️⃣ Ollama 설치된 모델 목록:{Color.RESET}")
try:
    result = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=10)
    models = result.stdout.strip().split('\n')
    
    jarvis_found = False
    qwen_found = False
    
    print("   설치된 모델:")
    for model in models[1:]:  # 첫 줄은 헤더
        if model.strip():
            print(f"     - {model}")
            if 'jarvis' in model.lower():
                jarvis_found = True
            if 'qwen' in model.lower():
                qwen_found = True
    
    if jarvis_found:
        print(f"   {Color.GREEN}✅ 'jarvis' 모델 발견!{Color.RESET}")
    else:
        print(f"   {Color.YELLOW}⚠️ 'jarvis' 모델 없음{Color.RESET}")
    
    if qwen_found:
        print(f"   {Color.GREEN}✅ Qwen 모델 발견{Color.RESET}")
        
except subprocess.TimeoutExpired:
    print(f"   {Color.RED}❌ ollama 명령 타임아웃{Color.RESET}")
except FileNotFoundError:
    print(f"   {Color.RED}❌ ollama 명령 없음 (Ollama 설치 필요){Color.RESET}")
except Exception as e:
    print(f"   {Color.RED}❌ 오류: {e}{Color.RESET}")

# 4️⃣ Ollama API 테스트 - "JARVIS" 모델
print(f"\n{Color.BLUE}4️⃣ Ollama API 테스트 - 'JARVIS' 모델:{Color.RESET}")
try:
    response = httpx.post(
        f"{ollama_url}/api/chat",
        json={
            "model": "JARVIS",
            "messages": [{"role": "user", "content": "test"}],
            "stream": False
        },
        timeout=5
    )
    
    if response.status_code == 200:
        print(f"   {Color.GREEN}✅ 'JARVIS' 모델 작동!{Color.RESET}")
    else:
        print(f"   {Color.RED}❌ HTTP {response.status_code}{Color.RESET}")
        if response.status_code == 404:
            print(f"      모델을 찾을 수 없음 (Model not found)")
        try:
            error = response.json()
            print(f"      응답: {error}")
        except:
            print(f"      응답: {response.text[:100]}")
            
except httpx.ConnectError:
    print(f"   {Color.RED}❌ Ollama 연결 불가 (http://{ollama_url}){Color.RESET}")
except httpx.TimeoutException:
    print(f"   {Color.YELLOW}⚠️ Ollama 타임아웃{Color.RESET}")
except Exception as e:
    print(f"   {Color.RED}❌ 오류: {e}{Color.RESET}")

# 5️⃣ Ollama API 테스트 - "qwen2.5-coder" 모델
print(f"\n{Color.BLUE}5️⃣ Ollama API 테스트 - 'qwen2.5-coder:latest' 모델:{Color.RESET}")
try:
    response = httpx.post(
        f"{ollama_url}/api/chat",
        json={
            "model": "qwen2.5-coder:latest",
            "messages": [{"role": "user", "content": "Hello"}],
            "stream": False
        },
        timeout=10
    )
    
    if response.status_code == 200:
        result = response.json()
        content = result.get("message", {}).get("content", "응답 없음")
        print(f"   {Color.GREEN}✅ 'qwen2.5-coder:latest' 작동!{Color.RESET}")
        print(f"      응답 샘플: {content[:50]}...")
    else:
        print(f"   ❌ HTTP {response.status_code}")
            
except Exception as e:
    print(f"   {Color.YELLOW}⚠️ qwen2.5-coder 테스트 실패: {str(e)[:50]}{Color.RESET}")

# 6️⃣ llm_router.py 확인
print(f"\n{Color.BLUE}6️⃣ backend/app/llm_router.py 호출 메커니즘:{Color.RESET}")
try:
    with open("backend/app/llm_router.py", 'r') as f:
        content = f.read()
        if 'settings.jarvis_model' in content:
            print(f"   ✅ settings.jarvis_model 사용 중")
            # Extract the actual setting
            for line in content.split('\n'):
                if '"model": settings.jarvis_model' in line:
                    print(f"      호출: {line.strip()}")
except:
    print(f"   ℹ️ llm_router.py 분석 불가")

print(f"\n{Color.BLUE}{'='*60}")
print("진단 완료")
print(f"{'='*60}{Color.RESET}\n")

# 최종 결론
print(f"{Color.BLUE}📊 최종 결론:{Color.RESET}\n")
print("위 결과를 바탕으로:")
print("1. 'JARVIS' 모델이 작동하는가?")
print("   - YES: 별칭 또는 커스텀 모델 설정됨")
print("   - NO: 설정 오류, 'qwen2.5-coder' 사용 권장")
print("\n2. 설정 파일 수정 필요:")
print("   기존: jarvis_model: str = \"JARVIS\"")
print("   변경: jarvis_model: str = \"qwen2.5-coder:latest\"")
print("\n3. 또는 Ollama 커스텀 모델 생성:")
print("   ollama tag qwen2.5-coder:latest jarvis")
