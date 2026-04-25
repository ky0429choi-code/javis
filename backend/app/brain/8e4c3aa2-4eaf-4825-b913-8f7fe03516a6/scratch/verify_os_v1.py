import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(os.getcwd()) / "backend"))

async def test_verification():
    print("--- Verification Test Starting ---")
    
    # 1. System Ingestor Test
    from app.core.system_ingestor import SystemIngestor
    ing = SystemIngestor(os.getcwd())
    summary = ing.scan_project()
    print(f"Ingestor: Found {len(summary['files'])} files.")
    
    # 2. Backup Tool (FileTool) Test
    from app.tools.file_tool import FileTool
    ft = FileTool()
    test_path = "AX_Vault/test_backup_logic.txt"
    ft.create_file(test_path, "Version 1: Baseline")
    ft.update_file(test_path, "Version 2: Updated")
    
    import glob
    backups = glob.glob("AX_Vault/05_History/backups/*_test_backup_logic.txt")
    if backups:
        print(f"OK: Backup created -> {backups[0]}")
    else:
        print("FAIL: Backup not found.")

    # 3. Core Protection Test
    from app.schemas.v4_core import SubTask
    from app.agents.executor import executor
    
    core_task = SubTask(
        id="test_core",
        title="Modify Core",
        action="update_file",
        path="backend/app/core/conductor.py",
        instruction="Modify core logic"
    )
    
    print("Security: Testing core file protection...")
    res = await executor.execute(core_task)
    if res.get("status") == "pending_approval" and res.get("pattern") == "CORE_FILE_PROTECTION":
        print("OK: Core file modification BLOCKED for approval.")
    else:
        print(f"FAIL: Core file protection logic. Result: {res}")

    print("--- Verification Test Completed ---")

if __name__ == "__main__":
    asyncio.run(test_verification())
