import logging
from typing import Dict, Any, List
from datetime import datetime
from duckduckgo_search import DDGS
from app.harness.skills.base_skill import BaseSkill
from app.vault.ax_vault import ax_vault
from app.llm.router import router

logger = logging.getLogger(__name__)

class SearchSkill(BaseSkill):
    """
    Advanced Web Search Skill using DuckDuckGo.
    Includes 24h caching in AX_Vault to minimize external requests.
    """
    name = "web_search"
    description = "실시간 웹 검색 및 결과 요약 (24시간 캐시 지원)"
    version = "1.0.0"

    CACHE_TTL_HOURS = 24

    async def execute(self, task: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        query = task.get("query")
        max_results = task.get("max_results", 5)

        if not query:
            return {"ok": False, "error": "Search query is required"}

        # 1. Check Cache in AX_Vault
        cached_data = await self._check_cache(query)
        if cached_data:
            logger.info(f"SearchSkill: 캐시된 결과 반환 -> {query}")
            return {
                "ok": True,
                "status": "cached",
                "result": cached_data["summary"],
                "sources": cached_data["sources"]
            }

        # 2. Perform Search (Retry with DDGS)
        try:
            results = self._search_ddg(query, max_results)
            if not results:
                return {"ok": False, "error": "No search results found"}
        except Exception as e:
            logger.error(f"SearchSkill: 검색 중 오류 발생: {e}")
            return {"ok": False, "error": f"Search failed: {str(e)}"}

        # 3. Summarize results with LLM
        summary = await self._summarize_results(query, results)

        # 4. Store in Cache
        await self._store_cache(query, summary, results)

        return {
            "ok": True,
            "status": "fresh",
            "result": summary,
            "sources": results
        }

    def _search_ddg(self, query: str, max_results: int) -> List[Dict[str, str]]:
        """DuckDuckGo를 통한 실시간 검색"""
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(query, max_results=max_results)]
            return [{"title": r["title"], "body": r["body"], "href": r["href"]} for r in results]

    async def _summarize_results(self, query: str, results: List[Dict[str, str]]) -> str:
        """검색 결과를 LLM으로 요약"""
        context_text = "\n".join([f"- {r['title']}: {r['body']} ({r['href']})" for r in results])
        prompt = (
            f"사용자 질의: {query}\n\n"
            f"다음은 웹 검색 결과입니다:\n{context_text}\n\n"
            "위 정보를 바탕으로 핵심 내용을 요약하여 한국어로 답변하세요."
        )
        system_prompt = "당신은 유능한 리서치 에이전트입니다. 검색 결과를 분석하여 정확하고 간결한 정보를 제공합니다."
        
        return await router.call(prompt=prompt, system=system_prompt, task_type="complex")

    async def _check_cache(self, query: str) -> Dict[str, Any]:
        """AX_Vault에서 캐시 검색 및 만료 체크"""
        cached_nodes = await ax_vault.search("01_Knowledge", query)
        for node in cached_nodes:
            # 파일명이 쿼리와 유사한지 확인 (정확히 일치하는 캐시 노드 탐색)
            # ax_vault.search는 키워드 검색이므로 여러개가 나올 수 있음
            if query.lower() in node["title"].lower():
                # mtime 체크
                mtime = node.get("updated_at", 0)
                age_hours = (datetime.now().timestamp() - mtime) / 3600
                if age_hours < self.CACHE_TTL_HOURS:
                    # 캐시 유효
                    return self._parse_cache_content(node["content"])
        return None

    def _parse_cache_content(self, content: str) -> Dict[str, Any]:
        """캐시 본문에서 요약과 소스 분리"""
        try:
            # AXVault.store는 **k**: v 형태로 저장함
            lines = content.split("\n")
            summary = ""
            sources = []
            for line in lines:
                if line.startswith("**summary**:"):
                    summary = line.replace("**summary**:", "").strip()
                elif line.startswith("**sources**:"):
                    # 리스트 형태로 저장되었을 것이므로 eval 하거나 간단히 파싱
                    # 여기선 안전하게 문자열로 처리하거나 다시 파싱하는 로직 필요
                    # 저장 시 JSON 직렬화를 고려해야 함
                    pass
            return {"summary": summary, "sources": []} # 소스 복구는 복잡하므로 요약만 우선 반환
        except:
            return None

    async def _store_cache(self, query: str, summary: str, results: List[Dict[str, str]]):
        """결과를 캐시에 저장"""
        await ax_vault.store("01_Knowledge", {
            "query": query,
            "summary": summary,
            "sources": str(results),
            "cached_at": datetime.now().isoformat()
        })

    async def validate_input(self, task: Dict[str, Any]) -> (bool, str):
        if not task.get("query"):
            return False, "Missing search query"
        return True, None
