"""
PDF 전처리 MCP 서버 설정 및 테스트 스크립트
"""

import os
import sys
import subprocess
from pathlib import Path
import json

def install_dependencies():
    """필요한 의존성 설치"""
    print("PDF 전처리 MCP 서버 의존성 설치 중...")
    
    try:
        # requirements 파일 경로
        req_file = Path(__file__).parent / "requirements_pdf_mcp.txt"
        
        # pip install 실행
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", str(req_file)
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ 의존성 설치 완료")
        else:
            print(f"❌ 의존성 설치 실패: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ 설치 중 오류 발생: {str(e)}")
        return False
    
    return True

def setup_environment():
    """환경 설정"""
    print("\n환경 설정 중...")
    
    # .env 파일 생성
    env_file = Path(__file__).parent / ".env"
    
    if not env_file.exists():
        print("UPSTAGE_API_KEY 설정이 필요합니다.")
        print("https://console.upstage.ai/ 에서 API 키를 발급받으세요.")
        
        api_key = input("Upstage API 키를 입력하세요 (입력하지 않으면 나중에 설정): ").strip()
        
        env_content = f"""# PDF 전처리 MCP 서버 환경 설정
UPSTAGE_API_KEY={api_key}

# 선택적 설정
BATCH_SIZE=100
SERVER_HOST=localhost
SERVER_PORT=8000
"""
        
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(env_content)
        
        print(f"✅ 환경 파일 생성: {env_file}")
    else:
        print("✅ 환경 파일이 이미 존재합니다.")
    
    # 디렉토리 구조 생성
    base_path = Path("C:/Users/user/Dropbox/_RAG/RAG_Coding")
    directories = ["in_box", "processing", "out_box", "archive"]
    
    for dir_name in directories:
        dir_path = base_path / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"✅ 디렉토리 생성: {dir_path}")

def create_test_config():
    """테스트용 설정 파일 생성"""
    print("\n테스트 설정 파일 생성 중...")
    
    config = {
        "server": {
            "host": "localhost",
            "port": 8000,
            "debug": True
        },
        "upstage": {
            "api_key_env": "UPSTAGE_API_KEY",
            "split_mode": "page",
            "batch_size": 100
        },
        "paths": {
            "in_box": "C:/Users/user/Dropbox/_RAG/RAG_Coding/in_box",
            "processing": "C:/Users/user/Dropbox/_RAG/RAG_Coding/processing",
            "out_box": "C:/Users/user/Dropbox/_RAG/RAG_Coding/out_box",
            "archive": "C:/Users/user/Dropbox/_RAG/RAG_Coding/archive"
        }
    }
    
    config_file = Path(__file__).parent / "config.json"
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 설정 파일 생성: {config_file}")

def create_start_script():
    """서버 시작 스크립트 생성"""
    print("\n시작 스크립트 생성 중...")
    
    start_script = """@echo off
echo PDF 전처리 MCP 서버 시작...

REM 환경 변수 로드
if exist .env (
    for /f "tokens=1,2 delims==" %%a in (.env) do (
        if not "%%a"=="" if not "%%b"=="" (
            set %%a=%%b
        )
    )
)

REM API 키 확인
if "%UPSTAGE_API_KEY%"=="" (
    echo 오류: UPSTAGE_API_KEY가 설정되지 않았습니다.
    echo .env 파일에 API 키를 설정하거나 환경변수로 설정하세요.
    pause
    exit /b 1
)

REM 서버 실행
python upstage_pdf_mcp_server.py

pause
"""
    
    script_file = Path(__file__).parent / "start_server.bat"
    with open(script_file, 'w', encoding='utf-8') as f:
        f.write(start_script)
    
    print(f"✅ 시작 스크립트 생성: {script_file}")

def main():
    """메인 설정 함수"""
    print("=== PDF 전처리 MCP 서버 설정 ===")
    
    # 1. 의존성 설치
    if not install_dependencies():
        print("❌ 설정 실패: 의존성 설치 오류")
        return
    
    # 2. 환경 설정
    setup_environment()
    
    # 3. 설정 파일 생성
    create_test_config()
    
    # 4. 시작 스크립트 생성
    create_start_script()
    
    print("\n=== 설정 완료 ===")
    print("다음 단계:")
    print("1. .env 파일에서 UPSTAGE_API_KEY 확인")
    print("2. start_server.bat 실행 또는")
    print("3. python upstage_pdf_mcp_server.py 직접 실행")
    print("\n테스트 방법:")
    print("- in_box 폴더에 PDF 파일 넣고 http://localhost:8000/process_inbox 호출")
    print("- 또는 http://localhost:8000/process_pdf?file_path=파일경로 직접 호출")

if __name__ == "__main__":
    main()