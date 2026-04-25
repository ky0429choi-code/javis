# JARVIS 하이브리드 시스템 - RED TEAM 검토 후 개선 아키텍처

**작성일**: 2026-04-18 (Red Team Feedback 반영)  
**버전**: 2.0 (현실적 설계)  
**주의**: 이전 문서의 낙관적 가정들을 모두 제거함

---

## ⚠️ 이전 설계의 4가지 심각 결함

### 1️⃣ 무료 한도 과신 (가장 위험)

**문제:**
```
이전 문서: Groq="∞ 무료", HuggingFace="∞ 무료"
실제: 
  - Groq: 분당 토큰 제한 (현재 약 30,000 tokens/min)
  - HF Inference API: 트래픽 몰리면 수초~수분 큐 대기
  - 정책 변경 가능성: 언제든 유료 전환 가능
```

**영향:**
- 무료 API를 플랜 A로 설계하면 "외부 정책 변경 1회 = 서비스 중단"
- 이미 Groq는 2024년 내내 Rate Limit 조정을 여러 차례 했음

**수정:**
```
무료 API는 절대 주요 경로로 쓰지 말 것
  ✅ 플랜 A: Ollama(로컬) + 명시 예산 API (Claude 또는 OpenAI)
  ✅ 플랜 B: Groq/HF (보조용, 예산 초과 회피용)
```

---

### 2️⃣ 캐시 일관성 결함 (구조적 버그)

**문제:**
```python
# 이전 문서의 get() 로직
async def get(self, key: str):
    # L1: Redis (1시간 TTL)
    result = await self.redis.get(key)
    if result:
        return result  # ← 버전 A
    
    # L2: SQLite (30일 TTL)
    cursor.execute("SELECT response FROM cache WHERE key = ?", (key,))
    result = cursor.fetchone()
    if result:
        # Redis 만료 후 SQLite에서 구버전 응답 프로모션
        await self.redis.set(key, result[0], ex=3600)
        return result[0]  # ← 버전 B (다를 수 있음!)

# 문제 상황:
# 1. 2026-04-15: LLM 모델 업그레이드 (Claude 3.5 → 4)
# 2. Redis 키 만료됨 (1시간 후)
# 3. SQLite에는 여전히 구모델 응답 (Claude 3.5)
# 4. 사용자는 구버전 응답 받음
```

**영향:**
- 모델 업그레이드 후에도 이전 버전 응답 반환
- 정책/보안 업데이트 미반영
- 무효화(invalidation) 전략 부재

**수정:**
```python
class CacheLayer:
    async def get(self, key: str, version: str = "current"):
        # 버전 정보를 캐시 키에 포함
        versioned_key = f"{key}:v{version}"
        
        # L1: Redis
        result = await self.redis.get(versioned_key)
        if result:
            return result
        
        # L2: SQLite (같은 버전만)
        cursor.execute("""
            SELECT response FROM cache 
            WHERE key = ? AND version = ? 
            AND created_at > datetime('now', '-7 days')
        """, (key, version))
        result = cursor.fetchone()
        if result:
            await self.redis.set(versioned_key, result[0], ex=3600)
            return result[0]
        
        return None
    
    async def invalidate_version(self, old_version: str, new_version: str):
        """버전 업그레이드 시 이전 버전 모두 무효화"""
        cursor.execute("""
            UPDATE cache SET invalidated = 1 
            WHERE version = ?
        """, (old_version,))
        self.sqlite.commit()
```

---

### 3️⃣ 민감 데이터 외부 전송 경계 미정의 (보안 결함)

**문제:**
```python
# 이전 문서의 폴백 로직
try:
    response = await ollama.generate(query)  # 로컬
except:
    response = await claude_mini.generate(query)  # ← 무조건 외부로 전송!

# 문제: 어떤 데이터가 나가는지 검증 없음
# 삼성웰스토리 맥락에서:
query = "직원 이름: 박준호, 직급: 팀장, 연봉: 8500, 조직파악..."
# → Groq/Claude 서버로 그대로 전송됨
```

**영향:**
- 내부 운영 데이터 유출
- 조직 구조/예산 정보 외부 노출
- GDPR/CCPA 위반 소지
- 경쟁사 정보수집 도구화 가능성

**수정:**
```python
class SecurityFilter:
    """민감 데이터 필터링"""
    
    SENSITIVE_KEYWORDS = {
        "내부": True,  # 조직명, 직원명
        "연봉": True,  # 급여 정보
        "조직도": True,  # 구조
        "고객": True,  # 고객 정보 (PII)
        "계약": True,  # 계약금액
    }
    
    async def check_if_sensitive(self, query: str) -> bool:
        """민감 데이터 포함 여부 검사"""
        for keyword in self.SENSITIVE_KEYWORDS:
            if keyword in query.lower():
                return True
        return False
    
    async def route_with_security(self, query: str, response_type: str):
        if await self.check_if_sensitive(query):
            # 민감 데이터: 로컬만 사용
            return await ollama.generate(query)  # 로컬
        else:
            # 일반 쿼리: 클라우드 사용 가능
            return await claude.generate(query)  # 클라우드 가능

# 사용 예:
async def smart_route(query: str):
    filter = SecurityFilter()
    
    # 1단계: 민감도 검사
    if await filter.check_if_sensitive(query):
        # 로컬 Ollama만 사용
        return await ollama.generate(query)
    
    # 2단계: 일반 쿼리는 최적 라우팅
    return await smart_router.route(query)
```

---

### 4️⃣ Batch API SLA 충돌 (아키텍처 모순)

**문제:**
```
이전 문서의 주장:
  "100 req/sec 처리량 달성"
  + "OpenAI Batch API 사용 (최대 24시간 처리)"

현실:
  - Batch API 응답 시간: 1시간 ~ 24시간 (불확정)
  - 사용자 요청: 즉시 응답 기대 (1-3초)
  - 이 둘은 근본적으로 양립 불가능
```

**올바른 이해:**
```
- Batch API (OpenAI): 대량 백그라운드 작업 (뉴스 분석, 보고서 생성)
  → 응답 시간: ~24시간, 비용: 50% 할인
  → 사용: 사용자 요청과 무관하게 '야간 배치'로만 실행

- Real-time API (Claude/Groq): 즉시 대응 필요한 작업  
  → 응답 시간: 0.5-2초
  → 사용: 사용자의 실시간 쿼리

혼합 불가!
```

**수정 아키텍처:**
```python
class SmartRouter:
    async def route(self, query: str, required_latency: str = "realtime"):
        """
        required_latency:
          - "realtime" (1-3초): Claude/Groq/로컬 Ollama
          - "batch" (1-24시간): OpenAI Batch API
        """
        
        if required_latency == "realtime":
            # 즉시 응답 필요 → 캐시/로컬/클라우드 API
            if await self.cache.get(query):
                return await self.cache.get(query)  # 캐시
            else:
                return await self.fast_path(query)  # Claude/Groq
        
        elif required_latency == "batch":
            # 배경 작업 → 배치 API 큐에 추가
            job_id = await self.batch_queue.enqueue(query)
            return {
                "status": "queued",
                "job_id": job_id,
                "estimated_completion": "tomorrow 09:00"
            }
```

---

## 🏗️ 현실적 단계적 구현 계획

### Tier 0 (1주) - 최소 복잡도

**목표:** 기본 캐싱 + 로컬 LLM만 구축

```
구성요소:
  ✅ Ollama (로컬 모델)
  ✅ SQLite (캐시 저장소)
  ✅ FastAPI (라우팅)
  
제외:
  ❌ Redis (나중에)
  ❌ 클라우드 API (나중에)
  ❌ 배치 처리 (나중에)

성능 목표:
  - 응답 시간: 200ms (로컬) ~ 시간 (캐시)
  - 캐시 히트율: 실측 (기대값: 20-40%)
  - 처리량: 5-10 req/sec

코드 (완전 단순):
```python
class BasicCache:
    def __init__(self):
        self.db = sqlite3.connect("cache.db")
    
    async def get(self, key: str):
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT response FROM cache 
            WHERE key = ? 
            AND created_at > datetime('now', '-7 days')
        """, (key,))
        result = cursor.fetchone()
        return result[0] if result else None
    
    async def set(self, key: str, value: str):
        cursor = self.db.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO cache (key, response, created_at)
            VALUES (?, ?, datetime('now'))
        """, (key, value))
        self.db.commit()

@app.post("/api/chat")
async def chat(query: str):
    cache = BasicCache()
    
    # 캐시 확인
    cached = await cache.get(query)
    if cached:
        return {"response": cached, "source": "cache"}
    
    # 로컬 Ollama
    response = await ollama.generate(query)
    await cache.set(query, response)
    
    return {"response": response, "source": "ollama"}
```

**체크리스트:**
- [ ] Ollama 설치 및 모델 로드 (jarvis)
- [ ] SQLite 테이블 생성
- [ ] 기본 캐시 로직 구현
- [ ] 응답 시간 측정 (로컬, 캐시)
- [ ] 캐시 히트율 계산
- [ ] 메모리 사용량 모니터링

---

### Tier 1 (2-3주) - 조건부 클라우드 연동

**조건:** Tier 0 캐시 히트율 측정 후 결정

```
IF 히트율 >= 40%:
  → Groq API 추가 (로컬 실패 시 폴백)
  → 민감 데이터 필터 추가
  → Claude 예산 API 추가 (선택)

IF 히트율 < 40%:
  → 캐싱 전략 자체 재검토
  → 쿼리 정규화 고려 (같은 의미의 다양한 표현)
  → Redis 추가 고려 (메모리 기반 L1 캐시)
```

**구현 (선택적):**

```python
class TieredRouter:
    def __init__(self, security_filter):
        self.cache = BasicCache()
        self.security = security_filter
    
    async def route(self, query: str):
        # 1단계: 캐시
        cached = await self.cache.get(query)
        if cached:
            return {"response": cached, "source": "cache_hit"}
        
        # 2단계: 민감도 검사
        if await self.security.is_sensitive(query):
            # 민감 데이터 → 로컬만
            response = await ollama.generate(query)
        else:
            # 일반 쿼리 → 로컬 우선
            try:
                response = await ollama.generate(query, timeout=2.0)
            except:
                # 로컬 실패 → Groq (조건부)
                if self.groq_available:
                    response = await groq.generate(query)
                else:
                    raise
        
        # 캐시 저장
        await self.cache.set(query, response)
        return {"response": response, "source": "generated"}
```

**체크리스트:**
- [ ] 히트율이 40% 이상인지 확인
- [ ] Groq API 키 발급 (필요시)
- [ ] 민감 데이터 필터 구현
- [ ] Groq 폴백 로직 추가
- [ ] 오류율 모니터링 (로컬/Groq 구분)

---

### Tier 2 (필요할 때만) - 클라우드 확장

**조건:** Tier 1이 안정화되고 추가 기능 필요할 때

```
선택지:
  A. Redis 추가 (성능 개선, L1 캐시)
  B. Supabase 추가 (원격 동기화)
  C. 배치 처리 (보고서 생성 등)

주의: 둘 다 하지 말 것! 1개씩만 추가.
```

**Redis 추가 (권장):**
```python
class TwoLayerCache:
    def __init__(self):
        self.redis = redis.Redis()  # L1: 빠름
        self.sqlite = sqlite3.connect("cache.db")  # L2: 오래 보관
    
    async def get(self, key: str):
        # L1: Redis (1시간)
        try:
            result = await self.redis.get(key)
            if result:
                return json.loads(result)
        except:
            pass
        
        # L2: SQLite (30일)
        cursor = self.sqlite.cursor()
        cursor.execute("""
            SELECT response FROM cache 
            WHERE key = ? AND created_at > datetime('now', '-30 days')
        """, (key,))
        result = cursor.fetchone()
        if result:
            # SQLite→Redis 프로모션
            await self.redis.set(key, json.dumps(result[0]), ex=3600)
            return result[0]
        
        return None
```

**체크리스트:**
- [ ] 보조 기능이 정말로 필요한지 확인
- [ ] 복잡도 vs 이득 계산
- [ ] 한 개 기능만 선택
- [ ] 모니터링 대시보드 추가

---

## 📊 현실적 성능 예측

### Tier 0 (Ollama + SQLite)

```
응답 시간:
  - 캐시 히트: 20-50ms ✅
  - 로컬 생성: 800ms-3s ⚠️
  - 평균: 상황에 따라 크게 변함

처리량: 5-10 req/sec

비용: $0/월

캐시 히트율:
  - 초기 (1주): ~0%
  - 1개월: ~20-40% (추정, 실측 필수)
```

### Tier 1 (+ Groq + 민감도 필터)

```
응답 시간:
  - 캐시 히트: 20-50ms ✅
  - 로컬 생성: 800ms-3s ⚠️
  - Groq (로컬 실패): 1-3s ⚠️
  - 평균: 500ms-2s

처리량: 10-30 req/sec (Groq Rate Limit 고려)

비용: $1-3/월 (로컬+무료 Groq 위주)

캐시 히트율: ~40% (목표)
```

### Tier 2 (+ Redis)

```
응답 시간:
  - 캐시 히트 (Redis): 5-10ms ✨
  - 캐시 히트 (SQLite): 20-50ms ✅
  - 로컬 생성: 800ms-3s ⚠️
  - 평균: 200ms-1s

처리량: 30-100 req/sec

비용: $1-5/월

캐시 히트율: ~60-70% (Redis 효율)
```

---

## ✅ 진짜 체크리스트

### Phase 1: 검증 (완료 전까지 진행 금지)

```
[ ] 로컬 Ollama 실제 응답 시간 측정 (5회 평균)
[ ] 예상 히트율이 25% 이상인지 확인
    - 쿼리 유형 분석
    - 반복도 검사
[ ] 개인정보 보호법 준수 확인
    - 캐시에 저장되는 데이터 검증
    - 외부 전송 가능성 점검
[ ] 팀 합의: "무료 API는 플랜 B" 원칙 확인
```

### Phase 2: Tier 0 구현

```
[ ] 의존성 설치 (fastapi, ollama, sqlite)
[ ] 기본 캐시 구현 (< 100 라인)
[ ] 테스트 (10개 쿼리, 캐시 히율 측정)
[ ] 지표 수집 (응답 시간, 히트율, 메모리)
[ ] 2주 运행 후 데이터 수집
```

### Phase 3: Tier 1 결정

```
[ ] 2주 데이터 분석
[ ] 히트율이 40% 이상?
    YES → Tier 1 진행
    NO → 캐싱 전략 재검토
[ ] Groq API 준비 (선택사항)
[ ] 민감 데이터 필터 정의
```

### Phase 4: 롤아웃

```
[ ] Tier 1 구현 (< 300 라인)
[ ] E2E 테스트
[ ] 로컬/Groq 분리 모니터링
[ ] 정책 변경 시 즉시 Groq 차단 절차
```

---

## 🚨 절대 하지 말아야 할 것

```
❌ 무료 API를 주요 경로로 설계
   → 서비스 종속성 매우 높음
   → 정책 변경 시 서비스 중단

❌ Redis + Supabase + Firebase 동시 운영
   → 복잡도 폭발
   → 디버깅 비용 > 구축 비용

❌ 민감 데이터 필터 없이 클라우드 연동
   → 데이터 유출 위험
   → 법무 문제

❌ 배치 API로 실시간 응답 기대
   → 사용자 만족도 최악
   → SLA 충돌

❌ Windows에서 Redis 네이티브 설치
   → WSL2 필수 (별도 복잡도)
   → 대신 로컬 메모리 캐시 우선 고려
```

---

## 🎯 결론

**이전 아키텍처의 문제:**
- 너무 복잡 (7개 이상의 컴포넌트)
- 낙관적 가정 (무료 API 무한 신뢰)
- 보안 고려 부족 (민감 데이터 필터 없음)
- SLA 충돌 (배치 + 실시간)

**현실적 아키텍처 원칙:**
1. **단순함이 최우선** (복잡도 ↓ = 버그 ↓)
2. **무료 API는 보조** (정책 변경에 무관)
3. **보안을 처음부터** (나중에 추가하면 비싼 수정)
4. **측정 후 결정** (가정 아님!)
5. **한 번에 한 가지만** (Tier별 단계적)

**여정:**
```
Tier 0 (1주)
  ↓ [히트율 측정]
Tier 1 (2-3주)
  ↓ [안정성 검증]
Tier 2 (필요시)
  ↓
Production (월 $1-5)
```

**매우 중요:** 구축 전에 "정말 이 복잡도가 필요한가?"를 팀에서 함께 확인하세요. 대부분의 경우 Tier 0-1만으로도 충분합니다.
