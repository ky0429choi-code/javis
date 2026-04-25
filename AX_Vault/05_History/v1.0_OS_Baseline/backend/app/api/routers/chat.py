from fastapi import APIRouter, Depends
import logging
from app.api.deps import verify_shared_key
from app.core.orchestrator import orchestrator
from app.schemas.chat import ChatRequest

logger = logging.getLogger(__name__)
router = APIRouter(tags=["chat"])

@router.post("/jarvis/chat")
async def jarvis_chat(payload: ChatRequest, _: str = Depends(verify_shared_key)) -> dict:
    """
    JARVIS Unified Chat API (Core 4.0).
    Routes through ChatModeClassifier:
    - chat mode: Direct LLM response (natural conversation)
    - task mode: Conductor pipeline (Plan → Execute → Review)
    - command mode: Slash command processing
    """
    try:
        message = payload.message
        context = {
            "mode": payload.mode or "auto",
            "user_id": "owner"
        }
        
        logger.info(f"Chat API: [{context['mode']}] {message[:50]}...")
        
        data = await orchestrator.handle_request(message, context)
        
        return {"ok": True, "data": data}
        
    except Exception as e:
        logger.error(f"Chat API: Fatal Error: {e}")
        return {
            "ok": False,
            "error": str(e),
            "data": {"message": "시스템 오류가 발생했습니다. 로그를 확인해주세요."}
        }
