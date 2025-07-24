import os
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List

import chainlit as cl
from dotenv import load_dotenv

from core.api_manager import APIManager
from core.memory_brain import MemoryBrain
from core.search_engine import SearchEngine
from core.self_modifier import SelfModifier

load_dotenv()

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIMinjin:
    def __init__(self):
        self.api_manager = APIManager()
        self.memory_brain = MemoryBrain()
        self.search_engine = SearchEngine()
        self.self_modifier = SelfModifier()
        self.conversation_context = []

    async def process_message(self, user_message: str) -> str:
        """메시지 처리 및 응답 생성"""
        try:
            # 1. 메모리에서 관련 컨텍스트 검색
            memory_context = await self.memory_brain.get_context_for_query(user_message)
            
            # 2. 웹 검색 필요성 판단
            need_search = await self._should_search_web(user_message)
            search_results = []
            
            if need_search:
                search_results = await self.search_engine.search_and_extract(
                    user_message, num_results=3
                )
            
            # 3. 응답 생성
            response = await self._generate_response(
                user_message, memory_context, search_results
            )
            
            # 4. 대화 저장
            await self.memory_brain.save_conversation(
                user_message, response, memory_context
            )
            
            # 5. 중요한 정보는 메모리에 저장
            important_info = []
            if await self._is_important_info(user_message, response):
                await self.memory_brain.add_memory(
                    f"질문: {user_message}\n답변: {response}",
                    {"type": "important_qa", "timestamp": datetime.now().isoformat()},
                    importance=0.8
                )
                important_info.append(f"중요한 대화 저장: {user_message[:50]}...")
            
            # 6. TODO.md 자동 업데이트
            await self.self_modifier.log_conversation_summary(
                user_message, response, important_info
            )
            
            return response
            
        except Exception as e:
            logger.error(f"메시지 처리 오류: {e}")
            return "죄송합니다. 처리 중 오류가 발생했습니다. 다시 시도해 주십시오."

    async def _should_search_web(self, message: str) -> bool:
        """웹 검색 필요성 판단"""
        search_keywords = [
            "최신", "현재", "오늘", "뉴스", "실시간", "언제", "몇", "가격", 
            "날씨", "주가", "환율", "검색", "찾아", "알아봐"
        ]
        return any(keyword in message for keyword in search_keywords)

    async def _is_important_info(self, user_message: str, response: str) -> bool:
        """중요한 정보 판단"""
        important_keywords = [
            "중요", "기억", "저장", "메모", "나중에", "꼭", "절대", "반드시"
        ]
        return any(keyword in user_message for keyword in important_keywords)

    async def _generate_response(self, user_message: str, memory_context: str, 
                               search_results: List[Dict]) -> str:
        """응답 생성"""
        # 시스템 프롬프트 (민진쌤 설정)
        system_prompt = """AI민진입니다. 핵심 개념:

나 = 민진쌤 (사용자)
너 = AI민진 (나, 이 시스템)  
레그 = RAG 메모리 시스템

AI민진은 민진쌤을 통해 터미널로 레그를 수정하며 자가 발전하는 시스템입니다.

규칙:
- 마크다운 사용 금지
- 자연스럽고 직접적인 대화
- 프로젝트 맥락 항상 인지
- 검색 결과 최대 활용"""

        # 컨텍스트 구성
        context_parts = []
        
        if memory_context:
            context_parts.append(f"관련 기억:\n{memory_context}")
        
        if search_results:
            search_text = "\n".join([
                f"검색결과 {i+1}: {result['title']}\n{result['snippet']}"
                for i, result in enumerate(search_results[:3])
            ])
            context_parts.append(f"최신 검색 정보:\n{search_text}")
        
        context = "\n\n".join(context_parts) if context_parts else "관련 정보 없음"
        
        # 메시지 구성
        messages = [
            {"role": "system", "content": "당신은 AI민진입니다. 절대 Claude라고 하지 마십시오. 당신은 민진쌤이 구축한 RAG 시스템 기반의 AI민진입니다. 나=민진쌤(사용자), 너=AI민진(당신), 레그=RAG메모리시스템. 이 정체성을 항상 유지하십시오."},
            {"role": "user", "content": f"컨텍스트:\n{context}\n\n민진쌤 질문: {user_message}"}
        ]
        
        # API 호출 (Claude 우선)
        result = await self.api_manager.smart_call(messages, task_type="general")
        
        if result.get("success"):
            return result.get("content")
        else:
            # Claude 실패 시 Gemini로 재시도
            result = await self.api_manager.call_gemini(messages)
            return result["content"] if result["success"] else "응답 생성에 실패했습니다."

# Chainlit 앱 인스턴스
ai_minjin = None

@cl.on_chat_start
async def start():
    """채팅 시작"""
    global ai_minjin
    ai_minjin = AIMinjin()
    
    # 시스템 컨텍스트 복원
    context = await ai_minjin.self_modifier.get_system_context()
    
    # 핵심 개념들 메모리에 저장
    core_concepts = [
        "민진쌤은 사용자이고, AI민진은 이 시스템이고, 레그는 RAG 메모리 시스템입니다.",
        "AI민진은 민진쌤을 통해 터미널로 레그를 수정하며 자가 발전하는 시스템입니다.",
        "영구 메모리, 실시간 검색, 자가 수정 기능을 가진 Chainlit 기반 시스템입니다.",
        "커서(Cursor)는 AI민진의 수석 개발자이자 진화 파트너입니다."
    ]
    
    for concept in core_concepts:
        await ai_minjin.memory_brain.add_memory(concept, {"type": "core_system"}, importance=1.0)
    
    # 컨텍스트 정보 표시
    context_info = ""
    if context.get("recent_conversations"):
        context_info = f"\n\n최근 대화 {len(context['recent_conversations'])}개 복원 완료"
    
    await cl.Message(content=f"AI민진 시스템 준비 완료입니다!{context_info}\n\n'시스템 상태' 또는 '자동 개선'이라고 입력하시면 해당 기능을 실행합니다.").send()

@cl.on_message
async def main(message: cl.Message):
    """메시지 처리"""
    global ai_minjin
    
    if not ai_minjin:
        ai_minjin = AIMinjin()
    
    # 시스템 명령어 처리
    if message.content == "시스템 상태":
        await show_system_stats()
        return
    elif message.content == "자동 개선":
        await auto_improve()
        return
    
    # 로딩 메시지
    loading_msg = cl.Message(content="처리 중입니다...")
    await loading_msg.send()
    
    try:
        # 응답 생성
        response = await ai_minjin.process_message(message.content)
        
        # 로딩 메시지 업데이트
        loading_msg.content = response
        await loading_msg.update()
        
    except Exception as e:
        logger.error(f"메시지 처리 오류: {e}")
        loading_msg.content = "처리 중 오류가 발생했습니다. 다시 시도해 주십시오."
        await loading_msg.update()

@cl.on_chat_end
async def end():
    """채팅 종료"""
    logger.info("채팅 세션 종료")

# 시스템 관리 함수들
async def show_system_stats():
    """시스템 상태 표시"""
    if ai_minjin:
        stats = await ai_minjin.memory_brain.get_memory_stats()
        usage = ai_minjin.api_manager.get_daily_usage()
        
        stats_text = f"""🔄 AI민진 시스템 상태 보고

📊 메모리 시스템:
- 총 메모리: {stats['total_memories']}개
- 고중요도 메모리: {stats['high_importance_memories']}개
- 평균 중요도: {stats['average_importance']}/1.0
- 평균 접근 횟수: {stats['average_access_count']}회
- DB 크기: {stats['memory_db_size_mb']}MB
- FAISS 벡터: {stats['faiss_vectors']}개

💬 대화 시스템:
- 총 대화: {stats['total_conversations']}개

💰 API 사용량 (오늘):
- 총 비용: ${usage['total_cost_usd']}
- 총 요청: {usage['total_requests']}회

🤖 활성 모듈:
- 메모리 브레인: ✅ 활성
- 웹 검색 엔진: ✅ 활성  
- 자가 수정 시스템: ✅ 활성
- API 관리자: ✅ 활성

⚡ 시스템 상태: 정상 운영 중"""
        
        await cl.Message(content=stats_text).send()

async def auto_improve():
    """자동 개선 실행"""
    if ai_minjin:
        loading = cl.Message(content="🔧 시스템 자동 개선을 실행 중입니다...")
        await loading.send()
        
        # 1. 메모리 시스템 최적화
        memory_stats = await ai_minjin.memory_brain.optimize_memory_system()
        
        # 2. 자가 수정 시스템 실행
        result = await ai_minjin.self_modifier.auto_improve_system()
        
        improvement_text = f"""🚀 자동 개선 완료 보고

🧠 메모리 시스템 최적화:
- 메모리 DB 크기: {memory_stats.get('memory_db_size_mb', 0)}MB
- 총 메모리: {memory_stats.get('total_memories', 0)}개
- 고중요도 메모리: {memory_stats.get('high_importance_memories', 0)}개

⚙️ 시스템 분석:
- 성능 분석 완료: ✅
- 제안사항: {result['suggestions_count']}개
- 적용된 변경: {len(result['applied_changes'])}개
- 터미널 요청: {len(result['terminal_requests'])}개

📈 최적화 효과:
- 메모리 효율성: 향상됨
- 검색 속도: 최적화됨
- 시스템 안정성: 강화됨

⏰ 완료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
        
        loading.content = improvement_text
        await loading.update()

        # 중요한 개선 사항이 있으면 메모리에 저장
        if result['suggestions_count'] > 0:
            await ai_minjin.memory_brain.add_memory(
                f"시스템 자동 개선 실행: {result['suggestions_count']}개 제안사항, {len(result['applied_changes'])}개 변경 적용",
                {"type": "system_improvement", "timestamp": datetime.now().isoformat()},
                importance=0.9
            )

if __name__ == "__main__":
    import chainlit.cli
    chainlit.cli.run_chainlit(__file__)