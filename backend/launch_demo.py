import os
import sys
import time

import httpx
from rich.console import Console
from rich.panel import Panel

console = Console()

HOST = os.getenv("JARVIS_HOST", "127.0.0.1")
PORT = os.getenv("JARVIS_PORT", "8000")
BASE_URL = f"http://{HOST}:{PORT}/api"
HEALTH_URL = f"{BASE_URL}/health"


def check_backend() -> bool:
    try:
        response = httpx.get(HEALTH_URL, timeout=3.0)
        return response.status_code == 200
    except Exception:
        return False


def main() -> None:
    console.print(
        Panel.fit(
            f"[bold cyan]JARVIS Launcher[/bold cyan]\n"
            f"Backend: {BASE_URL}",
            title="Startup",
        )
    )

    for _ in range(10):
        if check_backend():
            console.print(
                Panel.fit(
                    f"[green]Connected[/green]\n{BASE_URL}",
                    title="System Online",
                )
            )
            return
        time.sleep(1)

    console.print(
        Panel.fit(
            f"[red]Error:[/red] Cannot connect to JARVIS Backend at {BASE_URL}",
            title="System Offline",
        )
    )
    sys.exit(1)


if __name__ == "__main__":
    main()