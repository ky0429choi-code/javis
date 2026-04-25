import os
import logging
import glob
import uuid
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
        self._ensure_folders()

    def _ensure_folders(self):
        """기본 폴더 구조 보장"""
        folders = ["01_Knowledge", "02_Patterns", "03_Rules", "04_Errors"]
        for f in folders:
            path = os.path.join(self.vault_path, f)
            if not os.path.exists(path):
                os.makedirs(path, exist_ok=True)
                logger.info(f"AXVault: 폴더 생성 -> {path}")

    async def search(self, folder: str, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """로드맵 인터페이스 기준 검색"""
        return await self.rag_search(query, folder)

    async def store(self, folder: str, data: Dict[str, Any]):
        """로드맵 인터페이스 기준 저장 (JSON 데이터를 Markdown으로 변환 저장)"""
        title = data.get("title") or data.get("query") or f"node_{uuid.uuid4().hex[:6]}"
        
        # 메타데이터 포함한 본문 구성
        content_lines = []
        for k, v in data.items():
            if k not in ["title", "query"]:
                content_lines.append(f"**{k}**: {v}")
        
        content = "\n".join(content_lines)
        await self.save_node(title, content, folder)

    async def rag_search(self, query: str, folder: str = "01_Knowledge") -> List[Dict[str, Any]]:
        """
        패턴 기반 검색 (RAG 브릿지).
        폴더 내의 마크다운 파일을 검색하여 쿼리와 관련된 내용을 추출합니다.
        """
        logger.info(f"AXVault: '{query}' 검색 시작 (폴더: {folder})...")
        results = []
        
        target_dir = os.path.join(self.vault_path, folder)
        if not os.path.exists(target_dir):
            return []

        keywords = query.split()
        for md_file in glob.glob(os.path.join(target_dir, "*.md")):
            try:
                with open(md_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    if any(kw.lower() in content.lower() for kw in keywords):
                        # 파일 수정 시간 가져오기 (TTL 체크용)
                        mtime = os.path.getmtime(md_file)
                        results.append({
                            "title": os.path.basename(md_file),
                            "content": content,
                            "source": md_file,
                            "updated_at": mtime
                        })
            except Exception as e:
                logger.error(f"AXVault: 파일 읽기 실패 ({md_file}): {e}")

        # 키워드 매칭 개수 기준 정렬 (간단한 순위화)
        results.sort(key=lambda x: sum(1 for kw in keywords if kw.lower() in x["content"].lower()), reverse=True)
        
        logger.info(f"AXVault: {len(results)}개의 관련 지식을 찾았습니다.")
        return results

    async def save_node(self, title: str, content: str, folder: str = "01_Knowledge"):
        """지식 노드를 마크다운 형식으로 저장합니다."""
        target_dir = os.path.join(self.vault_path, folder)
        os.makedirs(target_dir, exist_ok=True)
        
        safe_title = "".join([c if c.isalnum() or c in " _-" else "_" for c in title])
        file_path = os.path.join(target_dir, f"{safe_title}.md")
        
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f"# {title}\n\n{content}\n\n--- \n*마지막 갱신: {__import__('datetime').datetime.now().isoformat()}*")
            logger.info(f"AXVault: 지식 노드 저장 완료 -> {file_path}")
        except Exception as e:
            logger.error(f"AXVault: 지식 저장 실패: {e}")

    async def delete(self, folder: str, key: str):
        """지식 노드 삭제 (MemorySkill용)"""
        safe_title = "".join([c if c.isalnum() or c in " _-" else "_" for c in key])
        file_path = os.path.join(self.vault_path, folder, f"{safe_title}.md")
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"AXVault: 노드 삭제 완료 -> {file_path}")
            return {"ok": True}
        return {"ok": False, "error": "Not found"}

    def get_rules(self, context: str = "BACKEND") -> str:
        """운영 규칙(Rule Memory)을 가져옵니다."""
        rule_file = os.path.join(self.vault_path, "03_Rules", f"{context.upper()}_RULES.md")
        if os.path.exists(rule_file):
            try:
                with open(rule_file, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception as e:
                logger.error(f"AXVault: 규칙 읽기 실패: {e}")
        return ""

ax_vault = AXVault()
