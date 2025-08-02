"""
집중 주제 30번 검색 시스템
하나의 주제를 30가지 각도로 심층 분석
"""

import requests
import json
import time
from datetime import datetime
import pytz
import os

class Focused30SearchSystem:
    def __init__(self):
        self.api_key = "AIzaSyBIBZNgGd_i_aG2IhlqFQqhl0MP3-J5CCA"
        self.search_engine_id = "2149f2d26311449a4"
        self.base_url = "https://www.googleapis.com/customsearch/v1"
        
        # 한국 표준시 설정
        self.kst = pytz.timezone('Asia/Seoul')
        
        # 검색 결과 저장
        self.search_results = []
        self.search_count = 0
        self.main_topic = ""
    
    def generate_30_queries(self, main_topic):
        """하나의 주제로 30개 검색 쿼리 생성"""
        self.main_topic = main_topic
        
        # 검색 각도별 패턴
        query_patterns = [
            # 1-5: 기본 정보
            f"{main_topic}",
            f"{main_topic} 최신 현황",
            f"{main_topic} 2025년",
            f"{main_topic} 통계",
            f"{main_topic} 데이터",
            
            # 6-10: 비교 분석
            f"{main_topic} 전년 대비",
            f"{main_topic} 역대 최고",
            f"{main_topic} 순위",
            f"{main_topic} 타 학교 비교",
            f"{main_topic} 경쟁률",
            
            # 11-15: 상세 분석
            f"{main_topic} 분석",
            f"{main_topic} 원인",
            f"{main_topic} 요인",
            f"{main_topic} 배경",
            f"{main_topic} 특징",
            
            # 16-20: 관련 키워드
            f"{main_topic} 입시",
            f"{main_topic} 진학",
            f"{main_topic} 합격",
            f"{main_topic} 교육",
            f"{main_topic} 학습",
            
            # 21-25: 전망/예측
            f"{main_topic} 전망",
            f"{main_topic} 예상",
            f"{main_topic} 미래",
            f"{main_topic} 계획",
            f"{main_topic} 목표",
            
            # 26-30: 관련 이슈
            f"{main_topic} 이슈",
            f"{main_topic} 문제",
            f"{main_topic} 해결",
            f"{main_topic} 개선",
            f"{main_topic} 후기"
        ]
        
        return query_patterns
    
    def search_google(self, query, result_count=10):
        """구글 검색 실행"""
        params = {
            'key': self.api_key,
            'cx': self.search_engine_id,
            'q': query,
            'num': result_count
        }
        
        try:
            print(f"🔍 [{self.search_count + 1}/30] 검색: {query}")
            
            response = requests.get(self.base_url, params=params, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                
                search_info = result.get('searchInformation', {})
                items = result.get('items', [])
                
                search_data = {
                    'query_number': self.search_count + 1,
                    'query': query,
                    'timestamp': datetime.now(self.kst).strftime('%Y-%m-%d %H:%M:%S KST'),
                    'total_results': search_info.get('totalResults', 'N/A'),
                    'search_time': search_info.get('searchTime', 'N/A'),
                    'results_count': len(items),
                    'results': []
                }
                
                for i, item in enumerate(items, 1):
                    search_data['results'].append({
                        'rank': i,
                        'title': item.get('title', ''),
                        'link': item.get('link', ''),
                        'snippet': item.get('snippet', ''),
                        'display_link': item.get('displayLink', '')
                    })
                
                self.search_results.append(search_data)
                self.search_count += 1
                
                print(f"✅ {len(items)}개 결과 (총 {search_info.get('totalResults', 'N/A')}개)")
                return True
                
            else:
                print(f"❌ 오류: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 예외: {str(e)}")
            return False
    
    def run_focused_search(self, main_topic, delay=3):
        """주제 집중 30번 검색 실행"""
        print(f"🎯 집중 주제: {main_topic}")
        print("🚀 30가지 각도 검색 시작!")
        print("=" * 60)
        
        # 30개 쿼리 생성
        queries = self.generate_30_queries(main_topic)
        
        start_time = datetime.now(self.kst)
        
        for i, query in enumerate(queries):
            success = self.search_google(query)
            
            if not success:
                print(f"⚠️ 검색 {i+1} 실패, 계속 진행...")
            
            # API 제한 방지 딜레이
            if i < len(queries) - 1:
                print(f"⏳ {delay}초 대기...")
                time.sleep(delay)
        
        end_time = datetime.now(self.kst)
        duration = end_time - start_time
        
        print("\n" + "=" * 60)
        print(f"🎉 '{main_topic}' 30번 검색 완료!")
        print(f"📊 성공: {self.search_count}/30")
        print(f"⏱️ 소요시간: {duration}")
        print(f"💾 결과 저장 중...")
        
        self.save_results()
    
    def save_results(self):
        """검색 결과 저장"""
        timestamp = datetime.now(self.kst).strftime("%Y%m%d_%H%M%S")
        safe_topic = self.main_topic.replace(" ", "_").replace("/", "_")
        
        # JSON 상세 저장
        filename_json = f"focused_search_{safe_topic}_{timestamp}.json"
        with open(filename_json, 'w', encoding='utf-8') as f:
            json.dump(self.search_results, f, ensure_ascii=False, indent=2)
        
        # 요약 리포트 생성
        filename_summary = f"focused_summary_{safe_topic}_{timestamp}.md"
        self.generate_summary_report(filename_summary)
        
        print(f"✅ 상세 결과: {filename_json}")
        print(f"✅ 요약 리포트: {filename_summary}")
    
    def generate_summary_report(self, filename):
        """요약 리포트 생성"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"# '{self.main_topic}' 집중 검색 리포트\n\n")
            f.write(f"생성일시: {datetime.now(self.kst).strftime('%Y년 %m월 %d일 %H:%M')} (KST)\n\n")
            
            f.write("## 검색 개요\n")
            f.write(f"- **주제**: {self.main_topic}\n")
            f.write(f"- **총 검색 수**: {self.search_count}/30\n")
            f.write(f"- **성공률**: {(self.search_count/30)*100:.1f}%\n\n")
            
            f.write("## 검색 각도별 결과\n\n")
            
            # 각도별 그룹화
            angles = [
                ("기본 정보 (1-5)", self.search_results[0:5]),
                ("비교 분석 (6-10)", self.search_results[5:10]),
                ("상세 분석 (11-15)", self.search_results[10:15]),
                ("관련 키워드 (16-20)", self.search_results[15:20]),
                ("전망/예측 (21-25)", self.search_results[20:25]),
                ("관련 이슈 (26-30)", self.search_results[25:30])
            ]
            
            for angle_name, results in angles:
                f.write(f"### {angle_name}\n\n")
                
                for result in results:
                    if result:
                        f.write(f"**{result['query_number']}. {result['query']}**\n")
                        f.write(f"- 검색 결과: {result['total_results']}개\n")
                        
                        # 상위 3개 결과만 표시
                        if result['results']:
                            f.write("- 주요 결과:\n")
                            for i, item in enumerate(result['results'][:3], 1):
                                f.write(f"  {i}. [{item['title']}]({item['link']})\n")
                        f.write("\n")
                
                f.write("\n")
            
            f.write("## 종합 분석\n\n")
            f.write("### 핵심 발견사항\n")
            f.write("- (검색 결과를 바탕으로 작성 필요)\n\n")
            
            f.write("### 블로그 콘텐츠 제안\n")
            f.write("- (이 데이터로 만들 수 있는 블로그 글 아이디어)\n\n")
            
            f.write("### 추가 조사 필요 영역\n")
            f.write("- (더 깊이 파야 할 부분들)\n\n")

def main():
    # 사용 예시
    topic = input("집중 검색할 주제를 입력하세요: ")
    
    searcher = Focused30SearchSystem()
    searcher.run_focused_search(topic, delay=3)

if __name__ == "__main__":
    main()