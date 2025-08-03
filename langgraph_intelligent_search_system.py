#!/usr/bin/env python3
"""
LangGraph 기반 지능형 검색 시스템
동적 검색 워크플로우와 품질 기반 자동 최적화

주요 혁신사항:
- 다중 소스 병렬 검색 및 결과 통합
- 실시간 품질 평가 및 재검색 로직
- 사용자 만족도 기반 학습 시스템
- 컨텍스트 인식 검색 쿼리 최적화
"""

import asyncio
import json
import time
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Literal
from dataclasses import dataclass, asdict
from typing_extensions import TypedDict, Annotated
import logging
import hashlib
import pytz

# LangGraph 임포트
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ============================================================================
# LangGraph State 정의
# ============================================================================

class SearchWorkflowState(TypedDict):
    """검색 워크플로우 상태"""
    original_query: str
    processed_query: str
    search_context: Dict[str, Any]
    search_results: Dict[str, Any]
    quality_scores: Dict[str, float]
    messages: Annotated[List[str], add_messages]
    search_sources: List[str]
    retry_count: int
    user_satisfaction: Optional[float]
    final_results: List[Dict]
    search_metadata: Dict[str, Any]
    escalation_needed: bool
    optimization_suggestions: List[str]

# ============================================================================
# 데이터 모델
# ============================================================================

@dataclass
class SearchResult:
    """검색 결과"""
    id: str
    title: str
    content: str
    url: str
    source: str
    relevance_score: float
    quality_score: float
    timestamp: str
    metadata: Dict[str, Any] = None

@dataclass
class SearchSession:
    """검색 세션"""
    session_id: str
    original_query: str
    processed_queries: List[str]
    results: List[SearchResult]
    user_feedback: Dict[str, Any]
    created_at: str
    completed_at: Optional[str] = None
    success_metrics: Dict[str, float] = None

# ============================================================================
# LangGraph 노드 함수들
# ============================================================================

class SearchWorkflowNodes:
    """검색 워크플로우 노드 구현"""
    
    def __init__(self, search_system):
        self.search_system = search_system
        self.kst = pytz.timezone('Asia/Seoul')
    
    def analyze_query(self, state: SearchWorkflowState) -> SearchWorkflowState:
        """검색 쿼리 분석 노드"""
        original_query = state["original_query"]
        
        # AI 기반 쿼리 분석
        query_analysis = self._analyze_search_intent(original_query)
        processed_query = self._optimize_query(original_query, query_analysis)
        search_sources = self._determine_search_sources(query_analysis)
        
        return {
            **state,
            "processed_query": processed_query,
            "search_context": {
                "intent": query_analysis["intent"],
                "complexity": query_analysis["complexity"],
                "suggested_sources": search_sources,
                "optimization_applied": processed_query != original_query,
                "analysis_timestamp": datetime.now(self.kst).isoformat()
            },
            "search_sources": search_sources,
            "messages": [f"쿼리 분석 완료: {query_analysis['intent']} 의도, {len(search_sources)}개 소스 선택"]
        }
    
    def execute_parallel_search(self, state: SearchWorkflowState) -> SearchWorkflowState:
        """병렬 검색 실행 노드"""
        processed_query = state["processed_query"]
        search_sources = state["search_sources"]
        
        # 병렬 검색 실행
        search_results = {}
        quality_scores = {}
        
        for source in search_sources:
            try:
                results = self._search_single_source(source, processed_query)
                quality_score = self._evaluate_source_quality(results, processed_query)
                
                search_results[source] = results
                quality_scores[source] = quality_score
                
                logger.info(f"{source} 검색 완료: {len(results)}개 결과, 품질 {quality_score:.2f}")
                
            except Exception as e:
                logger.error(f"{source} 검색 실패: {e}")
                search_results[source] = []
                quality_scores[source] = 0.0
        
        return {
            **state,
            "search_results": search_results,
            "quality_scores": quality_scores,
            "search_metadata": {
                "sources_attempted": len(search_sources),
                "sources_successful": sum(1 for score in quality_scores.values() if score > 0),
                "total_results": sum(len(results) for results in search_results.values()),
                "search_timestamp": datetime.now(self.kst).isoformat()
            },
            "messages": [f"병렬 검색 완료: {len(search_sources)}개 소스, 총 {sum(len(r) for r in search_results.values())}개 결과"]
        }
    
    def evaluate_results_quality(self, state: SearchWorkflowState) -> SearchWorkflowState:
        """결과 품질 평가 노드"""
        search_results = state["search_results"]
        processed_query = state["processed_query"]
        
        # 통합 품질 평가
        overall_quality = self._calculate_overall_quality(search_results, quality_scores=state["quality_scores"])
        relevance_scores = self._calculate_relevance_scores(search_results, processed_query)
        
        # 품질 기준 판단
        quality_threshold = 0.7
        needs_improvement = overall_quality < quality_threshold
        
        # 개선 제안 생성
        optimization_suggestions = []
        if needs_improvement:
            optimization_suggestions = self._generate_optimization_suggestions(
                search_results, state["quality_scores"], processed_query
            )
        
        return {
            **state,
            "search_metadata": {
                **state["search_metadata"],
                "overall_quality": overall_quality,
                "quality_threshold": quality_threshold,
                "needs_improvement": needs_improvement,
                "relevance_scores": relevance_scores
            },
            "optimization_suggestions": optimization_suggestions,
            "escalation_needed": overall_quality < 0.3,  # 매우 낮은 품질
            "messages": [f"품질 평가 완료: 전체 품질 {overall_quality:.2f}, 개선 필요 {needs_improvement}"]
        }
    
    def optimize_search_strategy(self, state: SearchWorkflowState) -> SearchWorkflowState:
        """검색 전략 최적화 노드"""
        original_query = state["original_query"]
        optimization_suggestions = state["optimization_suggestions"]
        retry_count = state["retry_count"]
        
        # 최적화 전략 적용
        if "expand_query" in optimization_suggestions:
            optimized_query = self._expand_query(original_query)
        elif "refine_query" in optimization_suggestions:
            optimized_query = self._refine_query(original_query)
        elif "add_context" in optimization_suggestions:
            optimized_query = self._add_context_to_query(original_query)
        else:
            optimized_query = self._apply_advanced_optimization(original_query, state["search_context"])
        
        # 새로운 소스 전략
        additional_sources = self._identify_additional_sources(optimization_suggestions)
        updated_sources = list(set(state["search_sources"] + additional_sources))
        
        return {
            **state,
            "processed_query": optimized_query,
            "search_sources": updated_sources,
            "retry_count": retry_count + 1,
            "search_context": {
                **state["search_context"],
                "optimization_applied": True,
                "optimization_strategy": optimization_suggestions,
                "retry_attempt": retry_count + 1
            },
            "messages": [f"검색 최적화 완료: 쿼리 재구성, {len(additional_sources)}개 소스 추가"]
        }
    
    def consolidate_results(self, state: SearchWorkflowState) -> SearchWorkflowState:
        """결과 통합 노드"""
        search_results = state["search_results"]
        quality_scores = state["quality_scores"]
        
        # 결과 통합 및 순위 조정
        consolidated_results = self._merge_and_rank_results(search_results, quality_scores)
        
        # 중복 제거 및 정제
        final_results = self._deduplicate_and_refine(consolidated_results)
        
        # 최종 품질 검증
        final_quality_score = self._validate_final_quality(final_results, state["processed_query"])
        
        return {
            **state,
            "final_results": final_results,
            "search_metadata": {
                **state["search_metadata"],
                "final_result_count": len(final_results),
                "final_quality_score": final_quality_score,
                "consolidation_timestamp": datetime.now(self.kst).isoformat()
            },
            "messages": [f"결과 통합 완료: {len(final_results)}개 최종 결과, 품질 {final_quality_score:.2f}"]
        }
    
    def save_results_and_learn(self, state: SearchWorkflowState) -> SearchWorkflowState:
        """결과 저장 및 학습 노드"""
        final_results = state["final_results"]
        search_metadata = state["search_metadata"]
        
        # 결과 저장
        saved_file = self._save_search_results(state)
        
        # 학습 데이터 수집
        learning_data = self._extract_learning_data(state)
        self._update_search_intelligence(learning_data)
        
        # 성능 메트릭 계산
        performance_metrics = self._calculate_performance_metrics(state)
        
        return {
            **state,
            "search_metadata": {
                **search_metadata,
                "results_saved_to": saved_file,
                "learning_data_extracted": len(learning_data),
                "performance_metrics": performance_metrics,
                "session_completed": True
            },
            "messages": [f"검색 완료: {saved_file}에 저장, 학습 데이터 {len(learning_data)}개 수집"]
        }
    
    def handle_escalation(self, state: SearchWorkflowState) -> SearchWorkflowState:
        """에스컬레이션 처리 노드"""
        original_query = state["original_query"]
        
        # 에스컬레이션 액션
        escalation_actions = [
            "manual_review_required",
            "expert_intervention",
            "alternative_search_methods"
        ]
        
        # 대안 검색 전략 제안
        alternative_strategies = self._generate_alternative_strategies(original_query)
        
        return {
            **state,
            "escalation_needed": True,
            "search_metadata": {
                **state["search_metadata"],
                "escalation_actions": escalation_actions,
                "alternative_strategies": alternative_strategies,
                "escalation_timestamp": datetime.now(self.kst).isoformat()
            },
            "messages": [f"에스컬레이션 처리: {len(escalation_actions)}개 액션, {len(alternative_strategies)}개 대안 전략"]
        }
    
    # ========================================================================
    # 헬퍼 메서드들
    # ========================================================================
    
    def _analyze_search_intent(self, query: str) -> Dict:
        """검색 의도 분석"""
        intent_keywords = {
            "research": ["연구", "분석", "조사", "리서치"],
            "implementation": ["구현", "개발", "코딩", "프로그래밍"],
            "troubleshooting": ["오류", "에러", "문제", "해결"],
            "learning": ["학습", "배우", "공부", "튜토리얼"],
            "comparison": ["비교", "차이", "vs", "대비"]
        }
        
        detected_intent = "general"
        for intent, keywords in intent_keywords.items():
            if any(keyword in query for keyword in keywords):
                detected_intent = intent
                break
        
        complexity = "medium"
        if len(query) < 20:
            complexity = "simple"
        elif len(query) > 100 or any(tech in query for tech in ["시스템", "아키텍처", "통합"]):
            complexity = "complex"
        
        return {
            "intent": detected_intent,
            "complexity": complexity,
            "keywords": query.split(),
            "technical_level": "high" if any(tech in query for tech in ["API", "프레임워크", "알고리즘"]) else "general"
        }
    
    def _optimize_query(self, original_query: str, analysis: Dict) -> str:
        """쿼리 최적화"""
        optimized = original_query
        
        # 의도 기반 최적화
        if analysis["intent"] == "research":
            optimized += " 최신 2024 2025 연구 논문"
        elif analysis["intent"] == "implementation":
            optimized += " 구현 예제 코드 튜토리얼"
        elif analysis["intent"] == "troubleshooting":
            optimized += " 해결방법 솔루션"
        
        # 복잡도 기반 최적화
        if analysis["complexity"] == "simple":
            optimized += " 간단한 기본"
        elif analysis["complexity"] == "complex":
            optimized += " 고급 심화 전문"
        
        return optimized
    
    def _determine_search_sources(self, analysis: Dict) -> List[str]:
        """검색 소스 결정"""
        base_sources = ["google_search", "internal_docs"]
        
        if analysis["intent"] == "research":
            base_sources.extend(["scholar_search", "arxiv_search"])
        elif analysis["intent"] == "implementation":
            base_sources.extend(["github_search", "stackoverflow"])
        elif analysis["technical_level"] == "high":
            base_sources.extend(["technical_docs", "api_docs"])
        
        return list(set(base_sources))
    
    def _search_single_source(self, source: str, query: str) -> List[Dict]:
        """단일 소스 검색"""
        if source == "google_search":
            return self._google_search(query)
        elif source == "internal_docs":
            return self._search_internal_docs(query)
        elif source == "github_search":
            return self._github_search(query)
        elif source == "scholar_search":
            return self._scholar_search(query)
        else:
            return []
    
    def _google_search(self, query: str) -> List[Dict]:
        """Google 검색"""
        try:
            # Google Custom Search API 호출 (기존 코드 재사용)
            api_key = "AIzaSyBIBZNgGd_i_aG2IhlqFQqhl0MP3-J5CCA"
            search_engine_id = "2149f2d26311449a4"
            
            params = {
                'key': api_key,
                'cx': search_engine_id,
                'q': query,
                'num': 10
            }
            
            response = requests.get("https://www.googleapis.com/customsearch/v1", params=params)
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            for item in data.get('items', []):
                results.append({
                    'title': item.get('title', ''),
                    'content': item.get('snippet', ''),
                    'url': item.get('link', ''),
                    'source': 'google',
                    'timestamp': datetime.now(self.kst).isoformat()
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Google 검색 오류: {e}")
            return []
    
    def _search_internal_docs(self, query: str) -> List[Dict]:
        """내부 문서 검색"""
        # RAG 시스템 내부 문서 검색 로직
        results = []
        
        # AI_Search_Results 폴더 검색
        search_dir = Path("C:/Users/user/Dropbox/_RAG/AI_Search_Results")
        if search_dir.exists():
            for file_path in search_dir.glob("*.md"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if any(keyword.lower() in content.lower() for keyword in query.split()):
                            results.append({
                                'title': file_path.stem,
                                'content': content[:500],  # 첫 500자
                                'url': str(file_path),
                                'source': 'internal_docs',
                                'timestamp': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                            })
                except Exception as e:
                    continue
        
        return results[:10]  # 최대 10개
    
    def _github_search(self, query: str) -> List[Dict]:
        """GitHub 검색 (시뮬레이션)"""
        # 실제 구현에서는 GitHub API 사용
        return []
    
    def _scholar_search(self, query: str) -> List[Dict]:
        """학술 검색 (시뮬레이션)"""
        # 실제 구현에서는 Google Scholar API 또는 arXiv API 사용
        return []
    
    def _evaluate_source_quality(self, results: List[Dict], query: str) -> float:
        """소스 품질 평가"""
        if not results:
            return 0.0
        
        quality_factors = {
            'result_count': min(len(results) / 10, 1.0),  # 결과 개수
            'content_relevance': self._calculate_relevance(results, query),  # 관련성
            'content_quality': self._assess_content_quality(results),  # 내용 품질
            'source_credibility': self._assess_source_credibility(results)  # 소스 신뢰도
        }
        
        # 가중 평균
        weights = {'result_count': 0.2, 'content_relevance': 0.4, 'content_quality': 0.2, 'source_credibility': 0.2}
        quality_score = sum(score * weights[factor] for factor, score in quality_factors.items())
        
        return quality_score
    
    def _calculate_relevance(self, results: List[Dict], query: str) -> float:
        """관련성 계산"""
        if not results:
            return 0.0
        
        query_keywords = set(query.lower().split())
        relevance_scores = []
        
        for result in results:
            content = (result.get('title', '') + ' ' + result.get('content', '')).lower()
            content_keywords = set(content.split())
            
            # 키워드 일치도
            common_keywords = query_keywords.intersection(content_keywords)
            relevance = len(common_keywords) / len(query_keywords) if query_keywords else 0
            relevance_scores.append(relevance)
        
        return sum(relevance_scores) / len(relevance_scores)
    
    def _assess_content_quality(self, results: List[Dict]) -> float:
        """내용 품질 평가"""
        if not results:
            return 0.0
        
        quality_scores = []
        for result in results:
            content = result.get('content', '')
            
            # 길이 기반 품질 (너무 짧지 않고 너무 길지 않음)
            length_score = 1.0 if 50 <= len(content) <= 500 else 0.5
            
            # 구조 품질 (문장 완성도 등)
            structure_score = 1.0 if content.count('.') > 0 else 0.5
            
            quality_scores.append((length_score + structure_score) / 2)
        
        return sum(quality_scores) / len(quality_scores)
    
    def _assess_source_credibility(self, results: List[Dict]) -> float:
        """소스 신뢰도 평가"""
        if not results:
            return 0.0
        
        credible_domains = [
            'github.com', 'stackoverflow.com', 'docs.python.org', 
            'developer.mozilla.org', 'arxiv.org', 'scholar.google.com'
        ]
        
        credibility_scores = []
        for result in results:
            url = result.get('url', '')
            
            if any(domain in url for domain in credible_domains):
                credibility_scores.append(1.0)
            elif url.startswith('https://'):
                credibility_scores.append(0.7)
            else:
                credibility_scores.append(0.5)
        
        return sum(credibility_scores) / len(credibility_scores)
    
    def _calculate_overall_quality(self, search_results: Dict, quality_scores: Dict) -> float:
        """전체 품질 계산"""
        if not quality_scores:
            return 0.0
        
        weighted_scores = []
        total_results = sum(len(results) for results in search_results.values())
        
        for source, score in quality_scores.items():
            result_count = len(search_results.get(source, []))
            weight = result_count / total_results if total_results > 0 else 0
            weighted_scores.append(score * weight)
        
        return sum(weighted_scores)
    
    def _calculate_relevance_scores(self, search_results: Dict, query: str) -> Dict:
        """관련성 점수 계산"""
        relevance_scores = {}
        
        for source, results in search_results.items():
            relevance_scores[source] = self._calculate_relevance(results, query)
        
        return relevance_scores
    
    def _generate_optimization_suggestions(self, search_results: Dict, quality_scores: Dict, query: str) -> List[str]:
        """최적화 제안 생성"""
        suggestions = []
        
        overall_quality = self._calculate_overall_quality(search_results, quality_scores)
        total_results = sum(len(results) for results in search_results.values())
        
        if overall_quality < 0.5:
            suggestions.append("expand_query")
        
        if total_results < 5:
            suggestions.append("add_sources")
        
        # 낮은 관련성 검출
        relevance_scores = self._calculate_relevance_scores(search_results, query)
        avg_relevance = sum(relevance_scores.values()) / len(relevance_scores) if relevance_scores else 0
        
        if avg_relevance < 0.3:
            suggestions.append("refine_query")
        
        if len(query.split()) < 3:
            suggestions.append("add_context")
        
        return suggestions
    
    def _expand_query(self, query: str) -> str:
        """쿼리 확장"""
        expansions = {
            "AI": "인공지능 artificial intelligence machine learning",
            "검색": "search engine algorithm optimization",
            "시스템": "system architecture framework platform"
        }
        
        expanded_query = query
        for keyword, expansion in expansions.items():
            if keyword in query:
                expanded_query += f" {expansion}"
        
        return expanded_query
    
    def _refine_query(self, query: str) -> str:
        """쿼리 정제"""
        # 불용어 제거 및 핵심 키워드 강조
        stopwords = ["의", "를", "을", "는", "은", "이", "가", "에", "에서"]
        
        refined_words = [word for word in query.split() if word not in stopwords]
        return " ".join(refined_words)
    
    def _add_context_to_query(self, query: str) -> str:
        """쿼리에 컨텍스트 추가"""
        context_additions = [
            "2024 2025 최신",
            "한국어 Korean",
            "실용적 practical",
            "예제 example tutorial"
        ]
        
        return f"{query} {' '.join(context_additions)}"
    
    def _apply_advanced_optimization(self, query: str, context: Dict) -> str:
        """고급 최적화 적용"""
        intent = context.get("intent", "general")
        complexity = context.get("complexity", "medium")
        
        optimized = query
        
        if intent == "research" and complexity == "complex":
            optimized += " 심화 연구 고급 분석 academic research"
        elif intent == "implementation" and complexity == "simple":
            optimized += " 기초 입문 beginner tutorial simple"
        
        return optimized
    
    def _identify_additional_sources(self, suggestions: List[str]) -> List[str]:
        """추가 소스 식별"""
        additional_sources = []
        
        if "add_sources" in suggestions:
            additional_sources.extend(["bing_search", "duckduckgo_search"])
        
        if "expand_query" in suggestions:
            additional_sources.extend(["wikipedia_search", "reddit_search"])
        
        return additional_sources
    
    def _merge_and_rank_results(self, search_results: Dict, quality_scores: Dict) -> List[Dict]:
        """결과 병합 및 순위 조정"""
        all_results = []
        
        for source, results in search_results.items():
            source_quality = quality_scores.get(source, 0.0)
            
            for result in results:
                result['source_quality'] = source_quality
                result['final_score'] = source_quality * 0.5 + len(result.get('content', '')) / 1000 * 0.3 + 0.2
                all_results.append(result)
        
        # 점수 기준 정렬
        all_results.sort(key=lambda x: x['final_score'], reverse=True)
        
        return all_results
    
    def _deduplicate_and_refine(self, results: List[Dict]) -> List[Dict]:
        """중복 제거 및 정제"""
        seen_urls = set()
        refined_results = []
        
        for result in results:
            url = result.get('url', '')
            title = result.get('title', '')
            
            # URL 기반 중복 제거
            if url and url not in seen_urls:
                seen_urls.add(url)
                refined_results.append(result)
            # 제목 기반 유사 중복 제거
            elif not any(title.lower() in existing['title'].lower() for existing in refined_results):
                refined_results.append(result)
        
        return refined_results[:20]  # 최대 20개
    
    def _validate_final_quality(self, results: List[Dict], query: str) -> float:
        """최종 품질 검증"""
        if not results:
            return 0.0
        
        # 다양성 점수
        sources = set(result.get('source', '') for result in results)
        diversity_score = len(sources) / 5  # 최대 5개 소스 가정
        
        # 관련성 점수
        relevance_score = self._calculate_relevance(results, query)
        
        # 품질 점수
        quality_score = self._assess_content_quality(results)
        
        return (diversity_score + relevance_score + quality_score) / 3
    
    def _save_search_results(self, state: SearchWorkflowState) -> str:
        """검색 결과 저장"""
        timestamp = datetime.now(self.kst).strftime('%Y%m%d_%H%M%S')
        query_hash = hashlib.md5(state["original_query"].encode()).hexdigest()[:8]
        
        filename = f"intelligent_search_{query_hash}_{timestamp}.md"
        filepath = Path("C:/Users/user/Dropbox/_RAG/AI_Search_Results") / filename
        
        # 결과 포맷팅
        content = f"""# 지능형 검색 결과

## 검색 정보
- **원본 쿼리**: {state["original_query"]}
- **처리된 쿼리**: {state["processed_query"]}
- **검색 시간**: {datetime.now(self.kst).strftime('%Y년 %m월 %d일 %H:%M')}
- **검색 소스**: {', '.join(state["search_sources"])}
- **재시도 횟수**: {state["retry_count"]}

## 품질 메트릭
- **전체 품질 점수**: {state["search_metadata"].get("overall_quality", 0):.2f}
- **최종 품질 점수**: {state["search_metadata"].get("final_quality_score", 0):.2f}
- **총 결과 개수**: {len(state["final_results"])}

## 검색 결과

"""
        
        for i, result in enumerate(state["final_results"][:10], 1):
            content += f"""### {i}. {result.get("title", "제목 없음")}
- **출처**: {result.get("source", "알 수 없음")}
- **URL**: {result.get("url", "N/A")}
- **점수**: {result.get("final_score", 0):.2f}

{result.get("content", "내용 없음")}

---

"""
        
        # 파일 저장
        filepath.parent.mkdir(exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return str(filepath)
    
    def _extract_learning_data(self, state: SearchWorkflowState) -> List[Dict]:
        """학습 데이터 추출"""
        learning_data = []
        
        learning_data.append({
            "query_pattern": state["original_query"],
            "optimization_applied": state["search_context"].get("optimization_applied", False),
            "sources_used": state["search_sources"],
            "final_quality": state["search_metadata"].get("final_quality_score", 0),
            "retry_count": state["retry_count"],
            "timestamp": datetime.now(self.kst).isoformat()
        })
        
        return learning_data
    
    def _update_search_intelligence(self, learning_data: List[Dict]):
        """검색 지능 업데이트"""
        # 학습 데이터를 바탕으로 검색 알고리즘 개선
        # 실제 구현에서는 ML 모델 학습 또는 규칙 업데이트
        logger.info(f"검색 지능 업데이트: {len(learning_data)}개 학습 데이터 처리")
    
    def _calculate_performance_metrics(self, state: SearchWorkflowState) -> Dict:
        """성능 메트릭 계산"""
        return {
            "search_latency": "실시간 측정 필요",
            "result_quality": state["search_metadata"].get("final_quality_score", 0),
            "user_satisfaction": state.get("user_satisfaction", "미측정"),
            "cost_efficiency": "API 호출 비용 기준",
            "success_rate": 1.0 if state["search_metadata"].get("final_quality_score", 0) > 0.7 else 0.0
        }
    
    def _generate_alternative_strategies(self, query: str) -> List[str]:
        """대안 전략 생성"""
        return [
            "manual_expert_search",
            "domain_specific_databases", 
            "multilingual_search",
            "temporal_search_expansion",
            "semantic_search_upgrade"
        ]

# ============================================================================
# 조건부 판단 함수들
# ============================================================================

def decide_after_quality_evaluation(state: SearchWorkflowState) -> str:
    """품질 평가 후 다음 단계 결정"""
    needs_improvement = state["search_metadata"].get("needs_improvement", False)
    retry_count = state["retry_count"]
    escalation_needed = state["escalation_needed"]
    
    if escalation_needed:
        return "escalate"
    elif needs_improvement and retry_count < 3:
        return "optimize"
    else:
        return "consolidate"

def decide_after_optimization(state: SearchWorkflowState) -> str:
    """최적화 후 다음 단계 결정"""
    retry_count = state["retry_count"]
    
    if retry_count >= 3:
        return "consolidate"  # 재시도 한계 도달
    else:
        return "research"  # 재검색 실행

def decide_final_action(state: SearchWorkflowState) -> str:
    """최종 액션 결정"""
    final_quality = state["search_metadata"].get("final_quality_score", 0)
    
    if final_quality >= 0.7:
        return "save_and_learn"
    else:
        return "escalate"

# ============================================================================
# LangGraph 워크플로우 구성
# ============================================================================

class LangGraphIntelligentSearchSystem:
    """LangGraph 기반 지능형 검색 시스템"""
    
    def __init__(self, base_path: str = "C:/Users/user/Dropbox/_RAG"):
        self.base_path = Path(base_path)
        self.results_dir = self.base_path / "AI_Search_Results"
        self.results_dir.mkdir(exist_ok=True)
        
        # LangGraph 설정
        self.memory = MemorySaver()
        self.workflow_nodes = SearchWorkflowNodes(self)
        self.workflow = self._create_workflow()
        
        logger.info("LangGraph Intelligent Search System 초기화 완료")
    
    def _create_workflow(self) -> StateGraph:
        """LangGraph 워크플로우 생성"""
        workflow = StateGraph(SearchWorkflowState)
        
        # 노드 추가
        workflow.add_node("analyze", self.workflow_nodes.analyze_query)
        workflow.add_node("search", self.workflow_nodes.execute_parallel_search)
        workflow.add_node("evaluate", self.workflow_nodes.evaluate_results_quality)
        workflow.add_node("optimize", self.workflow_nodes.optimize_search_strategy)
        workflow.add_node("consolidate", self.workflow_nodes.consolidate_results)
        workflow.add_node("save_learn", self.workflow_nodes.save_results_and_learn)
        workflow.add_node("escalate", self.workflow_nodes.handle_escalation)
        
        # 시작점 설정
        workflow.set_entry_point("analyze")
        
        # 엣지 연결
        workflow.add_edge("analyze", "search")
        workflow.add_edge("search", "evaluate")
        
        # 조건부 엣지
        workflow.add_conditional_edges(
            "evaluate",
            decide_after_quality_evaluation,
            {
                "optimize": "optimize",
                "consolidate": "consolidate",
                "escalate": "escalate"
            }
        )
        
        workflow.add_conditional_edges(
            "optimize",
            decide_after_optimization,
            {
                "research": "search",
                "consolidate": "consolidate"
            }
        )
        
        workflow.add_conditional_edges(
            "consolidate",
            decide_final_action,
            {
                "save_and_learn": "save_learn",
                "escalate": "escalate"
            }
        )
        
        workflow.add_edge("save_learn", END)
        workflow.add_edge("escalate", END)
        
        return workflow.compile(checkpointer=self.memory)
    
    async def intelligent_search(self, query: str, thread_id: str = None) -> Dict:
        """지능형 검색 실행"""
        if thread_id is None:
            thread_id = f"search_{hashlib.md5(query.encode()).hexdigest()[:8]}_{int(datetime.now().timestamp())}"
        
        # 초기 상태 설정
        initial_state = {
            "original_query": query,
            "processed_query": query,
            "search_context": {},
            "search_results": {},
            "quality_scores": {},
            "messages": [],
            "search_sources": [],
            "retry_count": 0,
            "user_satisfaction": None,
            "final_results": [],
            "search_metadata": {},
            "escalation_needed": False,
            "optimization_suggestions": []
        }
        
        # 워크플로우 실행
        config = {
            "configurable": {
                "thread_id": thread_id,
                "recursion_limit": 20
            }
        }
        
        try:
            result = await self.workflow.ainvoke(initial_state, config)
            
            logger.info(f"지능형 검색 완료: {query} - 품질 {result['search_metadata'].get('final_quality_score', 0):.2f}")
            
            return result
            
        except Exception as e:
            logger.error(f"검색 워크플로우 실행 오류: {e}")
            return {"error": str(e), "query": query}

# ============================================================================
# 사용 예제
# ============================================================================

async def main():
    """사용 예제"""
    search_system = LangGraphIntelligentSearchSystem()
    
    # 검색 실행
    test_queries = [
        "LangGraph와 MCP 통합 방법",
        "Python OCR 시스템 최적화 기법",
        "AI 기반 자동화 수익창출 전략"
    ]
    
    for query in test_queries:
        print(f"\n=== 검색 실행: {query} ===")
        result = await search_system.intelligent_search(query)
        
        if "error" not in result:
            print(f"최종 결과 개수: {len(result.get('final_results', []))}")
            print(f"품질 점수: {result['search_metadata'].get('final_quality_score', 0):.2f}")
            print(f"재시도 횟수: {result['retry_count']}")
            print(f"메시지: {result['messages'][-1] if result['messages'] else 'None'}")
        else:
            print(f"오류: {result['error']}")

if __name__ == "__main__":
    asyncio.run(main())