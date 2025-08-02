"""
30번 하이브리드 검색 시작 
클로드 15번 + 구글 15번으로 블로그 수익화 리서치
"""

from hybrid_search_manager import HybridSearchManager
import time

def main():
    print("🚀 30번 하이브리드 검색 시작!")
    print("=" * 60)
    
    # 검색 매니저 초기화
    manager = HybridSearchManager()
    
    # Google Search Engine ID 설정
    manager.setup_google_search("2149f2d26311449a4")
    
    # 블로그 수익화를 위한 30개 검색 쿼리
    search_queries = [
        # 클로드 15번 (일반 트렌드/키워드)
        "대일외고 입시 트렌드 2025",
        "외고 영어 내신 준비 방법",  
        "영어 학원 마케팅 전략",
        "블로그 SEO 키워드 리서치",
        "교육 블로그 수익화 방법",
        "애프릴리에이트 마케팅 교육",
        "구글 애드센스 승인 조건",
        "외고 입시 경쟁률 분석",
        "영어 교육 시장 현황",
        "학부모 검색 키워드",
        "교육 콘텐츠 제작 팁",
        "온라인 영어 강의 트렌드", 
        "입시 정보 블로그 성공사례",
        "교육 업계 인플루언서 분석",
        "2025년 교육 정책 변화",
        
        # 구글 15번 (구체적 정보)
        "대일외고 공식 입시요강 2025",
        "서울 외고 순위 비교",
        "영어 내신 교재 추천",
        "학원 선택 기준",
        "외고 합격생 후기",
        "영어 공부법 베스트셀러",
        "교육 관련 정부 정책",
        "사교육 시장 통계",
        "온라인 교육 플랫폼 비교",
        "학습 관리 앱 순위",
        "교육 투자 수익률",
        "영어 능력 평가 시험",
        "해외 교육 트렌드",
        "에듀테크 스타트업 현황",
        "영어학원 창업 가이드"
    ]
    
    print(f"📝 총 {len(search_queries)}개 쿼리 준비 완료")
    print("\n🔍 검색 시작...")
    
    # 검색 실행
    for i, query in enumerate(search_queries, 1):
        print(f"\n[{i}/30] 검색 중...")
        
        try:
            result = manager.search_with_balance(query)
            
            if "error" in result:
                print(f"❌ 검색 실패: {result['error']}")
            else:
                print(f"✅ 검색 성공")
            
            # API 제한을 위한 딜레이
            time.sleep(1)
            
        except Exception as e:
            print(f"❌ 예외 발생: {e}")
    
    # 최종 결과 저장
    manager.save_results("blog_research_results.json")
    
    print("\n" + "=" * 60)
    print("🎉 30번 하이브리드 검색 완료!")
    
    summary = manager.get_search_summary()
    for key, value in summary.items():
        print(f"📊 {key}: {value}")

if __name__ == "__main__":
    main()