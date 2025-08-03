# LangGraph Core Knowledge 2025
## 학습 완료된 LangGraph 핵심 개념 및 구현 방법론

### 🎯 LangGraph 탄생 배경 및 혁신성

#### 기존 RAG의 한계점
- **단방향 파이프라인**: 한 번에 완벽하게 수행해야 함
- **고정된 구조**: 실행 중 동적 변경 불가
- **복잡한 체인 확장**: 덕지덕지 붙이는 방식의 한계
- **순환 불가능**: 뒤로 돌아가서 수정하는 로직 구현 어려움

#### LangGraph의 혁신적 해결책
- **양방향 워크플로우**: 순환 가능한 동적 구조
- **조건부 분기**: 상황에 따른 다중 경로 선택
- **상태 기반 통신**: 노드 간 독립적이면서 협력적 구조
- **체크포인트 메모리**: 과거 상태 저장 및 되돌리기 기능

### 🏗️ LangGraph 핵심 구성 요소

#### 1. State (상태 관리)
```python
from typing_extensions import TypedDict, Annotated
from langgraph.graph.message import add_messages

class GraphState(TypedDict):
    question: str
    context: str
    answer: str
    messages: Annotated[list, add_messages]  # Reducer 개념
    score: str
    
# 주요 특징:
# - TypedDict 기반 타입 안전성
# - Reducer(add_messages)로 리스트 자동 병합
# - 모든 값 채우지 않아도 됨 (선택적 필드)
# - 새로운 값이 기존 값 덮어쓰기 (Reducer 제외)
```

#### 2. Node (처리 노드)
```python
def document_retrieval_node(state: GraphState) -> GraphState:
    """문서 검색 노드 - 파이썬 함수로 구현"""
    question = state["question"]
    
    # 검색 로직 구현 (LangChain 외 기술도 자유롭게 사용 가능)
    documents = custom_retriever.search(question)
    
    return {
        "context": documents,
        "question": question  # 기존 값 유지
    }

# 핵심 원칙:
# - 입력: State → 출력: State
# - 파이썬 함수로 자유로운 로직 구현
# - LangChain 의존성 최소화 가능
```

#### 3. Edge (연결 관계)
```python
# 단순 연결
workflow.add_edge("retrieve", "generate_answer")

# 조건부 연결 (핵심 기능!)
workflow.add_conditional_edges(
    "evaluate_answer",           # 시작 노드
    decide_next_step,           # 판단 함수
    {
        "good": END,            # 조건별 다음 노드
        "bad_query": "rewrite_query",
        "bad_retrieval": "retrieve", 
        "bad_answer": "generate_answer"
    }
)
```

#### 4. Conditional Edge (조건부 분기)
```python
def decide_next_step(state: GraphState) -> str:
    """조건부 판단 함수"""
    score = state.get("score", "")
    
    if score == "good":
        return "good"
    elif "query" in score.lower():
        return "bad_query"
    elif "retrieval" in score.lower():
        return "bad_retrieval"
    else:
        return "bad_answer"
```

#### 5. Compile & Execution
```python
from langgraph.graph import StateGraph
from langgraph.checkpoint.memory import MemorySaver

# 그래프 생성
workflow = StateGraph(GraphState)

# 노드 추가
workflow.add_node("retrieve", document_retrieval_node)
workflow.add_node("generate", answer_generation_node)
workflow.add_node("evaluate", evaluation_node)

# 엣지 추가
workflow.set_entry_point("retrieve")
workflow.add_edge("retrieve", "generate")
workflow.add_conditional_edges("evaluate", decide_next_step, path_map)

# 컴파일 (메모리 체크포인트 포함)
memory = MemorySaver()
app = workflow.compile(checkpointer=memory)

# 실행
config = {
    "configurable": {
        "thread_id": "conversation_1",
        "recursion_limit": 50
    }
}

result = app.invoke({
    "question": "생성형 AI 가우스를 만든 회사의 2023년 매출액은?"
}, config)
```

### 🔄 LangGraph 워크플로우 패턴

#### 1. 기본 RAG 개선 패턴
```
질문 입력 → 문서 검색 → 관련성 평가 → [분기]
                                    ↓
                              관련성 있음 → 답변 생성 → 종료
                                    ↓
                              관련성 없음 → 쿼리 재작성 → 문서 재검색
```

#### 2. 품질 보장 패턴
```
답변 생성 → 품질 평가 → [분기]
                      ↓
               품질 좋음 → 종료
                      ↓
               쿼리 문제 → 쿼리 재작성
               검색 문제 → 문서 재검색  
               답변 문제 → 답변 재생성
```

#### 3. 정보 보강 패턴
```
문서 검색 → 정보 충분성 평가 → [분기]
                            ↓
                    충분함 → 답변 생성
                            ↓
                    부족함 → 웹 검색 → 정보 보강 → 답변 생성
```

### 🎯 RAG 시스템별 LangGraph 적용 방안

#### 1. 작업 관리 시스템
- **상태**: Task 정보, 의존성, 진행률
- **노드**: 작업 생성, 상태 전환, 의존성 체크, 알림
- **조건부 엣지**: 우선순위 기반 자동 할당, 블로커 해결

#### 2. 검색 시스템
- **상태**: 검색 쿼리, 결과, 품질 점수, 사용자 만족도
- **노드**: 검색 실행, 결과 평가, 재검색, 결과 정제
- **조건부 엣지**: 품질 기반 재검색 여부 결정

#### 3. OCR 시스템
- **상태**: 문서 타입, 처리 단계, 텍스트 품질, 검증 결과
- **노드**: 레이아웃 분석, OCR 실행, 품질 검증, 후처리
- **조건부 엣지**: 문서 타입별 처리 경로, 품질 기반 재처리

#### 4. 대화 시스템
- **상태**: 대화 히스토리, 의도 파악, 응답 품질
- **노드**: 의도 분석, 응답 생성, 품질 체크, 사용자 피드백 처리
- **조건부 엣지**: 의도별 처리 경로, 만족도 기반 재응답

### 🚀 LangGraph + MCP 통합 아키텍처

#### 하이브리드 접근법
```python
class MCPLangGraphSystem:
    """MCP 서버들을 LangGraph 노드로 통합"""
    
    def __init__(self):
        self.mcp_clients = {
            'claude_ocr': MCPClient('claude_ocr_server'),
            'gemini_vision': MCPClient('gemini_vision_server'),
            'layout_analyzer': MCPClient('layout_analysis_server')
        }
        
    def create_mcp_node(self, server_name: str):
        """MCP 서버를 LangGraph 노드로 변환"""
        def mcp_node(state: GraphState) -> GraphState:
            client = self.mcp_clients[server_name]
            result = client.call_tool(state)
            return {**state, **result}
        return mcp_node
```

### 📈 성능 최적화 고려사항

#### 1. 메모리 관리
- 체크포인트 활용한 상태 영속성
- 스레드 ID 기반 세션 분리
- 메모리 사용량 모니터링

#### 2. 순환 제어
- recursion_limit 설정으로 무한 루프 방지
- 품질 임계값 기반 조기 종료
- 비용 최적화 로직

#### 3. 병렬 처리
- 독립적 노드들의 동시 실행
- 배치 처리 최적화
- 리소스 풀링

### 🎯 구현 우선순위

1. **Phase 1**: 작업 관리 시스템 LangGraph 변환
2. **Phase 2**: 검색 시스템 워크플로우 개선
3. **Phase 3**: OCR 시스템 복합 워크플로우 구현
4. **Phase 4**: MCP + LangGraph 완전 통합
5. **Phase 5**: 전체 RAG 시스템 LangGraph 기반 재구축

이는 테디노트 LangGraph 강의에서 학습한 핵심 내용을 바탕으로 RAG 전체 시스템 업그레이드를 위한 실용적 지식베이스입니다.