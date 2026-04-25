from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum

class HookAction(str, Enum):
    PASS = "pass"
    BLOCK = "block"
    PENDING_APPROVAL = "pending_approval"

class IntentResult(BaseModel):
    goal: str
    mode: str = "chat"
    context: Dict[str, Any] = Field(default_factory=dict)

class SubTask(BaseModel):
    title: str
    action: str
    path: str
    instruction: str

class PlanResult(BaseModel):
    goal: str
    priority: str = "medium"
    steps: List[SubTask] = Field(default_factory=list)
    status: str = "planned"
    instruction: Optional[str] = None

class MemoryType(str, Enum):
    LORE = "lore"       # 결정 내역 및 판단 근거
    KPI = "kpi"         # 성과 지표 및 통계
    RULE = "rule"       # 운영 규칙 및 프로토콜
    GOAL = "goal"       # 장기 목표 및 미션
    PATTERN = "pattern" # 실행 패턴 및 노하우

class MemoryNode(BaseModel):
    type: MemoryType
    context: str = "general"
    content: Any
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[str] = None

class RoutingResult(BaseModel):
    brain: str
    model: str
    provider: str
    is_local: bool = True

class HookResult(BaseModel):
    action: HookAction
    reason: Optional[str] = None
    pattern: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None
