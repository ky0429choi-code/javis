from pathlib import Path
from datetime import datetime

class BackupTool:
    def backup_text(self, base_dir: str, name: str, content: str) -> dict:
        target = Path(base_dir) / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{name}"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding='utf-8')
        return {'ok': True, 'path': str(target)}
