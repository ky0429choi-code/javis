import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, List
from app.llm_router import router
from app.utils.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class WikiAgent:
    def __init__(self):
        self.identity = "Jarvis"
        self.vault_path = settings.ax_vault_path
        self.raw_dir = os.path.join(self.vault_path, "00_Raw")
        self.knowledge_dir = os.path.join(self.vault_path, "02_Knowledge")
        self.system_base = f"당신은 {self.identity}의 지식 관리 에이전트입니다. 작업 로그를 분석하여 영구적인 지식 노드로 변환하세요."

    async def restructure_logs(self):
        """
        Background process to convert raw logs to structured knowledge.
        """
        logger.info("WikiAgent: Starting log restructuring...")
        # Placeholder for directory watchdog or loop logic
        pass

    async def generate_knowledge_node(self, raw_content: str) -> Dict[str, Any]:
        """
        Converts a raw log string into a structured Knowledge Node (Markdown).
        """
        # 1. Extract Metadata using LLM (JSON format requested)
        metadata_prompt = f"다음 작업 로그를 읽고 메타데이터를 추출하세요:\n{raw_content}\n\n결과를 반드시 JSON 형식으로만 반환하세요: {{'title': '...', 'summary': '...', 'tags': [], 'key_learnings': []}}"
        
        system_prompt = self.system_base + "\nJSON 파싱이 가능하도록 순수 JSON 데이터만 출력하세요."
        
        response = await router.call(prompt=metadata_prompt, system=system_prompt)
        
        try:
            # Simple cleanup for JSON extraction
            json_str = response.strip()
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0].strip()
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0].strip()
            
            metadata = json.loads(json_str)
        except Exception as e:
            logger.error(f"WikiAgent: Metadata extraction failed - {e}")
            metadata = {
                "title": "Untitled Work Log",
                "summary": "Summary extraction failed.",
                "tags": ["error", "manual_check"],
                "key_learnings": []
            }

        # 2. Generate Markdown Template
        node_content = self._create_markdown_template(metadata, raw_content)
        
        # 3. Save to 02_Knowledge
        filename = f"{datetime.now().strftime('%Y-%m-%d')}_{metadata['title'].replace(' ', '_')}.md"
        save_path = os.path.join(self.knowledge_dir, filename)
        
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(node_content)
            
        logger.info(f"WikiAgent: Knowledge node created at {save_path}")
        return {"ok": True, "path": save_path, "metadata": metadata}

    def _create_markdown_template(self, metadata: Dict[str, Any], raw_content: str) -> str:
        tags_str = " ".join([f"#{t}" for t in metadata.get('tags', [])])
        learnings_str = "\n".join([f"- {l}" for l in metadata.get('key_learnings', [])])
        
        return f"""# {metadata.get('title')}

**Tags**: {tags_str}
**Created**: {datetime.now().strftime('%Y-%m-%d')}
**Status**: 🟢 완성

## 핵심 요약
{metadata.get('summary')}

## 주요 학습 포인트
{learnings_str}

## 원본 참조 (Raw Content)
<details>
<summary>상세 로그 보기</summary>

{raw_content}

</details>

## 관련 노드
- [[INDEX]]
"""

    async def generate_weekly_review(self) -> str:
        """Command handler for /weekly_review."""
        return "주간 회고 생성을 시작합니다. 지난 일주일간의 12건의 지식 노드를 분석 중입니다..."

wiki_agent = WikiAgent()
