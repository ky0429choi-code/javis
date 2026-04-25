import os
import logging
from pathlib import Path
from typing import List, Dict

logger = logging.getLogger(__name__)

class SystemIngestor:
    """
    JARVIS System Ingestor.
    Scans the own codebase and rules to provide 'Self-Awareness' data.
    """
    def __init__(self, root_path: str):
        self.root = Path(root_path)
        self.exclude_dirs = {".git", ".venv", "__pycache__", "node_modules", "data", "AX_Vault", "dist"}
        self.include_extensions = {".py", ".md", ".json"}

    def scan_project(self) -> Dict[str, Any]:
        """Scans the project and returns a summary of the architecture and rules."""
        logger.info(f"System Ingestor: Scanning {self.root}...")
        
        summary = {
            "files": [],
            "rules": [],
            "architecture_overview": ""
        }

        # 1. Scan Rules (AX_Vault/01_Rules)
        rules_path = self.root / "AX_Vault" / "01_Rules"
        if rules_path.exists():
            for rule_file in rules_path.glob("*.md"):
                content = rule_file.read_text(encoding="utf-8")
                summary["rules"].append({"name": rule_file.name, "content": content[:1000]})

        # 2. Scan Core Logic
        core_path = self.root / "backend" / "app"
        if core_path.exists():
            for path in core_path.rglob("*"):
                if any(ex in path.parts for ex in self.exclude_dirs):
                    continue
                if path.suffix in self.include_extensions:
                    try:
                        content = path.read_text(encoding="utf-8")
                        # Basic logic: look for class/def to summarize
                        functions = [line.strip() for line in content.splitlines() if line.strip().startswith(("def ", "class "))]
                        summary["files"].append({
                            "path": str(path.relative_to(self.root)),
                            "definitions": functions[:10],
                            "size": path.stat().st_size
                        })
                    except Exception as e:
                        logger.warning(f"Failed to read {path}: {e}")

        return summary

    def get_ingestion_prompt(self, summary: dict) -> str:
        """Formats the scan results into a prompt for the Wiki Agent."""
        prompt = "## JARVIS 시스템 자가 분석 데이터\n\n"
        prompt += "### 1. 규칙 및 지침\n"
        for r in summary["rules"]:
            prompt += f"- **{r['name']}**: {r['content'][:200]}...\n"
        
        prompt += "\n### 2. 코드베이스 구조\n"
        for f in summary["files"][:20]: # Limit for token safety
            prompt += f"- `{f['path']}`: {', '.join(f['definitions'])}\n"
        
        prompt += "\n\n위 데이터를 분석하여 JARVIS AI OS의 '정체성(Identity)'과 '운영 로직(Operating Logic)'을 정의하고 02_Knowledge/SYSTEM_MAP.md에 저장할 내용을 생성하세요."
        return prompt

if __name__ == "__main__":
    ingestor = SystemIngestor("c:/Users/ky042/AI/개발/jarvis_agent_office_v1")
    res = ingestor.scan_project()
    print(f"Scanned {len(res['files'])} files and {len(res['rules'])} rules.")
