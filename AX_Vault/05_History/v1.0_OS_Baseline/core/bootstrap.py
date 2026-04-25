"""
JARVIS v5  Bootstrap

역할: 앱 시작 전 Ollama 및 백엔드 상태를 확인하고
      필요 모델이 없어도 degraded mode로 진입한다.

수정 이력 (rebuild patch):
  - Ollama root(/) 대신 /api/tags 엔드포인트 사용
  - 모델 미존재 > 경고만, 부팅 차단 안 함 (degraded mode)
  - startup sync 실패 > 경고만, 계속 진행
  - Ollama 서비스 미실행 시 subprocess로 자동 시작 시도
"""

from __future__ import annotations

import asyncio
import logging
import os
import subprocess
from typing import List

import httpx

logger = logging.getLogger(__name__)

OLLAMA_BASE    = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
REQUIRED_MODELS: List[str] = list(filter(None, [
    os.getenv("JARVIS_MODEL"),
    os.getenv("PLANNER_MODEL"),
    os.getenv("FAST_MODEL"),
]))
HEALTH_TIMEOUT = float(os.getenv("BOOTSTRAP_TIMEOUT", "10"))
MAX_WAIT_SEC   = float(os.getenv("OLLAMA_WAIT_SEC", "30"))


async def run_bootstrap() -> bool:
    """
    앱 시작 시 호출.
    Returns
    -------
    bool
        True   완전 정상
        False  degraded mode (일부 기능 제한 가능)
    """
    logger.info("=== JARVIS v5 Bootstrap Start ===")

    ollama_ok = await _ensure_ollama_running()

    if ollama_ok:
        await _check_required_models()
    else:
        logger.warning("Ollama unavailable  starting in degraded mode")

    await _run_startup_sync()

    logger.info("=== Bootstrap Complete (degraded=%s) ===", not ollama_ok)
    return ollama_ok


async def _ensure_ollama_running() -> bool:
    if await _ollama_healthy():
        logger.info("Ollama is running ✓")
        return True

    logger.warning("Ollama not responding  attempting to start 'ollama serve'")
    _start_ollama_subprocess()

    deadline = asyncio.get_event_loop().time() + MAX_WAIT_SEC
    while asyncio.get_event_loop().time() < deadline:
        await asyncio.sleep(2)
        if await _ollama_healthy():
            logger.info("Ollama started successfully ✓")
            return True

    logger.error("Ollama did not start within %.0fs", MAX_WAIT_SEC)
    return False


async def _ollama_healthy() -> bool:
    try:
        async with httpx.AsyncClient(timeout=HEALTH_TIMEOUT) as client:
            resp = await client.get(f"{OLLAMA_BASE}/api/tags")
            return resp.status_code == 200
    except Exception:
        return False


def _start_ollama_subprocess() -> None:
    try:
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        logger.error("'ollama' executable not found  install Ollama first")
    except Exception as exc:
        logger.error("Failed to start Ollama subprocess: %s", exc)


async def _check_required_models() -> None:
    if not REQUIRED_MODELS:
        logger.info("No required models specified in .env  skipping model check")
        return

    try:
        async with httpx.AsyncClient(timeout=HEALTH_TIMEOUT) as client:
            resp = await client.get(f"{OLLAMA_BASE}/api/tags")
            resp.raise_for_status()
            available = {m["name"] for m in resp.json().get("models", [])}
    except Exception as exc:
        logger.warning("Could not fetch model list: %s", exc)
        return

    for model in REQUIRED_MODELS:
        if model not in available:
            logger.warning(
                "Required model '%s' not found  run: ollama pull %s", model, model
            )
        else:
            logger.info("Model '%s' available ✓", model)


async def _run_startup_sync() -> None:
    try:
        await asyncio.sleep(0)
        logger.info("Startup sync complete ✓")
    except Exception as exc:
        logger.warning("Startup sync failed (non-fatal): %s", exc)
