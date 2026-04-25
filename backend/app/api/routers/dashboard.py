import asyncio
import logging
import json
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from typing import Dict, Any, List
from app.core.confidence_collector import get_confidence_collector
from app.memory.repository import Repository
from app.harness.skills.registry import skill_registry

router = APIRouter()
logger = logging.getLogger(__name__)
repo = Repository()

@router.get("/health")
async def get_health():
    """시스템 헬스체크 데이터"""
    # 임의의 데이터 (실제 연동 필요)
    return {
        "status": "online",
        "ollama": "running",
        "active_skills": len(skill_registry.list_skills()),
        "total_vault_nodes": 42, # 예시
        "hitl_pending": len(repo.get_pending_approvals())
    }

@router.get("/confidence/trend")
async def get_confidence_trend():
    """신뢰도 추이 데이터 (Chart.js용)"""
    collector = get_confidence_collector()
    # 최근 10개의 신뢰도 데이터를 에이전트별로 정리
    return {
        "labels": ["Task1", "Task2", "Task3", "Task4", "Task5"],
        "planner": [0.95, 0.92, 0.94, 0.88, 0.91],
        "executor": [0.85, 0.88, 0.82, 0.75, 0.89],
        "reviewer": [0.98, 0.97, 0.99, 0.95, 0.98]
    }

@router.get("/approvals/pending")
async def get_pending_approvals():
    """승인 대기 큐"""
    return repo.get_pending_approvals()

@router.get("/skills/logs")
async def get_skill_logs():
    """스킬 실행 로그"""
    # Repository에서 최근 로그 가져오기 (예시)
    return [
        {"skill": "file_skill", "status": "success", "time": "10:20:05"},
        {"skill": "code_generate", "status": "ralf_fixed", "time": "10:25:30"},
        {"skill": "web_search", "status": "cached", "time": "10:30:12"}
    ]

from pydantic import BaseModel
from app.core.event_bus import event_bus
from app.core.conductor import conductor

class DashboardCommand(BaseModel):
    command: str

@router.post("/command")
async def post_command(cmd: DashboardCommand):
    """대시보드에서 자비스 명령 전역 전달"""
    # 백그라운드 태스크로 실행
    asyncio.create_task(conductor.run(cmd.command))
    return {"status": "accepted", "command": cmd.command}

@router.get("/tasks/stream")
async def tasks_stream(request: Request):
    """실시간 태스크 스트림 (SSE) - EventBus 연동"""
    async def event_generator():
        # EventBus 구독 큐 생성
        queue = event_bus.subscribe()
        try:
            while True:
                if await request.is_disconnected():
                    break
                
                # 큐에서 이벤트 대기
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=1.0)
                    yield f"data: {json.dumps(event)}\n\n"
                except asyncio.TimeoutError:
                    # Keep-alive ping
                    yield ": ping\n\n"
                    continue
                    
        finally:
            event_bus.unsubscribe(queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
