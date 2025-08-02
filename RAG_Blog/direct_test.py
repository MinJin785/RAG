"""
직접 API 키로 Perplexity 테스트
"""

import requests
import json

def test_direct_research():
    api_key = "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"
    
    url = "https://api.perplexity.ai/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # 고등어닷컴 학원 리서치
    payload = {
        "model": "sonar",
        "messages": [
            {
                "role": "user",
                "content": "고등어닷컴 영어수학 학원에 대해 알려주세요. 대일외고 입시와 관련된 정보도 포함해서 자세히 조사해주세요."
            }
        ],
        "max_tokens": 1000
    }
    
    print("🔍 고등어닷컴 학원 리서치 시작...")
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            print("✅ 리서치 성공!")
            print("=" * 60)
            print(content)
            print("=" * 60)
            
            # 파일로 저장
            with open("research_result.md", "w", encoding="utf-8") as f:
                f.write("# 고등어닷컴 학원 리서치 결과\n\n")
                f.write(content)
            
            print("\n📁 결과가 research_result.md에 저장되었습니다!")
            
        else:
            print(f"❌ API 오류: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ 에러 발생: {e}")

if __name__ == "__main__":
    test_direct_research()