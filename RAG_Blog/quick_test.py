"""
Perplexity API 빠른 테스트 스크립트
API 키 받아온 후 바로 실행해보세요.
"""

import os
from dotenv import load_dotenv
from perplexity_search import PerplexitySearcher

def quick_test():
    """빠른 API 테스트"""
    print("🔍 Perplexity API 테스트 시작...")
    
    # 환경변수 로드
    load_dotenv()
    
    try:
        # API 키 확인
        api_key = os.getenv('PERPLEXITY_API_KEY')
        if not api_key:
            print("❌ API 키가 설정되지 않았습니다.")
            print("1. .env 파일에 PERPLEXITY_API_KEY=your_key_here 추가")
            print("2. 또는 환경변수로 설정")
            return False
        
        print(f"✅ API 키 확인: {api_key[:10]}...")
        
        # 검색 테스트
        searcher = PerplexitySearcher()
        
        print("\n🔍 테스트 검색 실행...")
        result = searcher.search_korean("고등어닷컴 영어수학 학원")
        
        print("\n📋 검색 결과:")
        print("=" * 50)
        print(result[:500] + "..." if len(result) > 500 else result)
        print("=" * 50)
        
        print("\n✅ 테스트 성공! Perplexity API 사용 준비 완료")
        return True
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        return False

def test_blog_research():
    """블로그 리서치 기능 테스트"""
    print("\n🔬 블로그 리서치 기능 테스트...")
    
    try:
        from blog_research_assistant import BlogResearchAssistant
        
        assistant = BlogResearchAssistant()
        
        # 간단한 리서치 테스트
        print("📝 대일외고 기본 정보 검색 중...")
        result = assistant.searcher.search_korean("대일외고 2025년 입시 정보")
        
        print("\n📋 리서치 결과 미리보기:")
        print("-" * 30)
        print(result[:300] + "..." if len(result) > 300 else result)
        print("-" * 30)
        
        print("\n✅ 블로그 리서치 기능 테스트 성공!")
        return True
        
    except Exception as e:
        print(f"❌ 블로그 리서치 테스트 실패: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Perplexity API 통합 테스트")
    print("=" * 40)
    
    # 기본 API 테스트
    basic_test = quick_test()
    
    if basic_test:
        # 블로그 리서치 테스트
        research_test = test_blog_research()
        
        if research_test:
            print("\n🎉 모든 테스트 통과!")
            print("\n📝 이제 다음을 실행할 수 있습니다:")
            print("1. python blog_research_assistant.py  # 대일외고 전체 리서치")
            print("2. from perplexity_search import *    # 개별 검색 함수 사용")
            print("3. 블로그 글 작성 시작!")
        else:
            print("\n⚠️ 기본 API는 작동하지만 블로그 리서치에 문제가 있습니다.")
    else:
        print("\n❌ API 설정부터 다시 확인해주세요.")
    
    print("\n📚 가이드: perplexity_setup_guide.md 참조")