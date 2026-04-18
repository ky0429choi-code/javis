from fastapi import APIRouter, Depends
import logging
from app.api.deps import verify_shared_key
from app.core.orchestrator import orchestrator
from app.llm_router import router as llm_router
from app.schemas.chat import ChatRequest

logger = logging.getLogger(__name__)
router = APIRouter(tags=["chat"])

class ChatModeClassifier:
    """
    Routes requests to appropriate handler based on mode/content.
    Modes:
    - chat: simple conversation (Direct LLM Call)
    - task: complex task with steps (Direct LLM for now, can extend)
    - command: slash commands (Orchestrator)
    """
    
    @staticmethod
    def classify(message: str, mode: str = None) -> str:
        """Classify request type."""
        # Explicit mode
        if mode and mode in ["chat", "task", "command"]:
            return mode
        
        # Heuristics
        if message.startswith("/"):
            return "command"
        
        # If message is complex query/task description
        task_keywords = ["파일", "작성", "생성", "코드", "수정", "업데이트", "저장", "작업", 
                         "create", "write", "generate", "code", "file", "task", "update"]
        if any(kw in message.lower() for kw in task_keywords):
            return "task"
        
        # Default to chat for simple queries/conversations
        return "chat"

class SimpleChat:
    """Direct simple chat without complex conductors."""
    
    async def chat(self, message: str) -> dict:
        """Simple direct chat to LLM."""
        try:
            logger.info(f"SimpleChat: Processing message: {message[:50]}...")
            
            # Use simple system prompt
            system_prompt = "You are JARVIS, a helpful AI assistant. Respond helpfully and concisely."
            
            # call LLM directly (JARVIS model)
            response = await llm_router.call(
                prompt=message,
                system=system_prompt
            )
            
            logger.info(f"SimpleChat: LLM response received")
            
            return {
                "intent": {"goal": message, "mode": "chat"},
                "plan": {"mode": "chat", "approach": "direct"},
                "route": {"brain": "default", "reason": "Direct LLM call"},
                "message": response,
                "reflection": {"quality": "good", "confidence": 0.8},
                "suggested_actions": []
            }
        except Exception as e:
            logger.error(f"SimpleChat failed: {e}")
            return {
                "intent": {"goal": message, "mode": "chat"},
                "message": f"Sorry, I encountered an error: {str(e)}",
                "error": str(e)
            }

class SimpleTask:
    """Simple task handler - extended chat for task-like requests."""
    
    async def execute(self, message: str) -> dict:
        """Execute simple task using LLM."""
        try:
            logger.info(f"SimpleTask: Processing task: {message[:50]}...")
            
            # Task system prompt
            system_prompt = """You are JARVIS task handler. For task requests:
1. Acknowledge what task was requested
2. Explain what steps would be taken
3. Provide a concise action plan

Format: Keep response practical and actionable."""
            
            # Call LLM for task planning
            response = await llm_router.call(
                prompt=message,
                system=system_prompt
            )
            
            logger.info(f"SimpleTask: Task processed")
            
            return {
                "identity": "Jarvis",
                "message": response,
                "status": "planned",
                "goal": message,
                "priority": "medium",
                "plan": {"steps": [], "status": "outlined"},
                "execution_steps": [],
                "knowledge": {"ok": False, "message": "Task planned"}
            }
        except Exception as e:
            logger.error(f"SimpleTask failed: {e}")
            return {
                "identity": "Jarvis",
                "message": f"Task processing error: {str(e)}",
                "status": "error",
                "error": str(e)
            }

# Global instances
simple_chat = SimpleChat()
simple_task = SimpleTask()

@router.post("/jarvis/chat")
async def jarvis_chat(payload: ChatRequest, _: str = Depends(verify_shared_key)) -> dict:
    """
    Main chat endpoint with intelligent routing.
    
    Request schema: ChatRequest
    - message: str (user input)
    - mode: str (optional: "chat", "task", "command")
    
    Returns:
    - {"ok": true, "data": {...response data...}}
    """
    try:
        message = payload.message
        mode = getattr(payload, "mode", None) or "auto"
        
        logger.info(f"Chat API: Received message (mode={mode}): {message[:50]}...")
        
        # 1. Classify request type
        if mode == "auto":
            mode = ChatModeClassifier.classify(message)
            logger.info(f"Chat API: Auto-classified as mode='{mode}'")
        
        # 2. Route to appropriate handler
        if mode == "chat":
            logger.debug("Chat API: Routing to SimpleChat")
            data = await simple_chat.chat(message)
        elif mode == "task":
            logger.debug("Chat API: Routing to SimpleTask")
            data = await simple_task.execute(message)
        else:  # command or default
            logger.debug("Chat API: Routing to Orchestrator (commands)")
            data = await orchestrator.handle_request(message)
        
        return {"ok": True, "data": data}
        
    except Exception as e:
        logger.error(f"Chat API: Error processing request: {e}")
        return {
            "ok": False,
            "error": str(e),
            "data": {"message": "Error processing  request"}
        }
