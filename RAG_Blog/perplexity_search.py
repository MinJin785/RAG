import requests
import json
import os
from typing import Dict, List

class PerplexitySearcher:
    def __init__(self, api_key: str = None):
        """
        Perplexity API를 사용한 웹 검색 클래스
        
        Args:
            api_key: Perplexity API 키 (환경변수에서 자동 로드)
        """
        self.api_key = api_key or os.getenv('PERPLEXITY_API_KEY')
        if not self.api_key:
            raise ValueError("PERPLEXITY_API_KEY가 설정되지 않았습니다.")
        
        self.base_url = "https://api.perplexity.ai/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def search(self, query: str, model: str = "llama-3.1-sonar-small-128k-online") -> Dict:
        """
        Perplexity API로 웹 검색 수행
        
        Args:
            query: 검색할 쿼리
            model: 사용할 모델 (기본: sonar-small)
            
        Returns:
            검색 결과와 소스 정보
        """
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": "당신은 정확한 정보를 제공하는 검색 전문가입니다. 최신 정보를 검색하고 출처를 명확히 제시해주세요."
                },
                {
                    "role": "user", 
                    "content": query
                }
            ],
            "max_tokens": 1000,
            "temperature": 0.2,
            "top_p": 0.9,
            "return_citations": True,
            "search_domain_filter": ["perplexity.ai"],
            "return_images": False,
            "return_related_questions": True
        }
        
        try:
            response = requests.post(self.base_url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"API 요청 실패: {str(e)}"}
    
    def search_korean(self, query: str) -> str:
        """
        한국어 검색에 최적화된 메서드
        
        Args:
            query: 한국어 검색 쿼리
            
        Returns:
            정리된 검색 결과 텍스트
        """
        # 한국어 검색 최적화 프롬프트 추가
        optimized_query = f"""
        다음 주제에 대해 한국어로 최신 정보를 검색해주세요: {query}
        
        다음 형식으로 답변해주세요:
        1. 핵심 정보 요약
        2. 최신 동향
        3. 관련 수치/데이터 
        4. 출처 URL
        """
        
        result = self.search(optimized_query)
        
        if "error" in result:
            return f"검색 오류: {result['error']}"
        
        try:
            content = result['choices'][0]['message']['content']
            citations = result.get('citations', [])
            
            # 출처 정보 추가
            if citations:
                content += "\n\n📚 출처:\n"
                for i, citation in enumerate(citations[:3], 1):
                    content += f"{i}. {citation.get('url', 'N/A')}\n"
            
            return content
        except (KeyError, IndexError) as e:
            return f"응답 파싱 오류: {str(e)}"

# 블로그 관련 특화 검색 함수들
def search_blog_competition(keyword: str, searcher: PerplexitySearcher) -> str:
    """블로그 키워드 경쟁 분석"""
    query = f"{keyword} 블로그 글 분석 SEO 키워드 경쟁도 2025년"
    return searcher.search_korean(query)

def search_monetization_trends(niche: str, searcher: PerplexitySearcher) -> str:
    """수익화 트렌드 검색"""  
    query = f"{niche} 블로그 수익화 애드센스 애프릴리에이트 2025년 트렌드"
    return searcher.search_korean(query)

def search_target_audience(topic: str, searcher: PerplexitySearcher) -> str:
    """타겟 오디언스 분석"""
    query = f"{topic} 관심있는 사람들 특징 연령대 관심사 검색 행동 패턴"
    return searcher.search_korean(query)

# 대일외고 특화 검색 함수
def search_daeil_info(searcher: PerplexitySearcher) -> str:
    """대일외고 최신 정보 검색"""
    query = "대일외고 입시 2025년 2026년 경쟁률 내신 영어 합격 후기"
    return searcher.search_korean(query)

if __name__ == "__main__":
    # 테스트 코드
    try:
        searcher = PerplexitySearcher()
        
        # 테스트 검색
        result = searcher.search_korean("고등어닷컴 영어수학 학원 대일외고")
        print("검색 결과:")
        print(result)
        
    except Exception as e:
        print(f"오류 발생: {e}")
        print("PERPLEXITY_API_KEY 환경변수를 설정해주세요.")