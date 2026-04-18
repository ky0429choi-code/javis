import json
import sqlite3
from pathlib import Path
from typing import Any
from app.utils.settings import get_settings

class Repository:
    def __init__(self) -> None:
        settings = get_settings()
        self.db_path = Path(__file__).resolve().parents[3] / settings.sqlite_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self):
        return sqlite3.connect(self.db_path)

    def append_log(self, event_type: str, payload: dict) -> None:
        with self.connect() as con:
            con.execute("INSERT INTO logs (event_type, payload) VALUES (?, ?)", (event_type, json.dumps(payload, ensure_ascii=False)))
            con.commit()

    def list_logs(self, limit: int = 50) -> list[dict[str, Any]]:
        with self.connect() as con:
            rows = con.execute("SELECT id, event_type, payload, created_at FROM logs ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [{"id": r[0], "event_type": r[1], "payload": json.loads(r[2]), "created_at": r[3]} for r in rows]

    def create_task(self, title: str, summary: str, task_type: str, priority: str, user_kpi: str | None) -> dict:
        with self.connect() as con:
            cur = con.execute(
                "INSERT INTO tasks (title, summary, task_type, priority, user_kpi, status) VALUES (?, ?, ?, ?, ?, ?)",
                (title, summary, task_type, priority, user_kpi, "pending"),
            )
            con.commit()
            task_id = cur.lastrowid
        return self.get_task(task_id)

    def get_task(self, task_id: int) -> dict:
        with self.connect() as con:
            row = con.execute("SELECT id, title, summary, task_type, priority, user_kpi, status, created_at FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not row:
            raise ValueError("TASK_NOT_FOUND")
        return {
            "id": row[0], "title": row[1], "summary": row[2], "task_type": row[3],
            "priority": row[4], "user_kpi": row[5], "status": row[6], "created_at": row[7]
        }

    def list_tasks(self) -> list[dict]:
        with self.connect() as con:
            rows = con.execute("SELECT id, title, summary, task_type, priority, user_kpi, status, created_at FROM tasks ORDER BY id DESC").fetchall()
        return [{"id": r[0], "title": r[1], "summary": r[2], "task_type": r[3], "priority": r[4], "user_kpi": r[5], "status": r[6], "created_at": r[7]} for r in rows]

    def create_approval(self, req: dict) -> dict:
        with self.connect() as con:
            cur = con.execute(
                "INSERT INTO approvals (request_id, action_type, target_path, reason, requested_by, content, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (req["request_id"], req["action_type"], req["target_path"], req["reason"], req["requested_by"], req.get("content"), req["status"]),
            )
            con.commit()
        return self.get_approval(req["request_id"])

    def list_approvals(self) -> list[dict]:
        with self.connect() as con:
            rows = con.execute("SELECT request_id, action_type, target_path, reason, requested_by, content, status, created_at FROM approvals ORDER BY id DESC").fetchall()
        return [{"request_id": r[0], "action_type": r[1], "target_path": r[2], "reason": r[3], "requested_by": r[4], "content": r[5], "status": r[6], "created_at": r[7]} for r in rows]

    def get_approval(self, request_id: str) -> dict:
        with self.connect() as con:
            r = con.execute("SELECT request_id, action_type, target_path, reason, requested_by, content, status, created_at FROM approvals WHERE request_id = ?", (request_id,)).fetchone()
        if not r:
            raise ValueError("APPROVAL_NOT_FOUND")
        return {"request_id": r[0], "action_type": r[1], "target_path": r[2], "reason": r[3], "requested_by": r[4], "content": r[5], "status": r[6], "created_at": r[7]}

    def update_approval(self, request_id: str, status: str) -> dict:
        with self.connect() as con:
            con.execute("UPDATE approvals SET status = ? WHERE request_id = ?", (status, request_id))
            con.commit()
        return self.get_approval(request_id)

    def get_prompts(self) -> dict:
        root = Path(__file__).resolve().parents[3] / "prompts"
        return {
            "master": (root / "master_prompt.md").read_text(encoding="utf-8"),
            "task": (root / "task_prompt.md").read_text(encoding="utf-8"),
            "redteam": (root / "redteam_prompt.md").read_text(encoding="utf-8"),
        }

    def save_prompts(self, prompts: dict) -> dict:
        root = Path(__file__).resolve().parents[3] / "prompts"
        mapping = {
            "master": "master_prompt.md",
            "task": "task_prompt.md",
            "redteam": "redteam_prompt.md",
        }
        for key, filename in mapping.items():
            if key in prompts:
                (root / filename).write_text(prompts[key], encoding="utf-8")
        return self.get_prompts()


def initialize_database() -> None:
    repo = Repository()
    with repo.connect() as con:
        con.execute(
            "CREATE TABLE IF NOT EXISTS logs (id INTEGER PRIMARY KEY AUTOINCREMENT, event_type TEXT NOT NULL, payload TEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
        )
        con.execute(
            "CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, summary TEXT, task_type TEXT, priority TEXT, user_kpi TEXT, status TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
        )
        con.execute(
            "CREATE TABLE IF NOT EXISTS approvals (id INTEGER PRIMARY KEY AUTOINCREMENT, request_id TEXT UNIQUE NOT NULL, action_type TEXT, target_path TEXT, reason TEXT, requested_by TEXT, content TEXT, status TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
        )
        con.commit()
