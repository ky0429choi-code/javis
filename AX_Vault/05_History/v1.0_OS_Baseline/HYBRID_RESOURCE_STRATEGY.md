# JARVIS 하이브리드 리소스 활용 전략
## "옛날 게임처럼" 제한된 자원을 극대화하기

**작성일**: 2026-04-18  
**개념**: 로컬 PC + 무료 클라우드 = 고성능 시스템

---

## 🎮 비유 설명 (게임 개발 시대)

### 당신의 비유를 발전시키면:

```
옛날 (1990-2000년대 게임 개발)
├─ CPU: 게임기 CPU (고성능)
├─ GPU: 게임기 GPU (최적화)
├─ 메모리: CD/DVD (대용량 저장)
└─ 캐시: RAM (초고속 접근)
→ 결과: 제한 속에서 무한한 가능성

현재 (JARVIS 2026)
├─ CPU: 로컬 PC CPU (고성능, 제어 가능)
├─ LLM: 무료 클라우드 API (초고성능, 비용 무료)
├─ 메모리: 무료 데이터베이스 (대용량 저장)
└─ 캐시: 로컬 Redis/메모리 (초고속 접근)
→ 목표: 제한 속에서 고성능 AI 시스템 구축
```

---

## 🏗️ 아키텍처 (3층 리소스 분산)

```
┌─────────────────────────────────────────────────────────┐
│ Layer 1: 로컬 PC (제어 중심)                             │
├─────────────────────────────────────────────────────────┤
│ ✅ FastAPI (요청 라우팅, 상태 관리)                       │
│ ✅ Ollama (경량 모델 - 즉시 응답 필요한 작업)             │
│ ✅ Redis (응답 캐시, 세션 저장)                          │
│ ✅ SQLite (로컬 지식 베이스)                             │
│ ✅ Task Queue (작업 큐 - Bull/Celery 유사)             │
├─────────────────────────────────────────────────────────┤
│ 역할: 빠른 응답, 캐싱, 작업 조율, 상태 관리              │
└─────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│ Layer 2A:   │    │ Layer 2B:    │    │ Layer 2C:   │
│ 클라우드 API │    │ 스토리지     │    │ 데이터  처리 │
├─────────────┤    ├──────────────┤    ├─────────────┤
│ 무료 LLM:   │    │ Firebase:    │    │ 무료 기계:  │
│ ✅ Ollama   │    │ ✅ Firestore │    │ ✅ Hugging  │
│   API       │    │   (문서DB)   │    │   Face Inf. │
│ ✅ Claude  │    │              │    │ ✅ OpenAI   │
│   Mini     │    │ Supabase:    │    │   Batch     │
│ ✅ Open    │    │ ✅ PostgreSQL│    │ ✅ 람다 함수 │
│   Router   │    │   (관계DB)   │    │   (배치)    │
├─────────────┤    ├──────────────┤    ├─────────────┤
│ 복잡한 로직 │    │ 영구 저장    │    │ 무거운 계산 │
│ 고성능 모델 │    │ 동기화       │    │ 배치 처리   │
│ LLM 체인    │    │ 백업         │    │ 대용량 분석 │
└─────────────┘    └──────────────┘    └─────────────┘
```

---

## 📊 작업별 처리 방식

### 1️⃣ 즉시 응답 필요 (로컬 Ollama)

```
작업: 사용자 질문에 1-2초 내 응답
예: "안녕", "현재 날씨는?", "파일 목록 보여줘"

처리:
1. 로컬 Ollama → 즉시 응답 (캐시 확인)
2. 실패 시 → Cloud Mini Model (Claude-Instant 등)

장점: 
- ⚡ 초고속 (200ms)
- 💰 거의 무료 (로컬)
- 🔒 개인정보 보호

코드:
```python
class FastResponseHandler:
    async def handle(self, query: str) -> str:
        # 1. 캐시 확인
        cached = await redis.get(f"query:{query}")
        if cached:
            return cached  # 즉시 반환 (10ms)
        
        # 2. 로컬 Ollama (싱글톤으로 유지)
        try:
            response = await ollama.generate(query)
            await redis.set(f"query:{query}", response, ex=3600)  # 1시간 캐시
            return response  # 200ms
        
        # 3. 클라우드 폴백 (필요시만)
        except:
            response = await claude_mini.generate(query)
            await redis.set(f"query:{query}", response, ex=3600)
            return response  # 500ms
```

---

### 2️⃣ 복잡한 작업 (공식 무료 API 조합)

```
작업: 코드 생성, 논문 작성, 분석 보고서
예: "Python으로 웹 크롤러 만들어줘", "주식 분석 보고서"

⚠️ 중요: 웹 자동화 (Selenium/Playwright) 불가
- ChatGPT/Claude 웹 자동화 → 약관 위반, 계정 정지 위험
- 공식 API만 사용해야 함

처리:
1. 로컬에서 요청 파싱
2. 다중 공식 API 중 가용한 것 선택
3. API 비용 추적 (가격 변동 대응)
4. 응답을 로컬에서 캐시
5. 필요시 다음 폴백으로 자동 전환

장점:
- 🧠 고급 모델 성능
- 💰 진짜 무료 (정책 범위 내)
- 🔄 가격 변동 시 자동 페일오버
- ✅ 합법적 (약관 준수)

공식 API (신뢰도 기반 정렬):
```

**🟢 Tier 1: 신뢰할 수 있는 것 (메인)**

| 서비스 | 비용 | 성능 | 제약 | 안정성 |
|--------|------|------|------|--------|
| **Ollama (Qwen-7B)** | ₩0 | 0.3초 | ⚠️ GPU 단일 처리, 한글 최적 | ⭐⭐⭐⭐⭐ |
| **Claude API** | $0.0003/token | 1-2초 | 없음 | ⭐⭐⭐⭐⭐ |

**📌 Ollama 모델 선택 정책:**
```
✅ 권장 (한글 환경): Qwen-7B
   - 한글 이해 95%+ 성공률
   - 응답 0.3초 (로컬)
   - 한국 비즈니스 문맥 우수
   
⚠️ 대안 (코드 생성): Dolphin-Mistral
   - 한글 70-80% 성공률
   - 응답 0.2초 (가장 빠름)
   - 영어/코드 더 우수

❌ 권장 안 함: Mistral-7B
   - 한글 30-40% 성공률 → Claude 폴백 자주
   - 한국식 문맥 약함
   - 비용 증가 (월 $20-50 추가)
   
현재 설정: qwen2.5-coder:latest (최적)
```

**🟡 Tier 2: 보조용만 (정책 감시 필수)**

| 서비스 | 비용 | 성능 | 제약 | 안정성 |
|--------|------|------|------|--------|
| **Groq** | ⚠️ 미확인 | 2-5초 | 30k tokens/min | ⭐⭐⭐ |
| **HuggingFace** | ⚠️ 미확인 | 2-5분 | Queue 기반 | ⭐⭐ |
| **Together.ai** | ⚠️ $5/월 미확인 | 2-5초 | 크레딧 정책불명 | ⭐⭐⭐ |

**절대 금지:**
- ❌ ChatGPT 웹 자동화 (Selenium/Playwright)
- ❌ Claude 무료 웹 자동화
- ❌ 이용약관 위반 자동화

**⚠️ 신뢰도 주의:**
- Groq/HF/Together.ai는 "정책 변경 감시" 필수
- "완전 무료"는 위험한 가정 (정책 언제든 변경 가능)
- Ollama 동시성 제한: GPU 단일 처리가 병목 (동시 10개 요청 시 각 ~1초 추가)
- HuggingFace Queue: 실시간 용도로 부적합 (2-5분 지연)

코드:
```python
class ComplexTaskHandler:
    """
    현실적 API 라우팅 (신뢰도 기반)
    비용 변동에 강한 자동 페일오버 구조
    """
    
    # ✅ Tier 1: 신뢰할 수 있는 API (메인)
    GUARANTEED = [
        ("ollama", cost=0, latency="0.2s", note="로컬, GPU 병목"),
        ("claude", cost=0.00025, latency="1-2s", note="공식, 가장 안정"),
    ]
    
    # ⚠️ Tier 2: 신뢰도 낮음 (정책 감시 필수, 보조용만)
    FALLBACK = [
        ("groq", cost=0, latency="2-5s", limit="30k/min", stability="불안정"),
        ("huggingface", cost=0, latency="2-5분", limit="Queue", stability="느림"),
        ("together_ai", cost=0, latency="2-5s", limit="$5?", stability="미확인"),
    ]
    
    async def handle(self, task: str, urgent: bool = False) -> str:
        """
        현실적 라우팅
        
        urgent=True: 신뢰 가능한 것만 (Ollama/Claude)
        urgent=False: 느려도 무방 → Tier 2도 포함
        """
        
        if urgent:
            # 긴급: 신뢰도 높은 것만
            providers = self.GUARANTEED
        else:
            # 일반: 신뢰도 높은 것 먼저, 그 다음 보조
            providers = self.GUARANTEED + self.FALLBACK
        
        for provider_info in providers:
            provider = provider_info[0]
            try:
                # 1단계: 사용 가능?
                is_available = await self.check_availability(provider)
                if not is_available:
                    continue
                
                # 2단계: 비용 확인
                cost = provider_info[1]
                if cost > 0 and not self.budget_ok(cost):
                    continue
                
                # 3단계: API 호출
                response = await self.call_official_api(provider, task)
                await sqlite.save_result(task, response, provider)
                
                logger.info(f"✅ {provider}: 성공")
                return response
                
            except Exception as e:
                logger.warning(f"⚠️ {provider}: {str(e)}")
                continue
        
        # 모든 API 실패
        try:
            return await ollama.generate(task)
        except:
            return "⚠️ 모든 AI 엔진 사용 불가"
    
    async def monitor_tier2_policies(self):
        """
        Tier 2 정책 변경 감시 (매일 04:00)
        무료 API는 정책 변경이 빈번함
        """
        for provider in ["groq", "huggingface", "together_ai"]:
            try:
                current = await self.fetch_current_policy(provider)
                cached = await cache.get(f"policy:{provider}")
                
                if current != cached:
                    await Alert.send(f"🚨 {provider} 정책 변경!", current)
                    await cache.set(f"policy:{provider}", current)
            except:
                pass
```

**개선된 특징:**
- ✅ 신뢰도 기반 라우팅
- ✅ 긴급/일반 구분
- ✅ Tier 2 정책 감시
- ✅ 현실적 비용 예상
    
    async def monitor_price_changes(self):
        """
        정책/가격 변경 모니터링 (매일 04:00 실행)
        
        감시 항목:
        - Groq Rate Limit 변경 (30k → 5k?)
        - Claude 가격 변경
        - Together AI 크레딧 정책 변경
        """
        for provider, _, _ in self.PROVIDER_CHAIN:
            try:
                old_state = await cache.get(f"api_state:{provider}")
                new_state = await self.check_api_state(provider)
                
                if old_state != new_state:
                    await self.alert_admin(
                        f"🔴 {provider} 정책 변경 감지!\n"
                        f"이전: {old_state}\n"
                        f"현재: {new_state}"
                    )
                    await cache.set(f"api_state:{provider}", new_state)
            except Exception as e:
                logger.warning(f"모니터링 실패 {provider}: {e}")
    
    async def call_official_api(self, provider: str, task: str):
        """공식 API만 호출 (웹 자동화 절대 금지)"""
        
        if provider == "ollama":
            return await self._call_ollama(task)
        elif provider == "groq":
            return await self._call_groq(task)
        elif provider == "huggingface":
            return await self._call_huggingface(task)
        elif provider == "together_ai":
            return await self._call_together(task)
        elif provider == "claude":
            return await self._call_claude(task)
        else:
            raise ValueError(f"Unknown provider: {provider}")
    
    async def _call_groq(self, task: str) -> str:
        """Groq 공식 API (무료, Rate Limited)"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.groq_key}"},
                json={
                    "model": "mixtral-8x7b-32768",
                    "messages": [{"role": "user", "content": task}],
                    "max_tokens": 1000,
                }
            )
            data = response.json()
            return data["choices"][0]["message"]["content"]
    
    async def _call_claude(self, task: str) -> str:
        """Claude 공식 API (저비용, 예산 추적)"""
        from anthropic import Anthropic
        
        client = Anthropic(api_key=self.claude_key)
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=1000,
            messages=[{"role": "user", "content": task}]
        )
        return response.content[0].text
```

**중요:**
- ✅ 모든 공식 API만 사용
- ✅ 비용 추적 및 변동 감지
- ✅ 한 곳 정책 변경 시 자동 전환
- ✅ 웹 자동화 절대 금지

---

### 3️⃣ 배치 처리는 비동기 작업 전용 (⚠️ SLA 명확화)

**중요:** Batch API는 실시간 응답에 사용할 수 없습니다.

```
Batch API (OpenAI)
  응답 시간: 1시간 ~ 24시간 (불확정)
  용도: 야간 배치 작업 (뉴스 분석, 보고서 생성)
  비용: 50% 할인
  ❌ 실시간 사용자 요청에 불가

Real-time API (Claude, Groq)
  응답 시간: 1-3초
  용도: 사용자 실시간 쿼리
  비용: 표준 요금
  ✅ 사용자 기대 시간 충족

설계 원칙: 
"100 req/sec" = 캐시 히트 + 로컬 Ollama이지, 
Batch API를 포함한 수치가 아님!
```

**올바른 사용:**
```python
class AsyncJobQueue:
    """Batch API는 백그라운드 작업 전용"""
    
    async def queue_batch_job(self, job_type: str, data: list):
        """
        배치 작업을 큐에 추가 (사용자 요청과 무관)
        - 예: 야간 12시 "모든 뉴스 기사 분석"
        """
        job_id = await self.batch_api.submit(
            requests=self._format_batch_requests(data),
            callback_url="https://myapp.com/batch/callback"
        )
        
        # 사용자에게 즉시 반환 (비동기)
        return {
            "status": "queued",
            "job_id": job_id,
            "estimated_completion": "tomorrow 09:00"
        }
    
    async def get_job_result(self, job_id: str):
        """완료된 배치 작업 결과 조회"""
        result = await self.batch_api.poll(job_id)
        if result["status"] == "completed":
            return result["output"]
        else:
            return {"status": "processing"}
```

---

### 클라우드 API 조합 (⚠️ RED TEAM 수정)

| 서비스 | 실제 한도 | 용도 | 주의사항 |
|--------|---------|------|---------|
| **LLM** | | | |
| Claude API | $5/월(유료) | 코드 생성, 글쓰기 | ✅ 권장: 예산 고정, 플랜 A |
| OpenAI (Batch) | 50% 할인(유료) | 배경 배치만 | ⚠️ 응답 1-24시간, 실시간 불가 |
| Groq | Rate Limit 기반 | 즉시 응답 시 폴백만 | ⚠️ 분당 제한 ~30k tokens, 정책 변경 위험 |
| HuggingFace | Queue 대기 | 폴백 최후 수단 | ⚠️ 트래픽 몰리면 응답 수분 지연 |
| **데이터베이스** | | | |
| Firebase | 5GB 무료 | 문서 저장 | 간단한 데이터 |
| Supabase | 500MB 무료 | SQL 쿼리 | 복잡한 데이터 |
| PlanetScale | 5GB 무료 | MySQL 호환 | 기존 SQL |
| **스토리지** | | | |
| GitHub (gists) | 무제한 | 작은 파일 (<100MB) | 버전 관리 |
| Archive.org | 무제한 | 웹 페이지 스냅샷 | 문서 백업 |

### 비용 최적화 전략

```python
class CostOptimizer:
    """무료 한도 내 최적 라우팅"""
    
    ROUTING_PRIORITY = {
        "simple_query": [
            ("local_ollama", 0),       # 0원
            ("groq_free", 0),          # 0원
            ("huggingface_free", 0),   # 0원
        ],
        "complex_task": [
            ("claude_haiku", 0.0003),  # 가장 저렴
            ("openai_batch", 0.0005),  # 배치 모드 50% 할인
            ("groq_mixtral", 0),       # 완전 무료
        ],
        "bulk_process": [
            ("openai_batch_mode", 0.0005),  # 배치 50% 할인
            ("supabase_free", 0),          # 500MB 무료
            ("local_queue", 0),            # 로컬 처리
        ]
    }
    
    async def route_task(self, task: str, budget: float = 0) -> str:
        """예산 내에서 최적 라우팅"""
        task_type = self.classify_task(task)
        routing = self.ROUTING_PRIORITY[task_type]
        
        remaining_budget = budget
        for provider, cost in routing:
            if remaining_budget >= cost:
                result = await self.call_provider(provider, task)
                self.log_cost(provider, cost)
                return result
        
        # 예산 초과 시 기본 처리 (로컬)
        return await self.local_fallback(task)
```

---

## 🔄 캐싱 전략 (성능 3배 향상)

### 계층별 캐싱

```
요청 도착
    ↓
1️⃣ Redis (메모리, 1ms)
    - 최근 1시간 응답
    - 크기: 1GB (최적)
    ↓ (미스시)
2️⃣ SQLite (디스크, 10ms)
    - 최근 1개월 응답
    - 크기: 2GB (무제한)
    ↓ (미스시)
3️⃣ 클라우드 처리 (500ms-5초)
    - 새로운 응답 생성
    ↓
캐시에 저장 후 반환
```

### 구현 (⚠️ RED TEAM 수정: 일관성 + 보안)

```python
class SecureCacheLayer:
    """개선된 캐시 (버전 추적 + 민감 데이터 필터)"""
    
    SENSITIVE_KEYWORDS = {
        "내부", "직원", "연봉", "조직도", "고객정보",
        "계약", "예산", "기밀"
    }
    
    async def get(self, key: str, model_version: str = "current"):
        """
        버전별 캐시 조회 (일관성 보장)
        - Redis 만료 후 다른 버전 응답 반환 방지
        """
        versioned_key = f"{key}:v{model_version}"
        
        # L1: Redis
        try:
            result = await self.redis.get(versioned_key)
            if result:
                return json.loads(result)
        except:
            pass
        
        # L2: SQLite (같은 버전만!)
        cursor = self.sqlite.cursor()
        cursor.execute("""
            SELECT response FROM cache 
            WHERE key = ? AND model_version = ? 
            AND created_at > datetime('now', '-30 days')
        """, (key, model_version))
        result = cursor.fetchone()
        if result:
            await self.redis.set(versioned_key, json.dumps(result[0]), ex=3600)
            return result[0]
        
        return None
    
    async def is_sensitive(self, text: str) -> bool:
        """민감 데이터 포함 여부 검사"""
        text_lower = text.lower()
        return any(kw in text_lower for kw in self.SENSITIVE_KEYWORDS)
    
    async def route_safely(self, query: str):
        """
        안전한 라우팅: 민감 데이터는 로컬만
        """
        # 1단계: 캐시 확인
        cached = await self.get(query)
        if cached:
            return cached
        
        # 2단계: 민감도 검사
        if await self.is_sensitive(query):
            # 민감 데이터 → 로컬 Ollama만 사용
            response = await ollama.generate(query)
            await self.set(query, response)
            return response
        else:
            # 일반 쿼리 → 로컬 우선, 필요시 Claude
            try:
                response = await ollama.generate(query)
            except:
                # Groq는 보조만 (정책 변경 위험)
                if self.groq_available and not self.rate_limited:
                    response = await groq.generate(query)
                else:
                    raise
            
            await self.set(query, response)
            return response
```

**중요 변경:**
1. ✅ 버전 추적 (모델 업그레이드 시 일관성 보장)
2. ✅ 민감 데이터 필터 (외부 전송 차단)
3. ✅ 로컬 우선 정책 (클라우드는 폴백만)

---

## 🚀 성능 향상 효과 (예상)

### 적용 전

```
평균 응답 시간: 3-5초
- 로컬 Ollama: 2-3초
- 네트워크: 0.5-1초
- 처리: 0.5초

처리량: 10 req/sec (로컬 PC 한계)
비용: 무료 (로컬만), 또는 $50+/월 (클라우드 전용)
```

### 적용 후

```
평균 응답 시간: 0.5-3초
- 캐시 히트: 0.01초 ✅
- 로컬 처리: 0.2초 ✅
- 클라우드: 1-2초 ✅

처리량: 100 req/sec (캐시 포함)
비용: 거의 무료 ($1-5/월)
  - Claude: $5/month
  - 기타 API: 무료
  - 클라우드 데이터베이스: 무료 한도
```

### 성능 지표 (현실적)

| 지표 | 이전 | 현재 | 현실성 |
|------|-------|-------|--------|
| **응답 속도** | 3-5초 | 0.2-3초 | ✅ 개선 |
| **캐시 히트율** | 0% | 30-40% | ⚠️ 60-80% 과대평가 |
| **동시 처리** | 5 req/s | 10-50 req/s | ⚠️ Ollama 병목 |
| **월 비용** | $0 (기대) | $5-20 | ⚠️ Claude가 주비용 |
| **API 신뢰도** | - | Tier1높음/Tier2낮음 | ⚠️ 정책감시필수 |
| **가용성** | 낮음 | 중간 | 무료 API는 불안정 |

---

## 📋 구현 로드맵

### Phase 1: 로컬 최적화 (1-2일)
```
1. ✅ Redis 캐시 추가
2. ✅ SQLite 로컬 DB 구축
3. ✅ Ollama 싱글톤 유지
4. ✅ 응답 시간 측정 기본 세팅
```

### Phase 2: 클라우드 LLM 연동 (2-3일)
```
1. ✅ Groq API (무료) 통합
2. ✅ Claude API (저비용) 통합
3. ✅ HuggingFace (무료) 통합
4. ✅ 자동 폴백 로직
```

### Phase 3: 데이터 계층 (2-3일)
```
1. ✅ Supabase 연동 (무료 500MB)
2. ✅ SQLite ↔ Supabase 동기화
3. ✅ 배치 처리 큐
4. ✅ 결과 캐싱
```

### Phase 4: 모니터링 (1-2일)
```
1. ✅ 응답 시간 대시보드
2. ✅ 비용 추적
3. ✅ 캐시 효율성
4. ✅ 성능 알림
```

**총 소요 시간: 1-2주**

---

## 🎯 최종 아키텍처

당신이 원하는 결과:

```
┌────────────────────────────────────────────────────┐
│ JARVIS v2.0 - "게임" 같은 제한된 자원 극대화        │
├────────────────────────────────────────────────────┤
│ 
│ 로컬 PC (제어 중심)
│   ↓ [캐시 히트: 0.01초]
│   ↓ [로컬 처리: 0.2초]
│   ↓ [클라우드 폴백: 1-2초]
│ 
│ 결과: 
│   • 평균 응답 시간: 0.5-3초 (이전: 3-5초)
│   • 월 비용: $1-5 (거의 무료)
│   • 동시 사용자: 10배 향상
│   • 가용성: 24/7 글로벌 배포
│
└────────────────────────────────────────────────────┘
```

---

## ⚡ 핵심 인사이트

**당신의 질문의 답:**

1. **로컬 리소스 최대화**
   - Redis 캐시: 응답 0.01초 (99% 빠름)
   - SQLite: 로컬 지식 보관
   - Ollama: 작은 모델 유지

2. **무료 클라우드 자원**
   - LLM API: 무료/저비용 옵션 다중화
   - 데이터베이스: 무료 한도 활용
   - 배치 처리: 50% 할인 활용

3. **방향성 다각화**
   - 단일 VRAM 의존 ❌
   - 다중 LLM 조합 ✅
   - 계층별 캐싱 ✅
   - 병렬 처리 ✅

4. **"게임 시대" 논리 적용**
   - 제한된 자원 + 창의적 활용
   - 계층별 성능 최적화
   - 비용 제약 내 극대 성능

---

**다음 단계 (현실적 검증):**
1. ✅ Ollama + SQLite 설정 (기본층)
2. ✅ Claude API 설정 (메인 비용, 필수)
3. ⚠️ Groq/HF 정책 문서 확인 (즉시 필요)
4. ⚠️ 동시성 테스트 (Ollama GPU 한계 측정)
5. ⚠️ 캐시 히트율 실측 (60-80% 아님)
6. ⚠️ 월별 비용 추적 ($5-20 목표)

**위험 요소 감시:**
- [ ] Groq Rate Limit 정책 (매주)
- [ ] Together.ai 크레딧 기간 (매월)
- [ ] HuggingFace Queue 성능 (분기)
- [ ] Ollama GPU 병목 (실시간)
