"""
두 번째 Perplexity 검색: 외고 영어 내신 준비 방법
"""

import requests
import json

def search_foreign_language_prep():
    api_key = "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"
    
    url = "https://api.perplexity.ai/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "sonar",
        "messages": [
            {
                "role": "user",
                "content": "외국어고등학교 영어 내신 준비 방법과 공통영어, 심화영어 교재에 대해 자세히 알려주세요. 특히 대일외고 영어 내신 대비 방법과 교재 정보를 포함해서 설명해주세요."
            }
        ],
        "max_tokens": 1000
    }
    
    print("🔍 [2/30] 외고 영어 내신 준비 방법 검색 중...")
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            print("✅ 검색 성공!")
            print("=" * 60)
            print(content)
            print("=" * 60)
            
            # 파일로 저장
            with open("search_2_result.md", "w", encoding="utf-8") as f:
                f.write("# 외고 영어 내신 준비 방법 검색 결과\n\n")
                f.write(content)
            
            print("\n📁 결과가 search_2_result.md에 저장되었습니다!")
            
        else:
            print(f"❌ API 오류: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ 에러 발생: {e}")

if __name__ == "__main__":
    search_foreign_language_prep()