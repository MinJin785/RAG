#!/usr/bin/env python3
"""
LangGraph 기반 지능형 대화 시스템
동적 대화 워크플로우와 컨텍스트 기반 자동 최적화

주요 혁신사항:
- 의도 기반 동적 응답 전략 선택
- 멀티턴 대화 컨텍스트 지능적 관리
- 실시간 응답 품질 평가 및 개선
- 사용자 만족도 기반 학습 시스템
- 대화 히스토리 구조화 및 검색 최적화
"""

import asyncio
import json
import time
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Literal
from dataclasses import dataclass, asdict
from typing_extensions import TypedDict, Annotated
import logging
import hashlib
import pytz

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

class ConversationWorkflowState(TypedDict):
    """대화 워크플로우 상태"""
    conversation_id: str
    user_message: str
    conversation_history: List[Dict]
    user_intent: Dict[str, Any]
    context_analysis: Dict[str, Any]
    response_candidates: List[Dict]
    selected_response: Dict[str, Any]
    quality_metrics: Dict[str, float]
    messages: Annotated[List[str], add_messages]
    user_profile: Dict[str, Any]
    conversation_metadata: Dict[str, Any]
    requires_clarification: bool
    learning_data: List[Dict]
    satisfaction_score: Optional[float]

# ============================================================================
# 데이터 모델
# ============================================================================

@dataclass
class UserIntent:
    """사용자 의도"""
    primary_intent: str
    confidence: float
    entities: List[Dict]
    urgency_level: str
    complexity_level: str
    domain: str

@dataclass
class ConversationContext:
    """대화 컨텍스트"""
    topic: str
    sentiment: str
    previous_topics: List[str]
    unresolved_questions: List[str]
    user_preferences: Dict[str, Any]
    session_duration: float

@dataclass
class ResponseCandidate:
    """응답 후보"""
    text: str
    strategy: str
    confidence: float
    estimated_satisfaction: float
    reasoning: str

@dataclass
class QualityMetrics:
    """품질 메트릭"""
    relevance: float
    helpfulness: float
    clarity: float
    engagement: float
    accuracy: float

# ============================================================================
# LangGraph 노드 함수들
# ============================================================================

class ConversationWorkflowNodes:
    """대화 워크플로우 노드 구현"""
    
    def __init__(self, conversation_system):
        self.conversation_system = conversation_system
        self.kst = pytz.timezone('Asia/Seoul')
        
        # 인텐트 키워드 매핑
        self.intent_keywords = {
            "question": ["뭐", "무엇", "어떻게", "왜", "언제", "어디서", "?"],
            "request": ["해줘", "부탁", "도와", "만들어", "생성", "작성"],
            "complaint": ["문제", "오류", "안돼", "잘못", "버그"],
            "praise": ["좋다", "훌륭", "감사", "고마워", "최고"],
            "instruction": ["하라", "하세요", "명령", "실행", "시작"],
            "information_seeking": ["알려", "설명", "정보", "자료", "데이터"],
            "casual": ["안녕", "hello", "하이", "잘지내", "어때"]
        }
    
    def analyze_user_intent(self, state: ConversationWorkflowState) -> ConversationWorkflowState:
        """사용자 의도 분석 노드"""
        user_message = state["user_message"]
        conversation_history = state["conversation_history"]
        
        # 의도 분석
        intent_analysis = self._analyze_intent(user_message, conversation_history)
        
        # 사용자 프로필 업데이트
        user_profile = self._update_user_profile(state.get("user_profile", {}), intent_analysis)
        
        return {
            **state,
            "user_intent": intent_analysis,
            "user_profile": user_profile,
            "conversation_metadata": {
                "intent_analysis_timestamp": datetime.now(self.kst).isoformat(),
                "primary_intent": intent_analysis["primary_intent"],
                "confidence": intent_analysis["confidence"]
            },
            "messages": [f"의도 분석 완료: {intent_analysis['primary_intent']} (신뢰도: {intent_analysis['confidence']:.2f})"]
        }
    
    def analyze_conversation_context(self, state: ConversationWorkflowState) -> ConversationWorkflowState:
        """대화 컨텍스트 분석 노드"""
        user_message = state["user_message"]
        conversation_history = state["conversation_history"]
        user_intent = state["user_intent"]
        
        # 컨텍스트 분석
        context_analysis = self._analyze_context(user_message, conversation_history, user_intent)
        
        # 명확화 필요성 판단
        requires_clarification = self._needs_clarification(context_analysis, user_intent)
        
        return {
            **state,
            "context_analysis": context_analysis,
            "requires_clarification": requires_clarification,
            "conversation_metadata": {
                **state.get("conversation_metadata", {}),
                "context_topic": context_analysis["topic"],
                "sentiment": context_analysis["sentiment"],
                "complexity": context_analysis["complexity"]
            },
            "messages": [f"컨텍스트 분석 완료: 주제 {context_analysis['topic']}, 감정 {context_analysis['sentiment']}"]
        }
    
    def generate_response_candidates(self, state: ConversationWorkflowState) -> ConversationWorkflowState:
        """응답 후보 생성 노드"""
        user_message = state["user_message"]
        user_intent = state["user_intent"]
        context_analysis = state["context_analysis"]
        user_profile = state["user_profile"]
        
        # 다양한 전략으로 응답 후보 생성
        response_candidates = []
        
        # 전략 1: 직접적 답변
        direct_response = self._generate_direct_response(user_message, user_intent, context_analysis)
        response_candidates.append(direct_response)
        
        # 전략 2: 맥락적 답변
        contextual_response = self._generate_contextual_response(user_message, context_analysis, user_profile)
        response_candidates.append(contextual_response)
        
        # 전략 3: 교육적 답변 (복잡한 질문의 경우)
        if user_intent["complexity_level"] == "high":
            educational_response = self._generate_educational_response(user_message, user_intent)
            response_candidates.append(educational_response)
        
        # 전략 4: 대화형 답변 (명확화가 필요한 경우)
        if state["requires_clarification"]:
            clarifying_response = self._generate_clarifying_response(user_message, context_analysis)
            response_candidates.append(clarifying_response)
        
        return {
            **state,
            "response_candidates": [asdict(candidate) for candidate in response_candidates],
            "messages": [f"응답 후보 생성 완료: {len(response_candidates)}개 전략"]
        }
    
    def select_best_response(self, state: ConversationWorkflowState) -> ConversationWorkflowState:
        """최적 응답 선택 노드"""
        response_candidates = state["response_candidates"]
        user_intent = state["user_intent"]
        context_analysis = state["context_analysis"]
        user_profile = state["user_profile"]
        
        # 각 후보 평가
        evaluated_candidates = []
        for candidate in response_candidates:
            evaluation = self._evaluate_response_candidate(candidate, user_intent, context_analysis, user_profile)
            candidate["evaluation"] = evaluation
            evaluated_candidates.append(candidate)
        
        # 최고 점수 후보 선택
        best_candidate = max(evaluated_candidates, key=lambda x: x["evaluation"]["overall_score"])
        
        return {
            **state,
            "response_candidates": evaluated_candidates,
            "selected_response": best_candidate,
            "conversation_metadata": {
                **state.get("conversation_metadata", {}),
                "selected_strategy": best_candidate["strategy"],
                "selection_score": best_candidate["evaluation"]["overall_score"]
            },
            "messages": [f"최적 응답 선택: {best_candidate['strategy']} 전략 (점수: {best_candidate['evaluation']['overall_score']:.2f})"]
        }
    
    def evaluate_response_quality(self, state: ConversationWorkflowState) -> ConversationWorkflowState:
        """응답 품질 평가 노드"""
        selected_response = state["selected_response"]
        user_intent = state["user_intent"]
        context_analysis = state["context_analysis"]
        
        # 품질 메트릭 계산
        quality_metrics = self._calculate_quality_metrics(selected_response, user_intent, context_analysis)
        
        # 전체 품질 점수
        overall_quality = sum(quality_metrics.values()) / len(quality_metrics)
        
        # 사용자 만족도 예측
        predicted_satisfaction = self._predict_user_satisfaction(quality_metrics, user_intent)
        
        return {
            **state,
            "quality_metrics": quality_metrics,
            "satisfaction_score": predicted_satisfaction,
            "conversation_metadata": {
                **state.get("conversation_metadata", {}),
                "quality_score": overall_quality,
                "predicted_satisfaction": predicted_satisfaction
            },
            "messages": [f"품질 평가 완료: 전체 품질 {overall_quality:.2f}, 예상 만족도 {predicted_satisfaction:.2f}"]
        }
    
    def improve_response_if_needed(self, state: ConversationWorkflowState) -> ConversationWorkflowState:
        """필요시 응답 개선 노드"""
        quality_metrics = state["quality_metrics"]
        selected_response = state["selected_response"]
        satisfaction_score = state["satisfaction_score"]
        
        # 개선이 필요한지 판단
        needs_improvement = satisfaction_score < 0.7 or any(score < 0.6 for score in quality_metrics.values())
        
        if needs_improvement:
            # 응답 개선
            improved_response = self._improve_response(selected_response, quality_metrics, state)
            
            # 개선된 응답으로 품질 재평가
            improved_quality = self._calculate_quality_metrics(
                improved_response, state["user_intent"], state["context_analysis"]
            )
            
            return {
                **state,
                "selected_response": improved_response,
                "quality_metrics": improved_quality,
                "conversation_metadata": {
                    **state.get("conversation_metadata", {}),
                    "response_improved": True,
                    "improvement_reason": "품질 기준 미달"
                },
                "messages": ["응답 개선 완료: 품질 향상 적용"]
            }
        else:
            return {
                **state,
                "conversation_metadata": {
                    **state.get("conversation_metadata", {}),
                    "response_improved": False
                },
                "messages": ["응답 품질 만족: 개선 불필요"]
            }
    
    def update_conversation_history(self, state: ConversationWorkflowState) -> ConversationWorkflowState:
        """대화 히스토리 업데이트 노드"""
        conversation_history = state["conversation_history"]
        user_message = state["user_message"]
        selected_response = state["selected_response"]
        
        # 새로운 대화 항목 추가
        new_conversation_item = {
            "timestamp": datetime.now(self.kst).isoformat(),
            "user_message": user_message,
            "ai_response": selected_response["text"],
            "intent": state["user_intent"]["primary_intent"],
            "context": state["context_analysis"]["topic"],
            "quality_score": sum(state["quality_metrics"].values()) / len(state["quality_metrics"]),
            "strategy": selected_response["strategy"]
        }
        
        # 히스토리 업데이트 (최근 20개만 유지)
        updated_history = conversation_history + [new_conversation_item]
        if len(updated_history) > 20:
            updated_history = updated_history[-20:]
        
        return {
            **state,
            "conversation_history": updated_history,
            "messages": [f"대화 히스토리 업데이트: 총 {len(updated_history)}개 항목"]
        }
    
    def extract_learning_data(self, state: ConversationWorkflowState) -> ConversationWorkflowState:
        """학습 데이터 추출 노드"""
        learning_data = []
        
        # 의도 인식 학습 데이터
        learning_data.append({
            "type": "intent_recognition",
            "user_message": state["user_message"],
            "predicted_intent": state["user_intent"]["primary_intent"],
            "confidence": state["user_intent"]["confidence"],
            "actual_intent": "미확인",  # 실제로는 사용자 피드백 필요
            "timestamp": datetime.now(self.kst).isoformat()
        })
        
        # 응답 전략 학습 데이터
        learning_data.append({
            "type": "response_strategy",
            "intent": state["user_intent"]["primary_intent"],
            "context": state["context_analysis"]["topic"],
            "selected_strategy": state["selected_response"]["strategy"],
            "quality_score": sum(state["quality_metrics"].values()) / len(state["quality_metrics"]),
            "predicted_satisfaction": state["satisfaction_score"],
            "timestamp": datetime.now(self.kst).isoformat()
        })
        
        # 사용자 선호도 학습 데이터
        learning_data.append({
            "type": "user_preference",
            "user_profile": state["user_profile"],
            "preferred_response_style": state["selected_response"]["strategy"],
            "context_type": state["context_analysis"]["sentiment"],
            "timestamp": datetime.now(self.kst).isoformat()
        })
        
        return {
            **state,
            "learning_data": learning_data,
            "messages": [f"학습 데이터 추출 완료: {len(learning_data)}개 항목"]
        }
    
    def save_conversation_and_learn(self, state: ConversationWorkflowState) -> ConversationWorkflowState:
        """대화 저장 및 학습 노드"""
        conversation_id = state["conversation_id"]
        
        # 대화 저장
        saved_files = self._save_conversation_data(state)
        
        # 학습 시스템 업데이트
        self._update_learning_system(state["learning_data"])
        
        # 성능 메트릭 계산
        performance_metrics = self._calculate_conversation_metrics(state)
        
        return {
            **state,
            "conversation_metadata": {
                **state.get("conversation_metadata", {}),
                "conversation_saved": True,
                "saved_files": saved_files,
                "learning_data_processed": len(state["learning_data"]),
                "performance_metrics": performance_metrics,
                "completion_timestamp": datetime.now(self.kst).isoformat()
            },
            "messages": [f"대화 저장 및 학습 완료: {len(saved_files)}개 파일 생성, {len(state['learning_data'])}개 학습 데이터 처리"]
        }
    
    # ========================================================================
    # 헬퍼 메서드들
    # ========================================================================
    
    def _analyze_intent(self, user_message: str, conversation_history: List[Dict]) -> Dict:
        """사용자 의도 분석"""
        message_lower = user_message.lower()
        
        # 키워드 기반 의도 분석
        intent_scores = {}
        for intent, keywords in self.intent_keywords.items():
            score = sum(1 for keyword in keywords if keyword in message_lower)
            if score > 0:
                intent_scores[intent] = score / len(keywords)
        
        # 최고 점수 의도 선택
        if intent_scores:
            primary_intent = max(intent_scores.keys(), key=lambda k: intent_scores[k])
            confidence = intent_scores[primary_intent]
        else:
            primary_intent = "general"
            confidence = 0.5
        
        # 복잡도 분석
        complexity = "low"
        if len(user_message) > 100 or len(user_message.split()) > 20:
            complexity = "medium"
        if any(keyword in message_lower for keyword in ["시스템", "아키텍처", "통합", "최적화"]):
            complexity = "high"
        
        # 긴급도 분석
        urgency = "normal"
        if any(keyword in message_lower for keyword in ["급해", "빨리", "즉시", "긴급"]):
            urgency = "high"
        elif any(keyword in message_lower for keyword in ["천천히", "나중에", "여유"]):
            urgency = "low"
        
        # 엔티티 추출 (간단한 버전)
        entities = []
        if "파일" in message_lower:
            entities.append({"type": "object", "value": "파일"})
        if "시스템" in message_lower:
            entities.append({"type": "system", "value": "시스템"})
        
        return {
            "primary_intent": primary_intent,
            "confidence": confidence,
            "complexity_level": complexity,
            "urgency_level": urgency,
            "entities": entities,
            "domain": self._determine_domain(user_message)
        }
    
    def _determine_domain(self, user_message: str) -> str:
        """도메인 결정"""
        message_lower = user_message.lower()
        
        domain_keywords = {
            "coding": ["코드", "프로그래밍", "개발", "함수", "변수"],
            "ocr": ["ocr", "텍스트 인식", "문서 처리"],
            "search": ["검색", "찾기", "조회"],
            "money": ["돈", "수익", "투자", "비즈니스"],
            "general": []
        }
        
        for domain, keywords in domain_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                return domain
        
        return "general"
    
    def _update_user_profile(self, current_profile: Dict, intent_analysis: Dict) -> Dict:
        """사용자 프로필 업데이트"""
        profile = current_profile.copy()
        
        # 의도 히스토리 업데이트
        if "intent_history" not in profile:
            profile["intent_history"] = []
        
        profile["intent_history"].append({
            "intent": intent_analysis["primary_intent"],
            "domain": intent_analysis["domain"],
            "timestamp": datetime.now(self.kst).isoformat()
        })
        
        # 최근 20개만 유지
        if len(profile["intent_history"]) > 20:
            profile["intent_history"] = profile["intent_history"][-20:]
        
        # 선호 도메인 계산
        recent_domains = [item["domain"] for item in profile["intent_history"][-10:]]
        if recent_domains:
            from collections import Counter
            profile["preferred_domain"] = Counter(recent_domains).most_common(1)[0][0]
        
        # 복잡도 선호도 업데이트
        profile["preferred_complexity"] = intent_analysis["complexity_level"]
        
        return profile
    
    def _analyze_context(self, user_message: str, conversation_history: List[Dict], user_intent: Dict) -> Dict:
        """대화 컨텍스트 분석"""
        # 주제 분석
        topic = user_intent["domain"]
        if conversation_history:
            last_context = conversation_history[-1].get("context", "general")
            if last_context != "general":
                topic = last_context  # 연속성 유지
        
        # 감정 분석 (간단한 버전)
        sentiment = "neutral"
        positive_words = ["좋다", "훌륭", "감사", "만족", "최고"]
        negative_words = ["문제", "안좋다", "실망", "화나", "짜증"]
        
        message_lower = user_message.lower()
        if any(word in message_lower for word in positive_words):
            sentiment = "positive"
        elif any(word in message_lower for word in negative_words):
            sentiment = "negative"
        
        # 이전 주제들
        previous_topics = []
        if conversation_history:
            previous_topics = [item.get("context", "general") for item in conversation_history[-5:]]
        
        # 미해결 질문들
        unresolved_questions = []
        for item in conversation_history[-3:]:  # 최근 3개 대화 확인
            if "?" in item.get("user_message", "") and item.get("intent") == "question":
                unresolved_questions.append(item["user_message"])
        
        return {
            "topic": topic,
            "sentiment": sentiment,
            "previous_topics": previous_topics,
            "unresolved_questions": unresolved_questions,
            "complexity": user_intent["complexity_level"],
            "session_length": len(conversation_history)
        }
    
    def _needs_clarification(self, context_analysis: Dict, user_intent: Dict) -> bool:
        """명확화 필요성 판단"""
        # 의도 신뢰도가 낮거나 모호한 경우
        if user_intent["confidence"] < 0.6:
            return True
        
        # 복잡한 질문이지만 컨텍스트가 부족한 경우
        if user_intent["complexity_level"] == "high" and context_analysis["session_length"] < 2:
            return True
        
        # 미해결 질문이 많은 경우
        if len(context_analysis["unresolved_questions"]) > 2:
            return True
        
        return False
    
    def _generate_direct_response(self, user_message: str, user_intent: Dict, context_analysis: Dict) -> ResponseCandidate:
        """직접적 답변 생성"""
        # 간단한 템플릿 기반 응답 (실제로는 LLM 사용)
        intent = user_intent["primary_intent"]
        
        response_templates = {
            "question": f"'{user_message}'에 대한 답변을 드리겠습니다. [구체적 답변 필요]",
            "request": f"요청하신 '{user_message}' 작업을 수행하겠습니다. [실행 계획 필요]",
            "information_seeking": f"'{context_analysis['topic']}' 관련 정보를 제공해드리겠습니다. [정보 검색 필요]",
            "instruction": f"지시하신 작업을 실행하겠습니다: {user_message}",
            "general": f"알겠습니다. {user_message}에 대해 도움을 드리겠습니다."
        }
        
        response_text = response_templates.get(intent, response_templates["general"])
        
        return ResponseCandidate(
            text=response_text,
            strategy="direct",
            confidence=0.8,
            estimated_satisfaction=0.7,
            reasoning="직접적이고 명확한 답변 제공"
        )
    
    def _generate_contextual_response(self, user_message: str, context_analysis: Dict, user_profile: Dict) -> ResponseCandidate:
        """맥락적 답변 생성"""
        topic = context_analysis["topic"]
        sentiment = context_analysis["sentiment"]
        previous_topics = context_analysis["previous_topics"]
        
        # 컨텍스트를 고려한 응답
        context_intro = ""
        if previous_topics and topic in previous_topics:
            context_intro = f"앞서 {topic}에 대해 이야기했던 것과 관련해서, "
        
        sentiment_tone = {
            "positive": "기쁘게 ",
            "negative": "신중하게 ",
            "neutral": ""
        }
        
        response_text = f"{context_intro}{sentiment_tone.get(sentiment, '')}'{user_message}'에 대해 도움을 드리겠습니다. [맥락 기반 상세 답변 필요]"
        
        return ResponseCandidate(
            text=response_text,
            strategy="contextual",
            confidence=0.75,
            estimated_satisfaction=0.8,
            reasoning="대화 맥락과 사용자 감정을 고려한 응답"
        )
    
    def _generate_educational_response(self, user_message: str, user_intent: Dict) -> ResponseCandidate:
        """교육적 답변 생성"""
        response_text = f"'{user_message}'는 복잡한 주제입니다. 단계별로 설명해드리겠습니다:\n\n1. 기본 개념 설명\n2. 구체적 방법론\n3. 실제 적용 예시\n4. 추가 학습 자료\n\n[각 단계별 상세 내용 필요]"
        
        return ResponseCandidate(
            text=response_text,
            strategy="educational",
            confidence=0.7,
            estimated_satisfaction=0.85,
            reasoning="복잡한 주제에 대한 체계적이고 교육적인 답변"
        )
    
    def _generate_clarifying_response(self, user_message: str, context_analysis: Dict) -> ResponseCandidate:
        """명확화 답변 생성"""
        unresolved = context_analysis["unresolved_questions"]
        
        clarification_text = f"'{user_message}'에 대해 더 정확한 도움을 드리기 위해 몇 가지 확인하고 싶습니다:\n\n"
        
        if unresolved:
            clarification_text += "먼저 이전 질문들에 대한 답변이 충분했는지 확인해주세요.\n\n"
        
        clarification_text += "구체적으로 어떤 부분에 대한 도움이 필요하신지 알려주시겠어요?"
        
        return ResponseCandidate(
            text=clarification_text,
            strategy="clarifying",
            confidence=0.9,
            estimated_satisfaction=0.75,
            reasoning="모호한 요청에 대한 명확화 질문으로 정확한 도움 제공"
        )
    
    def _evaluate_response_candidate(self, candidate: Dict, user_intent: Dict, context_analysis: Dict, user_profile: Dict) -> Dict:
        """응답 후보 평가"""
        # 기본 점수
        scores = {
            "relevance": 0.7,
            "helpfulness": 0.7,
            "clarity": 0.7,
            "engagement": 0.7
        }
        
        # 전략별 보정
        strategy = candidate["strategy"]
        intent = user_intent["primary_intent"]
        complexity = user_intent["complexity_level"]
        
        if strategy == "direct" and intent in ["question", "request"]:
            scores["relevance"] += 0.2
            scores["helpfulness"] += 0.15
        
        if strategy == "contextual" and context_analysis["session_length"] > 3:
            scores["engagement"] += 0.2
            scores["relevance"] += 0.1
        
        if strategy == "educational" and complexity == "high":
            scores["helpfulness"] += 0.25
            scores["clarity"] += 0.1
        
        if strategy == "clarifying" and user_intent["confidence"] < 0.6:
            scores["helpfulness"] += 0.3
        
        # 전체 점수 계산
        overall_score = sum(scores.values()) / len(scores)
        
        return {
            **scores,
            "overall_score": overall_score
        }
    
    def _calculate_quality_metrics(self, response: Dict, user_intent: Dict, context_analysis: Dict) -> Dict:
        """품질 메트릭 계산"""
        response_text = response["text"]
        strategy = response["strategy"]
        
        metrics = {
            "relevance": 0.7,
            "helpfulness": 0.7,
            "clarity": 0.7,
            "engagement": 0.7,
            "accuracy": 0.8
        }
        
        # 길이 기반 조정
        text_length = len(response_text)
        if 50 <= text_length <= 500:
            metrics["clarity"] += 0.1
        elif text_length > 1000:
            metrics["clarity"] -= 0.1
        
        # 전략 기반 조정
        if strategy == "educational":
            metrics["helpfulness"] += 0.1
        elif strategy == "clarifying":
            metrics["engagement"] += 0.1
        
        # 컨텍스트 적합성
        if context_analysis["sentiment"] == "negative" and "신중하게" in response_text:
            metrics["engagement"] += 0.15
        
        return metrics
    
    def _predict_user_satisfaction(self, quality_metrics: Dict, user_intent: Dict) -> float:
        """사용자 만족도 예측"""
        # 의도별 가중치
        intent_weights = {
            "question": {"helpfulness": 0.4, "accuracy": 0.3, "clarity": 0.3},
            "request": {"helpfulness": 0.5, "accuracy": 0.3, "engagement": 0.2},
            "information_seeking": {"accuracy": 0.4, "relevance": 0.3, "clarity": 0.3},
            "general": {"engagement": 0.3, "helpfulness": 0.3, "clarity": 0.2, "relevance": 0.2}
        }
        
        intent = user_intent["primary_intent"]
        weights = intent_weights.get(intent, intent_weights["general"])
        
        satisfaction = 0.0
        for metric, weight in weights.items():
            satisfaction += quality_metrics.get(metric, 0.7) * weight
        
        return min(satisfaction, 1.0)
    
    def _improve_response(self, response: Dict, quality_metrics: Dict, state: ConversationWorkflowState) -> Dict:
        """응답 개선"""
        improved_response = response.copy()
        
        # 낮은 점수 메트릭 개선
        low_metrics = [metric for metric, score in quality_metrics.items() if score < 0.6]
        
        improvements = []
        
        if "clarity" in low_metrics:
            improvements.append("명확성을 위해 구체적인 예시를 추가하겠습니다.")
        
        if "helpfulness" in low_metrics:
            improvements.append("더 실용적인 정보를 포함하겠습니다.")
        
        if "engagement" in low_metrics:
            improvements.append("더 친근하고 대화적인 톤으로 수정하겠습니다.")
        
        if improvements:
            improved_text = improved_response["text"] + "\n\n[개선사항: " + ", ".join(improvements) + "]"
            improved_response["text"] = improved_text
            improved_response["confidence"] += 0.1
            improved_response["estimated_satisfaction"] += 0.15
        
        return improved_response
    
    def _save_conversation_data(self, state: ConversationWorkflowState) -> List[str]:
        """대화 데이터 저장"""
        conversation_id = state["conversation_id"]
        timestamp = datetime.now(self.kst).strftime('%Y%m%d_%H%M%S')
        
        output_dir = Path("C:/Users/user/Dropbox/_RAG/RAG_Chat/Conversations")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        saved_files = []
        
        # 1. 대화 내용 저장 (TXT)
        conversation_file = output_dir / f"{timestamp}_{conversation_id}_conversation.txt"
        conversation_content = self._format_conversation_for_saving(state)
        
        with open(conversation_file, 'w', encoding='utf-8') as f:
            f.write(conversation_content)
        saved_files.append(str(conversation_file))
        
        # 2. 메타데이터 저장 (JSON)
        metadata_file = output_dir / f"{timestamp}_{conversation_id}_metadata.json"
        metadata = {
            "conversation_id": conversation_id,
            "timestamp": timestamp,
            "user_intent": state["user_intent"],
            "context_analysis": state["context_analysis"],
            "quality_metrics": state["quality_metrics"],
            "satisfaction_score": state["satisfaction_score"],
            "conversation_metadata": state["conversation_metadata"]
        }
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        saved_files.append(str(metadata_file))
        
        # 3. 학습 데이터 저장
        learning_file = output_dir / f"{timestamp}_{conversation_id}_learning.json"
        with open(learning_file, 'w', encoding='utf-8') as f:
            json.dump(state["learning_data"], f, ensure_ascii=False, indent=2)
        saved_files.append(str(learning_file))
        
        return saved_files
    
    def _format_conversation_for_saving(self, state: ConversationWorkflowState) -> str:
        """저장용 대화 포맷팅"""
        content = f"""대화 기록 | {datetime.now(self.kst).strftime('%Y년 %m월 %d일 %H:%M')}

=== 대화 정보 ===
대화 ID: {state["conversation_id"]}
사용자 의도: {state["user_intent"]["primary_intent"]} (신뢰도: {state["user_intent"]["confidence"]:.2f})
주제: {state["context_analysis"]["topic"]}
감정: {state["context_analysis"]["sentiment"]}
품질 점수: {sum(state["quality_metrics"].values()) / len(state["quality_metrics"]):.2f}
만족도 예측: {state["satisfaction_score"]:.2f}

=== 대화 내용 ===
👤 사용자: {state["user_message"]}

🤖 AI민진 ({state["selected_response"]["strategy"]} 전략): 
{state["selected_response"]["text"]}

=== 응답 후보들 ===
"""
        
        for i, candidate in enumerate(state["response_candidates"], 1):
            content += f"\n{i}. {candidate['strategy']} 전략 (점수: {candidate.get('evaluation', {}).get('overall_score', 0):.2f})\n"
            content += f"   {candidate['text'][:100]}...\n"
        
        content += f"\n=== 학습 데이터 ===\n"
        content += f"추출된 학습 데이터: {len(state['learning_data'])}개\n"
        
        return content
    
    def _update_learning_system(self, learning_data: List[Dict]):
        """학습 시스템 업데이트"""
        # 실제 구현에서는 ML 모델 업데이트 또는 규칙 개선
        logger.info(f"학습 시스템 업데이트: {len(learning_data)}개 데이터 처리")
    
    def _calculate_conversation_metrics(self, state: ConversationWorkflowState) -> Dict:
        """대화 성능 메트릭 계산"""
        return {
            "response_time": "실시간 측정 필요",
            "intent_confidence": state["user_intent"]["confidence"],
            "quality_score": sum(state["quality_metrics"].values()) / len(state["quality_metrics"]),
            "predicted_satisfaction": state["satisfaction_score"],
            "strategy_used": state["selected_response"]["strategy"],
            "improvement_applied": state["conversation_metadata"].get("response_improved", False),
            "learning_data_count": len(state["learning_data"])
        }

# ============================================================================
# 조건부 판단 함수들
# ============================================================================

def decide_after_context_analysis(state: ConversationWorkflowState) -> str:
    """컨텍스트 분석 후 다음 단계 결정"""
    requires_clarification = state["requires_clarification"]
    
    if requires_clarification:
        return "generate_clarifying"
    else:
        return "generate_responses"

def decide_after_response_selection(state: ConversationWorkflowState) -> str:
    """응답 선택 후 다음 단계 결정"""
    selected_response = state["selected_response"]
    confidence = selected_response.get("confidence", 0.0)
    
    if confidence >= 0.8:
        return "evaluate_quality"
    else:
        return "improve_response"

def decide_after_quality_evaluation(state: ConversationWorkflowState) -> str:
    """품질 평가 후 다음 단계 결정"""
    satisfaction_score = state["satisfaction_score"]
    quality_metrics = state["quality_metrics"]
    
    # 품질이 매우 낮으면 개선 필요
    overall_quality = sum(quality_metrics.values()) / len(quality_metrics)
    
    if overall_quality < 0.6 or satisfaction_score < 0.7:
        return "improve_response"
    else:
        return "finalize_response"

def decide_after_improvement(state: ConversationWorkflowState) -> str:
    """개선 후 다음 단계 결정"""
    response_improved = state["conversation_metadata"].get("response_improved", False)
    
    if response_improved:
        return "finalize_response"
    else:
        return "finalize_response"  # 개선이 안되어도 진행

# ============================================================================
# LangGraph 워크플로우 구성
# ============================================================================

class LangGraphIntelligentConversationSystem:
    """LangGraph 기반 지능형 대화 시스템"""
    
    def __init__(self, base_path: str = "C:/Users/user/Dropbox/_RAG"):
        self.base_path = Path(base_path)
        self.conversations_dir = self.base_path / "RAG_Chat" / "Conversations"
        self.conversations_dir.mkdir(parents=True, exist_ok=True)
        
        # LangGraph 설정
        self.memory = MemorySaver()
        self.workflow_nodes = ConversationWorkflowNodes(self)
        self.workflow = self._create_workflow()
        
        logger.info("LangGraph Intelligent Conversation System 초기화 완료")
    
    def _create_workflow(self) -> StateGraph:
        """LangGraph 워크플로우 생성"""
        workflow = StateGraph(ConversationWorkflowState)
        
        # 노드 추가
        workflow.add_node("analyze_intent", self.workflow_nodes.analyze_user_intent)
        workflow.add_node("analyze_context", self.workflow_nodes.analyze_conversation_context)
        workflow.add_node("generate_responses", self.workflow_nodes.generate_response_candidates)
        workflow.add_node("select_response", self.workflow_nodes.select_best_response)
        workflow.add_node("evaluate_quality", self.workflow_nodes.evaluate_response_quality)
        workflow.add_node("improve_response", self.workflow_nodes.improve_response_if_needed)
        workflow.add_node("update_history", self.workflow_nodes.update_conversation_history)
        workflow.add_node("extract_learning", self.workflow_nodes.extract_learning_data)
        workflow.add_node("save_and_learn", self.workflow_nodes.save_conversation_and_learn)
        
        # 시작점 설정
        workflow.set_entry_point("analyze_intent")
        
        # 엣지 연결
        workflow.add_edge("analyze_intent", "analyze_context")
        
        workflow.add_conditional_edges(
            "analyze_context",
            decide_after_context_analysis,
            {
                "generate_responses": "generate_responses",
                "generate_clarifying": "generate_responses"  # 명확화도 응답 생성으로
            }
        )
        
        workflow.add_edge("generate_responses", "select_response")
        
        workflow.add_conditional_edges(
            "select_response",
            decide_after_response_selection,
            {
                "evaluate_quality": "evaluate_quality",
                "improve_response": "improve_response"
            }
        )
        
        workflow.add_conditional_edges(
            "evaluate_quality",
            decide_after_quality_evaluation,
            {
                "improve_response": "improve_response",
                "finalize_response": "update_history"
            }
        )
        
        workflow.add_conditional_edges(
            "improve_response",
            decide_after_improvement,
            {
                "finalize_response": "update_history"
            }
        )
        
        workflow.add_edge("update_history", "extract_learning")
        workflow.add_edge("extract_learning", "save_and_learn")
        workflow.add_edge("save_and_learn", END)
        
        return workflow.compile(checkpointer=self.memory)
    
    async def process_conversation(self, user_message: str, conversation_id: str = None, thread_id: str = None, conversation_history: List[Dict] = None) -> Dict:
        """대화 처리 실행"""
        if conversation_id is None:
            conversation_id = f"conv_{hashlib.md5(user_message.encode()).hexdigest()[:8]}"
        
        if thread_id is None:
            thread_id = f"chat_{conversation_id}_{int(datetime.now().timestamp())}"
        
        if conversation_history is None:
            conversation_history = []
        
        # 초기 상태 설정
        initial_state = {
            "conversation_id": conversation_id,
            "user_message": user_message,
            "conversation_history": conversation_history,
            "user_intent": {},
            "context_analysis": {},
            "response_candidates": [],
            "selected_response": {},
            "quality_metrics": {},
            "messages": [],
            "user_profile": {},
            "conversation_metadata": {},
            "requires_clarification": False,
            "learning_data": [],
            "satisfaction_score": 0.0
        }
        
        # 워크플로우 실행
        config = {
            "configurable": {
                "thread_id": thread_id,
                "recursion_limit": 25
            }
        }
        
        try:
            result = await self.workflow.ainvoke(initial_state, config)
            
            logger.info(f"대화 처리 완료: {user_message[:50]}... - 만족도 {result['satisfaction_score']:.2f}")
            
            return result
            
        except Exception as e:
            logger.error(f"대화 워크플로우 실행 오류: {e}")
            return {"error": str(e), "user_message": user_message}

# ============================================================================
# 사용 예제
# ============================================================================

async def main():
    """사용 예제"""
    conversation_system = LangGraphIntelligentConversationSystem()
    
    # 테스트 대화들
    test_conversations = [
        "LangGraph가 뭐야?",
        "OCR 시스템을 어떻게 개선할 수 있을까?",
        "파일을 자동으로 처리하는 시스템을 만들어줘",
        "이전에 말한 내용 기억해?"
    ]
    
    conversation_history = []
    
    for user_message in test_conversations:
        print(f"\n=== 사용자: {user_message} ===")
        
        result = await conversation_system.process_conversation(
            user_message=user_message,
            conversation_history=conversation_history
        )
        
        if "error" not in result:
            response = result["selected_response"]["text"]
            print(f"AI민진: {response[:200]}...")
            
            print(f"\n📊 메트릭:")
            print(f"  - 의도: {result['user_intent']['primary_intent']} (신뢰도: {result['user_intent']['confidence']:.2f})")
            print(f"  - 전략: {result['selected_response']['strategy']}")
            print(f"  - 품질: {sum(result['quality_metrics'].values()) / len(result['quality_metrics']):.2f}")
            print(f"  - 만족도: {result['satisfaction_score']:.2f}")
            
            # 히스토리 업데이트
            conversation_history = result["conversation_history"]
            
        else:
            print(f"오류: {result['error']}")

if __name__ == "__main__":
    asyncio.run(main())