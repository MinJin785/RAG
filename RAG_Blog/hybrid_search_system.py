"""
하이브리드 검색 시스템: Google + Perplexity
비용 효율적인 검색 API 통합 사용
"""

import os
import requests
from typing import Dict, List, Optional
from datetime import datetime
import json

class HybridSearchSystem:
    def __init__(self):
        # Google API 설정
        self.google_api_keys = [
            os.getenv('GOOGLE_API_KEY_1'),
            os.getenv('GOOGLE_API_KEY_2')
        ]
        self.google_search_id = os.getenv('GOOGLE_SEARCH_ENGINE_ID')
        
        # Perplexity API 설정 (선택사항)
        self.perplexity_api_key = os.getenv('PERPLEXITY_API_KEY')
        
        # 사용량 추적
        self.usage_log = {
            'google_daily': 0,  # 일일 100개 제한
            'perplexity_monthly': 0,  # 월 600개 제한
            'date': datetime.now().date().isoformat()
        }
    
    def google_search(self, query: str, num_results: int = 10) -> Dict:
        """
        Google Custom Search API 사용
        무료: 100쿼리/일, 유료: $5/1000쿼리
        """
        try:
            # API 키 로테이션 (2개 키로 200쿼리/일 가능)
            api_key = self.google_api_keys[0] if self.usage_log['google_daily'] < 100 else self.google_api_keys[1]
            
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                'key': api_key,
                'cx': self.google_search_id,
                'q': query,
                'num': min(num_results, 10),
                'lr': 'lang_ko',  # 한국어 우선
                'safe': 'medium'
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            self.usage_log['google_daily'] += 1
            
            # 결과 정리
            data = response.json()
            results = []
            
            for item in data.get('items', []):
                results.append({
                    'title': item.get('title', ''),
                    'url': item.get('link', ''),
                    'snippet': item.get('snippet', ''),
                    'source': 'google'
                })
            
            return {
                'success': True,
                'results': results,
                'total_results': data.get('searchInformation', {}).get('totalResults', 0),
                'usage': f"Google API 사용 ({self.usage_log['google_daily']}/200)"
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def perplexity_search(self, query: str) -> Dict:
        """
        Perplexity API 사용 (고급 분석용)
        $20/월 = 600쿼리
        """
        if not self.perplexity_api_key:
            return {'success': False, 'error': 'Perplexity API 키가 없습니다'}
        
        try:
            url = "https://api.perplexity.ai/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.perplexity_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "llama-3.1-sonar-small-128k-online",
                "messages": [
                    {
                        "role": "system",
                        "content": "한국어로 정확하고 최신 정보를 제공하는 검색 전문가입니다."
                    },
                    {
                        "role": "user",
                        "content": query
                    }
                ],
                "max_tokens": 1000,
                "temperature": 0.2,
                "return_citations": True
            }
            
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            self.usage_log['perplexity_monthly'] += 1
            
            data = response.json()
            content = data['choices'][0]['message']['content']
            citations = data.get('citations', [])
            
            return {
                'success': True,
                'content': content,
                'citations': citations,
                'usage': f"Perplexity API 사용 ({self.usage_log['perplexity_monthly']}/600)",
                'source': 'perplexity'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def smart_search(self, query: str, search_type: str = 'auto') -> Dict:
        """
        지능형 검색: 상황에 맞는 API 자동 선택
        
        Args:
            query: 검색어
            search_type: 'google', 'perplexity', 'auto'
        """
        # 키워드 기반 API 선택
        expensive_keywords = ['분석', '트렌드', '비교', '예측', '전망']
        use_perplexity = any(keyword in query for keyword in expensive_keywords)
        
        if search_type == 'auto':
            if use_perplexity and self.perplexity_api_key and self.usage_log['perplexity_monthly'] < 500:
                return self.perplexity_search(query)
            else:
                return self.google_search(query)
        elif search_type == 'google':
            return self.google_search(query)
        elif search_type == 'perplexity':
            return self.perplexity_search(query)
    
    def blog_research(self, topic: str) -> Dict:
        """블로그 글을 위한 종합 리서치"""
        results = {
            'topic': topic,
            'timestamp': datetime.now().isoformat(),
            'searches': {}
        }
        
        # 1. 기본 정보 (Google 사용 - 저렴)
        print(f"📋 {topic} 기본 정보 검색 중...")
        basic_search = self.smart_search(f"{topic} 2025년 최신 정보", 'google')
        results['searches']['basic_info'] = basic_search
        
        # 2. 경쟁 분석 (Perplexity 사용 - 고급 분석)
        print(f"🏆 {topic} 경쟁 분석 중...")
        competition_search = self.smart_search(f"{topic} 블로그 경쟁 분석 트렌드", 'perplexity')
        results['searches']['competition'] = competition_search
        
        # 3. 키워드 검색 (Google 사용)
        print(f"🔍 {topic} 관련 키워드 검색 중...")
        keyword_search = self.smart_search(f"{topic} 인기 검색어 키워드", 'google')
        results['searches']['keywords'] = keyword_search
        
        return results
    
    def get_usage_report(self) -> str:
        """API 사용량 보고서"""
        return f"""
📊 API 사용량 현황 ({self.usage_log['date']})

🔍 Google API: {self.usage_log['google_daily']}/200 (일일)
💎 Perplexity API: {self.usage_log['perplexity_monthly']}/600 (월간)

💰 예상 비용:
- Google: 무료 (일일 한도 내)
- Perplexity: ${20 * (self.usage_log['perplexity_monthly'] / 600):.2f}

💡 권장사항:
{'Google API 위주 사용 (비용 절약)' if self.usage_log['perplexity_monthly'] > 300 else 'Perplexity 더 활용 가능'}
        """

# 사용 예시
def setup_hybrid_search():
    """하이브리드 검색 시스템 설정"""
    
    # .env 파일에 추가할 내용
    env_content = """
# Google Custom Search API
GOOGLE_API_KEY_1="AIzaSyCBqTFHJ9gLhUBygCA6bOjR1eCDSTXHES4"
GOOGLE_API_KEY_2="AIzaSyDMJSWkF2PEM-Z6tJzVSRxD69xk3mXtL_A"
GOOGLE_SEARCH_ENGINE_ID="your_search_engine_id_here"

# Perplexity API (선택사항)
PERPLEXITY_API_KEY="pplx-your_key_here"
    """
    
    with open('.env', 'a') as f:
        f.write(env_content)
    
    print("✅ 하이브리드 검색 시스템 설정 완료!")

if __name__ == "__main__":
    # 테스트
    searcher = HybridSearchSystem()
    
    # 대일외고 블로그 리서치
    results = searcher.blog_research("대일외고 영어 입시")
    
    print("📊 사용량 보고서:")
    print(searcher.get_usage_report())