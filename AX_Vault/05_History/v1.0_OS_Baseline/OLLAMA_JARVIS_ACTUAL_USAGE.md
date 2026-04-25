# 🔍 Ollama-JARVIS 실제 사용 부분 재확인

**작성일**: 2026-04-18  
**목적**: "JARVIS" 모델명이 실제로는 무엇인지 추적

---

## 🚨 발견: 3개의 모순되는 설정!

### 문제 1: 대문자 vs 소문자 모순

```
버전 A (backend/app/llm_router.py)
├─ jarvis_model: str = "JARVIS"  (대문자!)
└─ Ollama 호출: {"model": "JARVIS", ...}

버전 B (core/llm_router.py)
├─ JARVIS_MODEL env var
└─ 기본값: "qwen2.5:14b"  ← 실제 Ollama 모델

버전 C (hybrid_settings.py + api/main.py)
├─ LOCAL_OLLAMA_MODEL: str = "jarvis"  (소문자!)
└─ model_key: str = "jarvis"
```

---

## 🔴 핵심 문제: "JARVIS"라는 모델이 존재하는가?

### Ollama에서 실제로 설치된 모델

```bash
# 실제로 다음이 설치되어 있을 것으로 예상
ollama list

# 예상 결과:
qwen2.5:14b        5.2GB
qwen2.5-coder:latest  7.1GB
gemma3:4b          2.3GB
# "JARVIS" 모델은 없음! ❌
```

---

## 📋 라우터별 실제 동작 흐름

### 라우터 1: backend/app/llm_router.py (현재 사용 중)

```
사용자 채팅
    ↓
chat.py → llm_router.py.call()
    ↓
settings.jarvis_model = "JARVIS"  ← 문제!
    ↓
Ollama /api/chat 호출:
POST http://127.0.0.1:11434/api/chat
{
    "model": "JARVIS",  ← Ollama에 이 모델이 없으면 에러!
    "messages": [...]
}
    ↓
? Ollama 응답: 404 Model not found OR Auto-pull?
```

---

### 라우터 2: core/llm_router.py (백업 버전)

```
보조 라우터:
- JARVIS_MODEL env var 읽음
- 기본값: qwen2.5:14b
- 실제 작동:
  POST http://127.0.0.1:11434/api/chat
  {
      "model": "qwen2.5:14b",  ← 실제 모델 사용
      ...
  }
```

---

### 라우터 3: hybrid_settings.py (하이브리드)

```
LOCAL_OLLAMA_MODEL: str = "jarvis"  ← 소문자!
- 이것도 Ollama에 존재하지 않을 가능성
- SmartRouter 사용 시 로컬 폴백
```

---

## ⚠️ 3가지 가능한 시나리오

### 시나리오 1: Ollama Auto-Pull (가능성: 낮음)

```
Ollama 설정:
- Pull missing models automatically: ❌ 보통 비활성화

결과:
"JARVIS" 모델 요청 → Ollama 에러
```

---

### 시나리오 2: 모델 별칭 구성 (가능성: 중간)

```
Ollama 설정 (.ollama/models)
- "JARVIS" → "qwen2.5:14b" 별칭 가능?

실제로 그런 설정이 있는가?
→ 확인 필요!
```

---

### 시나리오 3: 실제 "jarvis" 커스텀 모델 존재 (가능성: 중간)

```
사용자가 직접 생성한 모델:
- Modelfile로 "jarvis" 모델 생성 후 push?
- OR "qwen2.5:14b"를 "jarvis"로 태그?

예:
ollama tag qwen2.5:14b jarvis

실제 존재하는가?
→ 확인 필요!
```

---

## 🔧 실제 동작 확인 방법

### 방법 1: Ollama 모델 목록 확인

```bash
# 실제 설치된 모델 확인
ollama list

# 찾을 것:
# - "JARVIS" (대문자)
# - "jarvis" (소문자)  
# - "qwen2.5:14b"
# - "qwen2.5-coder:latest"
```

---

### 방법 2: Ollama API 직접 테스트

```bash
# curl로 직접 테스트
curl -X POST http://127.0.0.1:11434/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "JARVIS",
    "messages": [
      {"role": "user", "content": "test"}
    ]
  }'

# 결과:
# {"error":"model not found"}  ← JARVIS 무조건 없음!
# OR
# {"message":{"content":"response..."}}  ← 작동 중
```

---

### 방법 3: 환경 변수 확인

```bash
# Ollama 환경 변수 확인
echo $JARVIS_MODEL
echo $OLLAMA_BASE_URL

# .env 파일 확인
cat backend/.env | grep -i "JARVIS\|OLLAMA"
```

---

## 📊 최종 진단표

| 항목 | 설정값 | 실제 모델 | 상태 | 위험도 |
|------|--------|---------|------|--------|
| backend/app | "JARVIS" | ❓ 불명확 | 문제 | 🔴 높음 |
| core/llm_router.py | env var | "qwen2.5:14b" | 명확 | 🟢 안전 |
| hybrid_settings.py | "jarvis" | ❓ 불명확 | 문제 | 🔴 높음 |
| 실제 Ollama | ? | ? | 확인 필수 | 🔴 높음 |

---

## 🎯 가장 가능성 높은 시나리오

**가설: "JARVIS" 모델은 존재하지 않으며, 실제로는 다음 중 하나**

```
1. fallback 발생:
   JARVIS 요청 에러 → 자동 재시도 → qwen 사용?

2. 처음부터 잘못된 설정:
   jarvis_model = "JARVIS" ← 오타?
   실제 의도: DEFAULT_OLLAMA_MODEL = "qwen2.5-coder:latest"?

3. 환경변수 override:
   .env에서 JARVIS_MODEL=qwen2.5:14b 설정됨?
```

---

## 🔴 실제 문제점

### Problem 1: 모델명 불일치

```python
# backend/app/utils/settings.py
jarvis_model: str = "JARVIS"

# Ollama에 전달됨
{"model": "JARVIS", ...}

# But Ollama에는 이 모델이 없음!
```

### Problem 2: 버전 간 모순

```python
# 버전 1 (새로움)
backend/app/llm_router.py: "JARVIS"

# 버전 2 (오래됨)
core/llm_router.py: "qwen2.5:14b"

# 버전 3 (하이브리드)
hybrid_settings.py: "jarvis"

→ 어느 것을 사용 중인가?
```

### Problem 3: 자동 폴백 없음

```python
# llm_router.py에서
response.raise_for_status()  ← 실패 시 예외 발생

# 따라서 JARVIS 없으면:
# ❌ 에러 반환, 다른 모델로 폴백하지 않음
```

---

## ✅ 해결 방안

### 1단계: 현재 상태 파악 (지금!)

```bash
# A. Ollama 모델 확인
ollama list

# B. 환경 변수 확인
echo $JARVIS_MODEL
cat backend/.env | grep JARVIS

# C. API 직접 테스트
curl -X POST http://127.0.0.1:11434/api/chat \
  -d '{"model": "JARVIS", "messages": [...]}'
```

### 2단계: 설정 명확화 및 수정

```python
# 수정 안:
DEFAULT_OLLAMA_MODEL = "qwen2.5-coder:latest"

또는 (기존 시스템 유지하려면):
JARVIS_MODEL = "qwen2.5-coder:latest"

그리고:
jarvis_model: str = os.getenv("JARVIS_MODEL", "qwen2.5-coder:latest")
```

### 3단계: 폴백 로직 추가

```python
# llm_router.py 수정
FALLBACK_MODELS = [
    "qwen2.5-coder:latest",
    "qwen2.5:14b",
    "mistral:latest"
]

if model_not_found:
    for fallback in FALLBACK_MODELS:
        try request_ollama(fallback)
```

---

## 🎬 스크립트: 현재 상태 진단

저장 이름: `diagnose_jarvis_model.py`

```python
#!/usr/bin/env python3
import subprocess
import httpx
import os

print("🔍 JARVIS 모델 진단 시작\n")

# 1. 환경 변수 확인
print("1️⃣ 환경 변수 확인:")
jarvis_model_env = os.getenv("JARVIS_MODEL", "없음")
print(f"   JARVIS_MODEL = {jarvis_model_env}\n")

# 2. Ollama 모델 목록
print("2️⃣ Ollama 설치된 모델:")
try:
    result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
    print(result.stdout)
    
    if "JARVIS" in result.stdout.upper():
        print("   ✅ JARVIS 모델 발견!")
    elif "jarvis" in result.stdout.lower():
        print("   ✅ jarvis 모델 발견!")
    else:
        print("   ❌ JARVIS/jarvis 모델 없음!")
        
except Exception as e:
    print(f"   ❌ Ollama 확인 실패: {e}\n")

# 3. Ollama API 테스트
print("3️⃣ Ollama API 테스트 (JARVIS 모델):")
try:
    response = httpx.post(
        "http://127.0.0.1:11434/api/chat",
        json={
            "model": "JARVIS",
            "messages": [{"role": "user", "content": "test"}]
        },
        timeout=10
    )
    if response.status_code == 200:
        print("   ✅ JARVIS 모델 작동!")
    else:
        print(f"   ❌ HTTP {response.status_code}")
        print(f"   응답: {response.text}")
except Exception as e:
    print(f"   ❌ API 호출 실패: {e}\n")

print("\n결론: 위 결과를 바탕으로 설정 수정 필요")
```

---

## 📝 최종 결론

**문제**: jarvis_model = "JARVIS"는 실제 Ollama 모델명이 아니다!

**원인**:
1. 설정 파일의 불명확한 모델명
2. 버전 간 불일치
3. 실제 모델 이름과 다름

**결과**:
- 현재 작동 여부: ❓ 불명확 (확인 필요)
- 만약 작동 중이면: 다른 메커니즘 (auto-pull? 별칭?) 사용 중
- 만약 실패하면: 에러 처리 미흡

**즉시 조치**: 위 진단 스크립트 실행 후 실제 모델명 파악, 설정 수정
