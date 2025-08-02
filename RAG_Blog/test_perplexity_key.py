"""
Perplexity API 키 테스트
받은 API 키가 실제로 작동하는지 확인
"""

import requests
import os
from dotenv import load_dotenv

def test_perplexity_api_key(api_key: str):
    """
    Perplexity API 키 테스트
    """
    print(f"🔑 API 키 테스트: {api_key[:10]}...")
    
    url = "https://api.perplexity.ai/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # 간단한 테스트 요청 (최신 모델명 사용)
    payload = {
        "model": "sonar",
        "messages": [
            {
                "role": "user",
                "content": "안녕하세요. API 테스트입니다."
            }
        ],
        "max_tokens": 100
    }
    
    try:
        print("📡 API 요청 전송 중...")
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        print(f"📊 응답 상태: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            content = data['choices'][0]['message']['content']
            print("✅ API 키 정상 작동!")
            print(f"🤖 응답: {content}")
            return True
            
        elif response.status_code == 401:
            print("❌ 인증 실패: API 키가 잘못되었거나 권한이 없습니다.")
            print("💡 가능한 원인:")
            print("   1. Pro 구독은 했지만 API 권한이 없음")
            print("   2. API 키가 잘못 복사됨")
            print("   3. 별도 API 구독 필요")
            return False
            
        elif response.status_code == 402:
            print("❌ 결제 필요: API 사용을 위한 별도 결제가 필요합니다.")
            return False
            
        elif response.status_code == 429:
            print("❌ 사용량 초과: API 한도를 초과했습니다.")
            return False
            
        else:
            print(f"❌ 알 수 없는 오류: {response.status_code}")
            print(f"📄 응답: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("⏰ 요청 시간 초과")
        return False
    except requests.exceptions.RequestException as e:
        print(f"🌐 네트워크 오류: {e}")
        return False
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
        return False

def check_api_subscription_status(api_key: str):
    """API 구독 상태 확인"""
    print("\n🔍 API 구독 상태 확인 중...")
    
    # 사용량 확인 엔드포인트 (있다면)
    usage_url = "https://api.perplexity.ai/usage"  # 실제 엔드포인트는 다를 수 있음
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    
    try:
        response = requests.get(usage_url, headers=headers)
        if response.status_code == 200:
            print("📊 사용량 정보:")
            print(response.json())
        else:
            print(f"⚠️ 사용량 정보 확인 불가: {response.status_code}")
    except:
        print("⚠️ 사용량 정보 확인 API 없음")

if __name__ == "__main__":
    # API 키 직접 테스트
    api_key = "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"
    
    print("🧪 Perplexity API 키 테스트")
    print("=" * 50)
    
    # 기본 API 테스트
    success = test_perplexity_api_key(api_key)
    
    if success:
        print("\n🎉 좋은 소식! API 키가 정상 작동합니다!")
        print("📝 이제 블로그 리서치에 바로 사용할 수 있어요.")
        
        # 구독 상태 확인
        check_api_subscription_status(api_key)
        
    else:
        print("\n💡 해결 방법:")
        print("1. Perplexity 웹사이트에서 API 전용 구독 확인")
        print("2. 설정 > API에서 API 키 재생성")
        print("3. 고객지원에 문의")
        print("\n🔄 대안: Google Custom Search API 사용 (무료)")
    
    print("\n" + "=" * 50)