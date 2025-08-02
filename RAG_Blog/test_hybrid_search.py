"""
하이브리드 검색 시스템 테스트
Google API 키 2개로 무료 200쿼리/일 활용
"""

from hybrid_search_system import HybridSearchSystem
from dotenv import load_dotenv

def test_google_search():
    """Google API 테스트"""
    print("🔍 Google Search API 테스트...")
    
    searcher = HybridSearchSystem()
    
    # 고등어닷컴 학원 검색
    result = searcher.google_search("고등어닷컴 영어수학 학원 대일외고")
    
    if result['success']:
        print(f"✅ 검색 성공! {len(result['results'])}개 결과")
        print(f"📊 {result['usage']}")
        
        print("\n📋 상위 3개 결과:")
        for i, item in enumerate(result['results'][:3], 1):
            print(f"{i}. {item['title']}")
            print(f"   🔗 {item['url']}")
            print(f"   📝 {item['snippet'][:100]}...")
            print()
    else:
        print(f"❌ 검색 실패: {result['error']}")

def test_blog_research():
    """블로그 리서치 테스트"""
    print("📝 대일외고 블로그 리서치 테스트...")
    
    searcher = HybridSearchSystem()
    
    # 실제 블로그 리서치 실행
    results = searcher.blog_research("대일외고 영어 내신")
    
    print("📊 리서치 결과:")
    print(f"주제: {results['topic']}")
    print(f"실행 시간: {results['timestamp']}")
    
    for search_type, search_result in results['searches'].items():
        print(f"\n🔎 {search_type}:")
        if search_result['success']:
            if 'results' in search_result:  # Google 결과
                print(f"  - {len(search_result['results'])}개 결과 발견")
            elif 'content' in search_result:  # Perplexity 결과  
                print(f"  - AI 분석 완료 ({len(search_result['content'])}자)")
        else:
            print(f"  - 오류: {search_result['error']}")
    
    # 사용량 보고서
    print(searcher.get_usage_report())

def daily_usage_simulation():
    """하루 사용량 시뮬레이션"""
    print("📊 하루 사용량 시뮬레이션...")
    
    searcher = HybridSearchSystem()
    
    # 블로그 작업 (노트북)
    blog_topics = [
        "대일외고 입시 준비",
        "대일외고 영어 내신 관리법", 
        "외고 영어 학원 선택 가이드"
    ]
    
    for topic in blog_topics:
        print(f"📝 {topic} 리서치 중...")
        results = searcher.blog_research(topic)
        print(f"   ✅ 완료")
    
    # AI민진 작업 (데스크탑) 시뮬레이션
    ai_minjin_queries = [
        "Python 웹 크롤링 최신 방법",
        "Claude API 사용법 2025",
        "블로그 SEO 자동화 도구"
    ]
    
    for query in ai_minjin_queries:
        print(f"🤖 AI민진: {query} 검색 중...")
        result = searcher.smart_search(query)
        print(f"   ✅ 완료")
    
    print("\n📊 하루 종합 사용량:")
    print(searcher.get_usage_report())
    
    print("\n💡 결론:")
    print("- Google API 2개로 200쿼리/일 = 월 6000쿼리")
    print("- 예상 비용: 거의 무료 (무료 한도 내)")
    print("- Perplexity 없이도 충분한 검색 품질")

if __name__ == "__main__":
    load_dotenv()
    
    print("🚀 하이브리드 검색 시스템 테스트")
    print("=" * 50)
    
    # 1. 기본 Google 검색 테스트
    test_google_search()
    
    print("\n" + "=" * 50)
    
    # 2. 블로그 리서치 테스트  
    test_blog_research()
    
    print("\n" + "=" * 50)
    
    # 3. 하루 사용량 시뮬레이션
    daily_usage_simulation()