"""
새로운 구글 API 키 테스트
"""

import requests

def test_new_google_api():
    # 새로운 API 키
    api_key = "AIzaSyBIBZNgGd_i_aG2IhlqFQqhl0MP3-J5CCA"
    search_engine_id = "2149f2d26311449a4"
    
    # 테스트 쿼리
    query = "대일외고 입시 트렌드 2025"
    
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        'key': api_key,
        'cx': search_engine_id,
        'q': query,
        'num': 5
    }
    
    print(f"🔍 새 구글 API 키 테스트: {query}")
    print("=" * 50)
    
    try:
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"✅ 새 API 키 성공!")
            print(f"📊 총 결과: {result.get('searchInformation', {}).get('totalResults', 'N/A')}")
            print(f"⏱️ 검색 시간: {result.get('searchInformation', {}).get('searchTime', 'N/A')}초")
            
            items = result.get('items', [])
            print(f"\n📋 상위 {len(items)}개 결과:")
            
            for i, item in enumerate(items, 1):
                print(f"\n{i}. {item['title']}")
                print(f"   🔗 {item['link']}")
                print(f"   📝 {item['snippet'][:100]}...")
                
            return True
            
        else:
            print(f"❌ 오류 발생:")
            print(f"상태 코드: {response.status_code}")
            print(f"응답: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 예외 발생: {str(e)}")
        return False

if __name__ == "__main__":
    test_new_google_api()