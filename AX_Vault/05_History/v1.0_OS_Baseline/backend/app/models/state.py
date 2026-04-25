from pydantic import BaseModel, Field

class JarvisState(BaseModel):
    current_task_id: str | None = None
    current_goal: str | None = None
    current_mode: str = "idle"
    selected_brain: str = "gemma"
    requires_approval: bool = False
    risk_level: str = "low"
    notes: list[str] = Field(default_factory=list)
