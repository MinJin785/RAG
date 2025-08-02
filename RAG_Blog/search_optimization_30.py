"""
검색 최적화 방법 30번 집중 검색 시스템
"""

import requests
import json
import time
from datetime import datetime
import pytz
import os

class SearchOptimization30System:
    def __init__(self):
        self.api_key = "AIzaSyBIBZNgGd_i_aG2IhlqFQqhl0MP3-J5CCA"
        self.search_engine_id = "2149f2d26311449a4"
        self.base_url = "https://www.googleapis.com/customsearch/v1"

        self.kst = pytz.timezone('Asia/Seoul')

        self.search_results = []
        self.search_count = 0
        self.main_topic = "검색 최적화 방법"  # 주제 고정

        # 30가지 검색 각도 (검색 최적화 중심)
        self.search_angles = [
            # 기본 정보 (1-5)
            "최신 트렌드", "2025년", "통계", "데이터", "성공 사례",
            # 비교 분석 (6-10)
            "구글 vs 네이버", "SEO 도구 비교", "키워드 전략", "경쟁 분석", "순위 요인",
            # 상세 분석 (11-15)
            "알고리즘 원리", "검색 엔진 작동 방식", "인덱싱 과정", "크롤링 최적화", "콘텐츠 품질",
            # 기술적 방법 (16-20)
            "기술적 SEO", "페이지 속도", "모바일 친화성", "구조화 데이터", "내부 링크",
            # 전략/예측 (21-25)
            "키워드 리서치", "백링크 전략", "사용자 경험", "클릭률 향상", "전환율 최적화",
            # 실무 적용 (26-30)
            "실무 가이드", "체크리스트", "도구 활용법", "측정 방법", "개선 방안"
        ]

    def search_google(self, query: str, num_results: int = 10) -> bool:
        """Google Custom Search API를 사용하여 검색 수행"""
        params = {
            'key': self.api_key,
            'cx': self.search_engine_id,
            'q': query,
            'num': num_results
        }
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()

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
                    'snippet': item.get('snippet', '')
                })

            self.search_results.append(search_data)
            self.search_count += 1
            print(f"🔍 [{self.search_count}/30] 검색: {query}")
            print(f"✅ {len(items)}개 결과 (총 {search_info.get('totalResults', 'N/A')}개)")
            return True

        except requests.exceptions.RequestException as e:
            print(f"❌ 오류: {e}")
            print(f"⚠️ 검색 {self.search_count + 1} 실패, 계속 진행...")
            self.search_count += 1
            return False

    def run_30_searches(self):
        """30번 체계적 검색 실행"""
        print(f"🎯 집중 주제: {self.main_topic}")
        print("🚀 30가지 각도 검색 시작!")
        print("=" * 60)

        start_time = datetime.now(self.kst)

        for i, angle in enumerate(self.search_angles):
            query = f"{self.main_topic} {angle}"
            success = self.search_google(query)

            if i < len(self.search_angles) - 1:
                print(f"⏳ 3초 대기 중...")
                time.sleep(3)

        end_time = datetime.now(self.kst)
        duration = end_time - start_time

        print("\n" + "=" * 60)
        print(f"🎉 '{self.main_topic}' 30번 검색 완료!")
        print(f"📊 성공: {self.search_count}/30")
        print(f"⏱️ 소요시간: {duration}")

        print(f"💾 결과 저장 중...")
        self.save_results()

    def save_results(self):
        """검색 결과 저장"""
        timestamp = datetime.now(self.kst).strftime("%Y%m%d_%H%M%S")

        filename_json = f"search_optimization_results_{timestamp}.json"
        with open(filename_json, 'w', encoding='utf-8') as f:
            json.dump(self.search_results, f, ensure_ascii=False, indent=2)
        print(f"✅ 상세 결과: {filename_json}")

        filename_md = f"search_optimization_summary_{timestamp}.md"
        self.generate_summary_report(filename_md)
        print(f"✅ 요약 리포트: {filename_md}")

    def generate_summary_report(self, filename):
        """요약 리포트 생성"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"# '{self.main_topic}' 집중 검색 리포트\n\n")
            f.write(f"생성일시: {datetime.now(self.kst).strftime('%Y년 %m월 %d일 %H:%M')} (KST)\n\n")

            f.write("## 검색 개요\n")
            f.write(f"- **주제**: {self.main_topic}\n")
            f.write(f"- **총 검색 수**: {self.search_count}/30\n")
            f.write(f"- **성공률**: {(self.search_count/30)*100:.1f}%\n\n")

            f.write("## 검색 각도별 결과\n")
            for search_data in self.search_results:
                f.write(f"\n### {search_data['query_number']}. {search_data['query']}\n")
                f.write(f"- 검색 결과: {search_data['total_results']}개\n")
                f.write("- 주요 결과:\n")
                for item in search_data['results'][:3]:
                    f.write(f"  1. [{item['title']}]({item['link']})\n")
                    f.write(f"     {item['snippet'][:100]}...\n")
                f.write("\n")

            # 검색 최적화 방법론 정리
            f.write("## 검색 최적화 방법론 종합 분석\n\n")
            f.write("### 핵심 검색 최적화 원칙\n")
            f.write("1. **기본부터 시작**: 단순 키워드 우선 검색\n")
            f.write("2. **키워드 클러스터링**: 관련 키워드들을 그룹으로 묶어 다각도 접근\n")
            f.write("3. **체계적 사이트 분석**: 메인 페이지 → 하위 페이지 순서\n")
            f.write("4. **경쟁사 분석 활용**: 성공한 결과들 우선 분석\n")
            f.write("5. **검색 의도 파악**: 사용자가 진짜 찾는 것이 무엇인지 이해\n\n")
            
            f.write("### AI민진 프로젝트 적용 가이드\n")
            f.write("- 모든 검색은 **구글 API만 사용**\n")
            f.write("- **30번 검색 = 1개 주제** 집중 분석\n")
            f.write("- **3초 딜레이** 의무적 적용\n")
            f.write("- **KST 시간 기준** 모든 로그 작성\n")
            f.write("- **JSON + 마크다운** 이중 저장\n\n")

if __name__ == "__main__":
    search_system = SearchOptimization30System()
    search_system.run_30_searches()