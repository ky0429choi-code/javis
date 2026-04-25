from fastapi import APIRouter, Depends
from app.api.deps import verify_shared_key
from app.memory.repository import Repository

router = APIRouter(tags=["prompts"])
repo = Repository()

@router.get("/prompts")
def get_prompts(_: str = Depends(verify_shared_key)) -> dict:
    return {"ok": True, "data": repo.get_prompts()}

@router.put("/prompts")
def save_prompts(payload: dict, _: str = Depends(verify_shared_key)) -> dict:
    return {"ok": True, "data": repo.save_prompts(payload)}

@router.get("/logs")
def get_logs(_: str = Depends(verify_shared_key)) -> dict:
    return {"ok": True, "data": repo.list_logs()}
