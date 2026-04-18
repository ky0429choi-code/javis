from fastapi import APIRouter, Depends
from app.api.deps import verify_shared_key
from app.core.orchestrator import orchestrator
from app.memory.repository import Repository

router = APIRouter(tags=["approvals"])
repo = Repository()

@router.get("/approvals")
def list_approvals(_: str = Depends(verify_shared_key)) -> dict:
    return {"ok": True, "data": repo.list_approvals()}

@router.post("/approvals/{request_id}/approve")
def approve(request_id: str, _: str = Depends(verify_shared_key)) -> dict:
    # Logic moved to orchestrator in full implementation
    return {"ok": True, "data": {"status": "approved", "id": request_id}}

@router.post("/approvals/{request_id}/reject")
def reject(request_id: str, _: str = Depends(verify_shared_key)) -> dict:
    return {"ok": True, "data": {"status": "rejected", "id": request_id}}
