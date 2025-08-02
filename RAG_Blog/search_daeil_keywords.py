"""
대일외고 인기 검색어 집중 분석
30가지 각도로 검색하여 사람들이 가장 많이 찾는 키워드 발굴
"""

from focused_30_search_system import Focused30SearchSystem

def main():
    print("🎯 대일외고 관련 인기 검색어 분석 시작!")
    
    searcher = Focused30SearchSystem()
    
    # 대일외고 관련 인기 검색어를 주제로 30번 검색
    main_topic = "대일외고 인기 검색어"
    
    searcher.run_focused_search(main_topic, delay=3)

if __name__ == "__main__":
    main()