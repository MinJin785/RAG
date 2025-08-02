"""
$20 Perplexity API 최대한 활용하기
600쿼리를 전략적으로 사용하는 스마트 시스템
"""

from hybrid_search_system import HybridSearchSystem
from datetime import datetime
import json
import os

class SmartAPIManager:
    def __init__(self):
        self.hybrid_searcher = HybridSearchSystem()
        self.monthly_budget = 600  # Perplexity 월 쿼리 제한
        self.usage_file = "api_usage_log.json"
        self.load_usage_log()
    
    def load_usage_log(self):
        """사용량 로그 로드"""
        try:
            with open(self.usage_file, 'r', encoding='utf-8') as f:
                self.usage_log = json.load(f)
        except FileNotFoundError:
            self.usage_log = {
                'perplexity_used': 0,
                'google_used': 0,
                'month': datetime.now().strftime('%Y-%m'),
                'queries': []
            }
    
    def save_usage_log(self):
        """사용량 로그 저장"""
        with open(self.usage_file, 'w', encoding='utf-8') as f:
            json.dump(self.usage_log, f, ensure_ascii=False, indent=2)
    
    def should_use_perplexity(self, query: str, importance: str = 'medium') -> bool:
        """
        Perplexity 사용 여부 결정
        
        Args:
            query: 검색어
            importance: 'high', 'medium', 'low'
        """
        # 월별 리셋 확인
        current_month = datetime.now().strftime('%Y-%m')
        if self.usage_log['month'] != current_month:
            self.usage_log = {
                'perplexity_used': 0,
                'google_used': 0,
                'month': current_month,
                'queries': []
            }
        
        # 사용량 체크
        remaining = self.monthly_budget - self.usage_log['perplexity_used']
        
        # 중요도별 임계값
        thresholds = {
            'high': 50,    # 50쿼리 남아도 사용
            'medium': 100, # 100쿼리 남을 때까지 사용  
            'low': 200     # 200쿼리 남을 때는 사용 안함
        }
        
        return remaining > thresholds.get(importance, 100)
    
    def smart_search(self, query: str, purpose: str = "일반", importance: str = "medium") -> dict:
        """
        스마트 검색: 상황에 맞는 API 선택
        
        Args:
            query: 검색어
            purpose: 검색 목적 (블로그, AI민진, 분석 등)
            importance: 중요도 (high, medium, low)
        """
        
        # 고급 분석이 필요한 키워드들
        advanced_keywords = [
            '분석', '트렌드', '비교', '예측', '전망', '경쟁', 
            '시장', '통계', '데이터', '인사이트', '전략'
        ]
        
        needs_advanced = any(keyword in query for keyword in advanced_keywords)
        use_perplexity = needs_advanced and self.should_use_perplexity(query, importance)
        
        # 검색 실행
        if use_perplexity:
            print(f"💎 Perplexity API 사용: {query[:30]}...")
            result = self.hybrid_searcher.perplexity_search(query)
            if result['success']:
                self.usage_log['perplexity_used'] += 1
                api_used = 'perplexity'
            else:
                # Perplexity 실패시 Google로 폴백
                result = self.hybrid_searcher.google_search(query)
                self.usage_log['google_used'] += 1
                api_used = 'google_fallback'
        else:
            print(f"🔍 Google API 사용: {query[:30]}...")
            result = self.hybrid_searcher.google_search(query)
            self.usage_log['google_used'] += 1
            api_used = 'google'
        
        # 로그 기록
        self.usage_log['queries'].append({
            'timestamp': datetime.now().isoformat(),
            'query': query,
            'purpose': purpose,
            'importance': importance,
            'api_used': api_used,
            'success': result.get('success', False)
        })
        
        self.save_usage_log()
        return result
    
    def blog_research_smart(self, topic: str) -> dict:
        """블로그를 위한 스마트 리서치 ($20 최대 활용)"""
        print(f"📝 '{topic}' 블로그 리서치 시작...")
        
        results = {
            'topic': topic,
            'timestamp': datetime.now().isoformat(),
            'searches': {}
        }
        
        # 1. 기본 정보 - Google 사용 (비용 절약)
        basic_result = self.smart_search(
            f"{topic} 2025년 최신 정보 현황",
            purpose="블로그_기본정보",
            importance="low"
        )
        results['searches']['basic_info'] = basic_result
        
        # 2. 경쟁 분석 - Perplexity 사용 (고급 분석)
        competition_result = self.smart_search(
            f"{topic} 블로그 경쟁 분석 키워드 트렌드 SEO",
            purpose="블로그_경쟁분석", 
            importance="high"
        )
        results['searches']['competition'] = competition_result
        
        # 3. 수익화 분석 - Perplexity 사용 (중요)
        monetization_result = self.smart_search(
            f"{topic} 수익화 방법 애드센스 애프릴리에이트 전략",
            purpose="블로그_수익화",
            importance="high"
        )
        results['searches']['monetization'] = monetization_result
        
        # 4. 키워드 리서치 - Google 사용
        keyword_result = self.smart_search(
            f"{topic} 관련 인기 검색어 키워드",
            purpose="블로그_키워드",
            importance="medium"
        )
        results['searches']['keywords'] = keyword_result
        
        return results
    
    def get_monthly_report(self) -> str:
        """월간 사용량 리포트"""
        remaining = self.monthly_budget - self.usage_log['perplexity_used']
        percentage = (self.usage_log['perplexity_used'] / self.monthly_budget) * 100
        
        report = f"""
📊 {self.usage_log['month']} API 사용량 리포트

💎 Perplexity API: {self.usage_log['perplexity_used']}/{self.monthly_budget} ({percentage:.1f}%)
🔍 Google API: {self.usage_log['google_used']} (무료)

📈 투자 효율성:
- 월 투자: $20
- 쿼리당 비용: ${20/max(1, self.usage_log['perplexity_used']):.2f}
- 남은 쿼리: {remaining}개

💡 추천 사항:
"""
        if remaining > 400:
            report += "- 🟢 Perplexity 더 적극적으로 활용하세요!"
        elif remaining > 200:
            report += "- 🟡 적절한 사용량입니다. 중요한 분석에 집중하세요."
        else:
            report += "- 🔴 사용량이 많습니다. Google API 위주로 사용하세요."
        
        return report

# 블로그 특화 함수들
def research_daeil_blog_smart():
    """대일외고 블로그를 위한 스마트 리서치"""
    manager = SmartAPIManager()
    
    topics = [
        "대일외고 입시 준비",
        "대일외고 영어 내신 관리",
        "외고 영어 학원 선택 가이드"
    ]
    
    for topic in topics:
        results = manager.blog_research_smart(topic)
        
        # 결과 저장
        filename = f"research_{topic.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"📄 {filename} 저장 완료")
    
    print(manager.get_monthly_report())

if __name__ == "__main__":
    # 이미 $20 낸 상황에서 최대한 활용하기
    research_daeil_blog_smart()