"""
클로드 web_search + 구글 API 하이브리드 검색 관리자
30번 검색을 50:50으로 분배하여 신뢰도 극대화
"""

import requests
import json
import os
from datetime import datetime
from typing import Dict, List

class HybridSearchManager:
    def __init__(self):
        # 구글 API 설정
        self.google_api_keys = [
            "AIzaSyCBqTFHJ9gLhUBygCA6bOjR1eCDSTXHES4",
            "AIzaSyDMJSWkF2PEM-Z6tJzVSRxD69xk3mXtL_A"
        ]
        self.google_search_id = None  # 사용자가 설정해야 함
        
        # 검색 카운터
        self.search_counts = {
            "claude": 0,
            "google": 0,
            "total": 0
        }
        
        # 검색 결과 저장
        self.search_results = []
        
    def search_with_balance(self, query: str, source: str = "auto") -> Dict:
        """
        균형잡힌 검색 수행
        source: "auto", "claude", "google"
        """
        if source == "auto":
            # 50:50 비율 유지
            if self.search_counts["claude"] < 15 and self.search_counts["google"] < 15:
                # 둘 다 가능하면 교대로
                source = "claude" if self.search_counts["total"] % 2 == 0 else "google"
            elif self.search_counts["claude"] < 15:
                source = "claude"
            elif self.search_counts["google"] < 15:
                source = "google"
            else:
                return {"error": "검색 한도 초과 (30회)"}
        
        print(f"🔍 [{source.upper()}] 검색: {query}")
        
        if source == "claude":
            result = self._claude_search(query)
        elif source == "google":
            result = self._google_search(query)
        else:
            return {"error": "잘못된 검색 소스"}
        
        # 결과 저장
        search_record = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "source": source,
            "result": result
        }
        self.search_results.append(search_record)
        
        # 카운터 업데이트
        self.search_counts[source] += 1
        self.search_counts["total"] += 1
        
        print(f"📊 검색 현황: Claude {self.search_counts['claude']}/15, Google {self.search_counts['google']}/15")
        
        return result
    
    def _claude_search(self, query: str) -> Dict:
        """Claude web_search 도구 시뮬레이션"""
        # 실제로는 web_search 도구를 호출해야 함
        return {
            "source": "claude",
            "query": query,
            "note": "이 부분은 실제 web_search 도구 호출로 대체되어야 함",
            "method": "claude_web_search_tool"
        }
    
    def _google_search(self, query: str) -> Dict:
        """Google Custom Search API 호출"""
        if not self.google_search_id:
            return {
                "error": "Google Search Engine ID가 설정되지 않았습니다",
                "setup_needed": True
            }
        
        api_key = self.google_api_keys[0]  # 첫 번째 키 사용
        
        url = f"https://www.googleapis.com/customsearch/v1"
        params = {
            "key": api_key,
            "cx": self.google_search_id,
            "q": query,
            "num": 10
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                results = []
                
                for item in data.get('items', []):
                    results.append({
                        "title": item.get('title'),
                        "url": item.get('link'),
                        "snippet": item.get('snippet')
                    })
                
                return {
                    "source": "google",
                    "query": query,
                    "total_results": data.get('searchInformation', {}).get('totalResults'),
                    "results": results
                }
            else:
                return {
                    "error": f"Google API 오류: {response.status_code}",
                    "response": response.text
                }
        except Exception as e:
            return {
                "error": f"Google 검색 실패: {e}"
            }
    
    def setup_google_search(self, search_engine_id: str):
        """Google Search Engine ID 설정"""
        self.google_search_id = search_engine_id
        print(f"✅ Google Search Engine ID 설정 완료: {search_engine_id}")
    
    def get_search_summary(self) -> Dict:
        """검색 현황 요약"""
        return {
            "총_검색": self.search_counts["total"],
            "Claude_검색": self.search_counts["claude"],
            "Google_검색": self.search_counts["google"],
            "남은_Claude": 15 - self.search_counts["claude"],
            "남은_Google": 15 - self.search_counts["google"],
            "균형_상태": "균형" if abs(self.search_counts["claude"] - self.search_counts["google"]) <= 1 else "불균형"
        }
    
    def save_results(self, filename: str = "search_results.json"):
        """검색 결과 저장"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                "summary": self.get_search_summary(),
                "searches": self.search_results
            }, f, ensure_ascii=False, indent=2)
        print(f"💾 검색 결과가 {filename}에 저장되었습니다")

def main():
    manager = HybridSearchManager()
    
    print("🔧 하이브리드 검색 시스템 시작")
    print("=" * 50)
    
    # Google Search Engine ID 설정 필요
    print("⚠️ Google Custom Search 설정이 필요합니다:")
    print("1. https://programmablesearchengine.google.com/ 방문")
    print("2. Search Engine 생성 (Sites to search: *)")
    print("3. Search Engine ID 복사")
    print("4. manager.setup_google_search('your_id') 호출")
    
    print("\n📊 현재 검색 현황:")
    summary = manager.get_search_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")

if __name__ == "__main__":
    main()