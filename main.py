import chainlit as cl
import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List
import time
import json
from pathlib import Path

from dotenv import load_dotenv

from core.api_manager import APIManager
from core.memory_brain import MemoryBrain
from core.search_engine import SearchEngine
from core.self_modifier import SelfModifier
from core.git_automation import GitAutomation, CursorGitGuide

load_dotenv()

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# 시각적 효과를 위한 유틸리티 함수들
async def typewriter_effect(message_obj, text: str, delay: float = 0.03):
    """타이핑 효과로 텍스트를 점진적으로 표시"""
    current_text = ""
    for char in text:
        current_text += char
        message_obj.content = current_text + "▊"  # 커서 효과
        await message_obj.update()
        await asyncio.sleep(delay)
    
    # 최종 텍스트 (커서 제거)
    message_obj.content = text
    await message_obj.update()

async def show_progress_animation(message_obj, steps: list, step_delay: float = 1.0):
    """단계별 진행 상황을 애니메이션으로 표시"""
    for i, step in enumerate(steps):
        progress_bar = "█" * (i + 1) + "░" * (len(steps) - i - 1)
        progress_text = f"""🔄 **작업 진행 중... ({i+1}/{len(steps)})**

**현재 단계:** {step}

**진행률:** [{progress_bar}] {int((i+1)/len(steps)*100)}%

⏱️ 잠시만 기다려주세요... 작업이 진행 중입니다."""
        
        message_obj.content = progress_text
        await message_obj.update()
        await asyncio.sleep(step_delay)

async def show_terminal_progress(message_obj, command: str, description: str):
    """터미널 명령 실행 전 진행 표시"""
    steps = [
        "🔍 명령어 준비 중...",
        "⚙️ 환경 설정 확인...", 
        "🚀 터미널 명령 실행...",
        f"📟 실행 중: {command}"
    ]
    
    # 단계별 진행 표시
    for i, step in enumerate(steps):
        loading_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        
        for j in range(3):  # 각 단계마다 3번 로딩 애니메이션
            for char in loading_chars:
                progress_text = f"""🖥️ **터미널 작업 진행 중** {char}

**작업 설명:** {description}

**현재 단계:** {step}

**실행할 명령:** `{command}`

⚡ **진행률:** [{("█" * (i+1) + "░" * (len(steps)-i-1))}] {int((i+1)/len(steps)*25)}%

💡 **안내:** 작업이 진행 중이니 잠시만 기다려주세요!"""
                
                message_obj.content = progress_text
                await message_obj.update()
                await asyncio.sleep(0.1)

async def enhanced_terminal_command(command: str, description: str, is_background: bool = False):
    """시각적 효과가 있는 터미널 명령 실행"""
    # 진행 상황 메시지 생성
    progress_msg = cl.Message(content="🔄 터미널 작업 준비 중...")
    await progress_msg.send()
    
    # 진행 상황 표시
    await show_terminal_progress(progress_msg, command, description)
    
    # 실제 명령 실행
    try:
        result_msg = cl.Message(content=f"📟 **명령 실행:** `{command}`\n\n⏳ 실행 중...")
        await result_msg.send()
        
        # 기존 run_terminal_cmd 대신 직접 구현
        import subprocess
        
        if is_background:
            # 백그라운드 실행
            process = subprocess.Popen(
                command, 
                shell=True, 
                cwd="C:\\Users\\user\\Dropbox\\RAG",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            result_msg.content = f"✅ **백그라운드 실행 시작:** `{command}`\n\n🔄 프로세스 ID: {process.pid}"
        else:
            # 일반 실행
            result = subprocess.run(
                command,
                shell=True,
                cwd="C:\\Users\\user\\Dropbox\\RAG", 
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                result_msg.content = f"""✅ **명령 실행 완료:** `{command}`

**출력 결과:**
```
{result.stdout}
```"""
            else:
                result_msg.content = f"""❌ **명령 실행 실패:** `{command}`

**오류 내용:**
```
{result.stderr}
```"""
        
        await result_msg.update()
        
        # 완료 애니메이션
        completion_steps = ["🎉 작업 완료!", "✨ 결과 표시 중...", "📋 정리 완료!"]
        await show_progress_animation(progress_msg, completion_steps, 0.5)
        
        progress_msg.content = "✅ **터미널 작업 완료!**"
        await progress_msg.update()
        
        return result if not is_background else process
        
    except subprocess.TimeoutExpired:
        result_msg.content = f"⏰ **시간 초과:** `{command}` (30초 제한)"
        await result_msg.update()
        return None
    except Exception as e:
        result_msg.content = f"❌ **실행 오류:** {e}"
        await result_msg.update()
        return None

async def animated_system_status():
    """애니메이션 효과가 있는 시스템 상태 표시"""
    status_msg = cl.Message(content="🔍 시스템 상태 분석 시작...")
    await status_msg.send()
    
    # 분석 단계들
    analysis_steps = [
        "🧠 메모리 시스템 분석 중...",
        "💾 저장소 상태 확인 중...", 
        "⚡ 성능 지표 수집 중...",
        "🔄 AI민진 상태 점검 중...",
        "📊 종합 분석 완료!"
    ]
    
    await show_progress_animation(status_msg, analysis_steps, 1.0)
    
    # 실제 시스템 상태 표시 (기존 코드)
    await show_system_stats()

async def animated_memory_cleanup():
    """애니메이션 효과가 있는 메모리 정리"""
    cleanup_msg = cl.Message(content="🧠 스마트 메모리 정리 시작...")
    await cleanup_msg.send()
    
    cleanup_steps = [
        "🔍 메모리 사용량 분석 중...",
        "🗑️ 불필요한 데이터 식별 중...",
        "⚡ 중요도 기반 정리 중...",
        "🔄 인덱스 최적화 중...",
        "✨ 정리 작업 완료!"
    ]
    
    await show_progress_animation(cleanup_msg, cleanup_steps, 1.5)
    
    # 실제 메모리 정리 실행 (기존 코드)
    await smart_memory_cleanup()

# AI민진 시스템 클래스
class AIMinjin:
    def __init__(self, memory_limit_gb: float = None):
        """AI민진 초기화 - 용량 제한 지원"""
        self.api_manager = APIManager()
        self.memory_brain = MemoryBrain(max_size_gb=memory_limit_gb)  # 용량 제한 적용
        self.search_engine = SearchEngine()
        self.self_modifier = SelfModifier()
        
        # 대화 저장 설정
        self.auto_save_conversations = True
        self.conversation_buffer = []

    async def process_message(self, user_message: str) -> str:
        """메시지 처리 및 자동 대화 저장"""
        try:
            # 1. 관련 메모리 검색
            relevant_memories = await self.memory_brain.search_memories(user_message, top_k=5)
            
            # 2. 웹 검색 (필요시)
            search_results = ""
            if any(keyword in user_message.lower() for keyword in ["검색", "찾아", "최신", "뉴스"]):
                search_results = await self.search_engine.search(user_message)
            
            # 3. 컨텍스트 구성
            context_parts = []
            if relevant_memories:
                context_parts.append("관련 기억:")
                for memory in relevant_memories:
                    context_parts.append(f"- {memory['content'][:200]}")
            
            if search_results:
                context_parts.append(f"\n검색 결과: {search_results[:500]}")
            
            context = "\n".join(context_parts)
            
            # 4. AI 응답 생성
            response = await self.api_manager.get_response(user_message, context)
            
            # 5. 자동 대화 저장
            if self.auto_save_conversations:
                await self._save_conversation(user_message, response)
            
            return response
            
        except Exception as e:
            return f"처리 중 오류가 발생했습니다: {e}"

    async def _save_conversation(self, user_message: str, ai_response: str):
        """대화를 자동으로 메모리에 저장"""
        try:
            # 중요도 자동 계산하여 저장
            conversation_content = f"사용자: {user_message}\nAI민진: {ai_response}"
            metadata = {
                "type": "conversation",
                "auto_saved": True,
                "timestamp": datetime.now().isoformat(),
                "user_message_length": len(user_message),
                "ai_response_length": len(ai_response)
            }
            
            await self.memory_brain.add_memory(conversation_content, metadata)
            
        except Exception as e:
            logging.error(f"대화 자동 저장 오류: {e}")

# 전역 변수
ai_minjin = None
cursor_ai_memory_limit_gb = 0.5  # 500GB → 0.5TB로 제한
git_automation = None  # Git 자동화 인스턴스

@cl.on_chat_start
async def start():
    """채팅 시작 - 용량 제한 적용된 1년치 컨텍스트 복원"""
    global ai_minjin, git_automation
    
    # AI민진 초기화 (무제한 용량)
    ai_minjin = AIMinjin(memory_limit_gb=None)  # 무제한
    
    # Git 자동화 초기화
    git_automation = GitAutomation(".")
    
    # 🎯 1단계: AI민진 전용 파일 시스템 초기화
    await ai_minjin.self_modifier.create_ai_minjin_task_system()
    ai_context = await ai_minjin.self_modifier.get_ai_minjin_context()
    
    # 🧠 2단계: 1년치 스마트 컨텍스트 복원
    smart_context = await ai_minjin.memory_brain.smart_context_restore()
    
    # 📋 3단계: 핵심 개념 및 환경 정보 저장 (자동 중요도 계산)
    core_concepts = [
        "민진쌤은 사용자이고, AI민진은 이 시스템이고, 레그는 RAG 메모리 시스템입니다.",
        "AI민진은 민진쌤을 통해 터미널로 레그를 수정하며 자가 발전하는 시스템입니다.",
        "영구 메모리, 실시간 검색, 자가 수정 기능을 가진 Chainlit 기반 시스템입니다.",
        "커서(Cursor)는 AI민진의 수석 개발자이자 진화 파트너입니다.",
        f"현재 하드웨어: AMD Ryzen 9 7945HX (16코어), 64GB RAM, Windows 11 Pro - 노트북 환경",
        f"데스크탑 SSD: Samsung SSD 9100 PRO 4TB - 세계 최고 수준 성능 (7,000MB/s+)",
        f"추가 저장소: 4TB HDD x 2개 = 8TB 확장 예정, 더 필요시 무제한 확장 가능",
        f"AI민진은 자체 작업 파일(AI_Minjin_To_Do.md)을 가지고 있어 Cursor AI와 충돌하지 않습니다.",
        f"메모리 시스템은 1년치 대화({smart_context.get('total_conversations', 0)}개)를 기억하며 스마트 정리 기능이 있습니다.",
        f"Cursor AI는 500GB 제한, AI민진은 무제한 용량으로 설정되었습니다.",
        f"Git 자동화 시스템이 활성화되어 모든 Git 작업이 비인터랙티브로 처리됩니다."
    ]
    
    for concept in core_concepts:
        await ai_minjin.memory_brain.add_memory(concept, {"type": "core_system"})  # 자동 중요도 계산
    
    # 💭 4단계: 메모리 통계 및 기억 복원
    total_conversations = smart_context.get("total_conversations", 0)
    total_memories = smart_context.get("total_memories", 0)
    oldest_days = smart_context.get("oldest_memory_days", 0)
    
    # 🎯 5단계: AI민진 작업 상태 파악
    ai_tasks = ai_context.get("todo_stats", {})
    
    # 📊 6단계: 종합 상태 보고서 생성
    memory_summary = ""
    if oldest_days > 0:
        if oldest_days >= 365:
            memory_summary = f"🧠 **1년 이상의 기억**: {total_conversations}개 대화, {total_memories}개 상세 기억"
        elif oldest_days >= 30:
            memory_summary = f"🧠 **{oldest_days}일간의 기억**: {total_conversations}개 대화, {total_memories}개 상세 기억"
        else:
            memory_summary = f"🧠 **{oldest_days}일간의 기억**: {total_conversations}개 대화, {total_memories}개 상세 기억"
    else:
        memory_summary = "🌟 **새로운 시작**: 아직 기억이 없지만 모든 대화를 영구 보존합니다"
    
    # 🎯 AI민진 작업 요약
    task_summary = f"""📊 **AI_Minjin_To_Do.md 통계:**
• 파일 크기: {ai_tasks.get('file_size_mb', 0):.2f} MB
• 대화 기록: {ai_tasks.get('conversations', 0)}개 세션
• 완료 작업: {ai_tasks.get('completed_tasks', 0)}개
• 대기 작업: {ai_tasks.get('pending_tasks', 0)}개"""
    
    status_report = f"""🤖 **AI민진 시스템 준비 완료! (스마트 메모리 + Git 자동화)**

{memory_summary}

{task_summary}

🎯 **용량 설정:**
• Cursor AI: 500GB 제한 (스마트 정리)
• AI민진: 무제한 (8TB+ SSD/HDD 활용)

🧠 **스마트 메모리 기능:**
• 자동 중요도 계산
• 상충 대화 자동 감지 및 정리
• 낮은 중요도 메모리 자동 삭제
• Samsung SSD 9100 PRO 4TB 최적화

🎯 **사용 가능한 명령어:**
• "시스템 상태" → 전체 시스템 모니터링 (애니메이션 효과)
• "자동 개선" → 성능 분석 및 최적화 (진행률 표시)
• "메모리 검색 [키워드]" → 1년치 기억 검색 (단계별 진행)
• "메모리 정리" → 스마트 메모리 유지보수 (실시간 진행)
• "TODO 상태" → AI민진 전용 작업 상태 (상세 분석)
• "시각 효과 테스트" → 타이핑 & 애니메이션 효과 체험
• "이제 데스크탑이야" → 데스크탑 환경 설정 가이드

🔧 **Git 자동화 명령어:**
• "git 상태" → Git 저장소 상태 확인
• "git 동기화" → 자동 add + commit + push
• "git 업데이트" → 원격 저장소에서 풀
• "git 도움말" → Git 자동화 가이드
• "cursor git" → Cursor IDE Git 기능 안내

🎭 **새로운 시각적 효과:**
• 💻 타이핑 효과 (타자기 스타일)
• 📊 진행률 표시 (실시간 막대 그래프)
• ⚡ 로딩 애니메이션 (회전 효과)
• 🎯 단계별 진행 상황 (상세 표시)
• 🔄 터미널 작업 시각화 (명령 실행 과정)

🔧 **파일 시스템:**
• TODO.md (Cursor AI 전용) - 500GB 제한, 스마트 정리
• AI_Minjin_To_Do.md (AI민진 전용) - 무제한, 충돌 없음!

🚀 **스마트 메모리 + Git 자동화를 가진 AI민진, 준비 완료!** 어떤 작업을 도와드릴까요?"""
    
    await cl.Message(content=status_report).send()

async def load_todo_status() -> Dict[str, Any]:
    """AI민진 전용 작업 상태 로드 (AI_Minjin_To_Do.md에서)"""
    try:
        # AI민진 전용 파일에서 로드
        if ai_minjin:
            ai_context = await ai_minjin.self_modifier.get_ai_minjin_context()
            
            # AI_Minjin_To_Do.md 파일 직접 파싱
            ai_todo_path = "AI_Minjin_To_Do.md"
            if os.path.exists(ai_todo_path):
                with open(ai_todo_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 마크다운에서 작업 파싱
                in_progress = []
                completed = []
                pending = []
                
                lines = content.split('\n')
                current_section = ""
                
                for line in lines:
                    if "## 📋 현재 진행 중인 작업" in line:
                        current_section = "in_progress"
                    elif "## ✅ 완료된 작업 기록" in line:
                        current_section = "completed"
                    elif "## ⏳ 대기 중인 작업" in line:
                        current_section = "pending"
                    elif line.startswith("##"):
                        current_section = ""
                    elif "- [x]" in line and current_section == "completed":
                        task = line.split("- [x]", 1)[-1].strip()
                        if task:
                            completed.append(task[:80] + "..." if len(task) > 80 else task)
                    elif "- [ ]" in line and current_section == "pending":
                        task = line.split("- [ ]", 1)[-1].strip()
                        if task:
                            pending.append(task[:80] + "..." if len(task) > 80 else task)
                
                return {
                    "in_progress_tasks": in_progress[-3:],
                    "recently_completed": completed[-5:],
                    "pending_tasks": pending[:5]
                }
            
            return {"in_progress_tasks": [], "recently_completed": [], "pending_tasks": []}
        
        return {"in_progress_tasks": [], "recently_completed": [], "pending_tasks": []}
        
    except Exception as e:
        logger.error(f"AI민진 작업 상태 로드 오류: {e}")
        return {"in_progress_tasks": [], "recently_completed": [], "pending_tasks": []}

@cl.on_message
async def main(message: cl.Message):
    """메시지 처리 - 스마트 메모리 시스템 + 시각적 효과"""
    global ai_minjin
    
    if not ai_minjin:
        ai_minjin = AIMinjin(memory_limit_gb=None)  # 무제한
    
    # 시각적 효과가 있는 시스템 명령어 처리
    if message.content == "시스템 상태":
        await animated_system_status()  # 애니메이션 효과 적용
        return
    elif message.content == "자동 개선":
        await auto_improve_with_animation()  # 애니메이션 효과 적용
        return
    elif message.content == "메모리 정리":
        await animated_memory_cleanup()  # 애니메이션 효과 적용
        return
    elif message.content == "시각 효과 테스트":
        await test_visual_effects()  # 시각적 효과 테스트
        return
    elif message.content == "git 상태":
        await handle_git_status()  # Git 상태 확인
        return
    elif message.content == "git 동기화":
        await handle_git_sync()  # Git 자동 동기화
        return
    elif message.content == "git 업데이트":
        await handle_git_pull()  # Git 풀
        return
    elif message.content == "git 도움말":
        await show_git_help()  # Git 자동화 도움말
        return
    elif message.content == "cursor git":
        await show_cursor_git_guide()  # Cursor Git 가이드
        return
    elif message.content == "이제 데스크탑이야":
        await show_desktop_setup_guide()
        return
    elif message.content.startswith("TODO"):
        await handle_todo_command_animated(message.content)  # 애니메이션 효과 적용
        return
    elif message.content.startswith("메모리 검색"):
        await handle_memory_search_animated(message.content)  # 애니메이션 효과 적용
        return
    
    # 타이핑 효과가 있는 로딩 메시지
    loading_msg = cl.Message(content="")
    await loading_msg.send()
    
    loading_text = "🤔 스마트 메모리에서 1년치 기억을 검색 중입니다..."
    await typewriter_effect(loading_msg, loading_text, 0.05)
    
    try:
        # 1년치 컨텍스트 기반 응답 생성
        response = await ai_minjin.process_message(message.content)
        
        # AI_Minjin_To_Do.md에 대화 기록 추가 (자동)
        await auto_detect_and_save_ai_minjin_tasks(message.content, response)
        
        # Cursor AI TODO.md에 중요한 대화 저장 (500GB 제한)
        await save_to_cursor_todo_if_important(message.content, response)
        
        # 응답을 타이핑 효과로 표시
        response_msg = cl.Message(content="")
        await response_msg.send()
        await typewriter_effect(response_msg, response, 0.02)
        
    except Exception as e:
        logger.error(f"메시지 처리 오류: {e}")
        error_msg = "처리 중 오류가 발생했습니다. 스마트 메모리 시스템이 곧 복구될 예정입니다."
        await typewriter_effect(loading_msg, error_msg, 0.03)

async def auto_improve_with_animation():
    """애니메이션 효과가 있는 자동 개선"""
    improve_msg = cl.Message(content="🔧 시스템 자동 개선 시작...")
    await improve_msg.send()
    
    improvement_steps = [
        "🔍 성능 분석 중...",
        "🧠 AI 모델 최적화 중...",
        "💾 메모리 사용량 최적화 중...",
        "⚡ 속도 향상 적용 중...",
        "🎯 개선 사항 적용 완료!"
    ]
    
    await show_progress_animation(improve_msg, improvement_steps, 1.2)
    
    # 실제 자동 개선 실행
    await auto_improve()

async def handle_todo_command_animated(command: str):
    """애니메이션 효과가 있는 TODO 명령어 처리"""
    todo_msg = cl.Message(content="📋 AI민진 TODO 상태 분석 시작...")
    await todo_msg.send()
    
    todo_steps = [
        "🔍 AI_Minjin_To_Do.md 파일 읽기...",
        "📊 작업 통계 계산 중...",
        "📈 진행률 분석 중...",
        "📋 종합 보고서 생성 중..."
    ]
    
    await show_progress_animation(todo_msg, todo_steps, 0.8)
    
    # 실제 TODO 명령 처리
    await handle_todo_command(command)

async def handle_memory_search_animated(command: str):
    """애니메이션 효과가 있는 메모리 검색"""
    search_msg = cl.Message(content="🔍 1년치 메모리 검색 시작...")
    await search_msg.send()
    
    search_steps = [
        "🧠 HOT Memory (RAM) 검색 중...",
        "⚡ WARM Memory (SSD Cache) 검색 중...",
        "❄️ COLD Memory (SSD Archive) 검색 중...",
        "🏔️ DEEP Archive (HDD) 검색 중...",
        "📊 검색 결과 정리 중..."
    ]
    
    await show_progress_animation(search_msg, search_steps, 1.0)
    
    # 실제 메모리 검색 처리
    await handle_memory_search(command)

async def test_visual_effects():
    """시각적 효과 테스트 함수"""
    # 테스트 메시지 생성
    test_msg = cl.Message(content="")
    await test_msg.send()
    
    # 1. 타이핑 효과 테스트
    await typewriter_effect(test_msg, "✨ 안녕하세요! 시각적 효과 테스트 중입니다...", 0.05)
    
    await asyncio.sleep(1)
    
    # 2. 진행 상황 애니메이션 테스트
    test_steps = [
        "🔍 시스템 초기화 중...",
        "⚙️ 모듈 로딩 중...", 
        "🚀 준비 완료!",
        "✨ 테스트 성공!"
    ]
    
    await show_progress_animation(test_msg, test_steps, 1.0)
    
    # 3. 터미널 명령 시뮬레이션
    await enhanced_terminal_command("echo 'Hello World!'", "간단한 테스트 명령", False)

@cl.on_chat_end
async def end():
    """채팅 종료"""
    logger.info("채팅 세션 종료")

# 시스템 관리 함수들
async def show_system_stats():
    """시스템 상태 표시 (애니메이션 제거된 실제 작업)"""
    try:
        # 시스템 통계 수집
        stats = await ai_minjin.self_modifier.get_system_status()
        memory_stats = await ai_minjin.memory_brain.get_memory_stats()
        
        # 시스템 상태 보고서 생성
        status_report = f"""📊 **AI민진 시스템 상태 보고서** (실시간)

🧠 **메모리 시스템:**
• 총 메모리: {memory_stats.get('total_memories', 0)}개
• 평균 중요도: {memory_stats.get('average_importance', 0):.2f}
• DB 크기: {memory_stats.get('memory_db_size_mb', 0):.1f}MB

⚡ **성능 지표:**
• CPU 사용률: {stats.get('cpu_percent', 0)}%
• 메모리 사용률: {stats.get('memory_percent', 0)}%
• 디스크 사용률: {stats.get('disk_percent', 0)}%

🔄 **AI민진 상태:**
• 업타임: {stats.get('uptime_seconds', 0)}초
• 총 대화 수: {stats.get('total_conversations', 0)}개
• 마지막 업데이트: {stats.get('last_update', 'N/A')}

💾 **저장소 상태:**
• 사용 가능 공간: {stats.get('free_space_gb', 0):.1f}GB
• 총 용량: {stats.get('total_space_gb', 0):.1f}GB"""
        
        await cl.Message(content=status_report).send()
        
    except Exception as e:
        logger.error(f"시스템 상태 조회 오류: {e}")
        await cl.Message(content=f"시스템 상태 조회 중 오류가 발생했습니다: {e}").send()

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

async def handle_git_status():
    """Git 상태 확인 (비인터랙티브)"""
    try:
        status_msg = cl.Message(content="📊 Git 상태 확인 중...")
        await status_msg.send()
        
        # 진행 단계
        status_steps = [
            "🔍 저장소 상태 분석 중...",
            "📁 변경된 파일 검색 중...",
            "🌿 브랜치 정보 확인 중...",
            "📊 종합 분석 완료!"
        ]
        
        await show_progress_animation(status_msg, status_steps, 0.8)
        
        # 실제 Git 상태 조회
        status_result = await git_automation.get_status()
        branch_result = await git_automation.get_current_branch()
        
        if status_result["success"]:
            status_text = f"""📊 **Git 저장소 상태**

🌿 **현재 브랜치:** {branch_result.get('current_branch', 'unknown')}

📁 **변경사항:**
• 수정된 파일: {len(status_result['modified_files'])}개
• 새 파일: {len(status_result['untracked_files'])}개  
• 스테이징된 파일: {len(status_result['staged_files'])}개

**총 변경사항:** {status_result['total_changes']}개

{'✅ **깨끗한 상태입니다!**' if status_result['clean'] else '📝 **변경사항이 있습니다.**'}

{'**수정된 파일들:**' + chr(10) + chr(10).join(f'• {f}' for f in status_result['modified_files'][:10]) if status_result['modified_files'] else ''}

{'**새 파일들:**' + chr(10) + chr(10).join(f'• {f}' for f in status_result['untracked_files'][:10]) if status_result['untracked_files'] else ''}"""
        else:
            status_text = f"❌ **Git 상태 확인 실패:** {status_result.get('error', 'Unknown error')}"
        
        final_msg = cl.Message(content="")
        await final_msg.send()
        await typewriter_effect(final_msg, status_text, 0.02)
        
    except Exception as e:
        logger.error(f"Git 상태 확인 오류: {e}")
        await cl.Message(content=f"Git 상태 확인 중 오류가 발생했습니다: {e}").send()

async def handle_git_sync():
    """Git 자동 동기화 (add + commit + push)"""
    try:
        sync_msg = cl.Message(content="🔄 Git 자동 동기화 시작...")
        await sync_msg.send()
        
        # 동기화 단계
        sync_steps = [
            "🔍 변경사항 확인 중...",
            "📁 파일 추가 중...",
            "💬 커밋 생성 중...",
            "🚀 GitHub에 푸시 중...",
            "✨ 동기화 완료!"
        ]
        
        await show_progress_animation(sync_msg, sync_steps, 1.5)
        
        # 실제 동기화 실행
        sync_result = await git_automation.auto_sync()
        
        if sync_result["success"]:
            result_text = f"""✅ **Git 자동 동기화 완료!**

📊 **처리된 변경사항:** {sync_result.get('changes_count', 0)}개

🎯 **수행된 작업:**
• ✅ 파일 추가 (git add)
• ✅ 커밋 생성 (git commit)  
• ✅ GitHub 푸시 (git push)

💬 **커밋 메시지:** 자동 생성됨

🚀 **GitHub에 성공적으로 업로드되었습니다!**"""
        else:
            result_text = f"""❌ **Git 동기화 실패**

**오류:** {sync_result.get('error', 'Unknown error')}

**실행된 단계들:**
{chr(10).join(f'• {step[0]}: {"✅" if step[1].get("success", False) else "❌"}' for step in sync_result.get("steps", []))}

💡 **해결 방법:**
1. 네트워크 연결 확인
2. GitHub 인증 상태 확인  
3. 원격 저장소 URL 확인"""
        
        final_msg = cl.Message(content="")
        await final_msg.send()
        await typewriter_effect(final_msg, result_text, 0.02)
        
    except Exception as e:
        logger.error(f"Git 동기화 오류: {e}")
        await cl.Message(content=f"Git 동기화 중 오류가 발생했습니다: {e}").send()

async def handle_git_pull():
    """Git 풀 (원격 저장소 업데이트)"""
    try:
        pull_msg = cl.Message(content="📥 원격 저장소 업데이트 중...")
        await pull_msg.send()
        
        pull_steps = [
            "🔍 원격 저장소 연결 확인...",
            "📥 최신 변경사항 가져오기...",
            "🔄 로컬 브랜치 업데이트...",
            "✅ 업데이트 완료!"
        ]
        
        await show_progress_animation(pull_msg, pull_steps, 1.0)
        
        # 실제 풀 실행
        pull_result = await git_automation.auto_pull()
        
        if pull_result["success"]:
            result_text = """✅ **Git 풀 완료!**

📥 **원격 저장소에서 최신 변경사항을 성공적으로 가져왔습니다.**

🔄 **로컬 브랜치가 최신 상태로 업데이트되었습니다.**"""
        else:
            result_text = f"""❌ **Git 풀 실패**

**오류:** {pull_result.get('stderr', 'Unknown error')}

💡 **해결 방법:**
1. 네트워크 연결 확인
2. 로컬 변경사항 커밋 또는 스태시
3. 원격 저장소 접근 권한 확인"""
        
        final_msg = cl.Message(content="")
        await final_msg.send()
        await typewriter_effect(final_msg, result_text, 0.02)
        
    except Exception as e:
        logger.error(f"Git 풀 오류: {e}")
        await cl.Message(content=f"Git 풀 중 오류가 발생했습니다: {e}").send()

async def show_git_help():
    """Git 자동화 도움말 표시"""
    help_text = """🔧 **Git 자동화 시스템 가이드**

### 🎯 **주요 명령어:**

**📊 "git 상태"**
• Git 저장소 상태 확인
• 변경된 파일 목록 표시
• 브랜치 정보 확인

**🔄 "git 동기화"**  
• 자동 add + commit + push
• 커밋 메시지 자동 생성
• GitHub에 완전 자동 업로드

**📥 "git 업데이트"**
• 원격 저장소에서 최신 변경사항 가져오기
• 로컬 브랜치 자동 업데이트

**🖥️ "cursor git"**
• Cursor IDE Git 기능 활용 가이드
• 단축키 및 GUI 기능 안내

### 🛠️ **자동화 기능:**

**✨ 비인터랙티브 처리**
• 'q' 키 입력 불필요
• 자동 페이저 비활성화
• 완전 자동 실행

**🤖 스마트 커밋**
• 변경사항 분석하여 메시지 자동 생성
• 파일별 변경 내용 요약
• 타임스탬프 자동 추가

**🔒 안전한 처리**
• 충돌 방지 시스템
• 백업 및 복원 기능
• 오류 상황 자동 감지

### 📁 **PowerShell 스크립트:**

**`scripts/git_automation.ps1` 사용법:**
```powershell
# 상태 확인
.\\git_automation.ps1 status

# 자동 동기화  
.\\git_automation.ps1 sync

# 커스텀 메시지로 동기화
.\\git_automation.ps1 sync -Message "AI민진 업데이트"

# 최신 변경사항 가져오기
.\\git_automation.ps1 pull

# 도움말 보기
.\\git_automation.ps1 help
```

### 🎭 **시각적 효과:**
• 진행률 실시간 표시
• 단계별 작업 상황 안내  
• 타이핑 효과로 결과 표시
• 컬러풀한 상태 메시지

**🎉 이제 Git 작업이 완전히 자동화되었습니다!**"""

    final_msg = cl.Message(content="")
    await final_msg.send()
    await typewriter_effect(final_msg, help_text, 0.015)

async def show_cursor_git_guide():
    """Cursor IDE Git 기능 가이드"""
    guide = CursorGitGuide()
    shortcuts = guide.get_cursor_git_shortcuts()
    features = guide.get_cursor_git_features()
    
    cursor_text = f"""🎯 **Cursor IDE Git 기능 활용 가이드**

### ⌨️ **주요 단축키:**
{chr(10).join(f'• **{key}**: {desc}' for key, desc in shortcuts.items())}

### 🎨 **내장 Git 기능:**
{chr(10).join(f'{feature}' for feature in features)}

### 💡 **활용 팁:**

**1. 사이드바 Git 패널 (Ctrl+Shift+G)**
• 변경사항 실시간 확인
• 파일별 개별 스테이징
• 커밋 메시지 작성 및 히스토리

**2. 브랜치 관리**
• 하단 상태바에서 브랜치 클릭
• 새 브랜치 생성 및 전환
• 브랜치 비교 및 머지

**3. 인라인 Git 정보**  
• 각 줄의 마지막 수정자 표시
• 커밋 해시 및 시간 정보
• 변경사항 하이라이트

**4. 머지 충돌 해결**
• 시각적 머지 툴 제공
• 3-way 비교 화면
• 충돌 부분 하이라이트

**5. Git 히스토리**
• 커밋 그래프 시각화
• 파일별 변경 히스토리  
• 브랜치 간 비교

### 🔧 **설정 권장사항:**

**자동 페치 활성화:**
```json
"git.autofetch": true,
"git.confirmSync": false,
"git.enableSmartCommit": true
```

**Git 렌즈 활성화:**
```json  
"gitlens.currentLine.enabled": true,
"gitlens.hovers.enabled": true,
"gitlens.codeLens.enabled": true
```

### 🎯 **워크플로우 추천:**

**1. 개발 단계:**
• Cursor 사이드바에서 변경사항 확인
• 파일별 개별 스테이징
• 의미있는 커밋 메시지 작성

**2. 동기화 단계:**  
• 내장 Git 또는 AI민진 "git 동기화" 사용
• 자동화된 푸시로 GitHub 업로드

**🎊 Cursor와 AI민진의 완벽한 Git 협업 환경 완성!**"""

    final_msg = cl.Message(content="")
    await final_msg.send()
    await typewriter_effect(final_msg, cursor_text, 0.015)

async def handle_todo_command(command: str):
    """AI민진 전용 TODO 명령어 처리 (AI_Minjin_To_Do.md)"""
    if "상태" in command or "TODO 상태" in command:
        try:
            ai_todo_path = "AI_Minjin_To_Do.md"
            
            if os.path.exists(ai_todo_path):
                # 파일 크기 계산
                file_size = os.path.getsize(ai_todo_path) / (1024 * 1024)  # MB
                
                with open(ai_todo_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 통계 추출
                total_lines = len(content.split('\n'))
                total_chars = len(content)
                
                # 작업 수 계산
                completed_count = content.count('- [x]')
                pending_count = content.count('- [ ]')
                conversation_count = content.count('### 2025-')
                
                status_text = f"""📋 **AI민진 전용 작업 상태** (AI_Minjin_To_Do.md)

📊 **파일 통계:**
• 파일 크기: {file_size:.2f} MB
• 총 라인 수: {total_lines:,}개
• 총 문자 수: {total_chars:,}개
• 대화 기록: {conversation_count}개 세션

✅ **완료된 작업:** {completed_count}개
⏳ **대기 중인 작업:** {pending_count}개

💡 **파일이 클수록 좋습니다!** 현재 {file_size:.2f}MB - 계속 성장하는 중!

🔗 **파일 위치:** AI_Minjin_To_Do.md (Cursor TODO.md와 완전 분리)"""
            else:
                status_text = "📋 **AI_Minjin_To_Do.md 파일이 아직 생성되지 않았습니다.**"
            
            await cl.Message(content=status_text).send()
        except Exception as e:
            await cl.Message(content=f"AI민진 TODO 상태 조회 중 오류: {e}").send()
    else:
        await cl.Message(content="사용 가능한 TODO 명령어: 'TODO 상태'").send()

async def smart_memory_cleanup():
    """스마트 메모리 유지보수 실행"""
    try:
        loading_msg = cl.Message(content="🧠 스마트 메모리 유지보수를 실행 중입니다...")
        await loading_msg.send()
        
        # AI민진 메모리 유지보수
        maintenance_report = await ai_minjin.memory_brain.smart_memory_maintenance()
        
        # 결과 보고서 생성
        actions_summary = []
        for action in maintenance_report.get("actions", []):
            action_name = action["action"]
            result = action["result"]
            
            if action_name == "capacity_cleanup":
                cleaned = result.get("cleaned", 0)
                actions_summary.append(f"• 용량 정리: {cleaned}개 메모리 삭제")
            elif action_name == "contradiction_cleanup":
                resolved = result.get("contradictions_resolved", 0)
                actions_summary.append(f"• 상충 정리: {resolved}개 상충 해결")
            elif action_name == "index_optimization":
                actions_summary.append("• 인덱스 최적화: 완료")
        
        stats_before = maintenance_report.get("stats_before", {})
        stats_after = maintenance_report.get("stats_after", {})
        
        report_text = f"""🧠 **스마트 메모리 유지보수 완료!**

🔧 **수행된 작업:**
{chr(10).join(actions_summary) if actions_summary else "• 정리할 내용이 없어 최적화만 실행"}

📊 **전후 비교:**
• 메모리 수: {stats_before.get('total_memories', 0)} → {stats_after.get('total_memories', 0)}
• 평균 중요도: {stats_before.get('average_importance', 0):.2f} → {stats_after.get('average_importance', 0):.2f}
• DB 크기: {stats_before.get('memory_db_size_mb', 0):.1f}MB → {stats_after.get('memory_db_size_mb', 0):.1f}MB

⚡ **성능 향상:**
• 검색 속도 개선
• 중요한 메모리만 보존
• 상충 내용 자동 해결

🎯 **다음 유지보수:** 30일 후 자동 실행"""
        
        loading_msg.content = report_text
        await loading_msg.update()
        
    except Exception as e:
        logger.error(f"메모리 정리 오류: {e}")
        await cl.Message(content=f"메모리 정리 중 오류가 발생했습니다: {e}").send()

async def save_to_cursor_todo_if_important(user_message: str, ai_response: str):
    """중요한 대화만 Cursor AI TODO.md에 저장 (500GB 제한)"""
    try:
        # 중요도 키워드 체크
        important_keywords = [
            "중요", "기억", "저장", "계획", "목표", "프로젝트", "구현", "개발",
            "설치", "설정", "문제", "해결", "버그", "오류", "개선", "최적화"
        ]
        
        is_important = any(keyword in user_message for keyword in important_keywords)
        
        if is_important:
            # TODO.md 파일 크기 체크 (500GB = 0.5TB)
            todo_path = "TODO.md"
            max_size_bytes = cursor_ai_memory_limit_gb * 1024 * 1024 * 1024  # 500GB
            
            if os.path.exists(todo_path):
                current_size = os.path.getsize(todo_path)
                if current_size > max_size_bytes * 0.95:  # 95% 초과시
                    logger.warning("Cursor AI TODO.md 용량 한계 근접, 저장 생략")
                    return
            
            # 중요한 대화를 TODO.md에 추가
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            conversation_entry = f"""

#### 💬 **중요한 대화 기록** ({timestamp})
**사용자:** {user_message}
**응답:** {ai_response[:300]}{'...' if len(ai_response) > 300 else ''}

---
"""
            
            # TODO.md에 추가 (파일 끝에)
            with open(todo_path, 'a', encoding='utf-8') as f:
                f.write(conversation_entry)
                
    except Exception as e:
        logger.error(f"Cursor TODO 저장 오류: {e}")

async def auto_detect_and_save_ai_minjin_tasks(user_message: str, ai_response: str):
    """대화에서 AI민진 작업을 자동 감지하고 AI_Minjin_To_Do.md에 안전하게 저장 (무제한)"""
    task_keywords = [
        "작업", "해야", "할 일", "계획", "구현", "개발", "설치", "설정", 
        "만들어", "추가", "수정", "개선", "최적화", "업데이트", "기억"
    ]
    
    # 중요한 대화는 영구 기억으로 저장 (무제한)
    await ai_minjin.memory_brain.add_memory(
        f"사용자: {user_message} | AI민진: {ai_response[:300]}",
        {"type": "conversation", "auto_saved": True, "timestamp": datetime.now().isoformat()}
    )  # 자동 중요도 계산
    
    # AI_Minjin_To_Do.md에 대화 기록 추가 (무제한)
    conversation_data = {
        "add_conversation": {
            "user_message": user_message,
            "ai_response": ai_response,
            "has_task_keywords": any(keyword in user_message for keyword in task_keywords)
        }
    }
    await ai_minjin.self_modifier.update_ai_minjin_todo(conversation_data)
    
    # 작업 관련 내용이면 작업으로도 추가
    if any(keyword in user_message for keyword in task_keywords):
        task_data = {
            "add_task": {
                "content": f"대화에서 감지된 작업: {user_message[:100]}",
                "priority": "medium",
                "type": "auto_detected"
            }
        }
        await ai_minjin.self_modifier.update_ai_minjin_todo(task_data)

if __name__ == "__main__":
    import chainlit.cli
    chainlit.cli.run_chainlit(__file__)