import os
from pathlib import Path


class FileTool:
    def _validate_path(self, target_path: str) -> None:
        """Ensures the target path is within the workspace and safe."""
        abs_target = Path(target_path).resolve()
        workspace_root = Path(os.getcwd()).resolve()

        if workspace_root not in abs_target.parents and abs_target != workspace_root:
            raise PermissionError(
                f"❌ 도구 보안 위반: 허가되지 않은 경로({target_path})입니다."
            )

    def create_file(self, target_path: str, content: str = "") -> dict:
        self._validate_path(target_path)
        path = Path(target_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return {"ok": True, "path": str(path), "action": "create_file"}

    def update_file(self, target_path: str, content: str) -> dict:
        self._validate_path(target_path)
        path = Path(target_path)
        path.write_text(content, encoding="utf-8")
        return {"ok": True, "path": str(path), "action": "update_file"}

    def delete_file(self, target_path: str) -> dict:
        self._validate_path(target_path)
        path = Path(target_path)
        if path.exists():
            path.unlink()
        return {"ok": True, "path": str(path), "action": "delete_file"}