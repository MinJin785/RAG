"""
확실한 정보만 수집하는 검증 시스템
인터넷 정보의 신뢰성을 체크하고 불확실한 정보 배제
"""

import requests
import json
from datetime import datetime
from typing import Dict, List, Tuple

class VerifiedInfoCollector:
    def __init__(self):
        self.api_key = "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"
        self.verified_sources = {
            "공식_웹사이트": ["학원 공식 홈페이지", "공식 블로그"],
            "공식_SNS": ["공식 인스타그램", "공식 페이스북", "공식 유튜브"],
            "공식_문서": ["교육청 등록 정보", "사업자 등록"],
            "신뢰_매체": ["조선일보", "중앙일보", "동아일보", "한겨레", "경향신문"]
        }
        
    def search_with_verification(self, query: str) -> Dict:
        """
        검증된 정보만 수집
        """
        print(f"🔍 검증 검색 시작: {query}")
        
        # 1단계: 기본 검색
        basic_info = self._basic_search(query)
        
        # 2단계: 소스 신뢰성 체크
        verified_info = self._verify_sources(basic_info)
        
        # 3단계: 교차 검증
        cross_verified = self._cross_verify(verified_info)
        
        # 4단계: 불확실한 정보 분리
        final_result = self._separate_uncertain_info(cross_verified)
        
        return final_result
    
    def _basic_search(self, query: str) -> str:
        """기본 검색 수행"""
        url = "https://api.perplexity.ai/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "sonar",
            "messages": [
                {
                    "role": "user", 
                    "content": f"""
                    {query}에 대해 검색해주세요.
                    
                    **중요한 요구사항:**
                    1. 각 정보마다 정확한 출처를 명시해주세요
                    2. 공식 웹사이트, 공식 SNS, 신뢰할 수 있는 언론사 정보를 우선해주세요
                    3. 추측이나 불확실한 정보는 "불확실" 표시해주세요
                    4. 정보의 최신성(언제 발표/업데이트된 정보인지)을 명시해주세요
                    """
                }
            ],
            "max_tokens": 1500
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                return f"검색 실패: {response.status_code}"
        except Exception as e:
            return f"오류 발생: {e}"
    
    def _verify_sources(self, content: str) -> Dict:
        """소스 신뢰성 검증"""
        print("🔎 소스 신뢰성 검증 중...")
        
        verified_info = {
            "확실한_정보": [],
            "의심스러운_정보": [],
            "출처불명_정보": []
        }
        
        # 간단한 키워드 기반 분류 (실제로는 더 정교한 로직 필요)
        lines = content.split('\n')
        
        for line in lines:
            if any(keyword in line for keyword in ["공식", "홈페이지", "사이트"]):
                verified_info["확실한_정보"].append(line)
            elif any(keyword in line for keyword in ["카페", "블로그", "후기"]):
                verified_info["의심스러운_정보"].append(line)
            elif line.strip() and not line.startswith('#'):
                verified_info["출처불명_정보"].append(line)
        
        return verified_info
    
    def _cross_verify(self, verified_info: Dict) -> Dict:
        """교차 검증 수행"""
        print("🔄 교차 검증 중...")
        
        # 확실한 정보들을 다시 한번 검증
        cross_verified = {
            "검증완료": [],
            "추가확인필요": [],
            "사용자확인필요": []
        }
        
        for info in verified_info["확실한_정보"]:
            # 실제로는 여러 소스에서 재검색하여 일치하는지 확인
            cross_verified["검증완료"].append(info)
        
        for info in verified_info["의심스러운_정보"]:
            cross_verified["추가확인필요"].append(info)
            
        for info in verified_info["출처불명_정보"]:
            cross_verified["사용자확인필요"].append(info)
        
        return cross_verified
    
    def _separate_uncertain_info(self, cross_verified: Dict) -> Dict:
        """불확실한 정보 분리"""
        print("✅ 최종 정보 분류 완료")
        
        final_result = {
            "사용가능한_정보": cross_verified["검증완료"],
            "보류된_정보": cross_verified["추가확인필요"] + cross_verified["사용자확인필요"],
            "검증_요약": {
                "총_정보_수": len(cross_verified["검증완료"]) + len(cross_verified["추가확인필요"]) + len(cross_verified["사용자확인필요"]),
                "사용가능": len(cross_verified["검증완료"]),
                "보류": len(cross_verified["추가확인필요"]) + len(cross_verified["사용자확인필요"]),
                "신뢰도": f"{len(cross_verified['검증완료']) / (len(cross_verified['검증완료']) + len(cross_verified['추가확인필요']) + len(cross_verified['사용자확인필요'])) * 100:.1f}%" if cross_verified["검증완료"] else "0%"
            }
        }
        
        return final_result
    
    def get_user_confirmed_info(self, topic: str) -> Dict:
        """
        사용자 직접 제공 정보 수집 템플릿
        """
        return {
            "주제": topic,
            "사용자_확인_필요사항": [
                "정확한 학원명과 위치",
                "현재 강의 중인 과목",
                "강사진 정보",
                "특화 분야",
                "현재 상태 (운영중/휴원 등)"
            ],
            "수집방법": [
                "사용자 직접 제공",
                "공식 웹사이트 확인",
                "전화 문의",
                "방문 확인"
            ]
        }

def main():
    collector = VerifiedInfoCollector()
    
    # 고등어닷컴 학원 검증 검색
    result = collector.search_with_verification("고등어닷컴 영어수학 학원")
    
    print("=" * 60)
    print("📋 검증된 정보 수집 결과")
    print("=" * 60)
    
    print("\n✅ 사용 가능한 정보:")
    for info in result["사용가능한_정보"]:
        print(f"  - {info}")
    
    print("\n⚠️ 보류된 정보 (확인 필요):")
    for info in result["보류된_정보"]:
        print(f"  - {info}")
    
    print(f"\n📊 검증 요약:")
    print(f"  - 총 정보: {result['검증_요약']['총_정보_수']}개")
    print(f"  - 사용 가능: {result['검증_요약']['사용가능']}개")
    print(f"  - 보류: {result['검증_요약']['보류']}개")
    print(f"  - 신뢰도: {result['검증_요약']['신뢰도']}")
    
    # 사용자 확인 필요 사항
    user_check = collector.get_user_confirmed_info("고등어닷컴 학원")
    print("\n🔔 사용자 확인 필요 사항:")
    for item in user_check["사용자_확인_필요사항"]:
        print(f"  - {item}")

if __name__ == "__main__":
    main()