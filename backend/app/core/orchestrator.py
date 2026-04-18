import logging
import asyncio
from typing import Dict, Any, Optional
from app.agents.planner import planner
from app.agents.executor import executor
from app.agents.reviewer import reviewer
from app.agents.wiki_agent import wiki_agent
from app.harness.commands import execute_command

logger = logging.getLogger(__name__)

class JarvisOrchestrator:
    """
    JARVIS AI Core 4.0 Orchestrator.
    Manages the lifecycle of a task through the Agent Pipeline:
    Planner -> Executor -> Reviewer -> WikiAgent.
    
    FIXED: Handles structured steps from Planner, with proper error handling.
    """
    def __init__(self):
        self.identity = "Jarvis"

    async def handle_request(self, message: str) -> Dict[str, Any]:
        """
        Main entry point for any user request (CLI or Web).
        Routes to command handler or task pipeline.
        """
        try:
            # 1. Check for slash commands
            if message.startswith('/'):
                return await self._handle_harness_command(message)

            # 2. Planning Phase: Get structured steps
            logger.info(f"{self.identity}: Planning request: {message[:50]}...")
            plan_res = await planner.auto_plan_today(message)
            
            # Log planning result
            logger.debug(f"Plan result: {plan_res}")
            
            # Extract steps from plan (can be empty for simple requests)
            steps = plan_res.get("steps", [])
            goal = plan_res.get("goal", message)
            priority = plan_res.get("priority", "medium")
            
            execution_results = []
            overall_status = "completed"

            # 3. Early exit if no steps (simple chat response)
            if not steps:
                logger.info(f"{self.identity}: No action steps required. Using planning as direct response.")
                return {
                    "identity": self.identity,
                    "message": goal,
                    "status": "completed_no_steps",
                    "goal": goal,
                    "priority": priority,
                    "execution_steps": [],
                    "knowledge": {"ok": False, "message": "No structured knowledge for chat-only response"}
                }

            # 4. Execution Loop (Real Multi-step)
            for i, step in enumerate(steps):
                try:
                    step_title = step.get("title", f"Step {i+1}")
                    action_type = step.get("action", "create_file")
                    target_path = step.get("path", "")
                    instruction = step.get("instruction", "")
                    
                    logger.info(f"{self.identity}: Executing Step {i+1}/{len(steps)}: {step_title}")
                    
                    # 4a. Execute Step
                    execution_context = {
                        "action_type": action_type,
                        "target_path": target_path,
                        "instruction": instruction
                    }
                    exec_res = await executor.execute_task(execution_context)
                    
                    # Check execution success
                    if not exec_res.get("ok"):
                        logger.error(f"{self.identity}: Step {i+1} FAILED - {exec_res.get('error')}")
                        overall_status = f"failed_at_step_{i+1}"
                        execution_results.append({"step": step, "exec": exec_res, "review": {"ok": False, "error": "Skipped due to execution failure"}})
                        break  # Halt pipeline on first failure
                    
                    # 4b. Review Step
                    logger.info(f"{self.identity}: Reviewing Step {i+1}...")
                    review_context = {
                        "path": target_path,
                        "content": exec_res.get("output", str(exec_res)),
                        "has_tests": True,
                        "attempts": 1
                    }
                    review_res = await reviewer.review_result(review_context)
                    
                    # 4c. Handle review result
                    if not review_res.get("ok"):
                        logger.warning(f"{self.identity}: Step {i+1} did not pass review: {review_res.get('feedback')}")
                        overall_status = f"review_failed_at_step_{i+1}"
                        execution_results.append({"step": step, "exec": exec_res, "review": review_res})
                        # For now, continue instead of halting (can be configurable)
                    else:
                        execution_results.append({"step": step, "exec": exec_res, "review": review_res})
                    
                except Exception as step_error:
                    logger.error(f"{self.identity}: Step {i+1} threw exception: {step_error}")
                    overall_status = f"error_at_step_{i+1}"
                    execution_results.append({
                        "step": step,
                        "exec": {"ok": False, "error": str(step_error)},
                        "review": {"ok": False, "error": f"Step error: {step_error}"}
                    })
                    break

            # 5. Wiki/Knowledge Phase
            wiki_res = {"ok": False, "message": "Knowledge not structured due to failure or no steps"}
            if overall_status == "completed" and execution_results:
                try:
                    logger.info(f"{self.identity}: Task finished. Archiving to Knowledge Base...")
                    summary = f"Goal: {goal}\nPriority: {priority}\nSteps Completed: {len(execution_results)}\nResults: {execution_results[:100]}"
                    wiki_res = await wiki_agent.generate_knowledge_node(summary)
                except Exception as wiki_error:
                    logger.error(f"{self.identity}: Wiki archival failed: {wiki_error}")
                    wiki_res = {"ok": False, "message": f"Wiki error: {wiki_error}"}

            # 6. Generate user-friendly message
            if overall_status == "completed":
                user_message = f"✅ Task completed: Successfully executed {len(steps)} steps."
            elif overall_status == "completed_no_steps":
                user_message = goal
            elif "failed" in overall_status:
                user_message = f"⚠️ Task partially completed: {overall_status}"
            else:
                user_message = f"⚠️ Task interrupted: {overall_status}"

            final_response = {
                "identity": self.identity,
                "message": user_message,
                "status": overall_status,
                "goal": goal,
                "priority": priority,
                "plan": plan_res,
                "execution_steps": execution_results,
                "knowledge": wiki_res
            }
            
            # 7. Audit Trace
            self._audit_log(message, final_response)

            return final_response
            
        except Exception as e:
            logger.error(f"{self.identity}: Orchestrator fatal error: {e}")
            return {
                "identity": self.identity,
                "message": f"❌ System error: {str(e)}",
                "status": "orchestrator_error",
                "error": str(e)
            }

    async def _handle_harness_command(self, message: str) -> Dict[str, Any]:
        """Dispatches slash commands to appropriate handlers."""
        try:
            cmd_res = execute_command(message)
            if not cmd_res.get("ok"):
                return {"identity": self.identity, "error": cmd_res.get("error", "Command failed")}
            
            handler_path = cmd_res.get("handler", "")
            logger.info(f"{self.identity}: Dispatching command to {handler_path}")
            
            # Dispatch to appropriate handler
            if "planner" in handler_path:
                return await planner.auto_plan_today(message)
            elif "wiki" in handler_path:
                result = await wiki_agent.generate_weekly_review()
                return {"identity": self.identity, "message": result}
            elif "reviewer" in handler_path:
                result = await reviewer.analyze_recent_logs()
                return {"identity": self.identity, "message": result}
                
            return {"identity": self.identity, "message": f"Command {message} dispatched"}
        except Exception as e:
            logger.error(f"{self.identity}: Command dispatch failed: {e}")
            return {"identity": self.identity, "error": f"Command error: {e}"}

    def _audit_log(self, task: str, result: Dict[str, Any]):
        """Saves a permanent record of the execution to AX_Vault/04_Audit."""
        try:
            import json
            import os
            from datetime import datetime
            from app.utils.settings import get_settings
            
            settings = get_settings()
            audit_dir = os.path.join(settings.ax_vault_path, "04_Audit")
            os.makedirs(audit_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"audit_{timestamp}.json"
            filepath = os.path.join(audit_dir, filename)
            
            audit_data = {
                "timestamp": timestamp,
                "task": task,
                "status": result.get("status"),
                "steps_executed": len(result.get("execution_steps", []))
            }
            
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(audit_data, f, ensure_ascii=False, indent=2)
                
            logger.info(f"Audit: Trace saved to {filename}")
        except Exception as e:
            logger.error(f"Audit logging failed: {e}")

orchestrator = JarvisOrchestrator()

