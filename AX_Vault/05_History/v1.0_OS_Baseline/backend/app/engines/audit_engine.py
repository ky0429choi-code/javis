from app.memory.repository import Repository

class AuditEngine:
    def __init__(self, repo: Repository) -> None:
        self.repo = repo

    def log(self, event_type: str, payload: dict) -> None:
        self.repo.append_log(event_type, payload)
