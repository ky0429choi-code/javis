from pydantic import BaseModel

class ApprovalRequestModel(BaseModel):
    request_id: str
    action_type: str
    target_path: str
    reason: str
    requested_by: str
    content: str | None = None
    status: str = "pending"
