# API 키 설정 가이드

## Claude API 키 설정

### 1. Anthropic 계정 생성
1. [https://console.anthropic.com](https://console.anthropic.com) 방문
2. Google 계정으로 로그인 또는 새 계정 생성
3. 이메일 인증 완료

### 2. API 키 생성
1. Console에서 "Get API Keys" 클릭
2. "Create API Key" 선택
3. API 키 이름 입력 (예: `ANTHROPIC_API_KEY`)
4. 생성된 키 복사 및 안전한 곳에 저장

### 3. 환경변수 설정

#### Windows (PowerShell)
```powershell
$env:ANTHROPIC_API_KEY="your_claude_api_key_here"
```

#### Windows (영구 설정)
```powershell
setx ANTHROPIC_API_KEY "your_claude_api_key_here"
```

#### Linux/macOS
```bash
export ANTHROPIC_API_KEY="your_claude_api_key_here"
```

#### Linux/macOS (영구 설정)
```bash
echo 'export ANTHROPIC_API_KEY="your_claude_api_key_here"' >> ~/.bashrc
source ~/.bashrc
```

## Gemini API 키 설정

### 1. Google AI Studio 접속
1. [https://aistudio.google.com](https://aistudio.google.com) 방문
2. Google 계정으로 로그인

### 2. API 키 생성
1. 메뉴에서 "Get API key" 클릭
2. "Create API key in new project" 선택
3. 프로젝트 생성 후 API 키 복사

### 3. 환경변수 설정

#### Windows (PowerShell)
```powershell
$env:GOOGLE_API_KEY="your_gemini_api_key_here"
```

#### Windows (영구 설정)
```powershell
setx GOOGLE_API_KEY "your_gemini_api_key_here"
```

#### Linux/macOS
```bash
export GOOGLE_API_KEY="your_gemini_api_key_here"
```

#### Linux/macOS (영구 설정)
```bash
echo 'export GOOGLE_API_KEY="your_gemini_api_key_here"' >> ~/.bashrc
source ~/.bashrc
```

## .env 파일 사용 (추천)

1. RAG_OCR 폴더에 `.env` 파일 생성:
```env
ANTHROPIC_API_KEY=your_claude_api_key_here
GOOGLE_API_KEY=your_gemini_api_key_here
```

2. Python 코드에 dotenv 로드 추가:
```python
from dotenv import load_dotenv
load_dotenv()
```

## API 키 확인

### Python에서 확인
```python
import os
print("Claude API:", "✅" if os.getenv('ANTHROPIC_API_KEY') else "❌")
print("Gemini API:", "✅" if os.getenv('GOOGLE_API_KEY') else "❌")
```

### 터미널에서 확인
```bash
echo $ANTHROPIC_API_KEY
echo $GOOGLE_API_KEY
```

## 비용 정보

### Claude API
- Claude 3 Sonnet: 입력 $3/1M tokens, 출력 $15/1M tokens
- Claude 3.5 Haiku: 입력 $0.25/1M tokens, 출력 $1.25/1M tokens

### Gemini API
- Gemini 1.5 Flash: 입력 $0.075/1M tokens, 출력 $0.30/1M tokens
- Gemini 1.5 Pro: 입력 $1.25/1M tokens, 출력 $5.00/1M tokens

## 보안 주의사항

1. **절대 코드에 하드코딩 금지**
2. **환경변수 또는 .env 파일 사용**
3. **Git에 API 키 커밋 금지** (.gitignore에 .env 추가)
4. **정기적으로 키 교체**
5. **사용량 모니터링**

## 문제 해결

### API 키 인식 안됨
1. 환경변수 재설정
2. 터미널/IDE 재시작
3. 키 유효성 재확인

### API 호출 실패
1. 인터넷 연결 확인
2. API 키 유효성 확인
3. 요금 결제 상태 확인
4. Rate limit 확인