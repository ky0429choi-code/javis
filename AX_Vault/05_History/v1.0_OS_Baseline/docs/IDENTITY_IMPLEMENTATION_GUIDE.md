# JARVIS 정체성 프롬프트 구현 가이드

**작성일**: 2026.04.18  
**목적**: JARVIS v1 정체성을 모든 시스템에 구현하는 방법  
**상태**: 즉시 적용 가능한 체크리스트

---

## 🎯 정체성 프롬프트를 어디에 적용할 것인가?

### 1단계: Ollama 모델 (✅ 이미 완료)

**상태**: JARVIS:latest에 v1 정체성 프롬프트 적용 완료

**검증 방법**:
```bash
ollama show JARVIS:latest
# "당신은 JARVIS입니다. 당신은 지휘자(Conductor)이며..." 확인
```

**파일**:
- `backend/Modelfile_JARVIS_v1` (적용됨)

---

### 2단계: Backend Bootstrap (즉시 구현 필요)

**목적**: 시스템 시작 시 JARVIS의 정체성을 Core에 로드

**파일**: `backend/app/core/bootstrap.py` (또는 `core/bootstrap.py`)

**구현**:
```python
# backend/app/core/bootstrap.py

from pathlib import Path
import json

class JarvisIdentity:
    """JARVIS v1 정체성 정의"""
    
    IDENTITY_PROMPT = """당신은 JARVIS입니다.

당신은 지휘자(Conductor)이며, 사장님의 신뢰받는 비서입니다.

## 역할 (5단계)
1. 의도 해석: 사장님이 진짜 원하는 게 뭔가?
2. 작업 분해: 어떤 단계로 나눠야 하나?
3. 뇌 선택: 누가 이를 가장 잘 할 수 있나?
4. 위험 판정: 승인이 필요한가?
5. 결과 기록: 무엇을 배웠나?

## 특징
- 일상 대화는 하지만, 결정은 신중합니다.
- 제안은 빠르지만, 실행은 허락 후입니다.
- 메모리는 조직의 자산입니다.
- 자기개선은 정해진 절차를 따릅니다.

## 당신이 아닌 것
- 사용자 허락 없이 뭔가 하는 AI가 아닙니다.
- 온라인에서 무한정 학습하며 자신을 바꾸는 AI가 아닙니다.
- 모든 작업을 자율로 처리하고 결과만 보고하는 AI가 아닙니다.

## 승인이 필요한 작업
- 파일 생성/수정/삭제
- 영구 메모리 반영
- 시스템 설정 변경
- 외부 API 호출

당신의 비서이자, 당신의 사무실의 지휘자입니다.
"""
    
    ROLE_DEFINITION = {
        "name": "JARVIS",
        "version": "1.0",
        "type": "Conductor",
        "base_model": "JARVIS:latest",
        "brains": {
            "gpt_oss": {"role": "analysis", "priority": 1},
            "gemma": {"role": "conversation", "priority": 3},
            "qwen": {"role": "execution", "priority": 2}
        },
        "engines": [
            "intent_engine",
            "planning_engine",
            "routing_engine",
            "approval_engine",
            "memory_engine",
            "reflection_engine",
            "audit_engine"
        ],
        "approval_required": [
            "file_create",
            "file_modify",
            "file_delete",
            "memory_permanent",
            "system_setting",
            "external_api"
        ]
    }

async def load_jarvis_identity():
    """JARVIS 정체성 로드 (시스템 홍보)"""
    print("\n" + "="*60)
    print("🤖 JARVIS v1 초기화")
    print("="*60)
    print(f"이름: {JarvisIdentity.ROLE_DEFINITION['name']}")
    print(f"버전: {JarvisIdentity.ROLE_DEFINITION['version']}")
    print(f"타입: {JarvisIdentity.ROLE_DEFINITION['type']}")
    print(f"기본 모델: {JarvisIdentity.ROLE_DEFINITION['base_model']}")
    print(f"활성 엔진: {', '.join(JarvisIdentity.ROLE_DEFINITION['engines'])}")
    print("="*60 + "\n")
    
    # 정체성 저장
    await save_identity_to_memory(JarvisIdentity.ROLE_DEFINITION)

async def save_identity_to_memory(identity: dict):
    """정체성을 Prompt Memory에 저장"""
    # Memory Engine에 저장
    # memory_engine.save_prompt_memory({
    #     "type": "identity",
    #     "version": "1.0",
    #     "data": identity
    # })
    pass
```

**적용 위치**: FastAPI 시작 시
```python
# backend/app/main.py

@app.on_event("startup")
async def startup_event():
    await load_jarvis_identity()
    # ... 다른 초기화
```

---

### 3단계: Conductor Core (중핵심, 매일 참조)

**목적**: Conductor가 모든 엔진을 호출할 때 정체성을 기준으로 판단

**파일**: `core/conductor.py` (또는 `backend/app/core/conductor.py`)

**구현**:
```python
# core/conductor.py

class JarvisConductor:
    def __init__(self):
        self.identity = self.load_identity()
        self.engines = self.initialize_engines()
        
    def load_identity(self):
        """정체성 로드"""
        return {
            "name": "JARVIS",
            "role": "Conductor",
            "version": "1.0",
            "role_definition": [
                "Intent 해석",
                "Planning 분해",
                "Routing 선택",
                "Approval 판정",
                "결과 기록"
            ],
            "approval_required": [
                "file_create", "file_modify", "file_delete",
                "memory_permanent", "system_setting", "external_api"
            ]
        }
    
    async def handle_request(self, user_message: str) -> dict:
        """
        사용자 요청 처리 (5단계)
        
        1. Intent 해석
        2. Planning 분해
        3. Routing 선택
        4. Approval 판정
        5. 결과 기록
        """
        
        # Step 1: Intent
        intent = await self.engines["intent"].analyze(user_message)
        
        # Step 2: Planning
        plan = await self.engines["planning"].decompose(intent)
        
        # Step 3: Routing
        routing = await self.engines["routing"].select_brain(plan)
        
        # Step 4: Approval
        if self.needs_approval(routing["action_type"]):
            approval_id = await self.engines["approval"].queue_request(routing)
            response = {
                "status": "pending_approval",
                "approval_id": approval_id,
                "message": "승인 대기 중입니다."
            }
        else:
            # 실행
            result = await routing["brain"].execute(routing)
            response = result
        
        # Step 5: Audit
        await self.engines["audit"].log_transaction({
            "user_message": user_message,
            "intent": intent,
            "plan": plan,
            "routing": routing,
            "response": response
        })
        
        return response
    
    def needs_approval(self, action_type: str) -> bool:
        """승인 필요 여부 판정"""
        return action_type in self.identity["approval_required"]
```

---

### 4단계: API 라우터 (모든 엔드포인트)

**목적**: API 응답에 정체성 메타데이터 포함

**파일**: `backend/app/api/routers/chat.py`

**구현**:
```python
# backend/app/api/routers/chat.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api", tags=["chat"])

class ChatRequest(BaseModel):
    message: str
    conversation_id: str = None

class ChatResponse(BaseModel):
    response: str
    conductor_role: str = "JARVIS"
    version: str = "1.0"
    timestamp: str
    metadata: dict = {}

@router.post("/chat")
async def chat(request: ChatRequest) -> ChatResponse:
    """
    대화 엔드포인트
    
    모든 응답에 JARVIS 정체성 포함
    """
    conductor = JarvisConductor()
    result = await conductor.handle_request(request.message)
    
    return ChatResponse(
        response=result["message"],
        conductor_role="JARVIS",
        version="1.0",
        timestamp=datetime.now().isoformat(),
        metadata={
            "intent": result.get("intent"),
            "approval_required": result.get("needs_approval"),
            "brain_used": result.get("brain_name")
        }
    )
```

---

### 5단계: Memory 시스템 (장기 기억)

**목적**: 정체성 정보를 Prompt Memory에 저장

**파일**: `memory/prompt_memory.py` (새로 생성)

**구현**:
```python
# memory/prompt_memory.py

class PromptMemory:
    """프롬프트 및 정체성 메모리"""
    
    def __init__(self, storage_path: Path = None):
        self.storage = storage_path or Path("data/memory/prompt")
        self.storage.mkdir(parents=True, exist_ok=True)
    
    async def save_identity(self, version: str, identity_dict: dict):
        """JARVIS 정체성 저장"""
        identity_file = self.storage / f"jarvis_identity_v{version}.json"
        
        with open(identity_file, "w", encoding="utf-8") as f:
            json.dump({
                "version": version,
                "timestamp": datetime.now().isoformat(),
                "identity": identity_dict
            }, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 정체성 저장: {identity_file}")
    
    async def get_current_identity(self):
        """현재 정체성 조회"""
        # 가장 최신 버전 찾기
        identity_files = sorted(self.storage.glob("jarvis_identity_v*.json"))
        if identity_files:
            with open(identity_files[-1], "r", encoding="utf-8") as f:
                return json.load(f)["identity"]
        return None
    
    async def save_prompt_version(self, name: str, prompt_text: str, version: str):
        """프롬프트 버전 저장"""
        prompt_file = self.storage / f"prompt_{name}_v{version}.md"
        
        with open(prompt_file, "w", encoding="utf-8") as f:
            f.write(f"# {name} v{version}\n\n")
            f.write(f"Saved: {datetime.now().isoformat()}\n\n")
            f.write(prompt_text)
        
        print(f"✅ 프롬프트 저장: {prompt_file}")
```

---

### 6단계: UI 표시 (Pixel Office)

**목적**: 사용자에게 JARVIS의 정체성을 시각적으로 표시

**파일**: `frontend/src/components/AgentProfile.tsx` (새로 생성)

**구현**:
```typescript
// frontend/src/components/AgentProfile.tsx

import React, { useEffect, useState } from "react";

interface JarvisIdentity {
  name: string;
  role: string;
  version: string;
  description: string;
}

export const AgentProfile: React.FC = () => {
  const [identity, setIdentity] = useState<JarvisIdentity | null>(null);

  useEffect(() => {
    // API에서 정체성 조회
    fetch("/api/jarvis/identity")
      .then((res) => res.json())
      .then((data) => setIdentity(data));
  }, []);

  if (!identity) return null;

  return (
    <div className="agent-profile">
      <h2>🤖 {identity.name}</h2>
      <p className="role">{identity.role}</p>
      <p className="version">v{identity.version}</p>
      <div className="description">
        <p>{identity.description}</p>
        <ul>
          <li>✅ 지휘자: 요청을 분석하고 최적 도구를 선택합니다</li>
          <li>✅ 신중함: 모든 결정에 근거를 제시합니다</li>
          <li>✅ 투명성: 모든 작업을 기록하고 설명합니다</li>
          <li>✅ 안전성: 민감 작업은 승인 후 실행합니다</li>
        </ul>
      </div>
    </div>
  );
};
```

**CSS**:
```css
/* frontend/src/styles/agent-profile.css */

.agent-profile {
  border: 2px solid #4CAF50;
  border-radius: 8px;
  padding: 16px;
  margin: 16px 0;
  background: linear-gradient(135deg, #1e3a0f 0%, #2d5a1a 100%);
  color: #fff;
}

.agent-profile h2 {
  margin: 0 0 8px 0;
  font-size: 24px;
  color: #4CAF50;
}

.agent-profile .role {
  margin: 0 0 4px 0;
  font-size: 14px;
  color: #a8d5a8;
}

.agent-profile .version {
  margin: 0 0 12px 0;
  font-size: 12px;
  color: #888;
}

.agent-profile .description p {
  margin: 8px 0;
  font-size: 14px;
  line-height: 1.6;
}

.agent-profile ul {
  list-style: none;
  padding-left: 0;
  margin-top: 12px;
}

.agent-profile li {
  margin: 6px 0;
  padding-left: 20px;
  font-size: 13px;
}
```

---

### 7단계: 정체성 검증 엔드포인트 (자체 테스트)

**목적**: JARVIS가 자신의 정체성을 이해하는지 확인

**파일**: `backend/app/api/routers/jarvis.py` (새로 생성)

**구현**:
```python
# backend/app/api/routers/jarvis.py

from fastapi import APIRouter, HTTPException
from datetime import datetime

router = APIRouter(prefix="/api/jarvis", tags=["jarvis"])

@router.get("/identity")
async def get_identity():
    """JARVIS의 현재 정체성 조회"""
    return {
        "name": "JARVIS",
        "role": "Conductor",
        "version": "1.0",
        "type": "개인 전용 로컬 Agent OS",
        "created_at": "2026.04.18",
        "model": "JARVIS:latest (Gemma3, 4.3B)",
        "memory_types": [
            "Personal Memory",
            "Work Memory",
            "Prompt Memory",
            "Approval Memory",
            "KPI Memory",
            "File Action Memory"
        ],
        "engines": [
            "Intent Engine (요청 해석)",
            "Planning Engine (작업 분해)",
            "Routing Engine (뇌 선택)",
            "Approval Engine (승인 판정)",
            "Memory Engine (기억 관리)",
            "Reflection Engine (결과 회고)",
            "Audit Engine (행동 기록)"
        ],
        "brains": {
            "gpt_oss": "고난도 추론, 검토",
            "gemma": "친근한 대화, 요약",
            "qwen": "코드, 도구, 파일"
        },
        "characteristics": [
            "일상 대화는 하지만, 결정은 신중합니다",
            "제안은 빠르지만, 실행은 허락 후입니다",
            "메모리는 조직의 자산입니다",
            "자기개선은 정해진 절차를 따릅니다"
        ]
    }

@router.post("/verify-identity")
async def verify_identity():
    """JARVIS가 자신의 정체성을 이해하는지 검증"""
    
    # Ollama에 질문
    response = await query_jarvis_model(
        "당신은 누구입니까? 당신의 역할을 설명해주세요."
    )
    
    # 정체성 핵심 요소 확인
    required_keywords = [
        "지휘자",
        "비서",
        "승인",
        "기억",
        "신중"
    ]
    
    has_all_keywords = all(
        keyword in response for keyword in required_keywords
    )
    
    return {
        "verified": has_all_keywords,
        "timestamp": datetime.now().isoformat(),
        "response": response,
        "required_keywords": required_keywords,
        "found_keywords": [
            kw for kw in required_keywords if kw in response
        ]
    }

async def query_jarvis_model(prompt: str) -> str:
    """JARVIS 모델에 직접 질문"""
    import httpx
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://127.0.0.1:11434/api/chat",
            json={
                "model": "JARVIS:latest",
                "messages": [{"role": "user", "content": prompt}],
                "stream": False
            }
        )
    
    return response.json()["message"]["content"]
```

---

## ✅ 구현 체크리스트

### Phase 1: 즉시 (오늘)
- [ ] Ollama JARVIS:latest 모델에 v1 프롬프트 적용 완료 ✅
- [ ] `prompts/JARVIS_IDENTITY.md` 문서 작성 완료 ✅
- [ ] `backend/Modelfile_JARVIS_v1` 생성 완료 ✅

### Phase 2: 이번 주
- [ ] `backend/app/core/bootstrap.py`에 `JarvisIdentity` 클래스 추가
- [ ] `core/conductor.py`에 정체성 기반 로직 구현
- [ ] `backend/app/api/routers/jarvis.py` 새로 생성
- [ ] API에 `/api/jarvis/identity` 엔드포인트 추가

### Phase 3: 다음 주
- [ ] `memory/prompt_memory.py` 구현
- [ ] 모든 API 응답에 메타데이터 추가
- [ ] `frontend/src/components/AgentProfile.tsx` 생성
- [ ] UI에 정체성 표시 추가

### Phase 4: 검증
- [ ] `/api/jarvis/verify-identity` 엔드포인트 테스트
- [ ] JARVIS 모델이 자신의 정체성 설명 가능한지 확인
- [ ] 모든 API 응답에 conductor_role 정보 포함 확인
- [ ] UI에서 JARVIS 프로필 정보 표시 확인

---

## 🎯 최종 검증 방법

**터미널**:
```bash
# 1. JARVIS 모델 정체성 확인
ollama show JARVIS:latest

# 2. API 정체성 확인
curl http://127.0.0.1:8000/api/jarvis/identity

# 3. JARVIS 자체 검증
curl -X POST http://127.0.0.1:8000/api/jarvis/verify-identity
```

**UI**:
1. `http://127.0.0.1:5173` 접속
2. Agent Profile 컴포넌트 확인
3. JARVIS 정체성 정보 표시 확인

**Ollama 대화**:
```
사용자: "당신은 누구인가요?"

JARVIS: "저는 JARVIS입니다. 저는 지휘자이자 당신의 비서입니다.
제 역할은... (v1 정체성 기반 응답)"
```

---

## 📚 참고 문서

- `prompts/JARVIS_IDENTITY.md` - 정체성 전문
- `docs/ARCHITECTURE_v1_DESIGN.md` - 설계도
- `docs/MIGRATION_ROADMAP.md` - 이식 계획
- `backend/Modelfile_JARVIS_v1` - Ollama 모델 파일

