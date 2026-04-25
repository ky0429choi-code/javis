# API 비용 정책 변동 대응 전략

**작성일**: 2026-04-18  
**목표**: 가격/정책 변경 시에도 서비스 중단 없음

---

## 📋 개요

### 문제
```
사용자: "API 비용이 언제든 올라갈 수 있다"

실제 발생 사례:
- Groq: 2024년 내 Rate Limit 여러 번 조정
- Claude: 가격 변동 (구 버전 사라짐)
- HuggingFace: 정책 변경 (인증 추가 등)
```

### 해결책
```
✅ 다중 공식 API 조합
✅ 자동 정책 모니터링
✅ 즉시 페일오버
✅ 웹 자동화 거부 (안정성)
```

---

## 🌍 공식 API 생태계 (안전한 것만)

### Tier 1: 완전 무료 (무제한)

| API | 한도 | 안정성 | 추천 |
|-----|------|--------|------|
| **Ollama (로컬)** | 로컬 메모리 | ⭐⭐⭐⭐⭐ | 1순위 |
| **Groq** | 30k tokens/min | ⭐⭐⭐⭐ | 2순위 |
| **HuggingFace** | Queue 기반 | ⭐⭐⭐⭐ | 3순위 |

### Tier 2: 무료 크레딧

| API | 크레딧 | 재충전 | 추천 |
|-----|--------|--------|------|
| **Together AI** | $5/월 | 무제한 | 4순위 |
| **Replicate** | $5/월 | 무제한 | 5순위 |

### Tier 3: 저비용 정액

| API | 비용 | 특징 | 추천 |
|-----|------|------|------|
| **Claude API** | $0.0003/input token | 저비용, 안정 | 예산 O |
| **OpenAI (Batch)** | 50% 할인 | 1-24hr SLA | 비용 최소 |

**절대 금지:**
- ❌ ChatGPT 웹 자동화 (약관 위반, 계정 정지)
- ❌ Claude 무료 웹 (자동 탐지)
- ❌ Gemini 웹 (IP 차단)

---

## 🔔 정책 변경 감시 체계

### 1️⃣ 자동 모니터링 (매일 04:00)

```python
class PolicyMonitor:
    """정책 변경 자동 감시"""
    
    async def daily_check(self):
        """매일 04:00에 실행"""
        changes = []
        
        # 각 API의 현재 상태 확인
        for provider in PROVIDERS:
            
            # 1. 공식 Docs 확인
            official_limits = await self.fetch_official_limits(provider)
            
            # 2. 기존 캐시와 비교
            cached_limits = await cache.get(f"limits:{provider}")
            
            # 3. 변경 감지 시 알림
            if official_limits != cached_limits:
                await self.alert_change(provider, cached_limits, official_limits)
        
        # 4. 캐시 업데이트
        await cache.update_all_limits()
```

### 2️⃣ 실시간 오류 감지

```python
class RealTimeMonitor:
    """API 호출 중 문제 감지"""
    
    async def call_with_detection(self, provider, query):
        """
        API 호출 및 오류 패턴 감시
        """
        try:
            response = await provider.call(query)
            return response
        
        except RateLimitError as e:
            # Rate limit 변경 감지
            await self.alert_rate_limit_change(provider, e)
        
        except AuthenticationError:
            # API 키 만료 또는 정책 변경
            await self.alert_auth_change(provider)
        
        except Exception as e:
            # 기타 문제
            await self.alert_unknown_error(provider, e)
```

### 3️⃣ 정책 변경 알림

```python
class Alert:
    """관리자 알림"""
    
    @staticmethod
    async def send(provider: str, change_type: str, details: dict):
        """변경사항 알림"""
        
        message = f"""
        🚨 API 정책 변경 감지
        
        서비스: {provider}
        변경 종류: {change_type}
        
        세부:
        {json.dumps(details, indent=2, ensure_ascii=False)}
        
        조치: 자동으로 다른 API로 전환됨
        """
        
        # 이메일/Slack/SMS로 전송
        await send_email("admin@example.com", message)
        await send_slack("#alerts", message)
```

---

## 📊 모니터링 항목

### Groq의 경우

```
감시 항목:
1. Rate Limit: "30000 tokens/min"
   ↓ 변경 시: "5000 tokens/min"로 줄어들 수 있음
   ↓ 감지: API 429 응답 또는 공식 문서 업데이트

2. 가격: 무료 (유지?)
   ↓ 변경 시: 갑자기 유료화
   ↓ 감지: 과금 알림

3. 모델: "mixtral-8x7b-32768"
   ↓ 변경 시: 이전 모델 제거
   ↓ 감지: "Model not found" 오류
```

**감시 코드:**
```python
async def monitor_groq():
    while True:
        # 1. 공식 Docs 확인
        docs = await fetch_groq_docs()
        current_limit = parse_rate_limit(docs)
        
        # 2. 캐시 확인
        cached_limit = await cache.get("groq:rate_limit")
        
        # 3. 변경 감지
        if current_limit != cached_limit:
            await Alert.send(
                "Groq",
                "Rate Limit Change",
                {"from": cached_limit, "to": current_limit}
            )
        
        # 4. 실시간 테스트 call
        try:
            await test_groq_call()
        except RateLimitError:
            await Alert.send("Groq", "Rate Limit Hit", {})
        
        # 1일 대기
        await asyncio.sleep(24 * 3600)
```

### Claude API의 경우

```
감시 항목:
1. 가격: $0.00025/input token
   ↓ 변경 시: $0.0005/input token (+100%)
   ↓ 감지: 과금 내역 확인

2. 모델: "claude-3-haiku-20240307"
   ↓ 변경 시: 구 버전 지원 중단
   ↓ 감지: "Model deprecated" 오류

3. 한도: API 없음
   ↓ 변경 시: Rate limit 추가
   ↓ 감지: 429 응답
```

**감시 코드:**
```python
async def monitor_claude():
    while True:
        # 1. 공식 가격표 확인
        pricing = await fetch_claude_pricing()  # anthropic.com/pricing
        
        # 2. 과금 확인 (console.anthropic.com)
        current_charges = await fetch_billing_page()
        
        # 3. 가격 변경 감지
        if pricing != cached_pricing:
            await Alert.send(
                "Claude",
                "Pricing Change",
                {"new": pricing}
            )
        
        # 4. 모델 지원 여부 확인
        try:
            await test_claude_with_all_models()
        except ModelNotFoundError as e:
            await Alert.send("Claude", "Model Deprecated", {"model": str(e)})
        
        # 1일 대기
        await asyncio.sleep(24 * 3600)
```

---

## 🔄 자동 페일오버 전략

### Step 1: 정책 변경 감지
```
API 호출 중 문제 발생
  ↓
오류 타입 분류:
- RateLimitError → Rate limit 변경
- AuthenticationError → API 키 만료 또는 정책 변경
- PricingError → 비용 정책 변경
```

### Step 2: 캐시 업데이트
```
감지된 문제 → 즉시 캐시 업데이트
  ↓
다음 호출부터 이 API 건너뜀
```

### Step 3: 다음 API로 자동 전환
```
Primary API 실패
  ↓ (Groq 실패 → 30k tokens/min 제한 감지)
Fallback API 사용
  ↓ (HuggingFace 사용)
응답 성공 (사용자는 지연만 느낌, 서비스 중단 없음)
```

**코드:**
```python
class ResilientRouter:
    """실패에 강한 라우터"""
    
    async def route_with_fallback(self, query: str):
        """한 곳 실패해도 서비스 지속"""
        
        providers = [
            ("groq", "30k tokens/min"),
            ("huggingface", "queue based"),
            ("together_ai", "$5/month"),
            ("ollama", "local"),
        ]
        
        for provider_name, limit in providers:
            try:
                # 이 API 사용 가능?
                if await is_provider_available(provider_name):
                    result = await call_provider(provider_name, query)
                    return result
            
            except RateLimitError as e:
                # Rate limit 변경 감지
                logger.warning(f"Rate limit 변경 감지: {e}")
                await cache.mark_unavailable(provider_name, duration=3600)
                # 다음 provider 시도
            
            except Exception as e:
                logger.warning(f"{provider_name} 실패: {e}")
                # 다음 provider 시도
        
        # 모든 외부 API 실패 → 로컬만 사용
        return await call_provider("ollama", query)
```

---

## 📈 비용 추적 및 예방

### 월별 비용 추적

```python
class CostTracker:
    """월별 비용 추적"""
    
    MONTHLY_BUDGET = 50.0  # $50/month 정책
    
    async def track_call(self, provider: str, tokens: int, cost_per_1k: float):
        """각 API 호출 비용 기록"""
        
        call_cost = (tokens / 1000) * cost_per_1k
        today = datetime.now().date()
        
        # 1. DB에 기록
        await db.insert_cost_log({
            "date": today,
            "provider": provider,
            "tokens": tokens,
            "cost": call_cost,
        })
        
        # 2. 월 누적
        monthly_total = await self.get_monthly_cost()
        
        # 3. 예산 초과 확인
        if monthly_total > self.MONTHLY_BUDGET:
            await Alert.send(
                "Budget Alert",
                "Over Budget",
                {"limit": self.MONTHLY_BUDGET, "current": monthly_total}
            )
            # 유료 API 비활성화
            await self.disable_paid_apis()
    
    async def get_monthly_cost(self) -> float:
        """이번 달 누적 비용"""
        today = datetime.now()
        month_start = today.replace(day=1)
        
        result = await db.query(f"""
            SELECT SUM(cost) FROM cost_logs
            WHERE date >= '{month_start}'
        """)
        
        return result[0][0] or 0.0
    
    async def disable_paid_apis(self):
        """예산 초과 시 유료 API 비활성화"""
        logger.warning("💰 예산 초과 → 유료 API 비활성화")
        await cache.set("paid_apis_disabled", True)
        # 이후 라우터는 무료 API만 사용
```

### 자동 비용 절감

```python
class CostOptimizer:
    """비용 자동 최적화"""
    
    async def optimize(self):
        """비용이 올라가면 자동 절감"""
        
        # 매주 검토
        while True:
            # 1. 현재 비용 분석
            costs_by_provider = await self.analyze_costs()
            
            # 2. 비싼 것 찾기
            most_expensive = self.find_expensive_providers(costs_by_provider)
            
            # 3. 비싼 것부터 비활성화
            for provider, cost in most_expensive.items():
                if cost > COST_THRESHOLD:
                    logger.info(f"비용 최적화: {provider} 비활성화 (${cost})")
                    await cache.disable_provider(provider)
            
            # 1주 대기
            await asyncio.sleep(7 * 24 * 3600)
```

---

## ✅ 체크리스트

- [ ] Groq Rate Limit 감시 (일일)
- [ ] Claude 가격 변경 감시 (일일)
- [ ] HuggingFace 정책 변경 감시 (일일)
- [ ] 월 비용 추적 활성화
- [ ] 예산 초과 알림 설정
- [ ] 페일오버 테스트 (주일)
- [ ] API 헬스 체크 (시간마다)

---

## 🎯 최종 결과

```
사용자 입장:
  "API 비용이 올라도 서비스는 계속된다"

기술적:
  ✅ 다중 공식 API 조합
  ✅ 자동 정책 모니터링
  ✅ 즉시 페일오버
  ✅ 비용 추적 및 최적화
  ✅ 웹 자동화 없음 (안정성)

결론:
  한 곳이 문제가 되어도 다른 곳에서 자동 처리
  정책 변경에도 서비스 중단 없음
```
