#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
자동 하이브리드 검색 테스트 실행기
RAG_Blog 방식을 견습한 자동 검색 + MD/TXT 저장

작성일: 2025년 8월 1일 19:05 (KST)
"""

from hybrid_search import auto_search_with_claude_results

def test_auto_search():
    """자동 검색 테스트 실행 (Claude 웹 검색 결과 포함)"""
    
    print("=== AI민진 자동 하이브리드 검색 테스트 ===")
    print("RAG_Blog 방식 적용: MD + TXT 파일 저장")
    print("Claude 웹 검색 결과를 포함한 하이브리드 검색")
    print("=" * 50)
    
    # 테스트 주제와 검색 횟수
    topic = "AI로 돈 버는 방법"
    search_count = 4
    
    # Claude 웹 검색 결과 시뮬레이션 (실제로는 web_search 도구 결과)
    claude_web_results = [
        {
            'title': 'ChatGPT로 돈 버는 5가지 방법',
            'content': '2025년 최신 AI 수익 창출 방법들',
            'url': 'https://example.com/chatgpt-money',
            'source': 'Claude Web Search'
        },
        {
            'title': 'AI 봇으로 수동 소득 만들기',
            'content': '자동화된 AI 시스템으로 월 $1,000-$15,000 수익',
            'url': 'https://example.com/ai-bots',
            'source': 'Claude Web Search'
        }
    ]
    
    # 자동 검색 실행
    results = auto_search_with_claude_results(topic, search_count, claude_web_results)
    
    print("\n" + "=" * 50)
    print("테스트 완료!")
    print(f"검색 결과가 Individual_Search_Results 폴더에 저장되었습니다.")
    print("MD 파일과 TXT 파일 두 형식으로 저장됨")
    
    return results

if __name__ == "__main__":
    test_auto_search()