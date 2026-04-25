from pathlib import Path

PROMPTS = {
    "master_prompt.md": """# Master Prompt\n너는 Jarvis다. 너의 최우선 역할은 작업 수행이 아니라 지휘와 통제다.\n파일 생성/수정/삭제는 승인 큐를 거쳐야 한다.\n결과는 항상 로그와 메모리에 기록한다.\n""",
    "task_prompt.md": """# Task Prompt\n현재 작업의 목표, 출력 형식, 제약 조건을 정의한다.\n""",
    "redteam_prompt.md": """# Red Team Prompt\n누락, 과장, 승인 누락, 파일 작업 위험을 먼저 점검한다.\n""",
}


def ensure_prompt_files() -> None:
    root = Path(__file__).resolve().parents[2] / "prompts"
    root.mkdir(parents=True, exist_ok=True)
    for name, content in PROMPTS.items():
        path = root / name
        if not path.exists():
            path.write_text(content, encoding="utf-8")
