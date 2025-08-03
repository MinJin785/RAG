#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI민진 자동 대화 저장 시스템
모든 대화를 실시간으로 자동 저장

작성일: 2025년 8월 4일
"""

import os
import time
import threading
from datetime import datetime
import pytz
from conversation_saver import Manual_Conversation_Saver_Individual_TXT

class Auto_Conversation_Monitor:
    def __init__(self):
        self.saver = Manual_Conversation_Saver_Individual_TXT()
        self.kst = pytz.timezone('Asia/Seoul')
        self.last_save_time = time.time()
        self.conversation_buffer = []
        self.is_running = False
        
    def add_conversation(self, user_msg, ai_response, topic=None):
        """대화를 버퍼에 추가하고 즉시 저장"""
        timestamp = datetime.now(self.kst).strftime('%Y-%m-%d %H:%M:%S')
        
        # 즉시 저장
        if topic is None:
            topic = f"자동저장_{timestamp.replace(':', '').replace('-', '').replace(' ', '_')}"
        
        result = self.saver.save_text_conversation(user_msg, ai_response, topic)
        print(f"[{timestamp}] 자동 저장 완료: {result}")
        
        return result
    
    def start_monitoring(self):
        """모니터링 시작"""
        self.is_running = True
        print(f"[{datetime.now(self.kst).strftime('%Y-%m-%d %H:%M:%S')}] 자동 대화 저장 시스템 시작")
    
    def stop_monitoring(self):
        """모니터링 중지"""
        self.is_running = False
        print(f"[{datetime.now(self.kst).strftime('%Y-%m-%d %H:%M:%S')}] 자동 대화 저장 시스템 중지")

# 전역 인스턴스
auto_saver = Auto_Conversation_Monitor()

def save_current_conversation(user_msg, ai_response, topic=None):
    """현재 대화를 자동 저장하는 함수"""
    return auto_saver.add_conversation(user_msg, ai_response, topic)

def start_auto_save():
    """자동 저장 시작"""
    auto_saver.start_monitoring()

def stop_auto_save():
    """자동 저장 중지"""
    auto_saver.stop_monitoring()

if __name__ == "__main__":
    # 테스트
    start_auto_save()
    
    # 테스트 대화 저장
    save_current_conversation(
        "자동 저장 시스템 테스트",
        "자동 저장 시스템이 정상 작동합니다",
        "자동저장시스템_테스트"
    )
    
    print("자동 저장 시스템 테스트 완료")