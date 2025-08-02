#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI민진 수동 대화 저장 시스템 (TXT 버전)
개별 대화를 사람이 읽기 쉬운 TXT 파일로 저장

작성일: 2025년 8월 1일 19:10 (KST)
저장 형식: TXT (사용자 가독성 + AI 검색 최적화)
"""

import os
from datetime import datetime
import pytz

class Manual_Conversation_Saver_Individual_TXT:
    def __init__(self, base_folder="C:\\Users\\user\\Dropbox\\_RAG\\Chat\\Conversations"):
        self.base_folder = base_folder
        self.kst = pytz.timezone('Asia/Seoul')
        
        # 폴더가 없으면 생성
        if not os.path.exists(self.base_folder):
            os.makedirs(self.base_folder)
            print(f"[{self.get_kst_time()}] Individual_Conversations 폴더 생성: {self.base_folder}")
    
    def get_kst_time(self):
        """KST 기준 현재 시간 반환"""
        return datetime.now(self.kst).strftime('%Y-%m-%d %H:%M:%S')
    
    def get_filename_timestamp(self):
        """파일명용 타임스탬프 생성 (KST 기준)"""
        return datetime.now(self.kst).strftime('%Y%m%d_%H%M%S')
    
    def save_conversation_txt(self, conversation_data, topic_name=None):
        """
        대화 내용을 개별 TXT 파일로 저장 (사람이 읽기 쉬운 형태)
        
        Args:
            conversation_data: 저장할 대화 데이터 (dict)
            topic_name: 주제명 (선택사항)
        """
        timestamp = self.get_filename_timestamp()
        
        # 시간순 정렬을 위한 파일명 형식: YYYYMMDD_HHMMSS_주제명.txt
        if topic_name:
            safe_topic = "".join(c for c in topic_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_topic = safe_topic.replace(' ', '_')[:30]
            filename = f"{timestamp}_{safe_topic}.txt"
        else:
            filename = f"{timestamp}_대화.txt"
        
        filepath = os.path.join(self.base_folder, filename)
        
        # TXT 형태로 변환
        txt_content = self.convert_to_readable_txt(conversation_data, timestamp, topic_name)
        
        # TXT 파일로 저장
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(txt_content)
            
            print(f"[{self.get_kst_time()}] 대화 저장 완료: {filename}")
            return filepath
            
        except Exception as e:
            print(f"[{self.get_kst_time()}] 대화 저장 실패: {e}")
            return None
    
    def convert_to_readable_txt(self, conversation_data, timestamp, topic_name=None):
        """대화 데이터를 최소한의 핵심 정보만으로 변환"""
        
        # 헤더: 주제 | 시간
        header = f"{topic_name if topic_name else '대화'} | {self.get_kst_time()}\n\n"
        
        # 메시지 핵심만
        content = ""
        messages = conversation_data.get('messages', [])
        
        if conversation_data.get('conversation_type') == 'simple_text':
            content += f"👤 {conversation_data.get('user_message', '')}\n\n"
            content += f"🤖 {conversation_data.get('ai_response', '')}"
        else:
            for message in messages:
                role = message.get('role', 'unknown')
                msg_content = message.get('content', '')
                
                if role == 'user':
                    content += f"👤 {msg_content}\n\n"
                elif role == 'assistant':
                    content += f"🤖 {msg_content}\n\n"
        
        return header + content
    
    def save_text_conversation(self, user_message, ai_response, topic_name=None):
        """
        간단한 텍스트 대화를 저장하는 편의 함수
        
        Args:
            user_message: 사용자 메시지
            ai_response: AI 응답
            topic_name: 주제명 (선택사항)
        """
        conversation_data = {
            'conversation_type': 'simple_text',
            'user_message': user_message,
            'ai_response': ai_response,
            'conversation_time': self.get_kst_time()
        }
        
        return self.save_conversation_txt(conversation_data, topic_name)
    
    def save_multi_turn_conversation(self, messages, topic_name=None):
        """
        다중 턴 대화를 저장하는 함수
        
        Args:
            messages: 메시지 리스트 [{'role': 'user'/'assistant', 'content': '...', 'timestamp': '...'}, ...]
            topic_name: 주제명 (선택사항)
        """
        conversation_data = {
            'conversation_type': 'multi_turn',
            'messages': messages,
            'conversation_start': self.get_kst_time()
        }
        
        return self.save_conversation_txt(conversation_data, topic_name)
    
    def list_saved_conversations(self, limit=10):
        """저장된 대화 목록 확인 (최신순)"""
        try:
            files = []
            for filename in os.listdir(self.base_folder):
                if filename.startswith('conversation_') and filename.endswith('.txt'):
                    filepath = os.path.join(self.base_folder, filename)
                    mtime = os.path.getmtime(filepath)
                    files.append((filename, mtime))
            
            # 최신순 정렬
            files.sort(key=lambda x: x[1], reverse=True)
            
            print(f"\n=== 저장된 대화 목록 (최신 {min(limit, len(files))}개) ===")
            for i, (filename, _) in enumerate(files[:limit], 1):
                print(f"{i}. {filename}")
            
            return [f[0] for f in files[:limit]]
            
        except Exception as e:
            print(f"[{self.get_kst_time()}] 대화 목록 조회 실패: {e}")
            return []

def main():
    """테스트 및 예시 실행"""
    saver = Manual_Conversation_Saver_Individual_TXT()
    
    print("=== AI민진 수동 대화 저장 시스템 (TXT 버전) ===")
    print(f"저장 폴더: {saver.base_folder}")
    
    # 예시 1: 간단한 대화 저장
    print("\n[테스트 1] 간단한 대화 저장")
    saver.save_text_conversation(
        user_message="TXT 파일로 저장하는 시스템이 좋을까?",
        ai_response="네! TXT 파일은 메모장으로 바로 열어서 읽기 쉽고, AI도 검색/처리하기 좋습니다. 파일 하나로 통일하는 것이 효율적입니다.",
        topic_name="TXT_저장_방식_논의"
    )
    
    # 예시 2: 다중 턴 대화 저장
    print("\n[테스트 2] 다중 턴 대화 저장")
    messages = [
        {
            'role': 'user',
            'content': '하이브리드 검색 시스템이 잘 작동하나요?',
            'timestamp': saver.get_kst_time()
        },
        {
            'role': 'assistant',
            'content': '네! Google API와 Claude 검색을 50:50으로 조합해서 다양하고 최신 정보를 효율적으로 수집합니다.',
            'timestamp': saver.get_kst_time()
        },
        {
            'role': 'user',
            'content': '파일 형식도 TXT 하나로 통일되었나요?',
            'timestamp': saver.get_kst_time()
        },
        {
            'role': 'assistant',
            'content': '맞습니다! 사용자 가독성과 AI 검색 모두를 위해 TXT 하나로 통일했습니다.',
            'timestamp': saver.get_kst_time()
        }
    ]
    
    saver.save_multi_turn_conversation(messages, "하이브리드_검색_TXT_통일")
    
    # 저장된 대화 목록 출력
    saver.list_saved_conversations(5)

if __name__ == "__main__":
    main()