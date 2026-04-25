#!/usr/bin/env python3
import asyncio
import httpx
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich.live import Live
from rich.table import Table
from rich.spinner import Spinner

# Load environment variables
load_dotenv(os.path.join("backend", ".env"))

BASE_URL = os.getenv("JARVIS_BACKEND_URL", "http://127.0.0.1:8000/api")
SHARED_KEY = os.getenv("APP_SHARED_KEY", "AIN_PAPA_SHARED_KEY")

console = Console()

class JarvisCLI:
    def __init__(self):
        self.headers = {"X-Shared-Key": SHARED_KEY}
        self.client = httpx.AsyncClient(timeout=60.0, headers=self.headers)

    async def check_health(self):
        """Wait for the backend to be ready (up to 15 seconds) to handle startup delays."""
        with Live(Spinner("dots", text=f"[yellow]Connecting to JARVIS Core at {BASE_URL}...[/yellow]"), refresh_per_second=10, transient=True):
            for _ in range(15):
                try:
                    res = await self.client.get(f"{BASE_URL}/health")
                    if res.status_code == 200:
                        return True
                except:
                    pass
                await asyncio.sleep(1)
        return False

    async def chat(self, message: str, mode: str = "chat"):
        try:
            res = await self.client.post(
                f"{BASE_URL}/jarvis/chat",
                json={"message": message, "mode": mode}
            )
            if res.status_code == 200:
                return res.json().get("data", {})
            else:
                return {"message": f"Error: Received {res.status_code} from server."}
        except Exception as e:
            return {"message": f"Connection Error: {str(e)}"}

    async def list_approvals(self):
        try:
            res = await self.client.get(f"{BASE_URL}/approvals")
            if res.status_code == 200:
                return res.json().get("data", [])
            return []
        except:
            return []

    async def resolve_approval(self, request_id: str, action: str):
        try:
            res = await self.client.post(f"{BASE_URL}/approvals/{request_id}/{action}")
            return res.status_code == 200
        except:
            return False

    async def run(self):
        console.print(Panel.fit(
            "[bold cyan]JARVIS Intelligence Core[/bold cyan]\n[dim]Terminal Interface v4.0 - Hardened[/dim]",
            border_style="cyan"
        ))

        if not await self.check_health():
            console.print(Panel(
                "[red]Error: Cannot connect to JARVIS Backend at " + BASE_URL + "[/red]\n\n"
                "[bold yellow]Troubleshooting Tips:[/bold yellow]\n"
                "1. Is the backend running? (Check the 'JARVIS Backend' window)\n"
                "2. Is the port 8000 shared with another app?\n"
                "3. Did you activate the virtual environment? (.venv\\Scripts\\activate)\n"
                "4. Check if the SHARED_KEY in .env matches the server.",
                title="[bold red]System Offline[/bold red]",
                border_style="red"
            ))
            return

        console.print("[green]System Online. Type 'exit' to quit, 'approvals' to check queue.[/green]\n")

        while True:
            try:
                user_input = Prompt.ask("[bold green]User[/bold green]")
                
                if user_input.lower() in ["exit", "quit", "q"]:
                    break
                
                if user_input.lower() in ["approvals", "pending"]:
                    await self.handle_approvals()
                    continue

                if not user_input.strip():
                    continue

                with Live(Spinner("dots", text="[cyan]Jarvis is processing your request...[/cyan]"), refresh_per_second=10, transient=True):
                    response_data = await self.chat(user_input)
                
                # Handle 4.0 Orchestrator response
                status = response_data.get("status", "unknown")
                plan = response_data.get("plan", {})
                steps_exec = response_data.get("execution_steps", [])
                knowledge = response_data.get("knowledge", {})

                if "failed" in status:
                    console.print(f"[bold red]Pipeline Halted: {status}[/bold red]")
                    if response_data.get("feedback"):
                        console.print(f"[yellow]Feedback: {response_data['feedback']}[/yellow]")

                # Show Plan
                if plan.get("steps"):
                    t = Table(title="[bold cyan]Execution Plan[/bold cyan]", box=None)
                    t.add_column("#", style="dim")
                    t.add_column("Step")
                    for i, s in enumerate(plan["steps"]):
                        t.add_row(str(i+1), s["title"])
                    console.print(t)

                # Show Step Results
                for i, step_info in enumerate(steps_exec):
                    mark = "[green]✔[/green]" if step_info["review"]["ok"] else "[red]✘[/red]"
                    console.print(f" {mark} [cyan]Step {i+1}: {step_info['step']['title']}[/cyan]")

                # Final Markdown Response
                if knowledge.get("ok"):
                    console.print(Panel(Markdown(knowledge.get("content", "Task completed.")), title="[bold cyan]JARVIS Result[/bold cyan]", border_style="cyan"))
                elif response_data.get("message"):
                    console.print(Panel(Markdown(response_data["message"]), title="[bold cyan]JARVIS[/bold cyan]", border_style="cyan"))

            except KeyboardInterrupt:
                break
        
        await self.client.aclose()
        console.print("\n[cyan]JARVIS signing off. Goodbye.[/cyan]")

    async def handle_approvals(self):
        approvals = await self.list_approvals()
        pending = [a for a in approvals if a["status"] == "pending"]
        
        if not pending:
            console.print("[dim]No pending approvals in queue.[/dim]")
            return

        table = Table(title="Pending Approvals")
        table.add_column("ID", style="dim")
        table.add_column("Action", style="cyan")
        table.add_column("Path", style="green")
        table.add_column("Reason")

        for a in pending:
            table.add_row(a["request_id"][:8], a["action_type"], a["target_path"], a["reason"])
        
        console.print(table)
        
        cmd = Prompt.ask("Enter ID to approve/reject (or 'c' to cancel)", default="c")
        if cmd == "c":
            return
        
        # Find matching ID
        target = next((a for a in pending if a["request_id"].startswith(cmd)), None)
        if target:
            choice = Prompt.ask(f"Approve {target['action_type']} on {target['target_path']}?", choices=["y", "n", "c"], default="c")
            if choice == "y":
                if await self.resolve_approval(target["request_id"], "approve"):
                    console.print("[green]Approved and executed.[/green]")
                else:
                    console.print("[red]Operation failed.[/red]")
            elif choice == "n":
                await self.resolve_approval(target["request_id"], "reject")
                console.print("[yellow]Rejected.[/yellow]")
        else:
            console.print("[red]Invalid ID.[/red]")

if __name__ == "__main__":
    cli = JarvisCLI()
    try:
        asyncio.run(cli.run())
    except KeyboardInterrupt:
        pass
