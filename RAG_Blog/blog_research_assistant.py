"""
블로그 글 작성을 위한 통합 리서치 도구
Perplexity API를 활용한 자동 조사 및 분석
"""

import os
from datetime import datetime
from perplexity_search import PerplexitySearcher
from typing import Dict, List

class BlogResearchAssistant:
    def __init__(self):
        self.searcher = PerplexitySearcher()
        self.research_results = {}
    
    def research_blog_topic(self, main_topic: str, target_keywords: List[str]) -> Dict:
        """
        블로그 주제에 대한 종합적 리서치 수행
        
        Args:
            main_topic: 메인 주제 (예: "대일외고 입시")
            target_keywords: 타겟 키워드 리스트
            
        Returns:
            종합 리서치 결과
        """
        print(f"🔍 {main_topic} 리서치 시작...")
        
        research_data = {
            "topic": main_topic,
            "keywords": target_keywords,
            "timestamp": datetime.now().isoformat(),
            "results": {}
        }
        
        # 1. 기본 정보 조사
        print("📋 기본 정보 조사 중...")
        research_data["results"]["basic_info"] = self.searcher.search_korean(
            f"{main_topic} 최신 정보 2025년 현황 트렌드"
        )
        
        # 2. 경쟁 분석
        print("🏆 경쟁 분석 중...")
        research_data["results"]["competition"] = self.searcher.search_korean(
            f"{main_topic} 블로그 글 분석 인기 키wordd 경쟁도"
        )
        
        # 3. 타겟 오디언스 분석
        print("👥 타겟 오디언스 분석 중...")
        research_data["results"]["audience"] = self.searcher.search_korean(
            f"{main_topic}에 관심있는 사람들 특징 니즈 검색 패턴"
        )
        
        # 4. 수익화 방안 조사
        print("💰 수익화 방안 조사 중...")
        research_data["results"]["monetization"] = self.searcher.search_korean(
            f"{main_topic} 관련 수익화 애드센스 애프릴리에이트 상품"
        )
        
        # 5. 키워드별 세부 조사
        print("🔑 키워드별 세부 조사 중...")
        research_data["results"]["keyword_analysis"] = {}
        
        for keyword in target_keywords[:3]:  # 상위 3개만
            print(f"  - {keyword} 분석 중...")
            research_data["results"]["keyword_analysis"][keyword] = self.searcher.search_korean(
                f"{keyword} 검색량 트렌드 관련 질문 사용자 의도"
            )
        
        self.research_results = research_data
        return research_data
    
    def generate_blog_outline(self, research_data: Dict) -> Dict:
        """리서치 결과를 바탕으로 블로그 글 개요 생성"""
        
        outline_prompt = f"""
        다음 리서치 결과를 바탕으로 SEO 최적화된 블로그 글 개요를 만들어주세요:
        
        주제: {research_data['topic']}
        키워드: {', '.join(research_data['keywords'])}
        
        요구사항:
        1. 클릭하고 싶은 제목 3개 제안
        2. H2 헤딩 5-7개 구성
        3. 각 섹션별 핵심 내용 요약
        4. 수익화 요소 배치 위치 제안
        5. 내부 링크 기회 제안
        6. FAQ 섹션 질문 5개
        
        리서치 데이터:
        {research_data['results']['basic_info'][:500]}...
        """
        
        outline_result = self.searcher.search_korean(outline_prompt)
        return {
            "outline": outline_result,
            "generated_at": datetime.now().isoformat()
        }
    
    def save_research_report(self, filename: str = None) -> str:
        """리서치 결과를 파일로 저장"""
        if not self.research_results:
            return "저장할 리서치 결과가 없습니다."
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            topic_safe = self.research_results['topic'].replace(' ', '_')
            filename = f"research_{topic_safe}_{timestamp}.md"
        
        content = f"""# {self.research_results['topic']} 리서치 보고서

생성일시: {self.research_results['timestamp']}
키워드: {', '.join(self.research_results['keywords'])}

## 📋 기본 정보
{self.research_results['results']['basic_info']}

## 🏆 경쟁 분석  
{self.research_results['results']['competition']}

## 👥 타겟 오디언스
{self.research_results['results']['audience']}

## 💰 수익화 방안
{self.research_results['results']['monetization']}

## 🔑 키워드 분석
"""
        
        for keyword, analysis in self.research_results['results']['keyword_analysis'].items():
            content += f"\n### {keyword}\n{analysis}\n"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return f"리서치 보고서가 {filename}에 저장되었습니다."

# 대일외고 특화 리서치 함수
def research_daeil_academy_blog():
    """대일외고 학원 블로그를 위한 특화 리서치"""
    assistant = BlogResearchAssistant()
    
    topic = "대일외고 영어 입시"
    keywords = [
        "대일외고 입시 준비",
        "대일외고 영어 내신", 
        "대일외고 합격 후기",
        "외고 영어 학원",
        "대일외고 경쟁률",
        "대일외고 면접 준비"
    ]
    
    # 종합 리서치 수행
    research_data = assistant.research_blog_topic(topic, keywords)
    
    # 블로그 개요 생성
    outline = assistant.generate_blog_outline(research_data)
    
    # 결과 저장
    report_file = assistant.save_research_report()
    
    print(f"\n✅ 리서치 완료!")
    print(f"📄 보고서: {report_file}")
    print(f"📝 블로그 개요 생성 완료")
    
    return research_data, outline

if __name__ == "__main__":
    # 대일외고 학원 블로그 리서치 실행
    try:
        research_data, outline = research_daeil_academy_blog()
        print("\n📋 생성된 블로그 개요:")
        print(outline['outline'])
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        print("Perplexity API 키가 설정되었는지 확인해주세요.")