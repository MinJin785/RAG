# 🧠 웹 Cursor → 데스크탑 Cursor 작업 지침

## 📅 마지막 업데이트: 2025-07-30

## 🎯 현재 우선순위 작업

### ⚡ 즉시 실행 필요
1. **Chainlit 설치**
   ```bash
   pip install -r requirements.txt
   ```
   - 실행 위치: 프로젝트 루트 디렉토리
   - 예상 시간: 2-3분
   - 완료 후: `cursor_app_status.json`에서 `chainlit_installed: true` 설정

### 🔄 순차 실행 계획
2. **Perplexity API 통합**
   - 파일: `core/search_engine.py`
   - 작업: AdvancedSearchEngine 클래스 추가
   - 상세 코드는 아래 참조

3. **이미지 업로드 기능**
   - 파일: `main.py`
   - 작업: Vision API 통합

## 📝 상세 구현 가이드

### Perplexity API 통합 코드:
```python
# core/search_engine.py에 추가할 클래스
class AdvancedSearchEngine:
    def __init__(self):
        self.google_search = GoogleCustomSearch()
        self.perplexity_api_key = os.getenv("PERPLEXITY_API_KEY")
        
    async def smart_search(self, query: str, context: str = None):
        """상황에 맞는 최적 검색 엔진 선택"""
        if context and "실시간" in query:
            return await self.perplexity_search(query, context)
        else:
            return await self.google_search.search_web(query)
    
    async def perplexity_search(self, query: str, context: str = None):
        # Perplexity API 호출 로직
        pass
```

## 🚨 주의사항
- 각 작업 완료 후 `cursor_app_status.json` 업데이트 필수
- 에러 발생시 즉시 `issues_encountered`에 기록
- 궁금한 점은 `to_web_cursor.message`에 질문 작성

## 📊 진행 상황 체크리스트
- [ ] Chainlit 설치 완료
- [ ] requirements.txt 의존성 모두 설치
- [ ] 애플리케이션 정상 실행 확인
- [ ] Perplexity API 키 설정
- [ ] AdvancedSearchEngine 클래스 구현
- [ ] 이미지 업로드 기능 테스트

## 💬 소통 프로토콜
1. **작업 시작시**: `work_log.session_start` 업데이트
2. **작업 완료시**: `completed_tasks`에 추가
3. **문제 발생시**: `issues_encountered`에 상세 기록
4. **도움 필요시**: `next_help_needed`에 구체적 요청사항 작성