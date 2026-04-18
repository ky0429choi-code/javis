"""
JARVIS v5  FastAPI Application

엔드포인트:
  GET  /api/health           Ollama 포함 전체 헬스 체크
  POST /api/jarvis/chat      단일 턴 채팅
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from core.bootstrap import run_bootstrap
from core.hooks import HookManager, HookMode, register_default_hooks
from core.llm_router import LLMRouter
from core.orchestrator import Orchestrator
from core.planner import Planner
from core.tool_registry import ToolRegistry

# ─────────────────────────────────────────────
#  Logging
# ─────────────────────────────────────────────

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)

OLLAMA_BASE = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")


# ─────────────────────────────────────────────
#  Lifespan (startup / shutdown)
# ─────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 시작
    degraded = not await run_bootstrap()
    app.state.degraded = degraded

    # 공유 싱글턴 초기화
    router = LLMRouter()
    await router.refresh_available_models()

    registry = ToolRegistry()
    # TODO: 실제 tool 등록  registry.register(MyTool())

    hook_mode = HookMode(os.getenv("HOOK_MODE", "WARN").upper())
    hook_manager = HookManager(mode=hook_mode)
    register_default_hooks(hook_manager)

    app.state.router       = router
    app.state.registry     = registry
    app.state.hook_manager = hook_manager
    app.state.planner      = Planner(router)
    app.state.orchestrator = Orchestrator(registry)

    yield

    # 종료 (필요 시 정리 작업)


# ─────────────────────────────────────────────
#  App
# ─────────────────────────────────────────────

app = FastAPI(title="JARVIS v5", version="5.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────
#  Schemas
# ─────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    model_key: str = "jarvis"


class ChatResponse(BaseModel):
    reply: str
    goal: str
    steps_executed: int
    success: bool
    warnings: List[Dict[str, Any]] = []


class HealthResponse(BaseModel):
    status: str
    ollama: bool
    degraded: bool
    available_models: List[str]


# ─────────────────────────────────────────────
#  Routes
# ─────────────────────────────────────────────

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    ollama_ok = False
    available: List[str] = []

    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{OLLAMA_BASE}/api/tags")
            if resp.status_code == 200:
                ollama_ok = True
                available = [m["name"] for m in resp.json().get("models", [])]
    except Exception:
        pass

    return HealthResponse(
        status="degraded" if app.state.degraded else "ok",
        ollama=ollama_ok,
        degraded=app.state.degraded,
        available_models=available,
    )


@app.get("/api/tasks")
async def get_tasks():
    return {"ok": True, "data": []}


@app.get("/api/approvals")
async def get_approvals():
    return {"ok": True, "data": []}


@app.post("/api/approvals/request")
async def request_approval(payload: Dict[str, Any]):
    return {"ok": True, "data": {"request_id": "test_req_1"}}


@app.post("/api/approvals/approve")
async def approve_request(request_id: str):
    return {"ok": True, "data": {"status": "approved", "request_id": request_id}}


@app.post("/api/approvals/reject")
async def reject_request(request_id: str):
    return {"ok": True, "data": {"status": "rejected", "request_id": request_id}}


@app.post("/api/jarvis/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    planner: Planner           = app.state.planner
    orchestrator: Orchestrator = app.state.orchestrator
    hook_manager: HookManager  = app.state.hook_manager

    # 1) 입력 훅
    input_ctx = {"messages": [{"role": "user", "content": req.message}]}
    warnings = [
        {"rule": v.rule, "detail": v.detail}
        for v in hook_manager.run("input", input_ctx)
    ]

    # 2) 계획 수립
    try:
        plan = planner.create_plan(req.message)
    except Exception as exc:
        logger.error("Planner error: %s", exc)
        raise HTTPException(status_code=500, detail="Planning failed")

    # 3) 계획 훅
    plan_ctx = {"steps": [s.to_dict() for s in plan.steps]}
    warnings += [
        {"rule": v.rule, "detail": v.detail}
        for v in hook_manager.run("plan", plan_ctx)
    ]

    # 4) 실행
    try:
        result = await orchestrator.run(plan)
    except Exception as exc:
        logger.error("Orchestrator error: %s", exc)
        raise HTTPException(status_code=500, detail="Execution failed")

    reply = str(result.final_output or "작업을 완료했습니다.")

    return ChatResponse(
        reply=reply,
        goal=plan.goal,
        steps_executed=len(result.step_results),
        success=result.success,
        warnings=warnings,
    )
