from fastapi import APIRouter, Depends
from app.api.deps import verify_shared_key
from app.core.orchestrator import orchestrator
from app.memory.repository import Repository
from app.schemas.chat import TaskRequest

router = APIRouter(tags=["tasks"])
repo = Repository()

@router.get("/tasks")
def list_tasks(_: str = Depends(verify_shared_key)) -> dict:
    return {"ok": True, "data": repo.list_tasks()}

@router.post("/tasks")
async def create_task(payload: TaskRequest, _: str = Depends(verify_shared_key)) -> dict:
    # Integrated with Orchestrator handle_request in AI Core 4.0
    data = await orchestrator.handle_request(f"작업 생성: {payload.title}")
    return {"ok": True, "data": data}
