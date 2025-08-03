#!/usr/bin/env python3
"""
LangGraph 기반 AI민진 고급 작업 관리 시스템
동적 워크플로우와 상태 기반 자동 관리

주요 혁신사항:
- 조건부 작업 할당 및 우선순위 자동 조정
- 의존성 기반 자동 상태 전환
- 블로커 감지 및 해결 워크플로우
- 스마트 알림 및 에스컬레이션 시스템
"""

import os
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional, Literal
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing_extensions import TypedDict, Annotated
import logging

# LangGraph 임포트
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ============================================================================
# LangGraph State 정의
# ============================================================================

class TaskWorkflowState(TypedDict):
    """작업 워크플로우 상태"""
    task_id: str
    task_data: Dict[str, Any]
    current_action: str
    workflow_context: Dict[str, Any]
    messages: Annotated[List[str], add_messages]
    dependencies: List[str]
    blockers: List[str]
    priority_score: int
    auto_actions: List[str]
    user_input_required: bool
    escalation_level: int

# ============================================================================
# 데이터 모델
# ============================================================================

@dataclass
class EnhancedTask:
    """향상된 작업 정의"""
    id: str
    title: str
    description: str
    status: str  # pending, analyzing, ready, in_progress, blocked, reviewing, completed, cancelled
    priority: str  # low, medium, high, urgent, critical
    category: str
    created_at: str
    updated_at: str
    due_date: Optional[str] = None
    assigned_to: str = "AI민진"
    dependencies: List[str] = None
    blockers: List[str] = None
    auto_rules: Dict[str, Any] = None
    workflow_history: List[Dict] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    quality_score: Optional[int] = None
    business_value: Optional[int] = None
    technical_complexity: Optional[int] = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.blockers is None:
            self.blockers = []
        if self.auto_rules is None:
            self.auto_rules = {}
        if self.workflow_history is None:
            self.workflow_history = []

# ============================================================================
# LangGraph 노드 함수들
# ============================================================================

class TaskWorkflowNodes:
    """작업 워크플로우 노드 구현"""
    
    def __init__(self, task_manager):
        self.task_manager = task_manager
    
    def analyze_new_task(self, state: TaskWorkflowState) -> TaskWorkflowState:
        """새 작업 분석 노드"""
        task_data = state["task_data"]
        
        # AI 기반 작업 분석
        analysis = self._analyze_task_complexity(task_data)
        priority_score = self._calculate_priority_score(task_data, analysis)
        dependencies = self._detect_dependencies(task_data)
        
        # 자동 규칙 설정
        auto_rules = self._generate_auto_rules(analysis, priority_score)
        
        return {
            **state,
            "workflow_context": {
                "analysis": analysis,
                "auto_generated": True,
                "analysis_timestamp": datetime.now().isoformat()
            },
            "dependencies": dependencies,
            "priority_score": priority_score,
            "auto_actions": auto_rules.get("actions", []),
            "messages": [f"작업 분석 완료: 복잡도 {analysis['complexity']}, 우선순위 {priority_score}"]
        }
    
    def check_dependencies(self, state: TaskWorkflowState) -> TaskWorkflowState:
        """의존성 체크 노드"""
        task_id = state["task_id"]
        dependencies = state["dependencies"]
        
        unresolved_deps = []
        resolved_deps = []
        
        for dep_id in dependencies:
            dep_task = self.task_manager.get_task(dep_id)
            if dep_task and dep_task.status == "completed":
                resolved_deps.append(dep_id)
            else:
                unresolved_deps.append(dep_id)
        
        can_proceed = len(unresolved_deps) == 0
        
        return {
            **state,
            "workflow_context": {
                **state["workflow_context"],
                "resolved_dependencies": resolved_deps,
                "unresolved_dependencies": unresolved_deps,
                "can_proceed": can_proceed
            },
            "blockers": unresolved_deps,
            "messages": [f"의존성 체크: {len(resolved_deps)}개 해결, {len(unresolved_deps)}개 미해결"]
        }
    
    def assign_task(self, state: TaskWorkflowState) -> TaskWorkflowState:
        """작업 할당 노드"""
        task_data = state["task_data"]
        priority_score = state["priority_score"]
        
        # 할당 로직
        assigned_to = self._determine_assignee(task_data, priority_score)
        due_date = self._calculate_due_date(task_data, priority_score)
        
        # 작업 상태 업데이트
        updated_task_data = {
            **task_data,
            "assigned_to": assigned_to,
            "due_date": due_date,
            "status": "ready"
        }
        
        return {
            **state,
            "task_data": updated_task_data,
            "current_action": "assigned",
            "messages": [f"작업 할당 완료: {assigned_to}에게 할당, 마감일 {due_date}"]
        }
    
    def execute_task(self, state: TaskWorkflowState) -> TaskWorkflowState:
        """작업 실행 노드"""
        task_data = state["task_data"]
        
        # 작업 실행 시작
        updated_task_data = {
            **task_data,
            "status": "in_progress",
            "started_at": datetime.now().isoformat()
        }
        
        # 자동 모니터링 설정
        monitoring_rules = self._setup_monitoring(updated_task_data)
        
        return {
            **state,
            "task_data": updated_task_data,
            "current_action": "executing",
            "workflow_context": {
                **state["workflow_context"],
                "monitoring_rules": monitoring_rules,
                "execution_started": True
            },
            "messages": [f"작업 실행 시작: {task_data['title']}"]
        }
    
    def check_blockers(self, state: TaskWorkflowState) -> TaskWorkflowState:
        """블로커 체크 노드"""
        task_data = state["task_data"]
        blockers = state["blockers"]
        
        # 블로커 상태 분석
        active_blockers = []
        resolved_blockers = []
        
        for blocker in blockers:
            blocker_status = self._check_blocker_status(blocker)
            if blocker_status["is_active"]:
                active_blockers.append(blocker)
            else:
                resolved_blockers.append(blocker)
        
        # 에스컬레이션 레벨 결정
        escalation_level = len(active_blockers)
        
        return {
            **state,
            "blockers": active_blockers,
            "escalation_level": escalation_level,
            "workflow_context": {
                **state["workflow_context"],
                "resolved_blockers": resolved_blockers,
                "blocker_analysis": {
                    "active_count": len(active_blockers),
                    "resolved_count": len(resolved_blockers)
                }
            },
            "messages": [f"블로커 체크: {len(active_blockers)}개 활성, {len(resolved_blockers)}개 해결"]
        }
    
    def escalate_task(self, state: TaskWorkflowState) -> TaskWorkflowState:
        """작업 에스컬레이션 노드"""
        task_data = state["task_data"]
        escalation_level = state["escalation_level"]
        blockers = state["blockers"]
        
        # 에스컬레이션 액션 결정
        escalation_actions = self._determine_escalation_actions(escalation_level, blockers)
        
        # 알림 발송
        notifications = self._send_escalation_notifications(task_data, escalation_actions)
        
        return {
            **state,
            "current_action": "escalated",
            "workflow_context": {
                **state["workflow_context"],
                "escalation_actions": escalation_actions,
                "notifications_sent": notifications
            },
            "user_input_required": escalation_level > 2,
            "messages": [f"작업 에스컬레이션: 레벨 {escalation_level}, 액션 {len(escalation_actions)}개"]
        }
    
    def complete_task(self, state: TaskWorkflowState) -> TaskWorkflowState:
        """작업 완료 노드"""
        task_data = state["task_data"]
        
        # 완료 처리
        updated_task_data = {
            **task_data,
            "status": "completed",
            "completed_at": datetime.now().isoformat()
        }
        
        # 품질 평가
        quality_score = self._evaluate_task_quality(updated_task_data)
        
        # 종속 작업 알림
        dependent_tasks = self._notify_dependent_tasks(task_data["id"])
        
        return {
            **state,
            "task_data": {**updated_task_data, "quality_score": quality_score},
            "current_action": "completed",
            "workflow_context": {
                **state["workflow_context"],
                "completion_quality": quality_score,
                "dependent_tasks_notified": dependent_tasks
            },
            "messages": [f"작업 완료: 품질 점수 {quality_score}, 종속 작업 {len(dependent_tasks)}개 알림"]
        }
    
    # ========================================================================
    # 헬퍼 메서드들
    # ========================================================================
    
    def _analyze_task_complexity(self, task_data: Dict) -> Dict:
        """작업 복잡도 분석"""
        description = task_data.get("description", "")
        
        # 간단한 복잡도 분석 (실제로는 더 정교한 AI 분석 사용)
        complexity_indicators = {
            "length": len(description),
            "technical_keywords": sum(1 for keyword in ["API", "시스템", "통합", "구현"] if keyword in description),
            "uncertainty_keywords": sum(1 for keyword in ["연구", "분석", "검토"] if keyword in description)
        }
        
        complexity = "low"
        if complexity_indicators["length"] > 200 or complexity_indicators["technical_keywords"] > 2:
            complexity = "high"
        elif complexity_indicators["length"] > 100 or complexity_indicators["technical_keywords"] > 1:
            complexity = "medium"
        
        return {
            "complexity": complexity,
            "indicators": complexity_indicators,
            "estimated_hours": {"low": 2, "medium": 8, "high": 24}[complexity]
        }
    
    def _calculate_priority_score(self, task_data: Dict, analysis: Dict) -> int:
        """우선순위 점수 계산"""
        base_score = {"low": 1, "medium": 3, "high": 5, "urgent": 7, "critical": 10}.get(
            task_data.get("priority", "medium"), 3
        )
        
        # 복잡도 가중치
        complexity_weight = {"low": 1, "medium": 1.2, "high": 1.5}[analysis["complexity"]]
        
        # 마감일 가중치
        due_date = task_data.get("due_date")
        deadline_weight = 1.0
        if due_date:
            try:
                due = datetime.fromisoformat(due_date)
                days_left = (due - datetime.now()).days
                if days_left <= 1:
                    deadline_weight = 2.0
                elif days_left <= 3:
                    deadline_weight = 1.5
            except:
                pass
        
        return int(base_score * complexity_weight * deadline_weight)
    
    def _detect_dependencies(self, task_data: Dict) -> List[str]:
        """의존성 자동 탐지"""
        description = task_data.get("description", "")
        detected_deps = []
        
        # 키워드 기반 의존성 탐지 (실제로는 더 정교한 분석 사용)
        if "이전" in description or "먼저" in description:
            # 기존 작업들과 연관성 분석
            pass
        
        return detected_deps
    
    def _generate_auto_rules(self, analysis: Dict, priority_score: int) -> Dict:
        """자동 규칙 생성"""
        rules = {
            "actions": [],
            "monitoring": {},
            "escalation": {}
        }
        
        if priority_score > 7:
            rules["actions"].append("immediate_notification")
            rules["monitoring"]["frequency"] = "hourly"
        elif priority_score > 5:
            rules["monitoring"]["frequency"] = "daily"
        
        if analysis["complexity"] == "high":
            rules["actions"].append("expert_review_required")
        
        return rules
    
    def _determine_assignee(self, task_data: Dict, priority_score: int) -> str:
        """담당자 결정"""
        category = task_data.get("category", "general")
        
        # 카테고리별 자동 할당 로직
        assignee_map = {
            "coding": "AI민진_개발팀",
            "research": "AI민진_연구팀", 
            "ocr": "AI민진_OCR팀",
            "money": "AI민진_수익팀"
        }
        
        return assignee_map.get(category, "AI민진")
    
    def _calculate_due_date(self, task_data: Dict, priority_score: int) -> str:
        """마감일 계산"""
        priority = task_data.get("priority", "medium")
        
        days_map = {
            "critical": 1,
            "urgent": 2, 
            "high": 5,
            "medium": 10,
            "low": 30
        }
        
        days = days_map.get(priority, 10)
        due_date = datetime.now() + timedelta(days=days)
        
        return due_date.isoformat()
    
    def _setup_monitoring(self, task_data: Dict) -> Dict:
        """모니터링 설정"""
        return {
            "check_frequency": "daily",
            "alerts_enabled": True,
            "auto_status_update": True
        }
    
    def _check_blocker_status(self, blocker: str) -> Dict:
        """블로커 상태 체크"""
        # 실제 구현에서는 외부 시스템 연동
        return {
            "is_active": True,
            "severity": "medium",
            "estimated_resolution": "2 days"
        }
    
    def _determine_escalation_actions(self, level: int, blockers: List) -> List[str]:
        """에스컬레이션 액션 결정"""
        actions = []
        
        if level >= 1:
            actions.append("notify_assignee")
        if level >= 2:
            actions.append("notify_manager")
        if level >= 3:
            actions.append("emergency_meeting")
        
        return actions
    
    def _send_escalation_notifications(self, task_data: Dict, actions: List) -> List[str]:
        """에스컬레이션 알림 발송"""
        sent_notifications = []
        
        for action in actions:
            # 실제 알림 발송 로직
            logger.info(f"알림 발송: {action} for task {task_data['id']}")
            sent_notifications.append(action)
        
        return sent_notifications
    
    def _evaluate_task_quality(self, task_data: Dict) -> int:
        """작업 품질 평가"""
        # 간단한 품질 평가 로직
        return 85  # 실제로는 복잡한 평가 시스템
    
    def _notify_dependent_tasks(self, task_id: str) -> List[str]:
        """종속 작업 알림"""
        # 종속 작업들 찾기 및 알림
        return []

# ============================================================================
# 조건부 판단 함수들
# ============================================================================

def decide_after_dependency_check(state: TaskWorkflowState) -> str:
    """의존성 체크 후 다음 단계 결정"""
    can_proceed = state["workflow_context"].get("can_proceed", False)
    
    if can_proceed:
        return "assign"
    else:
        return "wait_dependencies"

def decide_after_blocker_check(state: TaskWorkflowState) -> str:
    """블로커 체크 후 다음 단계 결정"""
    escalation_level = state["escalation_level"]
    
    if escalation_level == 0:
        return "proceed"
    elif escalation_level <= 2:
        return "escalate"
    else:
        return "emergency"

def decide_task_completion(state: TaskWorkflowState) -> str:
    """작업 완료 여부 결정"""
    current_status = state["task_data"].get("status", "")
    
    if current_status == "completed":
        return "complete"
    elif state["user_input_required"]:
        return "user_input"
    else:
        return "continue"

# ============================================================================
# LangGraph 워크플로우 구성
# ============================================================================

class LangGraphTaskManager:
    """LangGraph 기반 작업 관리자"""
    
    def __init__(self, base_path: str = "C:/Users/user/Dropbox/_RAG"):
        self.base_path = Path(base_path)
        self.tasks_file = self.base_path / "enhanced_tasks.json"
        
        # 기존 작업 로드
        self.tasks = self.load_tasks()
        
        # LangGraph 설정
        self.memory = MemorySaver()
        self.workflow_nodes = TaskWorkflowNodes(self)
        self.workflow = self._create_workflow()
        
        logger.info("LangGraph Task Manager 초기화 완료")
    
    def load_tasks(self) -> Dict[str, EnhancedTask]:
        """작업 로드"""
        if self.tasks_file.exists():
            with open(self.tasks_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {k: EnhancedTask(**v) for k, v in data.items()}
        return {}
    
    def save_tasks(self):
        """작업 저장"""
        data = {k: asdict(v) for k, v in self.tasks.items()}
        with open(self.tasks_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def get_task(self, task_id: str) -> Optional[EnhancedTask]:
        """작업 조회"""
        return self.tasks.get(task_id)
    
    def _create_workflow(self) -> StateGraph:
        """LangGraph 워크플로우 생성"""
        workflow = StateGraph(TaskWorkflowState)
        
        # 노드 추가
        workflow.add_node("analyze", self.workflow_nodes.analyze_new_task)
        workflow.add_node("check_deps", self.workflow_nodes.check_dependencies)
        workflow.add_node("assign", self.workflow_nodes.assign_task)
        workflow.add_node("execute", self.workflow_nodes.execute_task)
        workflow.add_node("check_blockers", self.workflow_nodes.check_blockers)
        workflow.add_node("escalate", self.workflow_nodes.escalate_task)
        workflow.add_node("complete", self.workflow_nodes.complete_task)
        workflow.add_node("wait_deps", lambda state: {**state, "current_action": "waiting"})
        workflow.add_node("user_input", lambda state: {**state, "user_input_required": True})
        
        # 시작점 설정
        workflow.set_entry_point("analyze")
        
        # 엣지 연결
        workflow.add_edge("analyze", "check_deps")
        
        # 조건부 엣지
        workflow.add_conditional_edges(
            "check_deps",
            decide_after_dependency_check,
            {
                "assign": "assign",
                "wait_dependencies": "wait_deps"
            }
        )
        
        workflow.add_edge("assign", "execute")
        workflow.add_edge("execute", "check_blockers")
        
        workflow.add_conditional_edges(
            "check_blockers", 
            decide_after_blocker_check,
            {
                "proceed": "complete",
                "escalate": "escalate", 
                "emergency": "user_input"
            }
        )
        
        workflow.add_conditional_edges(
            "escalate",
            decide_task_completion,
            {
                "complete": "complete",
                "user_input": "user_input",
                "continue": "check_blockers"
            }
        )
        
        workflow.add_edge("complete", END)
        workflow.add_edge("wait_deps", END)
        workflow.add_edge("user_input", END)
        
        return workflow.compile(checkpointer=self.memory)
    
    async def process_task_workflow(self, task_data: Dict, thread_id: str = None) -> Dict:
        """작업 워크플로우 실행"""
        if thread_id is None:
            thread_id = f"task_{task_data.get('id', 'unknown')}_{int(datetime.now().timestamp())}"
        
        # 초기 상태 설정
        initial_state = {
            "task_id": task_data.get("id", ""),
            "task_data": task_data,
            "current_action": "created",
            "workflow_context": {},
            "messages": [],
            "dependencies": task_data.get("dependencies", []),
            "blockers": [],
            "priority_score": 0,
            "auto_actions": [],
            "user_input_required": False,
            "escalation_level": 0
        }
        
        # 워크플로우 실행
        config = {
            "configurable": {
                "thread_id": thread_id,
                "recursion_limit": 50
            }
        }
        
        try:
            result = await self.workflow.ainvoke(initial_state, config)
            
            # 결과 저장
            if result["current_action"] in ["completed", "assigned"]:
                enhanced_task = EnhancedTask(**result["task_data"])
                self.tasks[enhanced_task.id] = enhanced_task
                self.save_tasks()
            
            logger.info(f"작업 워크플로우 완료: {task_data.get('title', 'Unknown')} - {result['current_action']}")
            
            return result
            
        except Exception as e:
            logger.error(f"워크플로우 실행 오류: {e}")
            return {"error": str(e), "task_id": task_data.get("id", "")}

# ============================================================================
# 사용 예제
# ============================================================================

async def main():
    """사용 예제"""
    task_manager = LangGraphTaskManager()
    
    # 새 작업 생성 테스트
    new_task = {
        "id": "task_001",
        "title": "LangGraph OCR 시스템 통합",
        "description": "기존 OCR 시스템에 LangGraph 워크플로우를 적용하여 동적 문서 처리 파이프라인 구현",
        "category": "coding",
        "priority": "high",
        "dependencies": []
    }
    
    # 워크플로우 실행
    result = await task_manager.process_task_workflow(new_task)
    
    print("=== 작업 워크플로우 결과 ===")
    print(f"최종 상태: {result.get('current_action', 'Unknown')}")
    print(f"메시지: {result.get('messages', [])}")
    print(f"워크플로우 컨텍스트: {result.get('workflow_context', {})}")

if __name__ == "__main__":
    asyncio.run(main())