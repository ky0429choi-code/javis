from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    mode: str = Field(default="chat")
    context: dict = Field(default_factory=dict)

class TaskRequest(BaseModel):
    title: str
    summary: str = ""
    task_type: str = "general"
    priority: str = "medium"
    user_kpi: str | None = None
    linked_docs: list[str] = Field(default_factory=list)
    materials: list[str] = Field(default_factory=list)
