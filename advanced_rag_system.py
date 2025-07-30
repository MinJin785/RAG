#!/usr/bin/env python3
"""
고급 3단계 RAG 시스템
1단계: AI-minjin 폴더(로컬 RAG) 검색
2단계: 웹 실시간 검색  
3단계: 통합 분석 및 응답 생성
"""

import asyncio
import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import aiohttp
from dataclasses import dataclass

@dataclass
class SearchResult:
    source: str  # "local" or "web"
    content: str
    relevance_score: float
    timestamp: datetime
    metadata: Dict[str, Any]

class AdvancedRAGSystem:
    """3단계 RAG 시스템 구현"""
    
    def __init__(self):
        self.local_knowledge_base = "/workspace"  # AI-minjin 폴더
        self.web_search_enabled = True
        self.search_history: List[SearchResult] = []
        
    async def stage1_local_rag_search(self, query: str) -> List[SearchResult]:
        """1단계: AI-minjin 폴더 내 RAG 검색"""
        print(f"🔍 1단계: 로컬 RAG 검색 - '{query}'")
        
        local_results = []
        
        # 프로젝트 파일들 검색
        search_files = [
            "main.py", "TODO.md", "requirements.txt",
            "core/memory_brain.py", "core/search_engine.py", 
            "core/api_manager.py", "core/self_modifier.py"
        ]
        
        for file_path in search_files:
            full_path = Path(self.local_knowledge_base) / file_path
            if full_path.exists():
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 간단한 관련성 점수 계산
                    relevance = self._calculate_relevance(query, content)
                    
                    if relevance > 0.1:  # 임계값
                        result = SearchResult(
                            source="local",
                            content=content[:500] + "..." if len(content) > 500 else content,
                            relevance_score=relevance,
                            timestamp=datetime.now(),
                            metadata={"file_path": str(file_path), "file_size": len(content)}
                        )
                        local_results.append(result)
                        
                except Exception as e:
                    print(f"❌ 파일 읽기 오류 {file_path}: {e}")
        
        # 관련성 순으로 정렬
        local_results.sort(key=lambda x: x.relevance_score, reverse=True)
        print(f"✅ 1단계 완료: {len(local_results)}개 로컬 결과 발견")
        
        return local_results[:5]  # 상위 5개만 반환
    
    async def stage2_web_search(self, query: str, local_context: str = "") -> List[SearchResult]:
        """2단계: 실시간 웹 검색"""
        print(f"🌐 2단계: 웹 검색 - '{query}'")
        
        if not self.web_search_enabled:
            print("⚠️ 웹 검색 비활성화됨")
            return []
        
        web_results = []
        
        # 검색 쿼리 최적화
        enhanced_query = self._enhance_query_with_context(query, local_context)
        
        try:
            # 실제 웹 검색 (여기서는 시뮬레이션)
            # 실제로는 Google Search API, Perplexity API 등 사용
            simulated_web_results = [
                {
                    "title": f"AI 개발 관련: {query}",
                    "content": f"웹에서 찾은 {query}에 대한 최신 정보...",
                    "url": "https://example.com/ai-development",
                    "relevance": 0.8
                },
                {
                    "title": f"RAG 시스템 최적화",
                    "content": f"{query} 관련 RAG 성능 개선 방법...",
                    "url": "https://example.com/rag-optimization", 
                    "relevance": 0.7
                }
            ]
            
            for web_data in simulated_web_results:
                result = SearchResult(
                    source="web",
                    content=web_data["content"],
                    relevance_score=web_data["relevance"],
                    timestamp=datetime.now(),
                    metadata={
                        "title": web_data["title"],
                        "url": web_data["url"],
                        "search_query": enhanced_query
                    }
                )
                web_results.append(result)
                
        except Exception as e:
            print(f"❌ 웹 검색 오류: {e}")
        
        print(f"✅ 2단계 완료: {len(web_results)}개 웹 결과 발견")
        return web_results
    
    async def stage3_integrated_analysis(self, query: str, local_results: List[SearchResult], 
                                       web_results: List[SearchResult]) -> Dict[str, Any]:
        """3단계: 통합 분석 및 응답 생성"""
        print(f"🧠 3단계: 통합 분석 및 응답 생성")
        
        # 모든 결과 통합
        all_results = local_results + web_results
        all_results.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # 컨텍스트 구성
        local_context = self._build_context(local_results, "로컬 지식")
        web_context = self._build_context(web_results, "웹 검색 결과")
        
        # 응답 생성 (실제로는 Claude/Gemini API 호출)
        response = {
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "analysis": {
                "local_insights": local_context,
                "web_insights": web_context,
                "integrated_response": self._generate_integrated_response(
                    query, local_context, web_context
                )
            },
            "sources": {
                "local_count": len(local_results),
                "web_count": len(web_results),
                "total_relevance": sum(r.relevance_score for r in all_results)
            },
            "recommendations": self._generate_recommendations(all_results)
        }
        
        print(f"✅ 3단계 완료: 통합 응답 생성됨")
        return response
    
    async def process_query(self, query: str) -> Dict[str, Any]:
        """전체 3단계 RAG 프로세스 실행"""
        print(f"\n🚀 3단계 RAG 시스템 시작: '{query}'")
        print("=" * 60)
        
        start_time = datetime.now()
        
        # 1단계: 로컬 RAG 검색
        local_results = await self.stage1_local_rag_search(query)
        
        # 로컬 컨텍스트 추출
        local_context = " ".join([r.content[:200] for r in local_results])
        
        # 2단계: 웹 검색  
        web_results = await self.stage2_web_search(query, local_context)
        
        # 3단계: 통합 분석
        final_response = await self.stage3_integrated_analysis(
            query, local_results, web_results
        )
        
        # 처리 시간 계산
        processing_time = (datetime.now() - start_time).total_seconds()
        final_response["processing_time_seconds"] = processing_time
        
        print("=" * 60)
        print(f"🎉 RAG 프로세스 완료! (소요시간: {processing_time:.2f}초)")
        
        return final_response
    
    def _calculate_relevance(self, query: str, content: str) -> float:
        """간단한 관련성 점수 계산"""
        query_words = query.lower().split()
        content_lower = content.lower()
        
        matches = sum(1 for word in query_words if word in content_lower)
        return matches / len(query_words) if query_words else 0
    
    def _enhance_query_with_context(self, query: str, context: str) -> str:
        """컨텍스트를 활용한 검색 쿼리 개선"""
        if context:
            # 컨텍스트에서 핵심 키워드 추출
            key_terms = ["AI", "RAG", "민진", "시스템", "최적화"]
            relevant_terms = [term for term in key_terms if term in context]
            
            if relevant_terms:
                return f"{query} {' '.join(relevant_terms[:2])}"
        
        return query
    
    def _build_context(self, results: List[SearchResult], source_type: str) -> str:
        """결과들로부터 컨텍스트 구성"""
        if not results:
            return f"{source_type}에서 관련 정보를 찾지 못했습니다."
        
        context_parts = []
        for i, result in enumerate(results[:3], 1):  # 상위 3개만
            context_parts.append(f"{i}. {result.content[:150]}...")
        
        return f"{source_type} ({len(results)}개 결과):\n" + "\n".join(context_parts)
    
    def _generate_integrated_response(self, query: str, local_context: str, web_context: str) -> str:
        """통합 응답 생성 (실제로는 LLM API 호출)"""
        return f"""
🎯 '{query}'에 대한 통합 분석 결과:

📁 로컬 지식 기반 분석:
{local_context[:200]}...

🌐 웹 검색 최신 정보:
{web_context[:200]}...

💡 결론:
로컬 지식과 웹 정보를 종합하여 분석한 결과, 현재 AI민진 시스템의 상태와 
웹상의 최신 동향을 고려할 때 다음과 같은 개선 방향을 제안합니다...
        """.strip()
    
    def _generate_recommendations(self, results: List[SearchResult]) -> List[str]:
        """결과 기반 추천사항 생성"""
        recommendations = []
        
        local_count = sum(1 for r in results if r.source == "local")
        web_count = sum(1 for r in results if r.source == "web")
        
        if local_count > 0:
            recommendations.append("로컬 지식 기반이 충분히 활용되었습니다.")
        
        if web_count > 0:
            recommendations.append("웹 검색을 통해 최신 정보가 보강되었습니다.")
        
        if local_count > web_count:
            recommendations.append("외부 최신 정보 추가 검색을 고려해보세요.")
        elif web_count > local_count:
            recommendations.append("로컬 지식 기반 확장을 고려해보세요.")
        
        return recommendations

# 사용 예시
async def demo_rag_system():
    """RAG 시스템 데모"""
    rag = AdvancedRAGSystem()
    
    # 테스트 쿼리들
    test_queries = [
        "AI민진 시스템 성능 최적화 방법",
        "RAG 메모리 브레인 개선 방안", 
        "Chainlit 이미지 업로드 구현"
    ]
    
    for query in test_queries:
        result = await rag.process_query(query)
        print(f"\n📊 쿼리: {query}")
        print(f"📈 관련성 점수: {result['sources']['total_relevance']:.2f}")
        print(f"⏱️ 처리 시간: {result['processing_time_seconds']:.2f}초")
        print("-" * 40)

if __name__ == "__main__":
    print("🚀 고급 3단계 RAG 시스템 - 웹 Cursor 구현")
    print("1️⃣ 로컬 RAG → 2️⃣ 웹 검색 → 3️⃣ 통합 분석")
    
    # 실제 실행은 데스크탑 앱에서 가능
    # asyncio.run(demo_rag_system())