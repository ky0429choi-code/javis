from app.brains.gemma_brain import GemmaBrain
from app.brains.gpt_oss_brain import GptOssBrain
from app.brains.qwen_brain import QwenBrain
from app.engines.intent_engine import IntentEngine
from app.engines.planning_engine import PlanningEngine
from app.engines.routing_engine import RoutingEngine
from app.engines.approval_engine import ApprovalEngine
from app.engines.reflection_engine import ReflectionEngine
from app.engines.audit_engine import AuditEngine
from app.memory.repository import Repository
from app.tools.file_tool import FileTool

class JarvisConductor:
    def __init__(self) -> None:
        self.repo = Repository()
        self.intent_engine = IntentEngine()
        self.planning_engine = PlanningEngine()
        self.routing_engine = RoutingEngine()
        self.approval_engine = ApprovalEngine()
        self.reflection_engine = ReflectionEngine()
        self.audit_engine = AuditEngine(self.repo)
        self.file_tool = FileTool()
        self.brains = {
            "gemma": GemmaBrain(),
            "gpt_oss": GptOssBrain(),
            "qwen": QwenBrain(),
        }

    async def chat(self, message: str, mode: str = "chat", context: dict | None = None) -> dict:
        context = context or {}
        intent = self.intent_engine.resolve(message, mode, context)
        plan = self.planning_engine.build(intent)
        route = self.routing_engine.select(intent)
        system = self.repo.get_prompts()["master"]
        result = await self.brains[route["brain"]].run(prompt=message, system=system)
        
        # New: Parse autonomous actions from brain result
        suggested_actions = self.parse_and_queue_actions(result)
        
        reflection = self.reflection_engine.review(result, intent)
        self.audit_engine.log("chat_handled", {"intent": intent, "route": route, "result": result[:500], "actions_queued": len(suggested_actions)})
        return {
            "intent": intent, 
            "plan": plan, 
            "route": route, 
            "message": result, 
            "reflection": reflection,
            "suggested_actions": suggested_actions
        }

    def parse_and_queue_actions(self, text: str) -> list[dict]:
        import json
        import re
        actions = []
        # Look for ACTION: { ... } pattern
        pattern = r"ACTION:\s*(\{.*?\})"
        matches = re.finditer(pattern, text, re.DOTALL)
        
        for match in matches:
            try:
                action_data = json.loads(match.group(1))
                # Validate required fields
                if "action_type" in action_data and "target_path" in action_data:
                    queued = self.request_file_action(
                        action_type=action_data["action_type"],
                        target_path=action_data["target_path"],
                        reason=action_data.get("reason", "자율 행동 분석기에서 자동 제안됨"),
                        content=action_data.get("content"),
                        requested_by="jarvis-autonomous-core"
                    )
                    actions.append(queued)
            except Exception as e:
                print(f"Error parsing action: {e}")
        return actions

    async def create_task(self, title: str, summary: str, task_type: str, priority: str, user_kpi: str | None) -> dict:
        task = self.repo.create_task(title, summary, task_type, priority, user_kpi)
        prompt = f"작업명: {title}\n요약: {summary}\n유형: {task_type}\n우선순위: {priority}\n사용자 지정 KPI: {user_kpi or '-'}\n초안 실행 계획을 간결하게 제안해라."
        system = self.repo.get_prompts()["task"]
        draft = await self.brains["gpt_oss"].run(prompt=prompt, system=system)
        self.audit_engine.log("task_created", {"task": task, "draft": draft[:500]})
        return {"task": task, "draft": draft}

    def request_file_action(self, action_type: str, target_path: str, reason: str, content: str | None = None, requested_by: str = "jarvis") -> dict:
        req = self.approval_engine.build_request(action_type, target_path, reason, requested_by, content).model_dump()
        saved = self.repo.create_approval(req)
        self.audit_engine.log("approval_requested", saved)
        return saved

    def resolve_approval(self, request_id: str, action: str) -> dict:
        req = self.repo.get_approval(request_id)
        if action == "approve":
            result = self.execute_action(req)
            updated = self.repo.update_approval(request_id, "approved")
            updated["execution_result"] = result
            self.audit_engine.log("approval_approved", updated)
            return updated
        else:
            updated = self.repo.update_approval(request_id, "rejected")
            self.audit_engine.log("approval_rejected", updated)
            return updated

    def execute_action(self, req: dict) -> dict:
        action_type = req["action_type"]
        target_path = req["target_path"]
        content = req.get("content", "")
        
        if action_type == "create_file":
            return self.file_tool.create_file(target_path, content)
        elif action_type == "update_file" or action_type == "modify_file":
            return self.file_tool.update_file(target_path, content)
        elif action_type == "delete_file":
            return self.file_tool.delete_file(target_path)
        else:
            return {"ok": False, "reason": f"Unsupported action: {action_type}"}

conductor = JarvisConductor()
