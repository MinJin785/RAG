"""
AI 검색 능력 향상 방법 30번 집중 검색 시스템
AI가 웹 검색을 잘하는 방법을 연구하여 실제 적용
"""

import requests
import json
import time
from datetime import datetime
import pytz
import os

class AISearchImprovementSystem:
    def __init__(self):
        self.api_key = "AIzaSyBIBZNgGd_i_aG2IhlqFQqhl0MP3-J5CCA"
        self.search_engine_id = "2149f2d26311449a4"
        self.base_url = "https://www.googleapis.com/customsearch/v1"

        self.kst = pytz.timezone('Asia/Seoul')

        self.search_results = []
        self.search_count = 0
        self.main_topic = "AI 웹 검색 능력 향상 방법"  # 주제 고정

        # 30가지 검색 각도 (AI 검색 능력 향상 중심)
        self.search_angles = [
            # 기본 정보 (1-5)
            "최신 연구", "2025년", "논문", "실험 결과", "성공 사례",
            # AI 검색 기법 (6-10)
            "쿼리 최적화", "키워드 선택", "검색 전략", "정보 필터링", "결과 분석",
            # 기술적 방법 (11-15)
            "자연어 처리", "의미 분석", "컨텍스트 이해", "정보 추출", "데이터 마이닝",
            # 실무 적용 (16-20)
            "실전 기법", "검색 패턴", "질문 구성", "정보 검증", "신뢰성 평가",
            # 고급 전략 (21-25)
            "다각도 접근", "교차 검증", "소스 다양화", "편향 제거", "정확도 향상",
            # 수익화 활용 (26-30)
            "비즈니스 활용", "시장 조사", "경쟁 분석", "트렌드 파악", "기회 발굴"
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
        print("🚀 AI 검색 능력 향상을 위한 30가지 각도 연구 시작!")
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
        print(f"🎉 '{self.main_topic}' 30번 연구 완료!")
        print(f"📊 성공: {self.search_count}/30")
        print(f"⏱️ 소요시간: {duration}")

        print(f"💾 결과 저장 및 분석 중...")
        self.save_results()
        self.analyze_money_making_opportunities()

    def save_results(self):
        """검색 결과 저장"""
        timestamp = datetime.now(self.kst).strftime("%Y%m%d_%H%M%S")

        filename_json = f"ai_search_improvement_results_{timestamp}.json"
        with open(filename_json, 'w', encoding='utf-8') as f:
            json.dump(self.search_results, f, ensure_ascii=False, indent=2)
        print(f"✅ 상세 결과: {filename_json}")

        filename_md = f"ai_search_improvement_summary_{timestamp}.md"
        self.generate_improvement_guide(filename_md)
        print(f"✅ AI 검색 향상 가이드: {filename_md}")

    def analyze_money_making_opportunities(self):
        """검색 결과에서 수익화 기회 분석"""
        print("\n💰 수익화 기회 분석 중...")
        
        money_keywords = ["수익", "돈", "매출", "수입", "비즈니스", "마케팅", "판매", "광고", "아피리에이트", "블로그", "유튜브", "틱톡"]
        
        opportunities = []
        for search_data in self.search_results:
            for result in search_data['results']:
                title = result['title'].lower()
                snippet = result['snippet'].lower()
                
                for keyword in money_keywords:
                    if keyword in title or keyword in snippet:
                        opportunities.append({
                            'query': search_data['query'],
                            'title': result['title'],
                            'link': result['link'],
                            'snippet': result['snippet'],
                            'money_keyword': keyword
                        })
                        break
        
        if opportunities:
            print(f"🎯 발견된 수익화 기회: {len(opportunities)}개")
            filename_money = f"money_opportunities_{datetime.now(self.kst).strftime('%Y%m%d_%H%M%S')}.md"
            with open(filename_money, 'w', encoding='utf-8') as f:
                f.write("# 💰 발견된 수익화 기회 분석\n\n")
                f.write(f"생성일시: {datetime.now(self.kst).strftime('%Y년 %m월 %d일 %H:%M')} (KST)\n\n")
                
                for i, opp in enumerate(opportunities, 1):
                    f.write(f"## {i}. {opp['title']}\n")
                    f.write(f"**검색 쿼리**: {opp['query']}\n")
                    f.write(f"**링크**: {opp['link']}\n")
                    f.write(f"**수익 키워드**: {opp['money_keyword']}\n")
                    f.write(f"**내용**: {opp['snippet']}\n\n")
                    f.write("---\n\n")
            
            print(f"✅ 수익화 기회 리포트: {filename_money}")
        else:
            print("💡 이번 검색에서는 직접적인 수익화 기회를 발견하지 못했습니다.")

    def generate_improvement_guide(self, filename):
        """AI 검색 능력 향상 가이드 생성"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"# AI 웹 검색 능력 향상 가이드\n\n")
            f.write(f"생성일시: {datetime.now(self.kst).strftime('%Y년 %m월 %d일 %H:%M')} (KST)\n\n")

            f.write("## 연구 개요\n")
            f.write(f"- **주제**: {self.main_topic}\n")
            f.write(f"- **총 검색 수**: {self.search_count}/30\n")
            f.write(f"- **성공률**: {(self.search_count/30)*100:.1f}%\n\n")

            f.write("## 검색 각도별 분석 결과\n")
            for search_data in self.search_results:
                f.write(f"\n### {search_data['query_number']}. {search_data['query']}\n")
                f.write(f"- 검색 결과: {search_data['total_results']}개\n")
                f.write("- 핵심 인사이트:\n")
                for item in search_data['results'][:3]:
                    f.write(f"  📌 [{item['title']}]({item['link']})\n")
                    f.write(f"     💡 {item['snippet'][:150]}...\n")
                f.write("\n")

            # AI 검색 능력 향상 방법론 정리
            f.write("## 🚀 AI 검색 능력 향상 핵심 방법론\n\n")
            f.write("### 1. 검색 쿼리 최적화 전략\n")
            f.write("- **단계적 접근**: 기본 키워드 → 세부 키워드 → 롱테일 키워드\n")
            f.write("- **의도 파악**: 정보성/상업성/거래성 의도 구분\n")
            f.write("- **컨텍스트 활용**: 검색 목적과 배경 정보 반영\n\n")
            
            f.write("### 2. 정보 검증 및 신뢰성 평가\n")
            f.write("- **소스 다양화**: 여러 출처에서 정보 수집\n")
            f.write("- **교차 검증**: 동일 정보의 다른 소스 확인\n")
            f.write("- **최신성 체크**: 정보의 발행/업데이트 날짜 확인\n\n")
            
            f.write("### 3. 수익화 기회 발굴 전략\n")
            f.write("- **키워드 모니터링**: 수익 관련 키워드 자동 탐지\n")
            f.write("- **트렌드 분석**: 새로운 비즈니스 기회 파악\n")
            f.write("- **경쟁사 연구**: 성공 사례 벤치마킹\n\n")

            f.write("### 4. 실제 적용 방법\n")
            f.write("- 모든 검색에 위 방법론 적용\n")
            f.write("- 검색 결과 체계적 분석 및 기록\n")
            f.write("- 수익화 기회 발견 시 즉시 보고\n")
            f.write("- 지속적인 방법론 개선 및 업데이트\n\n")

if __name__ == "__main__":
    search_system = AISearchImprovementSystem()
    search_system.run_30_searches()