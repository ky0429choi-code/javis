from uuid import uuid4
from app.models.approval import ApprovalRequestModel

SENSITIVE = {"create_file", "modify_file", "delete_file", "move_file", "memory_persist"}

class ApprovalEngine:
    def needs_approval(self, action_type: str) -> bool:
        return action_type in SENSITIVE

    def build_request(self, action_type: str, target_path: str, reason: str, requested_by: str, content: str | None = None) -> ApprovalRequestModel:
        return ApprovalRequestModel(
            request_id=f"REQ-{uuid4().hex[:8]}",
            action_type=action_type,
            target_path=target_path,
            reason=reason,
            requested_by=requested_by,
            content=content
        )
