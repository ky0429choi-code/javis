from fastapi import APIRouter
from typing import Optional
import logging
from app.core_v4.llm.router import router_v4

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v4/hybrid", tags=["v4_hybrid_routing"])

@router.post("/llm/query")
async def query_llm(
    query: str,
    system_prompt: Optional[str] = None,
    task_type: str = "immediate"
):
    """
    V4 Intelligent LLM Routing Query.
    Utilizes the new modular Core V4 Router.
    """
    try:
        # Call the unified V4 router
        response = await router_v4.call(
            prompt=query, 
            system=system_prompt, 
            task_type=task_type
        )
        
        return {
            "status": "success",
            "ok": True,
            "response": response,
            "v4": True
        }
    except Exception as e:
        logger.error(f"V4 LLM Routing error: {e}")
        return {
            "status": "error",
            "error": str(e),
        }
