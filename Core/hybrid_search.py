#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI민진 자동 하이브리드 검색 시스템 (RAG_Blog 방식 적용)
수동 실행 없이 자동으로 검색하고 MD/TXT 파일로 저장

작성일: 2025년 8월 1일 19:00 (KST)
저장 방식: RAG_Blog의 AI_Search_Results_Individual 방식 견습
"""

import requests
import json
import time
from datetime import datetime, timedelta
import pytz
import os
import re

class Auto_Hybrid_Search_System:
    def __init__(self):
        # ai민진 필수 참조.txt에서 제공된 API 정보
        self.google_api_key = "AIzaSyBIBZNgGd_i_aG2IhlqFQqhl0MP3-J5CCA"
        self.search_engine_id = "2149f2d26311449a4"
        self.google_base_url = "https://www.googleapis.com/customsearch/v1"
        self.kst = pytz.timezone('Asia/Seoul')
        
        # 무료 한도: 100쿼리/일
        self.google_daily_limit = 100
        self.google_request_count = 0
        
        # RAG_Blog 방식 적용: Search/results 폴더
        self.base_folder = "C:\\Users\\user\\Dropbox\\RAG_Minjin\\Search\\results"
        
        # 폴더가 없으면 생성
        if not os.path.exists(self.base_folder):
            os.makedirs(self.base_folder)
            print(f"[{self.get_kst_time()}] Individual_Search_Results 폴더 생성: {self.base_folder}")
        
        # 최신 콘텐츠 필터링 (1개월 기준)
        self.content_cutoff_date = datetime.now(self.kst) - timedelta(days=30)
        
    def get_kst_time(self):
        """KST 기준 현재 시간 반환"""
        return datetime.now(self.kst).strftime('%Y년 %m월 %d일 %H:%M')
    
    def get_filename_timestamp(self):
        """파일명용 타임스탬프 생성 (KST 기준)"""
        return datetime.now(self.kst).strftime('%Y%m%d_%H%M%S')
    
    def create_recent_query(self, base_query):
        """최신 1개월 내용만 검색하도록 쿼리 수정"""
        one_month_ago = (datetime.now(self.kst) - timedelta(days=30)).strftime('%Y/%m/%d')
        recent_query = f"{base_query} after:{one_month_ago}"
        return recent_query
    
    def google_search(self, query, num_results=10):
        """Google Custom Search API 검색"""
        if self.google_request_count >= self.google_daily_limit:
            print(f"[{self.get_kst_time()}] Google API 일일 한도 초과 ({self.google_daily_limit}회)")
            return None
        
        recent_query = self.create_recent_query(query)
        
        params = {
            'key': self.google_api_key,
            'cx': self.search_engine_id,
            'q': recent_query,
            'num': min(num_results, 10),
            'sort': 'date'
        }
        
        try:
            print(f"[{self.get_kst_time()}] Google API 검색: {query}")
            response = requests.get(self.google_base_url, params=params)
            response.raise_for_status()
            
            self.google_request_count += 1
            result = response.json()
            
            # 검색 메타데이터 추가
            result['search_metadata'] = {
                'original_query': query,
                'filtered_query': recent_query,
                'search_time': self.get_kst_time(),
                'search_engine': 'Google Custom Search API',
                'content_filter': '최신 1개월',
                'request_count': self.google_request_count
            }
            
            return result
            
        except requests.exceptions.RequestException as e:
            print(f"[{self.get_kst_time()}] Google API 검색 오류: {e}")
            return None
    
    def claude_web_search_result(self, query, web_search_data):
        """Claude 내장 검색 결과를 구조화"""
        print(f"[{self.get_kst_time()}] Claude 내장 검색: {query}")
        
        recent_query = f"{query} 최신 2025년 recent"
        
        search_result = {
            'search_metadata': {
                'original_query': query,
                'enhanced_query': recent_query,
                'search_time': self.get_kst_time(),
                'search_engine': 'Claude Web Search',
                'content_filter': '최신 내용 우선'
            },
            'web_search_data': web_search_data,
            'status': 'completed'
        }
        
        return search_result
    
    def auto_hybrid_search(self, topic, total_searches, web_search_results=None):
        """
        자동 하이브리드 검색 실행 (RAG_Blog 방식 적용)
        
        Args:
            topic: 검색 주제
            total_searches: 총 검색 횟수
            web_search_results: Claude 웹 검색 결과 (옵션)
        """
        print(f"=== 자동 하이브리드 검색 시작: {topic} ===")
        print(f"[{self.get_kst_time()}] 총 {total_searches}번 검색 (50% Google API + 50% Claude)")
        
        # 검색 횟수를 50:50으로 분할
        google_searches = total_searches // 2
        claude_searches = total_searches - google_searches
        
        print(f"Google API 검색: {google_searches}번")
        print(f"Claude 검색: {claude_searches}번")
        
        results = []
        
        # 다양한 검색 각도 생성
        search_angles = self.generate_search_angles(topic, total_searches)
        
        # Google API 검색
        for i in range(google_searches):
            if i < len(search_angles):
                query = search_angles[i]
                print(f"[{self.get_kst_time()}] Google 검색 {i+1}/{google_searches}: {query}")
                
                result = self.google_search(query, 10)
                if result:
                    result['search_number'] = i + 1
                    result['search_type'] = 'Google API'
                    result['search_angle'] = query
                    results.append(result)
                
                # API 제한 회피를 위한 딜레이
                if i < google_searches - 1:
                    time.sleep(2)
        
        # Claude 내장 검색 결과 처리
        if web_search_results:
            for i in range(min(claude_searches, len(web_search_results))):
                angle_index = google_searches + i
                if angle_index < len(search_angles):
                    query = search_angles[angle_index]
                    print(f"[{self.get_kst_time()}] Claude 검색 {i+1}/{claude_searches}: {query}")
                    
                    result = self.claude_web_search_result(query, web_search_results[i])
                    result['search_number'] = angle_index + 1
                    result['search_type'] = 'Claude Web Search'
                    result['search_angle'] = query
                    results.append(result)
        
        # RAG_Blog 방식으로 결과 저장
        self.save_individual_search_results(topic, results, total_searches)
        
        print(f"[{self.get_kst_time()}] 자동 하이브리드 검색 완료: {len(results)}개 결과")
        return results
    
    def generate_search_angles(self, topic, total_searches):
        """주제에 대한 다양한 검색 각도 생성"""
        base_angles = [
            f"{topic}",
            f"{topic} 최신 현황",
            f"{topic} 2025년",
            f"{topic} 최근 소식",
            f"{topic} 업데이트",
            f"{topic} 분석",
            f"{topic} 전망",
            f"{topic} 트렌드",
            f"{topic} 통계",
            f"{topic} 데이터",
            f"{topic} 비교",
            f"{topic} 순위",
            f"{topic} 평가",
            f"{topic} 리뷰",
            f"{topic} 후기",
            f"{topic} 특징",
            f"{topic} 장점",
            f"{topic} 단점",
            f"{topic} 문제",
            f"{topic} 해결"
        ]
        
        if total_searches <= len(base_angles):
            return base_angles[:total_searches]
        else:
            extended_angles = base_angles.copy()
            for i in range(total_searches - len(base_angles)):
                extended_angles.append(f"{topic} 관련 {i+1}")
            return extended_angles
    
    def save_individual_search_results(self, topic, results, total_searches):
        """
        RAG_Blog 방식을 견습한 개별 검색 결과 저장 (MD/TXT 파일)
        
        Args:
            topic: 검색 주제
            results: 검색 결과 리스트
            total_searches: 총 검색 횟수
        """
        timestamp = self.get_filename_timestamp()
        
        # 주제명에서 파일명에 사용할 수 없는 문자 제거
        safe_topic = "".join(c for c in topic if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_topic = safe_topic.replace(' ', '_')[:50]
        
        # 파일명 생성 (TXT 하나로 통일)
        filename_txt = f"Search_{safe_topic}_1_to_{total_searches}_{timestamp}.txt"
        filepath_txt = os.path.join(self.base_folder, filename_txt)
        
        # TXT 콘텐츠 생성 (가독성 좋은 상세 버전)
        txt_content = self.create_detailed_txt_content(topic, results, total_searches, timestamp)
        
        try:
            # TXT 파일만 저장 (하나로 통일)
            with open(filepath_txt, 'w', encoding='utf-8') as f:
                f.write(txt_content)
            print(f"[{self.get_kst_time()}] 검색 결과 저장 완료: {filename_txt}")
            
        except Exception as e:
            print(f"[{self.get_kst_time()}] 파일 저장 실패: {e}")
    
    def create_markdown_content(self, topic, results, total_searches, timestamp):
        """RAG_Blog 방식을 견습한 마크다운 콘텐츠 생성"""
        
        content = f"""# {topic} - 1-{total_searches}번 하이브리드 검색 결과

생성일시: {self.get_kst_time()} (KST)
검색 주제: {topic} (1-{total_searches}번)
검색 방식: 하이브리드 (Google API + Claude 내장 검색)
콘텐츠 필터: 최신 1개월 내용 또는 가장 최신 자료

"""
        
        # Google vs Claude 검색 분석
        google_results = [r for r in results if r.get('search_type') == 'Google API']
        claude_results = [r for r in results if r.get('search_type') == 'Claude Web Search']
        
        content += f"""## 검색 분포 현황

- Google API 검색: {len(google_results)}번
- Claude 내장 검색: {len(claude_results)}번
- 총 결과: {len(results)}개

"""
        
        # 각 검색 결과별 정리 (RAG_Blog 방식)
        for i, result in enumerate(results, 1):
            search_angle = result.get('search_angle', f'검색 {i}')
            search_type = result.get('search_type', '알 수 없음')
            
            content += f"""## {i}번째 검색 결과: {search_angle}

### 🔍 {search_type} 검색 결과

"""
            
            if search_type == 'Google API':
                # Google 검색 결과 처리
                items = result.get('items', [])
                if items:
                    content += f"#### 검색된 상위 결과 ({len(items)}개)\n\n"
                    for idx, item in enumerate(items[:5], 1):  # 상위 5개만
                        title = item.get('title', '제목 없음')
                        link = item.get('link', '')
                        snippet = item.get('snippet', '설명 없음')
                        
                        content += f"**{idx}. {title}**\n"
                        content += f"- 링크: {link}\n"
                        content += f"- 요약: {snippet}\n\n"
                else:
                    content += "검색 결과 없음\n\n"
            
            elif search_type == 'Claude Web Search':
                # Claude 검색 결과 처리
                web_data = result.get('web_search_data', {})
                content += f"#### Claude 내장 검색 결과\n\n"
                content += f"- 검색 쿼리: {result.get('search_metadata', {}).get('enhanced_query', search_angle)}\n"
                content += f"- 검색 시간: {result.get('search_metadata', {}).get('search_time', '알 수 없음')}\n"
                content += f"- 검색 엔진: Claude Web Search\n\n"
            
            content += "---\n\n"
        
        content += f"""## 검색 요약

### 하이브리드 검색의 장점
1. **다양성**: Google API와 Claude 검색의 서로 다른 강점 활용
2. **최신성**: 최신 1개월 내용 우선 수집
3. **효율성**: {total_searches}번의 맞춤 검색으로 리소스 최적화
4. **신뢰성**: 두 소스의 교차 검증 가능

### 검색 품질 평가
- 총 검색 횟수: {total_searches}번
- 성공한 검색: {len(results)}번
- 검색 성공률: {len(results)/total_searches*100:.1f}%

---
*이 리포트는 AI민진 자동 하이브리드 검색 시스템으로 생성되었습니다.*
"""
        
        return content
    
    def create_detailed_txt_content(self, topic, results, total_searches, timestamp):
        """가독성 좋은 상세 TXT 형식 콘텐츠 생성 (RAG_Blog 방식 적용)"""
        
        content = f"""{topic} - 1-{total_searches}번 하이브리드 검색 결과

생성일시: {self.get_kst_time()} (KST)
검색 주제: {topic} (1-{total_searches}번)
검색 방식: 하이브리드 (Google API + Claude 내장 검색)
콘텐츠 필터: 최신 1개월 내용 또는 가장 최신 자료

========================================

검색 분포 현황:
- Google API 검색: {len([r for r in results if r.get('search_type') == 'Google API'])}번
- Claude 내장 검색: {len([r for r in results if r.get('search_type') == 'Claude Web Search'])}번
- 총 결과: {len(results)}개

========================================

"""
        
        # 각 검색 결과별 상세 정리 (RAG_Blog 방식)
        for i, result in enumerate(results, 1):
            search_angle = result.get('search_angle', f'검색 {i}')
            search_type = result.get('search_type', '알 수 없음')
            
            content += f"{i}번째 검색 결과: {search_angle}\n"
            content += f"검색 엔진: {search_type}\n\n"
            
            if search_type == 'Google API':
                # Google 검색 결과 상세 처리
                items = result.get('items', [])
                if items:
                    content += f"검색된 상위 결과 ({len(items)}개):\n\n"
                    for idx, item in enumerate(items[:5], 1):  # 상위 5개만
                        title = item.get('title', '제목 없음')
                        link = item.get('link', '')
                        snippet = item.get('snippet', '설명 없음')
                        
                        content += f"  {idx}. {title}\n"
                        content += f"     링크: {link}\n"
                        content += f"     요약: {snippet}\n\n"
                else:
                    content += "검색 결과 없음\n\n"
            
            elif search_type == 'Claude Web Search':
                # Claude 검색 결과 처리
                web_data = result.get('web_search_data', {})
                metadata = result.get('search_metadata', {})
                
                content += "Claude 내장 검색 결과:\n"
                content += f"  - 검색 쿼리: {metadata.get('enhanced_query', search_angle)}\n"
                content += f"  - 검색 시간: {metadata.get('search_time', '알 수 없음')}\n"
                content += f"  - 검색 엔진: Claude Web Search\n"
                content += f"  - 콘텐츠 필터: 최신 내용 우선\n\n"
            
            content += "=" * 60 + "\n\n"
        
        content += f"""검색 요약:

하이브리드 검색의 장점:
1. 다양성: Google API와 Claude 검색의 서로 다른 강점 활용
2. 최신성: 최신 1개월 내용 우선 수집
3. 효율성: {total_searches}번의 맞춤 검색으로 리소스 최적화
4. 신뢰성: 두 소스의 교차 검증 가능

검색 품질 평가:
- 총 검색 횟수: {total_searches}번
- 성공한 검색: {len(results)}번
- 검색 성공률: {len(results)/total_searches*100:.1f}%

========================================
이 리포트는 AI민진 자동 하이브리드 검색 시스템으로 생성되었습니다.
파일 형식: TXT (사용자 가독성 + AI 검색 최적화)
"""
        
        return content

def auto_search_with_claude_results(topic, search_count, claude_web_results=None):
    """자동 검색 실행 함수 (Claude 웹 검색 결과 포함)"""
    
    search_system = Auto_Hybrid_Search_System()
    
    print(f"=== {topic} {search_count}번 자동 하이브리드 검색 ===")
    print(f"저장 방식: RAG_Blog 견습 (MD + TXT 파일)")
    print(f"저장 폴더: {search_system.base_folder}")
    print("=" * 50)
    
    # 자동 하이브리드 검색 실행
    results = search_system.auto_hybrid_search(topic, search_count, claude_web_results)
    
    print(f"\n=== 자동 검색 완료 ===")
    print(f"총 {len(results)}개 검색 결과 저장됨")
    
    # 간단한 결과 요약 출력
    google_count = sum(1 for r in results if r.get('search_type') == 'Google API')
    claude_count = sum(1 for r in results if r.get('search_type') == 'Claude Web Search')
    
    print(f"- Google API 검색: {google_count}번")
    print(f"- Claude 내장 검색: {claude_count}번")
    
    return results

if __name__ == "__main__":
    # 테스트 실행
    auto_search_with_claude_results("AI로 돈 버는 방법", 4)