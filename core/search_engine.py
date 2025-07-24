import os
import asyncio
import aiohttp
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import json
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str
    timestamp: datetime
    relevance_score: float = 0.0

class SearchEngine:
    def __init__(self):
        self.google_api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
        self.cse_id = os.getenv("GOOGLE_CSE_ID")
        self.logger = logging.getLogger(__name__)
        
        if not self.google_api_key or not self.cse_id:
            self.logger.warning("Google Search API 키 또는 CSE ID가 설정되지 않았습니다. 웹 검색 기능이 비활성화됩니다.")
            self.search_enabled = False
        else:
            self.search_enabled = True

    async def search_web(self, query: str, num_results: int = 10, 
                        lang: str = "ko") -> List[SearchResult]:
        """구글 커스텀 서치로 웹 검색"""
        if not self.search_enabled:
            self.logger.info("웹 검색 기능이 비활성화되어 있습니다.")
            return []
        
        try:
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                "key": self.google_api_key,
                "cx": self.cse_id,
                "q": query,
                "num": min(num_results, 10),
                "lr": f"lang_{lang}",
                "safe": "medium"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return await self._parse_search_results(data)
                    else:
                        self.logger.error(f"검색 API 오류: {response.status}")
                        return []
                        
        except Exception as e:
            self.logger.error(f"웹 검색 오류: {e}")
            return []

    async def _parse_search_results(self, data: Dict) -> List[SearchResult]:
        """검색 결과 파싱"""
        results = []
        items = data.get("items", [])
        
        for i, item in enumerate(items):
            result = SearchResult(
                title=item.get("title", ""),
                url=item.get("link", ""),
                snippet=item.get("snippet", ""),
                timestamp=datetime.now(),
                relevance_score=1.0 - (i * 0.1)  # 순서에 따른 관련성 점수
            )
            results.append(result)
        
        return results

    async def fetch_page_content(self, url: str, timeout: int = 10) -> Optional[str]:
        """웹페이지 내용 추출"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
                async with session.get(url, headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # 불필요한 태그 제거
                        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
                            tag.decompose()
                        
                        # 본문 텍스트 추출
                        text = soup.get_text(separator=' ', strip=True)
                        return ' '.join(text.split())[:5000]  # 5000자 제한
                    
        except Exception as e:
            self.logger.error(f"페이지 내용 추출 오류 ({url}): {e}")
        
        return None

    async def search_and_extract(self, query: str, num_results: int = 5, 
                               extract_content: bool = True) -> List[Dict[str, Any]]:
        """검색 + 내용 추출 통합"""
        search_results = await self.search_web(query, num_results)
        
        if not extract_content:
            return [
                {
                    "title": r.title,
                    "url": r.url,
                    "snippet": r.snippet,
                    "relevance_score": r.relevance_score
                }
                for r in search_results
            ]
        
        # 내용 추출을 병렬로 처리
        tasks = [self.fetch_page_content(result.url) for result in search_results]
        contents = await asyncio.gather(*tasks, return_exceptions=True)
        
        enhanced_results = []
        for i, result in enumerate(search_results):
            content = contents[i] if i < len(contents) and not isinstance(contents[i], Exception) else None
            
            enhanced_results.append({
                "title": result.title,
                "url": result.url,
                "snippet": result.snippet,
                "content": content,
                "relevance_score": result.relevance_score,
                "timestamp": result.timestamp.isoformat()
            })
        
        return enhanced_results

    async def smart_search(self, query: str, search_type: str = "general") -> List[Dict[str, Any]]:
        """검색 유형에 따른 스마트 검색"""
        if search_type == "news":
            query = f"{query} 뉴스 최신"
            return await self.search_and_extract(query, num_results=8)
        elif search_type == "academic":
            query = f"{query} 논문 연구"
            return await self.search_and_extract(query, num_results=6)
        elif search_type == "technical":
            query = f"{query} 기술 문서 가이드"
            return await self.search_and_extract(query, num_results=7)
        else:
            return await self.search_and_extract(query, num_results=5)