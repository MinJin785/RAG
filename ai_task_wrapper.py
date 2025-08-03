#!/usr/bin/env python3
"""
AI민진 자동 작업 관리 Wrapper
내가 대화 중에 자동으로 작업을 관리할 수 있도록 하는 도구
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from task_management_system import (
    ai_get_status, ai_create_task, ai_complete_task, 
    ai_daily_summary, init_task_system
)

def auto_track_conversation():
    """대화 시작시 자동 실행"""
    try:
        print("🤖 AI민진 작업 시스템 자동 시작...")
        
        # 시스템 초기화 및 상태 확인
        status = ai_get_status()
        
        # 진행중인 작업이 있으면 알림
        if status['in_progress'] > 0:
            print(f"⚠️ 진행중인 작업 {status['in_progress']}개가 있습니다")
        
        return True
        
    except Exception as e:
        print(f"❌ 자동 추적 시작 실패: {e}")
        return False

def auto_create_task_from_request(user_request: str) -> str:
    """사용자 요청을 분석해서 자동으로 작업 생성"""
    try:
        # 간단한 키워드 기반 카테고리 분류
        if any(word in user_request.lower() for word in ['ocr', 'pdf', '텍스트인식', '이미지']):
            category = "ocr"
        elif any(word in user_request.lower() for word in ['검색', 'search', '연구', '웹']):
            category = "research"
        elif any(word in user_request.lower() for word in ['코딩', 'python', '프로그래밍', '시스템']):
            category = "coding"
        elif any(word in user_request.lower() for word in ['돈', 'money', '수익', '블로그']):
            category = "money"
        else:
            category = "general"
        
        # 작업 제목 생성 (첫 50자)
        title = user_request[:50] + "..." if len(user_request) > 50 else user_request
        
        task_id = ai_create_task(title, category)
        return task_id
        
    except Exception as e:
        print(f"❌ 자동 작업 생성 실패: {e}")
        return ""

def auto_end_conversation():
    """대화 종료시 자동 실행"""
    try:
        print("🔄 대화 종료 - 일일 요약 업데이트 중...")
        summary_file = ai_daily_summary()
        print(f"✅ 일일 요약 업데이트 완료")
        return summary_file
        
    except Exception as e:
        print(f"❌ 종료 처리 실패: {e}")
        return ""

def quick_status():
    """빠른 상태 확인"""
    return ai_get_status()

def quick_complete(task_keyword: str):
    """키워드로 작업 완료"""
    return ai_complete_task(task_keyword)

# CLI 인터페이스
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법:")
        print("python ai_task_wrapper.py start    # 대화 시작")
        print("python ai_task_wrapper.py end      # 대화 종료") 
        print("python ai_task_wrapper.py status   # 상태 확인")
        print("python ai_task_wrapper.py create 'task_title' [category]  # 작업 생성")
        print("python ai_task_wrapper.py complete 'task_keyword'  # 작업 완료")
    else:
        command = sys.argv[1]
        
        if command == "start":
            auto_track_conversation()
        elif command == "end":
            auto_end_conversation()
        elif command == "status":
            quick_status()
        elif command == "create" and len(sys.argv) >= 3:
            title = sys.argv[2]
            category = sys.argv[3] if len(sys.argv) > 3 else "general"
            ai_create_task(title, category)
        elif command == "complete" and len(sys.argv) >= 3:
            keyword = sys.argv[2]
            quick_complete(keyword)
        else:
            print("❌ 잘못된 명령어")