# Perplexity API 설정 가이드

## 1단계: API 키 발급
1. https://www.perplexity.ai/settings/api 방문
2. 계정 생성/로그인
3. "Create API Key" 클릭
4. API 키 복사 (pplx-로 시작)

## 2단계: 환경 설정
```bash
# 패키지 설치
pip install -r requirements.txt

# 환경변수 파일 생성
cp .env.example .env

# .env 파일에 API 키 입력
# PERPLEXITY_API_KEY=여기에_실제_API_키_입력
```

## 3단계: 테스트
```python
from perplexity_search import PerplexitySearcher

# API 키 자동 로드 (환경변수에서)
searcher = PerplexitySearcher()

# 테스트 검색
result = searcher.search_korean("대일외고 입시 정보")
print(result)
```

## 4단계: 블로그 특화 사용법

### 키워드 경쟁 분석
```python
from perplexity_search import search_blog_competition

result = search_blog_competition("대일외고 영어", searcher)
print(result)
```

### 수익화 트렌드 분석
```python
from perplexity_search import search_monetization_trends

result = search_monetization_trends("영어 학원", searcher)
print(result)
```

### 대일외고 최신 정보
```python
from perplexity_search import search_daeil_info

result = search_daeil_info(searcher)
print(result)
```

## 주의사항
- API 키는 절대 공개하지 마세요
- 월 사용량 제한 확인하세요 ($20 플랜 기준)
- .env 파일은 .gitignore에 추가하세요

## 비용 정보
- $20/월: 600 쿼리
- $200/월: 10,000 쿼리  
- 블로그 초기에는 $20 플랜으로 충분

## 에러 해결
- `ValueError: PERPLEXITY_API_KEY가 설정되지 않았습니다` 
  → .env 파일 확인 또는 환경변수 설정
  
- `API 요청 실패: 401`
  → API 키 확인, 계정 상태 확인