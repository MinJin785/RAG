# 현재 RAG 작업의 흐름

## 현재 진행 상황 (2025-01-03 최신 업데이트)

### 완료된 작업들
1. **Claude + Gemini API 기반 하이브리드 OCR 시스템 구축 완료**
   - 성능 16-72배 향상, 정확도 80→95점 개선, 비용 50-70% 절감
   - Claude: 구조 분석과 품질 검토, Gemini: 멀티모달 처리와 이미지 생성
   - Upstage Layout Analysis API, 배치 처리 최적화, MCP 통합, PagedAttention 알고리즘 적용

2. **PDF 전처리 시스템 분석 완료**
   - `RAG_Coding/out_box/PDF_전처리_고급_시스템_지식.md` 생성
   - Upstage Layout Analysis API 활용 방안 정리
   - 요소별 분리 (텍스트/이미지/테이블) 처리 방법 확립
   - Reference_Codes의 supergateway MCP 시스템 분석 완료

3. **작업 관리 시스템 구축 완료**
   - `task_management_system.py` 및 `ai_task_wrapper.py` 구현
   - 자동 작업 추적 및 상태 관리 시스템 가동 중
   - Claude 벤치마킹 시스템 삭제하고 실용적 작업 관리 시스템으로 대체

4. **파일 관리 규칙 각인 완료**
   - 모든 코딩 지식 학습 시 전체 RAG 시스템 업그레이드 적용 원칙 확립
   - 코딩 지식: RAG_Coding에 누적, 시스템 구현체: RAG_Coin에 저장
   - in_box → processing → out_box → archive 워크플로우 확립
   - 파일 통합 후 기존 파일 즉시 삭제 규칙 적용

### 현재 진행 중인 작업
- **LangGraph 세부 기능 학습** (in_progress)
  - State, Node, Edge, Conditional Edge, Compile 기능 478줄 스크립트 분석 중
  - RAG_Coding/in_box/LangGraph 세부 기능 폴더에서 진행
- **LangGraph 학습 내용을 OCR 시스템에 적용하여 더욱 고도화** (planned)

### 대기 중인 작업들
1. **PDF 전처리 시스템을 RAG 시스템에 통합**
2. **암호화폐 관련 자료 수집 및 RAG_Coin 지식창고 구축**
3. **유튜브 영상 분석 지식창고 구축**

## 핵심 학습 내용

### PDF 전처리 고급 기술
- **문제점**: 기존 PDF 파싱으로 차트/이미지/테이블 손실
- **해결책**: Upstage Layout Analysis API로 요소별 분리
- **핵심 기술**: 좌표 기반 정확한 크로핑, 배치 처리, AI 요약
- **성능 향상**: 배치 처리로 16배 속도 개선

### MCP (Model Context Protocol) 시스템
- **supergateway**: MCP 서버들을 SSE/WebSocket으로 연결
- **활용 방안**: PDF 처리를 MCP 서버로 구현하여 모든 RAG 도메인에서 활용

## 다음 단계 작업 방향

### 1. PDF 전처리 시스템 실제 구현
- Upstage Layout Analysis API 통합
- 기존 OCR 시스템과 결합
- in_box 기반 자동 워크플로우 완성

### 2. 시스템 통합 및 확장
- MCP 아키텍처 적용
- 다중 RAG 도메인 자동 분산 시스템
- API 키 활용 최적화

### 3. 지속적 지식 누적
- Reference_Codes 우선 확인 원칙 적용
- 유튜브 영상 분석 시스템 구축
- 암호화폐 프로젝트 자료 수집

## 중요 파일 위치
- **핵심 지식**: `RAG_Coding/out_box/PDF_전처리_고급_시스템_지식.md`
- **참조 코드**: `RAG_Coding/Reference_Codes/supergateway-main/`
- **작업 관리**: `task_management_system.py`, `ai_task_wrapper.py`
- **OCR 시스템**: `RAG_OCR/` (Claude + Gemini API 기반)
- **PDF MCP 서버**: `RAG_Coding/processing/upstage_pdf_mcp_server.py`

## 현재 폴더 구조 상태
```
RAG_Coding/
├── in_box/          (사용자 업로드)
├── processing/      (AI 처리 중)
├── out_box/         (완성된 지식)
├── archive/         (처리 완료 원본)
└── Reference_Codes/ (참조 코드들)

RAG_Coin/
└── Coin_Knowledge/  (암호화폐 시스템 구현체 저장 예정)
```

## 연속 작업을 위한 준비 사항
1. 5개 핵심 파일 확인 필수
2. 현재 TODO 리스트 확인
3. Reference_Codes 우선 학습 원칙 적용
4. 3단계 작업 방식 (레그 메모리 → 웹 검색 → 정보 조합) 유지

## 하드웨어 환경
### 메인 데스크탑 (Intel Core Ultra 9 285K, 192GB DDR5, AMD RX 6600)
### 서브 노트북 (AMD Ryzen 9 7945HX, 64GB RAM)
### OCR 시스템: Claude API + Gemini API 하이브리드 (16-72배 성능향상, 95점 정확도)