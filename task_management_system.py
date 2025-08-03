#!/usr/bin/env python3
"""
AI민진 작업 관리 시스템
실용적이고 체계적인 작업 추적 및 관리 도구
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

# 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Task:
    """작업 정의"""
    id: str
    title: str
    description: str
    status: str  # pending, in_progress, completed, cancelled
    priority: str  # low, medium, high, urgent
    category: str  # coding, research, ocr, money, blog, etc.
    created_at: str
    updated_at: str
    due_date: Optional[str] = None
    assigned_to: str = "AI민진"
    notes: List[str] = None
    related_files: List[str] = None
    progress: int = 0  # 0-100%

    def __post_init__(self):
        if self.notes is None:
            self.notes = []
        if self.related_files is None:
            self.related_files = []

@dataclass
class Project:
    """프로젝트 정의"""
    id: str
    name: str
    description: str
    status: str
    tasks: List[str]  # task IDs
    rag_folder: str  # RAG_OCR, RAG_Money, etc.
    created_at: str
    updated_at: str

class TaskManager:
    """작업 관리 시스템"""
    
    def __init__(self, base_path: str = "C:/Users/user/Dropbox/_RAG", auto_mode: bool = True):
        self.base_path = Path(base_path)
        self.tasks_file = self.base_path / "tasks.json"
        self.projects_file = self.base_path / "projects.json"
        self.daily_log_dir = self.base_path / "Daily_Logs"
        self.auto_mode = auto_mode
        
        # 디렉토리 생성
        self.daily_log_dir.mkdir(exist_ok=True)
        
        # 데이터 로드
        self.tasks = self.load_tasks()
        self.projects = self.load_projects()
        
        # 자동 모드에서는 시작시 상태 체크
        if self.auto_mode:
            self.auto_check_and_update()
    
    def load_tasks(self) -> Dict[str, Task]:
        """작업 로드"""
        if self.tasks_file.exists():
            with open(self.tasks_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {k: Task(**v) for k, v in data.items()}
        return {}
    
    def save_tasks(self):
        """작업 저장"""
        data = {k: asdict(v) for k, v in self.tasks.items()}
        with open(self.tasks_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load_projects(self) -> Dict[str, Project]:
        """프로젝트 로드"""
        if self.projects_file.exists():
            with open(self.projects_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {k: Project(**v) for k, v in data.items()}
        return {}
    
    def save_projects(self):
        """프로젝트 저장"""
        data = {k: asdict(v) for k, v in self.projects.items()}
        with open(self.projects_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def create_task(self, title: str, description: str, category: str, 
                   priority: str = "medium", due_date: Optional[str] = None) -> str:
        """새 작업 생성"""
        task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        now = datetime.now().isoformat()
        
        task = Task(
            id=task_id,
            title=title,
            description=description,
            status="pending",
            priority=priority,
            category=category,
            created_at=now,
            updated_at=now,
            due_date=due_date
        )
        
        self.tasks[task_id] = task
        self.save_tasks()
        
        logger.info(f"작업 생성됨: {task_id} - {title}")
        return task_id
    
    def update_task_status(self, task_id: str, status: str, progress: int = None):
        """작업 상태 업데이트"""
        if task_id in self.tasks:
            self.tasks[task_id].status = status
            self.tasks[task_id].updated_at = datetime.now().isoformat()
            
            if progress is not None:
                self.tasks[task_id].progress = progress
            
            self.save_tasks()
            logger.info(f"작업 상태 업데이트: {task_id} -> {status}")
        else:
            logger.error(f"작업을 찾을 수 없음: {task_id}")
    
    def add_task_note(self, task_id: str, note: str):
        """작업에 노트 추가"""
        if task_id in self.tasks:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.tasks[task_id].notes.append(f"[{timestamp}] {note}")
            self.tasks[task_id].updated_at = datetime.now().isoformat()
            self.save_tasks()
        else:
            logger.error(f"작업을 찾을 수 없음: {task_id}")
    
    def get_tasks_by_status(self, status: str) -> List[Task]:
        """상태별 작업 조회"""
        return [task for task in self.tasks.values() if task.status == status]
    
    def get_tasks_by_category(self, category: str) -> List[Task]:
        """카테고리별 작업 조회"""
        return [task for task in self.tasks.values() if task.category == category]
    
    def create_daily_summary(self) -> str:
        """일일 작업 요약 생성"""
        today = datetime.now().strftime("%Y%m%d")
        summary_file = self.daily_log_dir / f"daily_summary_{today}.md"
        
        # 오늘 업데이트된 작업들
        today_tasks = [
            task for task in self.tasks.values() 
            if task.updated_at.startswith(today[:10])  # YYYY-MM-DD 형태
        ]
        
        # 요약 생성
        summary = f"""# 일일 작업 요약 - {today}

## 오늘 진행된 작업들

### 완료된 작업
"""
        
        completed_today = [t for t in today_tasks if t.status == "completed"]
        for task in completed_today:
            summary += f"- ✅ {task.title} ({task.category})\n"
        
        summary += "\n### 진행 중인 작업\n"
        in_progress_today = [t for t in today_tasks if t.status == "in_progress"]
        for task in in_progress_today:
            summary += f"- 🔄 {task.title} ({task.category}) - {task.progress}%\n"
        
        summary += "\n### 새로 생성된 작업\n"
        new_today = [t for t in today_tasks if t.created_at.startswith(today[:10])]
        for task in new_today:
            summary += f"- 📝 {task.title} ({task.category})\n"
        
        # 전체 상태
        total_tasks = len(self.tasks)
        completed_tasks = len([t for t in self.tasks.values() if t.status == "completed"])
        in_progress_tasks = len([t for t in self.tasks.values() if t.status == "in_progress"])
        pending_tasks = len([t for t in self.tasks.values() if t.status == "pending"])
        
        summary += f"""
## 전체 현황
- 총 작업: {total_tasks}개
- 완료: {completed_tasks}개
- 진행중: {in_progress_tasks}개  
- 대기중: {pending_tasks}개
- 완료율: {(completed_tasks/total_tasks*100):.1f}%

## 다음 우선순위 작업
"""
        
        # 우선순위 높은 미완료 작업들
        urgent_tasks = [
            t for t in self.tasks.values() 
            if t.status in ["pending", "in_progress"] and t.priority == "urgent"
        ]
        high_tasks = [
            t for t in self.tasks.values() 
            if t.status in ["pending", "in_progress"] and t.priority == "high"
        ]
        
        for task in urgent_tasks:
            summary += f"- 🚨 {task.title} ({task.category})\n"
        for task in high_tasks:
            summary += f"- ⭐ {task.title} ({task.category})\n"
        
        # 파일 저장
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(summary)
        
        logger.info(f"일일 요약 생성됨: {summary_file}")
        return str(summary_file)
    
    def auto_check_and_update(self):
        """자동 상태 체크 및 업데이트"""
        try:
            # 오늘 일일 요약이 없으면 생성
            today = datetime.now().strftime("%Y%m%d")
            summary_file = self.daily_log_dir / f"daily_summary_{today}.md"
            
            if not summary_file.exists():
                self.create_daily_summary()
                
            # 진행중인 작업이 있는지 체크
            in_progress = self.get_tasks_by_status("in_progress")
            pending = self.get_tasks_by_status("pending")
            
            print(f"🤖 자동 체크: 진행중 {len(in_progress)}개, 대기중 {len(pending)}개 작업")
            
        except Exception as e:
            logger.error(f"자동 체크 중 오류: {e}")
    
    def quick_task(self, title: str, category: str = "general", priority: str = "medium") -> str:
        """빠른 작업 생성 (AI가 사용하기 쉬운 버전)"""
        return self.create_task(title, f"자동 생성된 작업: {title}", category, priority)
    
    def complete_task_by_title(self, title: str) -> bool:
        """제목으로 작업 완료 처리"""
        for task in self.tasks.values():
            if title.lower() in task.title.lower():
                self.update_task_status(task.id, "completed", 100)
                return True
        return False
    
    def get_current_status(self) -> dict:
        """현재 상태 간단 조회"""
        return {
            "total": len(self.tasks),
            "pending": len(self.get_tasks_by_status("pending")),
            "in_progress": len(self.get_tasks_by_status("in_progress")),
            "completed": len(self.get_tasks_by_status("completed"))
        }

# AI가 쉽게 사용할 수 있는 전역 함수들
_global_manager = None

def init_task_system():
    """작업 시스템 초기화 (AI가 호출)"""
    global _global_manager
    if _global_manager is None:
        _global_manager = TaskManager()
    return _global_manager

def ai_create_task(title: str, category: str = "general") -> str:
    """AI가 작업 생성"""
    manager = init_task_system()
    task_id = manager.quick_task(title, category)
    print(f"✅ 새 작업 생성: {title}")
    return task_id

def ai_complete_task(title: str) -> bool:
    """AI가 작업 완료"""
    manager = init_task_system()
    success = manager.complete_task_by_title(title)
    if success:
        print(f"🎉 작업 완료: {title}")
    return success

def ai_get_status() -> dict:
    """AI가 현재 상태 확인"""
    manager = init_task_system()
    status = manager.get_current_status()
    print(f"📊 현재 상태: 총 {status['total']}개 | 진행중 {status['in_progress']}개 | 대기중 {status['pending']}개")
    return status

def ai_daily_summary() -> str:
    """AI가 일일 요약 생성"""
    manager = init_task_system()
    summary_file = manager.create_daily_summary()
    print(f"📝 일일 요약 생성됨")
    return summary_file

def main():
    """메인 실행"""
    manager = TaskManager()
    
    # 샘플 작업 생성 (처음 실행시)
    if not manager.tasks:
        print("작업 관리 시스템 초기화 중...")
        
        # 기본 작업들 생성
        manager.create_task(
            "OCR 시스템 최적화",
            "한글/영어 OCR 정확도 향상 및 처리 속도 개선",
            "ocr",
            "high"
        )
        
        manager.create_task(
            "검색 시스템 효율화",
            "웹 검색 결과 저장 및 분석 시스템 개선",
            "research",
            "medium"
        )
        
        manager.create_task(
            "메모리 정리 규칙 적용",
            "Cursor 메모리 최적화 및 성능 향상",
            "system",
            "low"
        )
        
        print("✅ 기본 작업들이 생성되었습니다.")
    
    # 현재 상태 출력
    print(f"\n📊 현재 작업 현황:")
    print(f"- 총 작업: {len(manager.tasks)}개")
    print(f"- 진행중: {len(manager.get_tasks_by_status('in_progress'))}개")
    print(f"- 대기중: {len(manager.get_tasks_by_status('pending'))}개")
    print(f"- 완료: {len(manager.get_tasks_by_status('completed'))}개")
    
    # 일일 요약 생성
    summary_file = manager.create_daily_summary()
    print(f"\n📝 일일 요약 생성됨: {summary_file}")

if __name__ == "__main__":
    main()