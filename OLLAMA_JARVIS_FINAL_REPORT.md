# 📊 Ollama의 JARVIS 실제 사용 부분 재확인 - 최종 보고서

**작성일**: 2026-04-18  
**목적**: JARVIS가 실제로 Ollama에서 어떻게 작동하는지 추적

---

## 🔴 핵심 발견: 3가지 모순된 모델명 설정

### 문제 상황

```
사용자 시스템에서:
1. settings.jarvis_model = "JARVIS"          (대문자)
2. hybrid_settings.LOCAL_OLLAMA_MODEL = "jarvis"  (소문자)  
3. core/llm_router JARVIS_MODEL env var = "qwen2.5:14b"  (실제 모델)

→ 어느 것이 실제로 호출되는가?
```

---

## 📈 현재 코드 흐름 추적

### 시나리오 1: 기본 Chat 사용 경로

```
사용자 메시지
    ↓
jarvis_cli.py
    ↓
/api/jarvis/chat (backend/app/api/routers/chat.py)
    ↓
SimpleChat.chat()
    ↓
llm_router.call(prompt, system)
    ↓
backend/app/llm_router.py:
    response = await client.post(
        f"{settings.intelligence_engine_url}/api/chat",
        json={
            "model": settings.jarvis_model,  ← "JARVIS"
            "messages": [...],
            "stream": False
        }
    )
    ↓
Ollama /api/chat 엔드포인트:
    POST http://127.0.0.1:11434/api/chat
    {
        "model": "JARVIS",  ← 이 모델이 Ollama에 존재하는가?
        ...
    }
    ↓
? Ollama 응답
```

---

### 시나리오 2: 부팅 시 모델 확인

```
Backend 시작
    ↓
bootstrap_application() (backend/app/core/bootstrap.py)
    ↓
model_name = settings.jarvis_model  (= "JARVIS")
    ↓
subprocess.run(["ollama", "list"])
    ↓
if model_name not in models_check.stdout:
    print("Model 'JARVIS' not found. Will auto-pull on first request.")
    ↓
    ? Ollama auto-pull mechanism?
    ? 또는 에러?
```

---

## 🎯 실제 상황 진단 (3가지 가능성)

### 가능성 A: "JARVIS"라는 커스텀 모델 존재 (가능성 20%)

```
사실: 사용자가 직접 만든 모델
예: ollama tag qwen2.5-coder:latest jarvis

Ollama list:
    jarvis          7.1GB
    qwen2.5:14b     5.2GB

결과: ✅ 정상 작동
```

---

### 가능성 B: Ollama 별칭 설정 (가능성 30%)

```
Ollama config (.ollama/modelfile에 별칭 설정):
- model JARVIS = qwen2.5:14b로 자동 매핑

Ollama list:
    JARVIS          7.1GB (별칭)
    qwen2.5:14b     7.1GB (원본)

결과: ✅ 정상 작동
```

---

### 가능성 C: 실제로 에러 발생 중 (가능성 50%) 🔴

```
Ollama list:
    qwen2.5:14b     5.2GB
    qwen2.5-coder   7.1GB
    gemma:latest    2.3GB
    # JARVIS 없음! ❌

사용자 요청 → llm_router 호출:
    "model": "JARVIS"
    ↓
Ollama 응답:
    HTTP 404: Model not found

결과: ❌ 에러, 응답 실패

backend/app/llm_router.py의 에러 처리:
    except Exception as e:
        return f"❌ [LLM_ERROR] 모델과 통신할 수 없습니다..."
        → 사용자에게 에러 메시지 반환
```

---

## 📋 버전별 설정 비교표

| 파일 | 설정 모델명 | 형식 | 실제 Ollama 모델 | 상태 |
|------|-----------|------|---------------|------|
| **backend/app/utils/settings.py** | "JARVIS" | 대문자 | ❓ | 불명확 |
| **backend/app/core/bootstrap.py** | settings.jarvis_model | "JARVIS" | ❓ | 불명확 |
| **core/llm_router.py** | $JARVIS_MODEL | env var | "qwen2.5:14b" | 명확 |
| **hybrid_settings.py** | "jarvis" | 소문자 | ❓ | 불명확 |
| **실제 Ollama** | ? | ? | ? | **확인 필수** |

---

## 🔧 문제점 분석

### 문제 1: 대소문자 혼동

```
"JARVIS" (대문자) ≠ "jarvis" (소문자)
→ 두 개의 다른 모델로 취급됨
```

---

### 문제 2: 버전 간 불일치

```
새 버전 (backend/app): "JARVIS"
오래 버전 (core): "qwen2.5:14b"

어느 쪽을 사용 중인가?
→ 양쪽 모두 존재, 혼동 가능성 높음
```

---

### 문제 3: 폴백 로직 부재

```
"JARVIS" 모델 없을 시:
- 자동 재시도? NO
- 다른 모델로 폴백? NO
- 에러 반환? YES

→ 에러 발생 시 사용자는 응답을 못 받음
```

---

## ✅ 실제 확인 방법

### 1단계: Ollama 상태 직접 확인

```bash
# Ollama 프로세스 확인
pgrep ollama

# 설치된 모델 확인
ollama list

# 예상 결과 (다음 중 하나 또는 여러 개):
# qwen2.5:14b
# qwen2.5-coder:latest
# jarvis
# gemma3:4b
# mistral:latest
```

---

### 2단계: 환경 변수 확인

```bash
# backend/.env 확인
cat backend/.env | grep -i "JARVIS\|OLLAMA"

# 또는 settings.py 직접 확인
grep -n "jarvis_model" backend/app/utils/settings.py
```

---

### 3단계: API 직접 테스트

```bash
# JARVIS 모델 테스트
curl -X POST http://127.0.0.1:11434/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "JARVIS",
    "messages": [
      {"role": "user", "content": "Hello"}
    ],
    "stream": false
  }'

# 결과 해석:
# 성공: {"message": {"content": "..."}}
# 실패: {"error": "model not found"}
# 또는: {"error": "pull required"}
```

---

### 4단계: 진단 스크립트 실행

```bash
cd backend/.venv/Scripts/activate
cd ../..
python diagnose_jarvis_model.py
```

---

## 🚀 권장 즉시 조치

### Phase 1: 상황 파악 (지금!)

```bash
# 진단 스크립트 실행
python diagnose_jarvis_model.py

# 결과 해석:
# ✅ JARVIS 작동 → 현재 상태 유지, OK
# ❌ JARVIS 실패 → Phase 2 진행
```

---

### Phase 2: 모델 설정 명확화 (필요시)

**만약 JARVIS가 없다면:**

```python
# 옵션 1: Qwen 모델 사용
# backend/app/utils/settings.py 수정:
jarvis_model: str = "qwen2.5-coder:latest"

또는

# 옵션 2: Ollama 커스텀 모델 생성
# 터미널에서:
ollama tag qwen2.5-coder:latest jarvis
```

---

### Phase 3: 폴백 로직 추가 (권장)

```python
# backend/app/llm_router.py 수정:
class LLMRouter:
    FALLBACK_MODELS = [
        "qwen2.5-coder:latest",
        "qwen2.5:14b",
        "mistral:latest"
    ]
    
    async def call(self, prompt: str, system: str):
        # 주 모델 시도
        try:
            return await self._call_ollama(
                settings.jarvis_model,
                prompt,
                system
            )
        except:
            # 폴백 시도
            for fallback in self.FALLBACK_MODELS:
                try:
                    return await self._call_ollama(
                        fallback,
                        prompt,
                        system
                    )
                except:
                    continue
            
            # 모든 폴백 실패
            raise Exception("모든 모델 작동 불가")
```

---

## 📊 최종 진단 체크리스트

```
□ ollama list 실행 → JARVIS 또는 jarvis 모델 존재 확인?
  ✅ 존재 → 현재 상태 정상
  ❌ 없음 → Phase 2 진행

□ backend/app/utils/settings.py 확인
  - jarvis_model 값: _______________
  - 설정: 명확한가? YES / NO

□ API 직접 테스트
  - "JARVIS" 모델: 작동? YES / NO
  - "qwen2.5-coder" 모델: 작동? YES / NO

□ 부팅 로그 확인
  - "Model 'JARVIS' not found" 메시지 있는가?
  - auto-pull 시도 메시지 있는가?

□ 실제 사용 테스트
  - jarvis_cli.py 실행 후 채팅: 작동? YES / NO
  - 응답 시간 정상: YES / NO
```

---

## 🎬 한 줄 요약

**현재 상태: 불명확**

`settings.jarvis_model = "JARVIS"`는 실제 Ollama 모델명인지 불명확하며, 진단 스크립트 실행으로 확인 후 필요시 설정 수정이 필요합니다.

**즉시 실행**: `python diagnose_jarvis_model.py`
