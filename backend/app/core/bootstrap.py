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

    # 1. 리소스 가용성 체크 (Local vs Cloud)
    h_settings = None
    try:
        from app.utils.hybrid_settings import get_hybrid_settings
        h_settings = get_hybrid_settings()
    except Exception:
        pass

    print(f"[BOOTSTRAP] Checking Local Engine (Ollama) at {settings.intelligence_engine_url}...")
    local_ready = False
    try:
        response = httpx.get(settings.intelligence_engine_url, timeout=1.0)
        if response.status_code == 200:
            local_ready = True
            print("  [OK] Local Engine is reachable.")
    except Exception:
        print("  [WARN] Local Engine is offline. Checking Cloud Resources...")

    # 2. Cloud Resources 가용성 요약
    if h_settings:
        providers = h_settings.validate_llm_providers()
        cloud_active = [p for p, info in providers.items() if p != 'local_ollama' and info['status'] == 'available']
        if cloud_active:
            print(f"  [OK] Cloud Resources Available: {', '.join(cloud_active)}")
        else:
            print("  [WARN] No Cloud Resources configured. System will be severely limited.")

    # 3. 모델 검증 (선택적)
    if local_ready:
        try:
            model_name = settings.jarvis_model
            models_check = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=2.0)
            if model_name in models_check.stdout:
                print(f"  [OK] Model '{model_name}' is loaded.")
            else:
                print(f"  [INFO] Model '{model_name}' pending (auto-pull enable).")
        except Exception:
            pass

    status = "OPERATIONAL" if (local_ready or (h_settings and cloud_active)) else "DEGRADED"
    print(f"\n[BOOTSTRAP] System Status: {status}")
    print("[BOOTSTRAP] JARVIS AI OS Kernel Ready.\n")
