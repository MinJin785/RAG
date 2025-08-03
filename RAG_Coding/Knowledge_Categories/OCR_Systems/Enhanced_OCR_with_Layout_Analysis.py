#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced OCR System with Advanced Layout Analysis
학습한 PDF 전처리 지식을 적용한 개선된 OCR 시스템
"""

import os
import json
import time
import base64
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import fitz  # PyMuPDF for advanced PDF processing

# 기존 무료 도구들
try:
    from unstructured.partition.auto import partition
    UNSTRUCTURED_AVAILABLE = True
except ImportError:
    UNSTRUCTURED_AVAILABLE = False

try:
    from pdftext import pdftext
    PDFTEXT_AVAILABLE = True
except ImportError:
    PDFTEXT_AVAILABLE = False

class LayoutElement:
    """문서 레이아웃 요소 클래스 (OmniDocBench 기반)"""
    
    # 19개 레이아웃 카테고리 (OmniDocBench 기반)
    CATEGORIES = {
        'title': '제목',
        'heading': '소제목', 
        'paragraph': '본문',
        'list': '목록',
        'table': '테이블',
        'figure': '그림',
        'caption': '캡션',
        'footnote': '각주',
        'header': '헤더',
        'footer': '푸터',
        'equation': '수식',
        'code': '코드',
        'quote': '인용문',
        'sidebar': '사이드바',
        'form': '양식',
        'chart': '차트',
        'diagram': '다이어그램',
        'signature': '서명',
        'other': '기타'
    }
    
    def __init__(self, category: str, text: str, bbox: List[float], confidence: float = 1.0):
        self.category = category
        self.text = text
        self.bbox = bbox  # [x1, y1, x2, y2]
        self.confidence = confidence
        self.page_num = 1
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            'category': self.category,
            'category_korean': self.CATEGORIES.get(self.category, '알 수 없음'),
            'text': self.text,
            'bbox': self.bbox,
            'confidence': self.confidence,
            'page_num': self.page_num
        }

class EnhancedLayoutAnalyzer:
    """고급 레이아웃 분석기 (Hybrid Approach 기반)"""
    
    def __init__(self, claude_api_key: str, gemini_api_key: str):
        self.claude_api_key = claude_api_key
        self.gemini_api_key = gemini_api_key
        self.claude_url = "https://api.anthropic.com/v1/messages"
        self.gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_api_key}"
        
    def analyze_layout_with_claude(self, image_path: str) -> Dict[str, Any]:
        """Claude를 사용한 고급 레이아웃 분석 (Query Encoding 방식)"""
        try:
            start_time = time.time()
            
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
            # 고급 레이아웃 분석 프롬프트 (19개 카테고리 기반)
            layout_prompt = """
이 문서 이미지를 분석하여 다음 19개 카테고리로 요소들을 분류해주세요:

1. title (제목) - 문서의 주제목
2. heading (소제목) - 섹션 제목들  
3. paragraph (본문) - 일반 텍스트 문단
4. list (목록) - 번호나 불릿 목록
5. table (테이블) - 표 형태 데이터
6. figure (그림) - 이미지, 사진
7. caption (캡션) - 그림이나 표 설명
8. footnote (각주) - 페이지 하단 주석
9. header (헤더) - 페이지 상단 정보
10. footer (푸터) - 페이지 하단 정보
11. equation (수식) - 수학 공식
12. code (코드) - 프로그래밍 코드
13. quote (인용문) - 인용된 텍스트
14. sidebar (사이드바) - 측면 정보
15. form (양식) - 입력 폼이나 체크박스
16. chart (차트) - 그래프나 차트
17. diagram (다이어그램) - 도식, 도표
18. signature (서명) - 서명이나 도장
19. other (기타) - 위에 해당하지 않는 요소

각 요소에 대해 다음 JSON 형식으로 응답해주세요:
{
  "elements": [
    {
      "category": "카테고리명",
      "text": "해당 영역의 텍스트",
      "bbox": [x1, y1, x2, y2],
      "confidence": 0.95
    }
  ],
  "document_type": "문서 유형 (예: 학술논문, 사업계획서, 계약서 등)",
  "reading_order": [요소들의 읽기 순서 인덱스],
  "layout_complexity": "간단함|보통|복잡함"
}

정확한 좌표값과 높은 신뢰도를 가진 분석 결과를 제공해주세요.
"""
            
            payload = {
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 4000,
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": layout_prompt},
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": base64_image
                            }
                        }
                    ]
                }]
            }
            
            headers = {
                "Content-Type": "application/json",
                "x-api-key": self.claude_api_key,
                "anthropic-version": "2023-06-01"
            }
            
            response = requests.post(self.claude_url, headers=headers, json=payload, timeout=30)
            process_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                layout_text = result['content'][0]['text']
                
                # JSON 파싱 시도
                try:
                    layout_data = json.loads(layout_text)
                    elements = []
                    
                    for elem in layout_data.get('elements', []):
                        element = LayoutElement(
                            category=elem['category'],
                            text=elem['text'],
                            bbox=elem['bbox'],
                            confidence=elem['confidence']
                        )
                        elements.append(element)
                    
                    return {
                        "success": True,
                        "elements": elements,
                        "document_type": layout_data.get('document_type', '알 수 없음'),
                        "reading_order": layout_data.get('reading_order', []),
                        "layout_complexity": layout_data.get('layout_complexity', '보통'),
                        "processing_time": process_time,
                        "total_elements": len(elements)
                    }
                    
                except json.JSONDecodeError:
                    # JSON 파싱 실패 시 텍스트 그대로 반환
                    return {
                        "success": True,
                        "raw_analysis": layout_text,
                        "processing_time": process_time,
                        "elements": []
                    }
                    
            else:
                return {
                    "success": False,
                    "error": f"Claude API 오류: {response.status_code}",
                    "processing_time": process_time
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"레이아웃 분석 실패: {str(e)}",
                "processing_time": 0
            }

class MultiPageDocumentProcessor:
    """멀티페이지 문서 처리기 (Beyond Document Page Classification 기반)"""
    
    def __init__(self, layout_analyzer: EnhancedLayoutAnalyzer):
        self.layout_analyzer = layout_analyzer
        
    def process_pdf_pages(self, pdf_path: str) -> Dict[str, Any]:
        """PDF 멀티페이지 처리 (f_d 전략)"""
        try:
            start_time = time.time()
            pdf_document = fitz.open(pdf_path)
            total_pages = pdf_document.page_count
            
            page_results = []
            document_elements = []
            
            print(f"📄 PDF 분석 시작: {total_pages}페이지")
            
            for page_num in range(total_pages):
                page = pdf_document[page_num]
                
                # 페이지를 이미지로 변환
                mat = fitz.Matrix(2.0, 2.0)  # 고해상도 변환
                pix = page.get_pixmap(matrix=mat)
                
                # 임시 이미지 파일 저장
                temp_img_path = f"temp_page_{page_num}.png"
                pix.save(temp_img_path)
                
                try:
                    # 각 페이지별 레이아웃 분석
                    page_layout = self.layout_analyzer.analyze_layout_with_claude(temp_img_path)
                    
                    if page_layout["success"]:
                        # 페이지 번호 설정
                        for element in page_layout.get("elements", []):
                            element.page_num = page_num + 1
                            document_elements.append(element)
                        
                        page_results.append({
                            "page_num": page_num + 1,
                            "layout_analysis": page_layout,
                            "success": True
                        })
                        
                        print(f"   ✅ 페이지 {page_num + 1}: {len(page_layout.get('elements', []))}개 요소")
                    else:
                        page_results.append({
                            "page_num": page_num + 1,
                            "error": page_layout.get("error", "분석 실패"),
                            "success": False
                        })
                        print(f"   ❌ 페이지 {page_num + 1}: 분석 실패")
                        
                finally:
                    # 임시 파일 정리
                    if os.path.exists(temp_img_path):
                        os.remove(temp_img_path)
            
            pdf_document.close()
            total_time = time.time() - start_time
            
            # 문서 전체 분류 (f_d: Document Classification)
            document_type = self._classify_document_type(document_elements)
            
            return {
                "success": True,
                "total_pages": total_pages,
                "page_results": page_results,
                "document_elements": [elem.to_dict() for elem in document_elements],
                "document_type": document_type,
                "total_elements": len(document_elements),
                "processing_time": total_time,
                "classification_strategy": "multi_page_analysis"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"멀티페이지 처리 실패: {str(e)}",
                "processing_time": 0
            }
    
    def _classify_document_type(self, elements: List[LayoutElement]) -> str:
        """문서 유형 분류 (요소 패턴 기반)"""
        
        # 요소 카테고리별 개수 분석
        category_counts = {}
        for element in elements:
            category_counts[element.category] = category_counts.get(element.category, 0) + 1
        
        # 문서 유형 추론 규칙
        if category_counts.get('equation', 0) > 3 and category_counts.get('figure', 0) > 2:
            return "학술논문"
        elif category_counts.get('table', 0) > 2 and category_counts.get('chart', 0) > 1:
            return "보고서"
        elif category_counts.get('form', 0) > 5:
            return "양식문서"
        elif category_counts.get('signature', 0) > 0:
            return "계약서"
        elif category_counts.get('list', 0) > 3 and category_counts.get('heading', 0) > 5:
            return "사업계획서"
        else:
            return "일반문서"

class EnhancedOCRSystem:
    """고급 OCR 시스템 (통합 버전)"""
    
    def __init__(self):
        self.claude_api_key = os.getenv('ANTHROPIC_API_KEY')
        self.gemini_api_key = os.getenv('GOOGLE_API_KEY')
        
        if not self.claude_api_key or not self.gemini_api_key:
            raise ValueError("API 키가 설정되지 않았습니다")
        
        self.layout_analyzer = EnhancedLayoutAnalyzer(self.claude_api_key, self.gemini_api_key)
        self.multipage_processor = MultiPageDocumentProcessor(self.layout_analyzer)
    
    def process_document(self, file_path: str) -> Dict[str, Any]:
        """메인 문서 처리 함수"""
        print(f"\n🚀 고급 OCR 분석 시작: {file_path}")
        
        results = {
            "file_path": file_path,
            "timestamp": datetime.now().isoformat(),
            "file_type": Path(file_path).suffix.lower(),
            "basic_ocr": None,
            "layout_analysis": None,
            "multipage_analysis": None,
            "final_result": None
        }
        
        try:
            # 1. 기본 OCR (기존 시스템)
            print("1️⃣ 기본 OCR 처리...")
            if file_path.lower().endswith('.pdf'):
                basic_result = self._basic_pdf_ocr(file_path)
            else:
                basic_result = self._basic_image_ocr(file_path)
            
            results["basic_ocr"] = basic_result
            
            # 2. 고급 레이아웃 분석
            if file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
                print("2️⃣ 레이아웃 분석...")
                layout_result = self.layout_analyzer.analyze_layout_with_claude(file_path)
                results["layout_analysis"] = layout_result
            
            # 3. 멀티페이지 분석 (PDF인 경우)
            if file_path.lower().endswith('.pdf'):
                print("3️⃣ 멀티페이지 분석...")
                multipage_result = self.multipage_processor.process_pdf_pages(file_path)
                results["multipage_analysis"] = multipage_result
            
            # 4. 최종 결과 통합
            final_text = self._integrate_results(results)
            
            results["final_result"] = {
                "success": True,
                "integrated_text": final_text,
                "enhancement_applied": True,
                "processing_strategy": "advanced_layout_analysis"
            }
            
            print("🎉 고급 OCR 분석 완료!")
            return results
            
        except Exception as e:
            results["final_result"] = {
                "success": False,
                "error": str(e)
            }
            return results
    
    def _basic_pdf_ocr(self, pdf_path: str) -> Dict[str, Any]:
        """기본 PDF OCR (pdftext 사용)"""
        if not PDFTEXT_AVAILABLE:
            return {"success": False, "error": "pdftext 라이브러리 없음"}
        
        try:
            from pdftext import plain_text_output
            text = plain_text_output(pdf_path, sort=True)
            return {
                "success": True,
                "text": text,
                "method": "pdftext"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _basic_image_ocr(self, image_path: str) -> Dict[str, Any]:
        """기본 이미지 OCR (unstructured 사용)"""
        if not UNSTRUCTURED_AVAILABLE:
            return {"success": False, "error": "unstructured 라이브러리 없음"}
        
        try:
            elements = partition(image_path)
            text = "\n".join([str(element) for element in elements])
            return {
                "success": True,
                "text": text,
                "method": "unstructured"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _integrate_results(self, results: Dict[str, Any]) -> str:
        """결과 통합"""
        integrated_text = ""
        
        # 기본 OCR 텍스트
        if results["basic_ocr"] and results["basic_ocr"]["success"]:
            integrated_text += "=== 기본 텍스트 ===\n"
            integrated_text += results["basic_ocr"]["text"] + "\n\n"
        
        # 레이아웃 분석 결과
        if results["layout_analysis"] and results["layout_analysis"]["success"]:
            integrated_text += "=== 구조화된 레이아웃 ===\n"
            elements = results["layout_analysis"].get("elements", [])
            
            for element in elements:
                if hasattr(element, 'to_dict'):
                    elem_dict = element.to_dict()
                else:
                    elem_dict = element
                    
                integrated_text += f"[{elem_dict['category_korean']}] {elem_dict['text']}\n"
            
            integrated_text += "\n"
        
        # 멀티페이지 분석 결과
        if results["multipage_analysis"] and results["multipage_analysis"]["success"]:
            integrated_text += "=== 멀티페이지 구조 ===\n"
            integrated_text += f"문서 유형: {results['multipage_analysis']['document_type']}\n"
            integrated_text += f"총 페이지: {results['multipage_analysis']['total_pages']}\n"
            integrated_text += f"총 요소: {results['multipage_analysis']['total_elements']}\n\n"
            
            # 페이지별 요소 정리
            for page_result in results["multipage_analysis"]["page_results"]:
                if page_result["success"]:
                    page_num = page_result["page_num"] 
                    integrated_text += f"--- 페이지 {page_num} ---\n"
                    
                    layout = page_result["layout_analysis"]
                    for element in layout.get("elements", []):
                        if hasattr(element, 'to_dict'):
                            elem_dict = element.to_dict()
                        else:
                            elem_dict = element
                            
                        integrated_text += f"[{elem_dict['category_korean']}] {elem_dict['text']}\n"
                    
                    integrated_text += "\n"
        
        return integrated_text
    
    def save_enhanced_results(self, results: Dict[str, Any], output_dir: str = "RAG_OCR/OCR_Output"):
        """향상된 결과 저장"""
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = Path(results["file_path"]).stem
        
        # JSON 저장 (전체 분석 결과)
        json_path = f"{output_dir}/{filename}_enhanced_{timestamp}.json"
        
        # LayoutElement 객체들을 딕셔너리로 변환
        json_results = self._prepare_for_json(results)
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_results, f, ensure_ascii=False, indent=2)
        
        # 텍스트 저장 (통합 결과)
        if results["final_result"]["success"]:
            txt_path = f"{output_dir}/{filename}_enhanced_{timestamp}.txt"
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write("=== 고급 OCR 분석 결과 ===\n\n")
                f.write(f"파일: {results['file_path']}\n")
                f.write(f"처리 시간: {results['timestamp']}\n")
                f.write(f"파일 유형: {results['file_type']}\n\n")
                f.write(results['final_result']['integrated_text'])
        
        print(f"\n💾 향상된 결과 저장:")
        print(f"   📄 JSON: {json_path}")
        if results["final_result"]["success"]:
            print(f"   📝 TXT: {txt_path}")
    
    def _prepare_for_json(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """JSON 직렬화를 위한 데이터 준비"""
        json_results = results.copy()
        
        # LayoutElement 객체들을 딕셔너리로 변환
        if "layout_analysis" in json_results and json_results["layout_analysis"]:
            if "elements" in json_results["layout_analysis"]:
                elements = json_results["layout_analysis"]["elements"]
                json_results["layout_analysis"]["elements"] = [
                    elem.to_dict() if hasattr(elem, 'to_dict') else elem 
                    for elem in elements
                ]
        
        if "multipage_analysis" in json_results and json_results["multipage_analysis"]:
            if "document_elements" in json_results["multipage_analysis"]:
                # 이미 to_dict()로 변환된 상태라면 그대로 유지
                pass
            
            # 페이지별 결과도 변환
            if "page_results" in json_results["multipage_analysis"]:
                for page_result in json_results["multipage_analysis"]["page_results"]:
                    if "layout_analysis" in page_result and "elements" in page_result["layout_analysis"]:
                        elements = page_result["layout_analysis"]["elements"]
                        page_result["layout_analysis"]["elements"] = [
                            elem.to_dict() if hasattr(elem, 'to_dict') else elem 
                            for elem in elements
                        ]
        
        return json_results

def main():
    """메인 실행 함수"""
    try:
        # 고급 OCR 시스템 초기화
        enhanced_ocr = EnhancedOCRSystem()
        
        # 테스트 파일들
        test_files = [
            "RAG_OCR/OCR_Input/real_korean_test.png",
            "RAG_OCR/OCR_Input/ocr test.pdf"
        ]
        
        for file_path in test_files:
            if os.path.exists(file_path):
                print(f"\n{'='*60}")
                results = enhanced_ocr.process_document(file_path)
                enhanced_ocr.save_enhanced_results(results)
                print(f"{'='*60}")
            else:
                print(f"⚠️ 파일 없음: {file_path}")
        
        print("\n🎊 고급 OCR 시스템 테스트 완료!")
        
    except Exception as e:
        print(f"❌ 시스템 오류: {str(e)}")

if __name__ == "__main__":
    main()