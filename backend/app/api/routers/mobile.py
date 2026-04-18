from fastapi import APIRouter, Depends, Query
from app.api.deps import verify_shared_key
from app.core.orchestrator import orchestrator
from app.schemas.chat import ChatRequest
import logging

logger = logging.getLogger(__name__)
router = APIRouter(tags=["mobile"])

@router.get("/mobile/info")
async def mobile_info(_: str = Depends(verify_shared_key)):
    """
    모바일 앱 초기화 정보
    - 서버 상태
    - API 엔드포인트
    - 버전 정보
    """
    return {
        "ok": True,
        "data": {
            "app_name": "JARVIS Agent Office",
            "version": "5.0.0",
            "status": "online",
            "endpoints": {
                "chat": "/api/jarvis/chat",
                "tasks": "/api/tasks",
                "approvals": "/api/approvals",
                "health": "/api/health",
            },
            "features": {
                "chat": True,
                "task_management": True,
                "approval_workflow": True,
                "real_time_sync": False,  # WebSocket support coming soon
            }
        }
    }

@router.post("/mobile/chat")
async def mobile_chat(
    payload: ChatRequest,
    _: str = Depends(verify_shared_key)
):
    """
    모바일 앱용 채팅 API
    모바일에서 `/api/mobile/chat` 로 메시지를 전송합니다.
    
    Request:
    {
        "message": "자비스, 파일을 만들어줘",
        "mode": "chat"
    }
    
    Response:
    {
        "ok": true,
        "data": {
            "status": "completed",
            "message": "작업 완료됨",
            "execution_steps": [...],
            "suggested_actions": [...]
        }
    }
    """
    try:
        data = await orchestrator.handle_request(payload.message)
        return {"ok": True, "data": data}
    except Exception as e:
        logger.error(f"Mobile chat error: {e}")
        return {
            "ok": False,
            "data": {
                "status": "error",
                "message": str(e)
            }
        }

@router.get("/mobile/status")
async def mobile_status(_: str = Depends(verify_shared_key)):
    """
    실시간 상태 조회
    - 진행 중인 작업
    - 대기 중인 승인
    - 시스템 상태
    """
    from app.api.routers import tasks, approvals
    
    try:
        # Get tasks and approvals
        tasks_res = await tasks.get_tasks()
        approvals_res = await approvals.list_approvals()
        
        return {
            "ok": True,
            "data": {
                "timestamp": __import__('time').time(),
                "active_tasks": len(tasks_res.get("data", [])),
                "pending_approvals": len(approvals_res.get("data", [])),
                "system_ready": True,
            }
        }
    except Exception as e:
        logger.error(f"Status check error: {e}")
        return {
            "ok": False,
            "data": {"error": str(e)}
        }

@router.post("/mobile/sync")
async def mobile_sync(
    _: str = Depends(verify_shared_key),
    last_sync: float = Query(0.0)
):
    """
    모바일 앱 동기화
    - 마지막 동기화 이후의 변경사항 반환
    - last_sync: Unix timestamp (기본값 0 = 전체 동기화)
    """
    return {
        "ok": True,
        "data": {
            "timestamp": __import__('time').time(),
            "changes": {
                "tasks": [],
                "approvals": [],
                "messages": [],
            }
        }
    }
