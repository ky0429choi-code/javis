import logging
import re
from typing import Dict, Any, Optional
from app.core.conductor import conductor
from app.llm.router import router

logger = logging.getLogger(__name__)

COMMAND_PREFIX = "/"

# ✅ 단순 키워드 → 동사+목적어 복합 패턴으로 교체
# "파일 있어?" 같은 일상 대화는 통과, "파일 만들어줘" 같은 작업만 task로 분류
TASK_PATTERNS = [
    # 파일/코드/문서 + 작업 동사
    r"(파일|코드|문서|스크립트|함수|클래스|모듈).{0,10}(만들|생성|작성|수정|삭제|읽어|열어|써줘|고쳐|짜줘|추가)",
    # 분석/보고서/계획서 + 작성 의도
    r"(분석|보고서|계획서|명세서|요약본|초안|정리).{0,10}(작성|만들|써줘|정리|뽑아|생성)",
    # 작업성 동사 단독 (배포, 설치, 빌드 등은 맥락상 거의 항상 task)
    r"(배포|설치|빌드|리팩터|디버그|구현|실행|테스트).{0,5}(해줘|해봐|시켜|진행|할래|해|하자)",
    # 영문 작업 동사 + 목적어
    r"\b(create|write|update|delete|deploy|build|refactor|debug|fix|implement|generate)\s+\w+",
    # "~를 만들어줘" 패턴
    r".{2,20}(을|를|좀|한번).{0,5}(만들어|생성해|작성해|수정해|삭제해|구현해)\s*(줘|봐|줄래|주세요)?",
]

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
            'chat'    — 일상 대화, 질문, 인사
            'task'    — 파일/코드 작업, 분석 생성 등 (복합 패턴 매칭)
            'command' — 슬래시 명령어
        """
        stripped = message.strip()

        # 슬래시 명령어
        if stripped.startswith(COMMAND_PREFIX):
            return "command"

        lower = stripped.lower()

        # ✅ 복합 정규식 패턴 매칭 (문맥 기반)
        for pattern in TASK_PATTERNS:
            if re.search(pattern, lower):
                logger.debug(f"Task pattern matched: {pattern}")
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
        self._awareness_cache = None

    async def _get_system_awareness(self) -> str:
        """지식 저장소에서 시스템 맵(자기 구조)을 읽어와 자아 인식을 부여합니다."""
        if self._awareness_cache:
            return self._awareness_cache

        import time
        from app.vault.ax_vault import ax_vault

        try:
            # SYSTEM_MAP.md 조회
            docs = await ax_vault.rag_search("SYSTEM_MAP", folder="02_Knowledge")
            if docs:
                node = docs[0]
                content = node["content"]
                mtime = node.get("updated_at", 0)
                
                # TTL 체크 (24시간)
                hours_since_sync = (time.time() - mtime) / 3600
                if hours_since_sync > 24:
                    logger.warning(f"⚠️ 시스템 맵이 {hours_since_sync:.1f}시간 전의 것입니다. /system_learn을 권장합니다.")
                    content = "⚠️ [CAUTION: Outdated Awareness] " + content

                self._awareness_cache = content
                return self._awareness_cache
        except Exception as e:
            logger.warning(f"Failed to load system awareness: {e}")
        
        return "시스템 구조 정보를 불러올 수 없습니다."

    async def handle_request(self, message: str, context: Optional[dict] = None) -> Dict[str, Any]:
        """요청을 분류하고 적절한 처리기로 라우팅합니다."""
        context = context or {}
        mode = context.get("mode", "auto")

        if mode == "auto":
            # ✅ auto: 분류기에 위임
            mode = self.classifier.classify(message)

        elif mode == "chat":
            # ✅ 명시적 chat: 분류기 결과와 무관하게 항상 chat 유지
            #    (단, command는 예외적으로 허용)
            detected = self.classifier.classify(message)
            mode = "command" if detected == "command" else "chat"

        elif mode == "task":
            # ✅ 명시적 task: 그대로 task 유지
            pass

        logger.info(f"Orchestrator: mode={mode}, message={message[:50]}...")

        if mode == "chat":
            return await self._handle_chat(message)
        elif mode == "task":
            return await self._handle_task(message, context)
        elif mode == "command":
            return await self._handle_command(message)
        else:
            # 알 수 없는 모드 → chat으로 폴백
            logger.warning(f"Unknown mode '{mode}', falling back to chat")
            return await self._handle_chat(message)

    async def _handle_chat(self, message: str) -> Dict[str, Any]:
        """단순 대화 — LLM에 직접 전달하여 자연스러운 응답."""
        try:
            # 자아 인식 컨텍스트 주입
            awareness = await self._get_system_awareness()
            full_system_prompt = f"{CHAT_SYSTEM_PROMPT}\n\n## 당신의 시스템 구조 (Self-Awareness)\n{awareness}"

            response = await router.call(
                prompt=message,
                system=full_system_prompt,
                task_type="immediate",
            )

            return {
                "identity": self.identity,
                "message": response,
                "mode": "chat",
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
        """복잡한 작업 — 관련 컨텍스트(지식 + 경험)를 검색한 후 Conductor 파이프라인으로 처리."""
        logger.info(f"Orchestrator: Searching multi-context for task -> {message[:50]}...")
        
        # ✅ 작업 전 관련 정보 검색 (방법 B)
        try:
            from app.vault.ax_vault import ax_vault
            
            # 1. 시스템 지식 검색 (Architecture/Rules)
            knowledge_docs = await ax_vault.rag_search(message, folder="02_Knowledge")
            # 2. 과거 경험 검색 (Patterns/Lessons Learned)
            pattern_docs = await ax_vault.rag_search(message, folder="02_Patterns")
            
            combined_ctx = []
            if knowledge_docs:
                combined_ctx.append("## [시스템 아키텍터 지식]\n" + "\n".join([f"- {d['title']}: {d['content'][:500]}" for d in knowledge_docs[:2]]))
            if pattern_docs:
                combined_ctx.append("## [과거 작업 경험 및 피드백]\n" + "\n".join([f"- {d['title']}: {d['content'][:500]}" for d in pattern_docs[:2]]))
                
            if combined_ctx:
                context["related_context"] = "\n\n".join(combined_ctx)
                logger.info(f"Orchestrator: Injected {len(knowledge_docs)} knowledge and {len(pattern_docs)} pattern nodes.")
        except Exception as e:
            logger.error(f"Context search failed: {e}")

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
        parts = message.strip().split()
        cmd = parts[0].lower()

        if cmd == "/help":
            return {
                "identity": self.identity,
                "message": (
                    "📋 JARVIS OS 커널 명령어:\n"
                    "  /help — 명령어 도움말\n"
                    "  /status — 커널 및 리소스 상태\n"
                    "  /system_learn — 시스템 자가 학습 (코드/규칙 동기화)\n"
                    "  /resources — 가용 지능 리소스 현황\n"
                    "  /skills — 등록된 도구(Skill) 목록 및 상태\n"
                    "  /recover — 시스템 및 로컬 엔진 자가 복구 시도\n"
                    "  /confidence — 신뢰도 통계 요약\n"
                ),
                "mode": "command",
                "status": "completed",
                "ok": True,
            }
        elif cmd == "/skills":
            try:
                from app.harness.skills.registry import skill_registry
                skills = skill_registry.list_skills()
                if not skills:
                    msg = "🔍 등록된 스킬이 없습니다. (Phase 2에서 빌트인 스킬 등록 예정)"
                else:
                    msg = "🛠️ 등록된 스킬 목록:\n" + "\n".join([f"  • {s}" for s in skills])
                return {
                    "identity": self.identity,
                    "message": msg,
                    "mode": "command",
                    "status": "completed",
                    "ok": True,
                }
            except Exception as e:
                return {"identity": self.identity, "message": f"스킬 조회 실패: {e}", "mode": "command", "status": "error", "ok": False}
        elif cmd == "/recover":
            try:
                from app.utils.hybrid_settings import get_hybrid_settings
                h_settings = get_hybrid_settings()
                providers = h_settings.validate_llm_providers()
                ollama = providers.get("local_ollama", {})

                if ollama.get("status") == "available":
                    msg = "✅ 로컬 엔진(Ollama)이 이미 정상 작동 중입니다."
                else:
                    msg = "🔄 시스템 자가 복구를 시도합니다...\n"
                    msg += "  • 로컬 엔진 상태 재점검 중...\n"
                    new_providers = h_settings.validate_llm_providers()
                    if new_providers.get("local_ollama", {}).get("status") == "available":
                        msg += "  ✅ 복구 성공: 로컬 엔진이 온라인입니다."
                    else:
                        msg += "  ❌ 복구 실패: 로컬 엔진(Ollama)이 응답하지 않습니다. 외부에서 직접 실행해 주세요."

                return {
                    "identity": self.identity,
                    "message": msg,
                    "mode": "command",
                    "status": "completed",
                    "ok": True,
                }
            except Exception as e:
                return {"identity": self.identity, "message": f"복구 시도 중 오류: {e}", "mode": "command", "status": "error", "ok": False}
        elif cmd == "/system_learn":
            from app.agents.wiki import wiki_agent
            success = await wiki_agent.sync_system_knowledge()
            msg = "✅ 시스템 자가 학습 완료. SYSTEM_MAP이 업데이트되었습니다." if success else "❌ 자가 학습 실패."
            return {
                "identity": self.identity,
                "message": msg,
                "mode": "command",
                "status": "completed",
                "ok": True,
            }
        elif cmd == "/resources":
            from app.utils.hybrid_settings import get_hybrid_settings
            h_settings = get_hybrid_settings()
            providers = h_settings.validate_llm_providers()
            msg = "📊 가용한 지능 리소스 현황:\n"
            for p, info in providers.items():
                status = "🟢" if info['status'] == 'available' else "🔴"
                msg += f"  {status} {p}: {info.get('model', 'N/A')} ({info['status']})\n"
            return {
                "identity": self.identity,
                "message": msg,
                "mode": "command",
                "status": "completed",
                "ok": True,
            }
        elif cmd == "/status":
            return {
                "identity": self.identity,
                "message": "🟢 JARVIS AI OS 커널 — 정상 작동 중",
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