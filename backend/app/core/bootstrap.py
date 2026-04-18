import httpx
import subprocess
import os
from app.memory.repository import initialize_database
from app.prompts_loader import ensure_prompt_files
from app.utils.settings import get_settings
from app.harness.hooks import get_hook_status
from app.config import ACTIVE_HOOKS, HOOK_MODE

def bootstrap_application() -> None:
    settings = get_settings()
    
    print(f"""
+------------------------------------------------+
|  JARVIS Configuration Summary                  |
+------------------------------------------------+
| Hook Mode:    {HOOK_MODE.value.upper():<32} |
| Protection:   {'ON' if ACTIVE_HOOKS.get('protection_enabled') else 'OFF':<32} |
| Reminder:     {'ON' if ACTIVE_HOOKS.get('reminder_enabled') else 'OFF':<32} |
+------------------------------------------------+
""")
    if HOOK_MODE.value == 'warn':
        print("[Phase warn] All hooks in WARNING mode (no blocking)\n")

    print("[BOOTSTRAP] Initializing database...")
    initialize_database()
    
    print("[BOOTSTRAP] Ensuring prompt files...")
    ensure_prompt_files()

    # 1. Check Ollama Connectivity (Harden: Short timeout to prevent hanging)
    print(f"[BOOTSTRAP] Checking Ollama at {settings.intelligence_engine_url}...")
    try:
        # Use a very short timeout for the initial health check
        response = httpx.get(settings.intelligence_engine_url, timeout=1.0)
        if response.status_code != 200:
             print("[WARNING] Ollama responded but with status error.")
        
        # 2. Check and Pull Model (Only if Ollama is alive)
        model_name = settings.jarvis_model
        print(f"[BOOTSTRAP] Verifying LLM Model: {model_name}...")
        # Check if model exists via CLI (also with timeout)
        models_check = subprocess.run(
            ["ollama", "list"], 
            capture_output=True, 
            text=True, 
            timeout=5.0 # Don't let this hang the whole app
        )
        if model_name not in models_check.stdout:
            print(f"[BOOTSTRAP] Model '{model_name}' not found. JARVIS will attempt auto-pull on first request.")
            # We don't block boot for pull anymore to ensure server starts
        else:
            print(f"[BOOTSTRAP] Model '{model_name}' is ready.")

    except (httpx.ConnectError, httpx.TimeoutException):
        print("! [WARNING] Ollama is NOT reachable. Jarvis will run in offline mode.")
    except subprocess.TimeoutExpired:
        print("! [WARNING] Ollama CLI timed out. Proceeding without model verification.")
    except Exception as e:
        print(f"[WARNING] Bootstrap connectivity check failed: {e}")

    print("[BOOTSTRAP] System ready.")
