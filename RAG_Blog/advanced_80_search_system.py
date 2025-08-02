"""
AI 검색 최적화를 위한 80번 심층 검색 시스템
각 검색마다 개별 파일로 저장하여 단계별 분석
"""

import requests
import json
import time
from datetime import datetime
import pytz
import os

class Advanced80SearchSystem:
    def __init__(self):
        self.api_key = "AIzaSyBIBZNgGd_i_aG2IhlqFQqhl0MP3-J5CCA"
        self.search_engine_id = "2149f2d26311449a4"
        self.base_url = "https://www.googleapis.com/customsearch/v1"
        
        self.kst = pytz.timezone('Asia/Seoul')
        
        # 저장 경로 설정
        self.save_path = "D:/AI_Search_Optimization/"
        if not os.path.exists(self.save_path):
            try:
                os.makedirs(self.save_path)
            except:
                self.save_path = "Search/advanced_search_results/"
                os.makedirs(self.save_path, exist_ok=True)
        
        # 80가지 검색 주제 (AI 검색 최적화 중심)
        self.search_topics = [
            # 1-10: 최신 AI 검색 기술
            "AI search optimization 2025",
            "neural information retrieval latest",
            "semantic search algorithms improvement",
            "LLM web search enhancement",
            "retrieval augmented generation optimization",
            "vector database search efficiency",
            "embedding model search accuracy",
            "attention mechanism search relevance",
            "transformer search architecture",
            "BERT search ranking improvement",
            
            # 11-20: 검색 성능 향상
            "search latency optimization",
            "query processing speed enhancement",
            "indexing efficiency improvement",
            "search result ranking algorithms",
            "personalized search optimization",
            "contextual search understanding",
            "multi-modal search integration",
            "real-time search processing",
            "distributed search systems",
            "search cache optimization",
            
            # 21-30: 검색 품질 향상
            "search result relevance scoring",
            "query intent understanding",
            "search diversity optimization",
            "knowledge graph search integration",
            "entity recognition search",
            "fact verification search",
            "source credibility assessment",
            "search bias reduction",
            "multilingual search optimization",
            "cross-domain search adaptation",
            
            # 31-40: 검색 인터페이스 개선
            "conversational search interfaces",
            "voice search optimization",
            "visual search enhancement",
            "gesture-based search interaction",
            "augmented reality search",
            "mobile search optimization",
            "accessibility search design",
            "search user experience design",
            "search interface personalization",
            "adaptive search interfaces",
            
            # 41-50: 검색 데이터 처리
            "big data search processing",
            "streaming search analytics",
            "search data preprocessing",
            "noisy data search handling",
            "sparse data search optimization",
            "temporal search analysis",
            "spatial search optimization",
            "graph-based search methods",
            "hierarchical search structures",
            "federated search systems",
            
            # 51-60: 검색 학습 방법
            "reinforcement learning search",
            "transfer learning search",
            "few-shot learning search",
            "meta-learning search",
            "continual learning search",
            "active learning search",
            "self-supervised search learning",
            "contrastive learning search",
            "adversarial search training",
            "curriculum learning search",
            
            # 61-70: 검색 평가 방법
            "search evaluation metrics",
            "A/B testing search systems",
            "user satisfaction search",
            "click-through rate optimization",
            "search success measurement",
            "search quality assessment",
            "search performance benchmarking",
            "search relevance evaluation",
            "search efficiency metrics",
            "search robustness testing",
            
            # 71-80: 검색 응용 분야
            "enterprise search optimization",
            "e-commerce search enhancement",
            "scientific literature search",
            "legal document search",
            "medical information search",
            "educational content search",
            "news search optimization",
            "social media search",
            "patent search systems",
            "code search optimization"
        ]
    
    def search_and_save(self, topic, search_number):
        """단일 검색 실행 및 파일 저장"""
        try:
            # 검색 실행
            params = {
                'key': self.api_key,
                'cx': self.search_engine_id,
                'q': topic,
                'num': 10,
                'dateRestrict': 'm1'  # 최근 1개월
            }
            
            response = requests.get(self.base_url, params=params)
            data = response.json()
            
            # 검색 결과 처리
            results = {
                'search_number': search_number,
                'topic': topic,
                'timestamp': datetime.now(self.kst).isoformat(),
                'total_results': data.get('searchInformation', {}).get('totalResults', '0'),
                'search_time': data.get('searchInformation', {}).get('searchTime', '0'),
                'items': []
            }
            
            if 'items' in data:
                for item in data['items']:
                    results['items'].append({
                        'title': item.get('title', ''),
                        'link': item.get('link', ''),
                        'snippet': item.get('snippet', ''),
                        'displayLink': item.get('displayLink', '')
                    })
            
            # 파일 저장
            filename = f"search_{search_number:03d}_{topic.replace(' ', '_').replace('/', '_')[:50]}.json"
            filepath = os.path.join(self.save_path, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 검색 {search_number}/80 완료: {topic}")
            print(f"📁 저장 위치: {filepath}")
            
            return True, filepath
            
        except Exception as e:
            print(f"❌ 검색 {search_number} 실패: {str(e)}")
            return False, None
    
    def run_batch_search(self, start_num=1, count=5):
        """배치 검색 실행 (5개씩)"""
        successful_searches = []
        
        for i in range(count):
            if start_num + i > 80:
                break
                
            search_num = start_num + i
            topic = self.search_topics[search_num - 1]
            
            success, filepath = self.search_and_save(topic, search_num)
            if success:
                successful_searches.append(filepath)
            
            # API 제한 방지 대기
            time.sleep(1)
        
        return successful_searches

if __name__ == "__main__":
    system = Advanced80SearchSystem()
    results = system.run_batch_search(1, 5)  # 첫 5개 검색
    print(f"\n🎯 완료된 검색: {len(results)}개")