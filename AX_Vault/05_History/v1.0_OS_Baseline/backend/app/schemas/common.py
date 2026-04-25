from pydantic import BaseModel

class ApiResponse(BaseModel):
    ok: bool = True
    data: dict | list | str | None = None
