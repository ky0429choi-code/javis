import os
import shutil
from pathlib import Path
import datetime

def create_baseline():
    root_dir = Path("c:/Users/ky042/AI/개발/jarvis_agent_office_v1")
    history_base_dir = root_dir / "AX_Vault" / "05_History"
    baseline_name = "v1.0_OS_Baseline"
    target_dir = history_base_dir / baseline_name

    # Exclusions
    exclude_items = {".git", ".venv", "__pycache__", "node_modules", "data", "05_History", "AX_Vault"}

    if target_dir.exists():
        # Clear it if it's partial
        shutil.rmtree(target_dir)

    print(f"Creating baseline at {target_dir}...")
    target_dir.mkdir(parents=True, exist_ok=True)

    for item in root_dir.iterdir():
        if item.name in exclude_items:
            continue
        
        try:
            if item.is_dir():
                shutil.copytree(item, target_dir / item.name, 
                                ignore=shutil.ignore_patterns(".git", ".venv", "__pycache__", "node_modules"))
            else:
                shutil.copy2(item, target_dir / item.name)
        except Exception as e:
            print(f"Skipping {item.name}: {e}")

    # Manually copy AX_Vault subfolders EXCEPT 05_History
    vault_dir = root_dir / "AX_Vault"
    target_vault = target_dir / "AX_Vault"
    target_vault.mkdir(exist_ok=True)
    
    for sub in vault_dir.iterdir():
        if sub.is_dir() and sub.name != "05_History":
            shutil.copytree(sub, target_vault / sub.name, 
                            ignore=shutil.ignore_patterns(".git", "__pycache__"))

    # Create a small metadata file
    with open(target_dir / "metadata.json", "w", encoding="utf-8") as f:
        f.write(f'{{ "version": "1.0", "description": "OS Independence Baseline", "timestamp": "{datetime.datetime.now().isoformat()}" }}')

    print("Baseline creation complete.")

if __name__ == "__main__":
    create_baseline()
