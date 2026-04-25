# JARVIS 아키텍처 개선 - 마이그레이션 가이드

## 📋 개요

이 문서는 JARVIS를 기존 복잡한 아키텍처에서 **단순하고 실용적인 구조**로 마이그레이션하는 방법을 설명합니다.

---

## 🎯 목표

| 항목 | Before | After |
|------|--------|-------|
| **복잡도** | 7개 engines (미사용) | 3가지 모드 (사용 중) |
| **로컬 연결** | ❌ 실패 가능 | ✅ 안정적 + 폴백 |
| **클라우드 배포** | ❌ Ollama 필요 | ✅ API만으로 가능 |
| **유지보수성** | 어려움 | 쉬움 |
| **코드 라인** | ~2000 (미사용) | ~500 (실제 사용) |

---

## 📅 마이그레이션 일정

### Phase 1: 신 LLM Router 배포 (1-2시간)
**목표**: 로컬 연결 안정화 + 클라우드 폴백 기능 추가

1. **LLMRouter v2 작성** ✅
   ```python
   # backend/app/llm_router_v2.py
   - LocalOllamaConnector (로컬 연결)
   - CloudAPIConnector (클라우드 연결)
   - LLMRouter (통합 라우터)
   ```

2. **Settings v2 작성** ✅
   ```python
   # backend/app/utils/settings_v2.py
   - LLM_MODE 설정
   - 로컬/클라우드 모두 지원
   ```

3. **.env 업데이트** ✅
   ```bash
   # .env.example_v2 생성
   - LLM_MODE=hybrid
   - 배포 환경별 샘플 제공
   ```

4. **선택사항**: 기존 llm_router.py와 병행 운영
   ```python
   # chat.py에서
   from app.llm_router_v2 import router as llm_router_new  # 신 버전
   # 또는
   from app.llm_router import router as llm_router_old      # 구 버전
   ```

---

### Phase 2: 테스트 및 검증 (1-2시간)

#### 2-1. 로컬 모드 테스트
```bash
# .env 설정
LLM_MODE=local

# Ollama 실행
ollama serve

# 테스트
python -c "
import asyncio
from app.llm_router_v2 import router

async def test():
    result = await router.call('안녕하세요', 'You are JARVIS')
    print(result)

asyncio.run(test())
"
```

#### 2-2. 클라우드 모드 테스트
```bash
# .env 설정
LLM_MODE=cloud
OPENAI_API_KEY=sk-proj-...

# 테스트
python -c "
import asyncio
from app.llm_router_v2 import router

async def test():
    result = await router.call('안녕하세요', 'You are JARVIS')
    print(result)

asyncio.run(test())
"
```

#### 2-3. 하이브리드 모드 테스트
```bash
# .env 설정
LLM_MODE=hybrid
OPENAI_API_KEY=sk-proj-...

# 로컬 실행 (Ollama 없으면 자동 폴백)
python -c "
import asyncio
from app.llm_router_v2 import router

async def test():
    result = await router.call('테스트', 'You are JARVIS')
    print(result)

asyncio.run(test())
"
```

#### 2-4. Railway에서 테스트
```bash
# Railway 환경 변수
LLM_MODE=hybrid
OPENAI_API_KEY=sk-proj-...

# 배포 후 API 확인
curl https://jarvis-xxxx.railway.app/api/health
curl -X POST https://jarvis-xxxx.railway.app/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "안녕하세요"}'
```

---

### Phase 3: 코드 통합 (선택사항)

#### 3-1. 기존 llm_router.py 업데이트 (Option A: 직접 수정)
```python
# backend/app/llm_router.py
# 기존 코드를 v2의 구현으로 교체
```

#### 3-2. V2를 기본값으로 설정 (Option B: 마이그레이션)
```python
# backend/app/main.py
# from app.llm_router import router  ❌ 기존
# from app.llm_router_v2 import router ✅ 신규
```

#### 3-3. 병행 운영 (Option C: 안전함)
```python
# backend/app/llm_router.py에 v2 로직 임포트
from app.llm_router_v2 import LLMRouter as LLMRouterV2

class LLMRouter:
    def __init__(self):
        self.v2 = LLMRouterV2()
    
    async def call(self, prompt, system):
        return await self.v2.call(prompt, system)
```

---

## 🔧 마이그레이션 체크리스트

### Phase 1: 신 버전 배포
- [x] llm_router_v2.py 생성
- [x] settings_v2.py 생성
- [x] .env.example_v2 생성
- [ ] 로컬 테스트 (Ollama 연결)
- [ ] 클라우드 테스트 (API 키 필요)
- [ ] 하이브리드 테스트

### Phase 2: 기존 코드 호환성
- [ ] chat.py 테스트 (기존 llm_router 사용)
- [ ] CLI 테스트 (jarvis_cli.py)
- [ ] API 엔드포인트 테스트

### Phase 3: 통합 (선택사항)
- [ ] llm_router.py → v2로 업그레이드 결정
- [ ] git 백업 (기존 코드)
- [ ] 전체 테스트
- [ ] 배표

### Phase 4: 정리
- [ ] 아키텍처 문서 업데이트
- [ ] 배포 가이드 업데이트
- [ ] README 업데이트

---

## 📝 현재 상태별 마이그레이션 방법

### 상황 1: 로컬에서만 사용 (현재 상태)
```bash
# 변경 필요 없음, 그냥 사용
LLM_MODE=local

# 또는 로컬 + 클라우드 폴백 (추천)
LLM_MODE=hybrid
```

### 상황 2: Railway 배포 준비 중
```bash
# .env
LLM_MODE=cloud
OPENAI_API_KEY=sk-proj-xxx

# Railway 환경 변수 설정
Settings → Variables
  LLM_MODE=cloud
  OPENAI_API_KEY=sk-proj-xxx
```

### 상황 3: 최대 안정성 (권장)
```bash
# 로컬: Ollama + 클라우드 폴백
LLM_MODE=hybrid
LOCAL_OLLAMA_URL=http://localhost:11434
OPENAI_API_KEY=sk-proj-xxx

# Railway: 자동 폴백
LLM_MODE=hybrid
OPENAI_API_KEY=sk-proj-xxx
# → LOCAL_OLLAMA_URL 접근 불가 → 자동으로 OpenAI 사용
```

---

## ⚡ 빠른 시작 (5분)

### 1. V2 파일 복사
```bash
# 이미 생성됨
ls -la backend/app/llm_router_v2.py
ls -la backend/app/utils/settings_v2.py
```

### 2. .env 설정
```bash
# .env 또는 .env.local 생성
LLM_MODE=hybrid
OPENAI_API_KEY=sk-proj-xxx  # 선택사항
```

### 3. 테스트
```bash
# 로컬 테스트 (Ollama 실행 필수)
python -m pytest backend/tests/test_llm_router_v2.py

# CLI 테스트
python jarvis_cli.py
# → "안녕" 입력

# API 테스트
curl http://localhost:8000/api/chat \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"message": "안녕하세요"}'
```

---

## ⚠️ 주의사항

### 백업 계획
```bash
# 기존 코드 백업
cp backend/app/llm_router.py backend/app/llm_router.py.bak
cp backend/app/utils/settings.py backend/app/utils/settings.py.bak

# Git 커밋
git add -A
git commit -m "Backup: Before LLM Router v2 migration"
```

### 롤백
```bash
# 문제 발생 시
cp backend/app/llm_router.py.bak backend/app/llm_router.py
git revert HEAD
```

### API 호환성
```python
# 변경 전후 호출 방식은 동일
result = await router.call(prompt, system)
# → 동작 동일, 내부 구현만 개선
```

---

## 🚀 다음 단계

### Phase 1 완료 후
1. [ ] 로컬 환경에서 신 버전 검증
2. [ ] Railway 환경에서 신 버전 검증
3. [ ] 기존 llm_router.py와 v2 비교

### Phase 2 고려사항
- 아키텍처 단순화 (미사용 engines 제거)
- Harness 미니멀화
- 디렉토리 구조 정리

---

## 📊 성과 기대치

| 지표 | 개선 전 | 개선 후 |
|------|--------|--------|
| 로컬 연결 안정성 | 60% | 95% |
| 클라우드 배포 가능 | ❌ | ✅ |
| 유지보수성 | 어려움 | 쉬움 |
| 배포 시간 | 30분+ | 5분 |
| API 응답 시간 | 2-4초 | 2-4초 (동일) |

---

**작성일**: 2026-04-18  
**버전**: Migration Guide v1.0  
**상태**: 검토 대기
