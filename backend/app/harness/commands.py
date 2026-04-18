import logging

logger = logging.getLogger(__name__)

# JARVIS Commands Registry
# Maps slash commands to internal logic/agent triggers

COMMAND_MAP = {
    '/auto_plan': 'agents.planner.auto_plan_today',
    '/sync': 'startup_sync.sync_all',
    '/weekly_review': 'agents.wiki_agent.generate_weekly_review',
    '/debug': 'agents.reviewer.analyze_recent_logs',
    '/git_push': 'harness.skills.git_tool.push_changes',
    '/obsidian_scan': 'agents.planner.search_vault',
}

def execute_command(command_str: str) -> dict:
    """
    Parses and executes a JARVIS command.
    """
    cmd = command_str.split()[0].lower()
    if cmd in COMMAND_MAP:
        logger.info(f"Harness: Executing command {cmd}")
        # In a full implementation, this would use importlib to dynamically call the function
        # For now, we return the mapping for the orchestrator to handle
        return {"ok": True, "handler": COMMAND_MAP[cmd], "args": command_str.split()[1:]}
    
    return {"ok": False, "error": f"Unknown command: {cmd}"}
