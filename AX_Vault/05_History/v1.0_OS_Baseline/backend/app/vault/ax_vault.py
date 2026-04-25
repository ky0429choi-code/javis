import os
import logging
import glob
from typing import List, Dict, Any
from app.utils.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class AXVault:
    """
    JARVIS AX_Vault (지식 엔진).
    RAG 검색 및 지식 기반 관리를 담당합니다.
    """
    def __init__(self):
        self.vault_path = settings.ax_vault_path

    async def rag_search(self, query: str, folder: str = "02_Knowledge") -> List[Dict[str, Any]]:
        """
        패턴 기반 검색 (RAG 브릿지).
        폴더 내의 마크다운 파일을 검색하여 쿼리와 관련된 내용을 추출합니다.
        """
        logger.info(f"AXVault: '{query}' 검색 시작 (폴더: {folder})...")
        results = []
        
        target_dir = os.path.join(self.vault_path, folder)
        if not os.path.exists(target_dir):
            return []

        # 단순 키워드 검색 구현 (Stage 3)
        # 모든 .md 파일을 읽어서 쿼리 단어가 포함되어 있는지 확인
        keywords = query.split()
        for md_file in glob.glob(os.path.join(target_dir, "*.md")):
            try:
                with open(md_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    if any(kw.lower() in content.lower() for kw in keywords):
                        results.append({
                            "title": os.path.basename(md_file),
                            "content": content[:500] + "...", # 프리뷰
                            "source": md_file
                        })
            except Exception as e:
                logger.error(f"AXVault: 파일 읽기 실패 ({md_file}): {e}")

        logger.info(f"AXVault: {len(results)}개의 관련 지식을 찾았습니다.")
        return results

    async def save_node(self, title: str, content: str, folder: str = "02_Knowledge"):
        """지식 노드를 마크다운 형식으로 저장합니다."""
        target_dir = os.path.join(self.vault_path, folder)
        os.makedirs(target_dir, exist_ok=True)
        
        # 파일명 정규화
        safe_title = "".join([c if c.isalnum() else "_" for c in title])
        file_path = os.path.join(target_dir, f"{safe_title}.md")
        
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f"# {title}\n\n{content}")
            logger.info(f"AXVault: 지식 노드 저장 완료 -> {file_path}")
        except Exception as e:
            logger.error(f"AXVault: 지식 저장 실패: {e}")

    def get_rules(self, context: str = "BACKEND") -> str:
        """운영 규칙(Rule Memory)을 가져옵니다."""
        rule_file = os.path.join(self.vault_path, "01_Rules", f"{context.upper()}_RULES.md")
        if os.path.exists(rule_file):
            try:
                with open(rule_file, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception as e:
                logger.error(f"AXVault: 규칙 읽기 실패: {e}")
        return ""

ax_vault = AXVault()
