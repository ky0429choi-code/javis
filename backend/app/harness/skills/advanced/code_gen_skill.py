import logging
import ast
import re
from typing import Dict, Any, List
from app.harness.skills.base_skill import BaseSkill
from app.vault.ax_vault import ax_vault
from app.llm.router import router

logger = logging.getLogger(__name__)

class CodeGenSkill(BaseSkill):
    """
    Advanced Code Generation Skill.
    Uses AX_Vault context (patterns and errors) to improve code quality.
    """
    name = "code_generate"
    description = "AX_Vault 컨텍스트(패턴/오류 사례)를 활용한 지능형 코드 생성"
    version = "1.0.0"

    async def execute(self, task: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        instruction = task.get("instruction") or task.get("task")
        language = task.get("language", "python").lower()
        path = task.get("path", "")

        if not instruction:
            return {"ok": False, "error": "Instruction is required"}

        # 1. Fetch context from AX_Vault
        vault_context = await self._fetch_vault_context(instruction)
        
        # 2. Build Prompt
        system_prompt = self._build_system_prompt(language, vault_context)
        user_prompt = f"대상 경로: {path}\n지시 사항: {instruction}\n\n최종 코드만 출력하세요. 설명은 생략합니다."

        # 3. Call LLM
        raw_code = await router.call(
            prompt=user_prompt,
            system=system_prompt,
            task_type="complex"
        )
        
        code = self._extract_code(raw_code)

        # 4. Standard Validation (Syntax Check)
        is_valid, validation_error = self._validate_syntax(code, language)
        
        return {
            "ok": is_valid,
            "status": "success" if is_valid else "syntax_error",
            "result": code,
            "error": validation_error,
            "metadata": {
                "context_used": vault_context["sources"],
                "language": language,
                "validated": is_valid
            }
        }

    async def _fetch_vault_context(self, task: str) -> Dict[str, Any]:
        """AX_Vault에서 관련 패턴과 과거 오류 사례 검색"""
        patterns = await ax_vault.search("02_Patterns", task, top_k=2)
        errors = await ax_vault.search("04_Errors", task, top_k=1)
        
        sources = [p["title"] for p in patterns] + [e["title"] for e in errors]
        
        context_text = ""
        if patterns:
            context_text += "\n### 참고할 성공 패턴:\n" + "\n".join([p["content"] for p in patterns])
        if errors:
            context_text += "\n### 피해야 할 과거 오류 사례:\n" + "\n".join([e["content"] for e in errors])
            
        return {"text": context_text, "sources": sources}

    def _build_system_prompt(self, language: str, context: Dict[str, Any]) -> str:
        prompt = f"당신은 {language} 전문가 수준의 코드 생성 엔진입니다.\n"
        if context["text"]:
            prompt += f"\n다음은 과거의 성공 사례 및 오류 방지 가이드입니다. 이를 엄격히 준수하여 코드를 작성하세요:\n{context['text']}\n"
        
        prompt += "\n규칙:\n1. 실행 가능한 완성된 코드만 응답하십시오.\n2. 마크다운 코드 블록(```)을 사용하십시오.\n3. 불필요한 설명이나 인사는 생략하십시오."
        return prompt

    def _extract_code(self, text: str) -> str:
        match = re.search(r"```(?:\w*)\s*\n([\s\S]*?)\n```", text)
        if match:
            return match.group(1).strip()
        return text.strip()

    def _validate_syntax(self, code: str, language: str) -> (bool, str):
        if not code:
            return False, "Generated code is empty"
            
        if language == "python":
            try:
                ast.parse(code)
                return True, None
            except SyntaxError as e:
                return False, f"Python SyntaxError: {e.msg} (line {e.lineno})"
        
        # Simple balanced braces check for JS/TS/CSS etc.
        if language in ["javascript", "typescript", "css", "html"]:
            stack = []
            for char in code:
                if char == "{": stack.append(char)
                elif char == "}":
                    if not stack: return False, "Unbalanced braces (extra closing brace)"
                    stack.pop()
            if stack:
                return False, "Unbalanced braces (missing closing brace)"
        
        return True, None

    async def validate_input(self, task: Dict[str, Any]) -> (bool, str):
        if not task.get("instruction") and not task.get("task"):
            return False, "Missing task instruction"
        return True, None
