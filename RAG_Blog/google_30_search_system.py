"""
구글 API 30번 체계적 검색 시스템
RAG_Blog 수익화를 위한 종합 리서치
"""

import requests
import json
import time
from datetime import datetime
import pytz
import os

class Google30SearchSystem:
    def __init__(self):
        self.api_key = "AIzaSyBIBZNgGd_i_aG2IhlqFQqhl0MP3-J5CCA"
        self.search_engine_id = "2149f2d26311449a4"
        self.base_url = "https://www.googleapis.com/customsearch/v1"
        
        # 한국 표준시 설정
        self.kst = pytz.timezone('Asia/Seoul')
        
        # 검색 결과 저장
        self.search_results = []
        self.search_count = 0
        
        # 30개 체계적 검색 쿼리 (블로그 수익화 중심)
        self.search_queries = [
            # 1-5: 대일외고 관련 (핵심 타겟)
            "대일외고 입시 트렌드 2025년 최신 정보",
            "대일외고 영어 내신 준비 방법 학습법",
            "대일외고 합격 후기 성공사례 2024",
            "대일외고 vs 다른 외고 비교 분석",
            "대일외고 영어 학원 추천 순위",
            
            # 6-10: 외고 일반 (확장 키워드)
            "외국어고등학교 입시 경쟁률 2025",
            "외고 영어 내신 1등급 받는 법",
            "외고 입학 후 대학 진학률 통계",
            "외고 영어 교재 추천 순위",
            "외고 학생 영어 공부법 노하우",
            
            # 11-15: 영어 학원 마케팅 (수익화 직결)
            "영어 학원 마케팅 전략 성공사례",
            "온라인 영어 교육 시장 트렌드 2025",
            "영어 학원 블로그 마케팅 방법",
            "영어 교육 업체 SEO 최적화 방법",
            "영어 학원 수강생 모집 광고 전략",
            
            # 16-20: 블로그 수익화 (핵심 전략)
            "교육 블로그 수익화 방법 2025",
            "구글 애드센스 승인 받는 방법",
            "애프릴리에이트 마케팅 교육 분야",
            "블로그 SEO 최적화 완벽 가이드",
            "교육 콘텐츠 제작으로 돈 버는 법",
            
            # 21-25: 경쟁 분석 (시장 조사)
            "대일외고 관련 블로그 인기 순위",
            "영어 교육 인플루언서 분석 2025",
            "교육 블로거 수익 모델 분석",
            "입시 정보 사이트 트래픽 분석",
            "영어 학습 앱 시장 현황 분석",
            
            # 26-30: 콘텐츠 아이디어 (실행 전략)
            "학부모가 자주 검색하는 교육 키워드",
            "영어 공부 관련 인기 검색어 2025",
            "입시 정보 검색 트렌드 분석",
            "교육 유튜브 인기 주제 분석",
            "온라인 교육 콘텐츠 제작 트렌드"
        ]
    
    def search_google(self, query, result_count=10):
        """구글 검색 실행"""
        params = {
            'key': self.api_key,
            'cx': self.search_engine_id,
            'q': query,
            'num': result_count
        }
        
        try:
            print(f"🔍 [{self.search_count + 1}/30] 검색 중: {query}")
            
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
                
                print(f"✅ 완료: {len(items)}개 결과, 총 {search_info.get('totalResults', 'N/A')}개")
                return True
                
            else:
                print(f"❌ 오류: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 예외 발생: {str(e)}")
            return False
    
    def run_30_searches(self, delay=2):
        """30번 체계적 검색 실행"""
        print("🚀 구글 API 30번 체계적 검색 시작!")
        print("=" * 60)
        
        start_time = datetime.now(self.kst)
        
        for i, query in enumerate(self.search_queries):
            success = self.search_google(query)
            
            if not success:
                print(f"⚠️ 검색 {i+1} 실패, 계속 진행...")
            
            # API 제한 방지를 위한 딜레이
            if i < len(self.search_queries) - 1:  # 마지막이 아니면
                print(f"⏳ {delay}초 대기 중...")
                time.sleep(delay)
        
        end_time = datetime.now(self.kst)
        duration = end_time - start_time
        
        print("\n" + "=" * 60)
        print(f"🎉 30번 검색 완료!")
        print(f"📊 성공: {self.search_count}개 / 30개")
        print(f"⏱️ 소요 시간: {duration}")
        print(f"💾 결과 저장 중...")
        
        # 결과 저장
        self.save_results()
        
    def save_results(self):
        """검색 결과 저장"""
        timestamp = datetime.now(self.kst).strftime("%Y%m%d_%H%M%S")
        
        # JSON 형태로 상세 저장
        filename_json = f"google_30_search_results_{timestamp}.json"
        with open(filename_json, 'w', encoding='utf-8') as f:
            json.dump(self.search_results, f, ensure_ascii=False, indent=2)
        
        # 요약 리포트 생성
        filename_summary = f"google_30_search_summary_{timestamp}.md"
        self.generate_summary_report(filename_summary)
        
        print(f"✅ 상세 결과: {filename_json}")
        print(f"✅ 요약 리포트: {filename_summary}")
    
    def generate_summary_report(self, filename):
        """요약 리포트 생성"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("# 구글 API 30번 검색 요약 리포트\n\n")
            f.write(f"생성일시: {datetime.now(self.kst).strftime('%Y년 %m월 %d일 %H:%M')} (KST)\n\n")
            
            f.write("## 검색 통계\n")
            f.write(f"- 총 검색 수: {self.search_count}/30\n")
            f.write(f"- 성공률: {(self.search_count/30)*100:.1f}%\n\n")
            
            f.write("## 카테고리별 검색 결과\n\n")
            
            categories = [
                ("대일외고 관련 (1-5번)", self.search_results[0:5]),
                ("외고 일반 (6-10번)", self.search_results[5:10]),
                ("영어 학원 마케팅 (11-15번)", self.search_results[10:15]),
                ("블로그 수익화 (16-20번)", self.search_results[15:20]),
                ("경쟁 분석 (21-25번)", self.search_results[20:25]),
                ("콘텐츠 아이디어 (26-30번)", self.search_results[25:30])
            ]
            
            for category_name, results in categories:
                f.write(f"### {category_name}\n\n")
                
                for result in results:
                    if result:  # 결과가 있는 경우만
                        f.write(f"**{result['query_number']}. {result['query']}**\n")
                        f.write(f"- 총 결과: {result['total_results']}\n")
                        f.write(f"- 상위 3개 결과:\n")
                        
                        for i, item in enumerate(result['results'][:3], 1):
                            f.write(f"  {i}. [{item['title']}]({item['link']})\n")
                        
                        f.write("\n")
                
                f.write("\n")
            
            f.write("## 다음 단계 추천\n\n")
            f.write("1. **높은 검색량 키워드 우선 타겟팅**\n")
            f.write("2. **경쟁사 분석 결과 활용한 차별화 전략**\n")
            f.write("3. **수익화 직결 키워드로 콘텐츠 제작**\n")
            f.write("4. **SEO 최적화된 블로그 글 작성 시작**\n")

def main():
    searcher = Google30SearchSystem()
    searcher.run_30_searches(delay=3)  # 3초 딜레이로 안전하게

if __name__ == "__main__":
    main()