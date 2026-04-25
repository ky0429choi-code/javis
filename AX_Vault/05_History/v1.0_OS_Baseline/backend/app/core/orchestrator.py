import logging
import re
from typing import Dict, Any, Optional
from app.core.conductor import conductor
from app.llm.router import router

logger = logging.getLogger(__name__)

# 대화 모드 키워드 (이 패턴에 해당하면 task 모드로 라우팅)
TASK_KEYWORDS = [
    "만들어", "생성", "작성", "수정", "삭제", "파일", "코드",
    "분석", "보고서", "계획", "설정", "배포", "설치",
    "create", "write", "update", "delete", "deploy", "build",
    "refactor", "debug", "fix", "implement",
]

COMMAND_PREFIX = "/"

# JARVIS 시스템 프롬프트 (대화 모드)
CHAT_SYSTEM_PROMPT = """당신은 JARVIS(Jarvis Agent Repository Intelligence Virtual System)입니다.
- 로컬 AI 지휘 코어, 사장님(사용자)의 개인 비서
- 존댓말을 사용하고, 친근하면서도 전문적인 톤을 유지합니다
- 질문에 자연스럽게 대화하고, 필요 시 작업을 제안합니다
- 한국어로 응답합니다"""


class ChatModeClassifier:
    """메시지를 chat/task/command 모드로 분류합니다."""

    @staticmethod
    def classify(message: str) -> str:
        """메시지 의도를 분류합니다.

        Returns:
            'chat' — 일상 대화, 질문, 인사
            'task' — 파일/코드 작업, 분석, 생성 등
            'command' — 슬래시 명령어
        """
        stripped = message.strip()

        # 슬래시 명령어
        if stripped.startswith(COMMAND_PREFIX):
            return "command"

        # 태스크 키워드 매칭
        lower = stripped.lower()
        for kw in TASK_KEYWORDS:
            if kw in lower:
                return "task"

        # 기본은 대화 모드
        return "chat"


class JarvisOrchestrator:
    """
    JARVIS AI Core 4.0 Orchestrator Bridge.
    채팅 모드 분류기를 통해 단순 대화와 복잡한 작업을 분리합니다.

    - chat 모드: LLM 직접 호출 (빠른 응답, 자연스러운 대화)
    - task 모드: Conductor 파이프라인 (Plan → Execute → Review)
    - command 모드: 슬래시 명령어 처리
    """
    def __init__(self):
        self.identity = "Jarvis"
        self.classifier = ChatModeClassifier()

    async def handle_request(self, message: str, context: Optional[dict] = None) -> Dict[str, Any]:
        """요청을 분류하고 적절한 처리기로 라우팅합니다."""
        context = context or {}
        mode = context.get("mode", "auto")

        # 명시적 모드 지정이 없으면 자동 분류
        if mode == "auto" or mode == "chat":
            detected = self.classifier.classify(message)
            # mode가 명시적으로 "chat"이면 항상 대화 모드
            if mode == "chat" and detected == "task":
                detected = "chat"
            mode = detected

        logger.info(f"Orchestrator: mode={mode}, message={message[:50]}...")

        if mode == "chat":
            return await self._handle_chat(message)
        elif mode == "task":
            return await self._handle_task(message, context)
        elif mode == "command":
            return await self._handle_command(message)
        else:
            return await self._handle_chat(message)

    async def _handle_chat(self, message: str) -> Dict[str, Any]:
        """단순 대화 — LLM에 직접 전달하여 자연스러운 응답."""
        try:
            response = await router.call(
                prompt=message,
                system=CHAT_SYSTEM_PROMPT,
                task_type="immediate",
            )

            return {
                "identity": self.identity,
                "message": response,
                "mode": "chat",
                "status": "completed",
                "ok": True,
            }
        except Exception as e:
            logger.error(f"Chat mode error: {e}")
            return {
                "identity": self.identity,
                "message": f"죄송합니다, 현재 응답을 생성할 수 없습니다: {e}",
                "mode": "chat",
                "status": "error",
                "ok": False,
            }

    async def _handle_task(self, message: str, context: dict) -> Dict[str, Any]:
        """복잡한 작업 — Conductor 파이프라인으로 처리."""
        logger.info(f"Orchestrator: Routing to Conductor -> {message[:50]}...")

        result = await conductor.process_request(message, context)

        return {
            "identity": self.identity,
            "message": result.get("message", "작업이 수행되었습니다."),
            "mode": "task",
            "status": result.get("status", "completed"),
            "goal": result.get("goal", message),
            "execution_steps": result.get("execution_trace", []),
            "plan": result.get("plan", {}),
            "confidence": result.get("confidence", {}),
            "task_id": result.get("task_id", ""),
            "ok": result.get("ok", True),
        }

    async def _handle_command(self, message: str) -> Dict[str, Any]:
        """슬래시 명령어 처리."""
        cmd = message.strip().split()[0].lower()

        # 기본 명령어
        if cmd == "/help":
            return {
                "identity": self.identity,
                "message": (
                    "📋 사용 가능한 명령어:\n"
                    "  /help — 도움말\n"
                    "  /status — 시스템 상태\n"
                    "  /confidence — 신뢰도 요약\n"
                ),
                "mode": "command",
                "status": "completed",
                "ok": True,
            }
        elif cmd == "/status":
            return {
                "identity": self.identity,
                "message": "🟢 JARVIS Core 4.0 — 정상 작동 중",
                "mode": "command",
                "status": "completed",
                "ok": True,
            }
        elif cmd == "/confidence":
            try:
                from app.core.confidence_collector import get_confidence_collector
                collector = get_confidence_collector()
                summary = collector.get_system_summary(days=7)
                health = summary.get("overall_health", "unknown")
                score = summary.get("overall_score", 0)
                msg = f"📊 시스템 신뢰도: {health} ({score:.2f})"
                for comp, s in summary.get("component_scores", {}).items():
                    msg += f"\n  • {comp}: {s:.2f}"
                return {
                    "identity": self.identity,
                    "message": msg,
                    "mode": "command",
                    "status": "completed",
                    "ok": True,
                }
            except Exception as e:
                return {
                    "identity": self.identity,
                    "message": f"신뢰도 조회 실패: {e}",
                    "mode": "command",
                    "status": "error",
                    "ok": False,
                }
        else:
            return {
                "identity": self.identity,
                "message": f"알 수 없는 명령어: {cmd}. /help를 입력해보세요.",
                "mode": "command",
                "status": "completed",
                "ok": True,
            }


orchestrator = JarvisOrchestrator()
