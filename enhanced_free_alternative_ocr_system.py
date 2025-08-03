#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced Free Alternative OCR System
학습한 PDF 전처리 지식을 기존 시스템에 통합한 업그레이드 버전
"""

import os
import json
import time
import base64
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import fitz  # PyMuPDF

# 기존 무료 도구들
try:
    from unstructured.partition.auto import partition
    UNSTRUCTURED_AVAILABLE = True
except ImportError:
    UNSTRUCTURED_AVAILABLE = False

try:
    from pdftext import plain_text_output, dictionary_output
    PDFTEXT_AVAILABLE = True
except ImportError:
    PDFTEXT_AVAILABLE = False

class LayoutElement:
    """레이아웃 요소 클래스 (OmniDocBench 19개 카테고리 기반)"""
    
    CATEGORIES = {
        'title': '제목', 'heading': '소제목', 'paragraph': '본문', 'list': '목록',
        'table': '테이블', 'figure': '그림', 'caption': '캡션', 'footnote': '각주',
        'header': '헤더', 'footer': '푸터', 'equation': '수식', 'code': '코드',
        'quote': '인용문', 'sidebar': '사이드바', 'form': '양식', 'chart': '차트',
        'diagram': '다이어그램', 'signature': '서명', 'other': '기타'
    }
    
    def __init__(self, category: str, text: str, bbox: List[float] = None, confidence: float = 1.0):
        self.category = category
        self.text = text
        self.bbox = bbox or [0, 0, 0, 0]
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

class EnhancedFreeAlternativeOCR:
    """업그레이드된 무료 대안 OCR 시스템"""
    
    def __init__(self):
        self.claude_api_key = os.getenv('ANTHROPIC_API_KEY')
        self.gemini_api_key = os.getenv('GOOGLE_API_KEY')
        
        if not self.claude_api_key:
            print("⚠️ ANTHROPIC_API_KEY가 설정되지 않았습니다")
        if not self.gemini_api_key:
            print("⚠️ GOOGLE_API_KEY가 설정되지 않았습니다")
        
        self.claude_url = "https://api.anthropic.com/v1/messages"
        self.gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={self.gemini_api_key}"
        
        print("🎯 업그레이드된 무료 대안 OCR 시스템 초기화 완료")
        print(f"   📦 unstructured: {'✅' if UNSTRUCTURED_AVAILABLE else '❌'}")
        print(f"   📄 pdftext: {'✅' if PDFTEXT_AVAILABLE else '❌'}")
        print(f"   🤖 Claude API: {'✅' if self.claude_api_key else '❌'}")
        print(f"   🔬 Gemini API: {'✅' if self.gemini_api_key else '❌'}")

    def unstructured_process(self, file_path: str) -> Dict[str, Any]:
        """unstructured 처리 (기존 + 레이아웃 정보 추출)"""
        if not UNSTRUCTURED_AVAILABLE:
            return {"success": False, "error": "unstructured 라이브러리 없음"}
        
        try:
            start_time = time.time()
            elements = partition(file_path)
            
            # 기본 텍스트 추출
            text_content = "\n".join([str(element) for element in elements])
            
            # 레이아웃 요소 분석 (업그레이드 부분)
            layout_elements = []
            for element in elements:
                element_type = type(element).__name__.lower()
                
                # unstructured 요소 타입을 우리 카테고리로 매핑
                category_mapping = {
                    'title': 'title',
                    'narrativetext': 'paragraph', 
                    'listitem': 'list',
                    'table': 'table',
                    'image': 'figure',
                    'header': 'header',
                    'footer': 'footer',
                    'formula': 'equation'
                }
                
                category = category_mapping.get(element_type, 'other')
                layout_elem = LayoutElement(
                    category=category,
                    text=str(element),
                    confidence=0.8  # unstructured 기본 신뢰도
                )
                layout_elements.append(layout_elem)
            
            process_time = time.time() - start_time
            
            return {
                "success": True,
                "text": text_content,
                "layout_elements": layout_elements,
                "total_elements": len(elements),
                "processing_time": process_time,
                "method": "unstructured_enhanced"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"unstructured 처리 실패: {str(e)}",
                "processing_time": 0
            }

    def pdftext_process_enhanced(self, file_path: str) -> Dict[str, Any]:
        """업그레이드된 pdftext 처리 (페이지별 구조 분석)"""
        if not PDFTEXT_AVAILABLE or not file_path.lower().endswith('.pdf'):
            return {"success": False, "error": "pdftext PDF 전용 또는 라이브러리 없음"}
        
        try:
            start_time = time.time()
            
            # 기본 텍스트 추출
            plain_text = plain_text_output(file_path, sort=True)
            
            # 구조화된 데이터 추출 (업그레이드 부분)
            structured_data = dictionary_output(file_path, sort=True)
            
            # 페이지별 레이아웃 분석
            layout_elements = []
            page_structures = []
            
            for page_idx, page_data in enumerate(structured_data):
                page_num = page_idx + 1
                blocks = page_data.get('blocks', [])
                
                page_elements = []
                for block in blocks:
                    # 블록 타입과 위치에 따른 카테고리 추론
                    bbox = block.get('bbox', [0, 0, 0, 0])
                    text = block.get('text', '').strip()
                    
                    if not text:
                        continue
                    
                    # 휴리스틱 기반 카테고리 분류 (업그레이드 부분)
                    category = self._classify_text_block(text, bbox, page_data.get('bbox', [0, 0, 612, 792]))
                    
                    layout_elem = LayoutElement(
                        category=category,
                        text=text,
                        bbox=bbox,
                        confidence=0.9
                    )
                    layout_elem.page_num = page_num
                    
                    layout_elements.append(layout_elem)
                    page_elements.append(layout_elem)
                
                page_structures.append({
                    "page": page_num,
                    "elements": len(page_elements),
                    "bbox": page_data.get('bbox', []),
                    "element_categories": [elem.category for elem in page_elements]
                })
            
            process_time = time.time() - start_time
            
            return {
                "success": True,
                "text": plain_text,
                "structured_data": structured_data,
                "layout_elements": layout_elements,
                "page_structures": page_structures,
                "total_pages": len(structured_data),
                "total_elements": len(layout_elements),
                "processing_time": process_time,
                "method": "pdftext_enhanced"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"pdftext 처리 실패: {str(e)}",
                "processing_time": 0
            }

    def _classify_text_block(self, text: str, bbox: List[float], page_bbox: List[float]) -> str:
        """텍스트 블록 카테고리 분류 (휴리스틱 기반)"""
        
        # 페이지 내 상대적 위치 계산
        if len(bbox) >= 4 and len(page_bbox) >= 4:
            rel_y_top = bbox[1] / page_bbox[3]  # 상단 상대 위치
            rel_y_bottom = bbox[3] / page_bbox[3]  # 하단 상대 위치
            rel_x_left = bbox[0] / page_bbox[2]  # 좌측 상대 위치
        else:
            rel_y_top = rel_y_bottom = rel_x_left = 0.5
        
        text_lower = text.lower().strip()
        
        # 규칙 기반 분류
        
        # 1. 페이지 위치 기반
        if rel_y_top < 0.1:  # 상단 10%
            if any(keyword in text_lower for keyword in ['page', '페이지', 'header', '제목']):
                return 'header'
            elif len(text.split()) <= 10 and text.isupper():
                return 'title'
        
        if rel_y_bottom > 0.9:  # 하단 10%
            return 'footer'
        
        # 2. 텍스트 패턴 기반
        if text.startswith(('1.', '2.', '•', '-', '*')) or text.startswith(('가.', '나.', 'ㄱ.', 'ㄴ.')):
            return 'list'
        
        # 3. 수식 패턴
        if any(symbol in text for symbol in ['=', '∑', '∫', '√', '±', '≤', '≥']):
            return 'equation'
        
        # 4. 제목 패턴
        if (len(text.split()) <= 8 and 
            (text.istitle() or text.isupper() or 
             any(keyword in text_lower for keyword in ['제목', 'title', '장', '절', 'chapter']))):
            return 'heading'
        
        # 5. 표 패턴
        if '\t' in text or text.count('|') > 2:
            return 'table'
        
        # 6. 인용문 패턴
        if text.startswith('"') and text.endswith('"'):
            return 'quote'
        
        # 7. 서명 패턴
        if any(keyword in text_lower for keyword in ['서명', 'signature', '도장', '인장']):
            return 'signature'
        
        # 8. 기본값: 본문
        return 'paragraph'

    def claude_layout_analysis(self, image_path: str) -> Dict[str, Any]:
        """Claude를 사용한 고급 레이아웃 분석 (새로운 기능)"""
        if not self.claude_api_key:
            return {"success": False, "error": "Claude API 키 없음"}
        
        try:
            start_time = time.time()
            
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
            layout_prompt = """
이 문서 이미지의 레이아웃을 분석하여 다음 정보를 JSON 형식으로 제공해주세요:

{
  "document_type": "문서 유형 (예: 논문, 계약서, 보고서 등)",
  "layout_complexity": "간단함|보통|복잡함",
  "elements": [
    {
      "category": "title|heading|paragraph|list|table|figure|caption|footnote|header|footer|equation|code|quote|sidebar|form|chart|diagram|signature|other",
      "text": "해당 영역의 텍스트",
      "position": "상단|중단|하단",
      "confidence": 0.95
    }
  ],
  "reading_order": "위에서 아래로 읽는 순서의 요소 인덱스 배열"
}

한국어와 영어 문서를 정확히 분석해주세요.
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
                
                try:
                    layout_data = json.loads(layout_text)
                    
                    # LayoutElement 객체 생성
                    elements = []
                    for elem in layout_data.get('elements', []):
                        element = LayoutElement(
                            category=elem.get('category', 'other'),
                            text=elem.get('text', ''),
                            confidence=elem.get('confidence', 0.8)
                        )
                        elements.append(element)
                    
                    return {
                        "success": True,
                        "elements": elements,
                        "document_type": layout_data.get('document_type', '알 수 없음'),
                        "layout_complexity": layout_data.get('layout_complexity', '보통'),
                        "reading_order": layout_data.get('reading_order', []),
                        "processing_time": process_time,
                        "method": "claude_layout_analysis"
                    }
                    
                except json.JSONDecodeError:
                    return {
                        "success": True,
                        "raw_analysis": layout_text,
                        "processing_time": process_time,
                        "elements": [],
                        "method": "claude_layout_raw"
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
                "error": f"Claude 레이아웃 분석 실패: {str(e)}",
                "processing_time": 0
            }

    def multipage_document_analysis(self, pdf_path: str) -> Dict[str, Any]:
        """멀티페이지 문서 분석 (f_d 전략 적용)"""
        if not pdf_path.lower().endswith('.pdf'):
            return {"success": False, "error": "PDF 파일만 지원"}
        
        try:
            start_time = time.time()
            
            # PyMuPDF로 PDF 열기
            pdf_document = fitz.open(pdf_path)
            total_pages = pdf_document.page_count
            
            print(f"📄 멀티페이지 분석: {total_pages}페이지")
            
            # 각 페이지 분석
            page_analyses = []
            all_elements = []
            
            for page_num in range(min(total_pages, 5)):  # 처음 5페이지만 분석 (비용 절약)
                page = pdf_document[page_num]
                
                # 페이지를 이미지로 변환
                mat = fitz.Matrix(1.5, 1.5)  # 적당한 해상도
                pix = page.get_pixmap(matrix=mat)
                
                # 임시 이미지 저장
                temp_path = f"temp_page_{page_num}.png"
                pix.save(temp_path)
                
                try:
                    # 해당 페이지 레이아웃 분석
                    page_layout = self.claude_layout_analysis(temp_path)
                    
                    if page_layout["success"]:
                        # 페이지 번호 설정
                        for element in page_layout.get("elements", []):
                            element.page_num = page_num + 1
                            all_elements.append(element)
                        
                        page_analyses.append({
                            "page_num": page_num + 1,
                            "analysis": page_layout,
                            "success": True
                        })
                        
                        print(f"   ✅ 페이지 {page_num + 1}: {len(page_layout.get('elements', []))}개 요소")
                    else:
                        page_analyses.append({
                            "page_num": page_num + 1,
                            "error": page_layout.get("error"),
                            "success": False
                        })
                        print(f"   ❌ 페이지 {page_num + 1}: 분석 실패")
                        
                finally:
                    # 임시 파일 삭제
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
            
            pdf_document.close()
            
            # 문서 전체 분류
            document_type = self._classify_multipage_document(all_elements)
            
            total_time = time.time() - start_time
            
            return {
                "success": True,
                "total_pages": total_pages,
                "analyzed_pages": len(page_analyses),
                "page_analyses": page_analyses,
                "all_elements": all_elements,
                "document_type": document_type,
                "total_elements": len(all_elements),
                "processing_time": total_time,
                "method": "multipage_analysis"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"멀티페이지 분석 실패: {str(e)}",
                "processing_time": 0
            }

    def _classify_multipage_document(self, elements: List[LayoutElement]) -> str:
        """멀티페이지 문서 분류 (요소 패턴 기반)"""
        category_counts = {}
        for element in elements:
            category_counts[element.category] = category_counts.get(element.category, 0) + 1
        
        total_elements = len(elements)
        if total_elements == 0:
            return "알 수 없음"
        
        # 상대적 비율 계산
        equation_ratio = category_counts.get('equation', 0) / total_elements
        table_ratio = category_counts.get('table', 0) / total_elements  
        figure_ratio = category_counts.get('figure', 0) / total_elements
        form_ratio = category_counts.get('form', 0) / total_elements
        
        # 분류 규칙
        if equation_ratio > 0.1 and figure_ratio > 0.05:
            return "학술논문"
        elif table_ratio > 0.15 or category_counts.get('chart', 0) > 1:
            return "보고서"
        elif form_ratio > 0.2 or category_counts.get('form', 0) > 3:
            return "양식문서"
        elif category_counts.get('signature', 0) > 0:
            return "계약서"
        elif category_counts.get('list', 0) > 5 and category_counts.get('heading', 0) > 3:
            return "사업계획서"
        else:
            return "일반문서"

    def enhanced_complete_process(self, file_path: str) -> Dict[str, Any]:
        """업그레이드된 완전 처리 파이프라인"""
        print(f"\n🚀 업그레이드된 무료 대안 OCR 시작: {file_path}")
        
        results = {
            "file_path": file_path,
            "timestamp": datetime.now().isoformat(),
            "file_type": Path(file_path).suffix.lower(),
            "basic_processing": {},
            "enhanced_features": {},
            "final_result": None
        }
        
        # 1. 기본 처리 (기존 방식 개선)
        print("1️⃣ 기본 처리...")
        if file_path.lower().endswith('.pdf'):
            basic_result = self.pdftext_process_enhanced(file_path)
        else:
            basic_result = self.unstructured_process(file_path)
        
        results["basic_processing"] = basic_result
        
        # 2. 고급 기능들 (새로운 기능)
        enhanced_features = {}
        
        # 2-1. 이미지 파일 레이아웃 분석
        if file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
            print("2️⃣ 레이아웃 분석...")
            layout_result = self.claude_layout_analysis(file_path)
            enhanced_features["layout_analysis"] = layout_result
            
            if layout_result["success"]:
                print(f"   ✅ 레이아웃 분석: {len(layout_result.get('elements', []))}개 요소")
                print(f"   📋 문서 유형: {layout_result.get('document_type', '알 수 없음')}")
        
        # 2-2. PDF 멀티페이지 분석
        if file_path.lower().endswith('.pdf'):
            print("2️⃣ 멀티페이지 분석...")
            multipage_result = self.multipage_document_analysis(file_path)
            enhanced_features["multipage_analysis"] = multipage_result
            
            if multipage_result["success"]:
                print(f"   ✅ 멀티페이지 분석: {multipage_result['total_elements']}개 요소")
                print(f"   📋 문서 유형: {multipage_result.get('document_type', '알 수 없음')}")
        
        results["enhanced_features"] = enhanced_features
        
        # 3. 결과 통합
        final_text = self._integrate_enhanced_results(results)
        
        # 처리 시간 계산
        total_time = basic_result.get("processing_time", 0)
        for feature in enhanced_features.values():
            total_time += feature.get("processing_time", 0)
        
        results["final_result"] = {
            "success": True,
            "integrated_text": final_text,
            "total_processing_time": total_time,
            "enhancement_level": "advanced_layout_analysis",
            "features_applied": list(enhanced_features.keys())
        }
        
        print(f"🎉 업그레이드된 처리 완료! 시간: {total_time:.2f}초")
        return results

    def _integrate_enhanced_results(self, results: Dict[str, Any]) -> str:
        """업그레이드된 결과 통합"""
        integrated = ""
        
        # 파일 정보
        integrated += f"=== 파일 정보 ===\n"
        integrated += f"파일: {results['file_path']}\n"
        integrated += f"유형: {results['file_type']}\n"
        integrated += f"처리 시간: {results['timestamp']}\n\n"
        
        # 기본 텍스트
        basic = results["basic_processing"]
        if basic.get("success"):
            integrated += "=== 기본 텍스트 ===\n"
            integrated += basic["text"] + "\n\n"
            
            # 레이아웃 요소 (기본 처리에서)
            if "layout_elements" in basic:
                integrated += "=== 구조 분석 (기본) ===\n"
                for element in basic["layout_elements"]:
                    elem_dict = element.to_dict() if hasattr(element, 'to_dict') else element
                    integrated += f"[{elem_dict.get('category_korean', '알 수 없음')}] {elem_dict.get('text', '')}\n"
                integrated += "\n"
        
        # 고급 기능 결과
        enhanced = results["enhanced_features"]
        
        # 레이아웃 분석
        if "layout_analysis" in enhanced and enhanced["layout_analysis"]["success"]:
            layout = enhanced["layout_analysis"]
            integrated += "=== 고급 레이아웃 분석 ===\n"
            integrated += f"문서 유형: {layout.get('document_type', '알 수 없음')}\n"
            integrated += f"복잡도: {layout.get('layout_complexity', '보통')}\n\n"
            
            for element in layout.get("elements", []):
                elem_dict = element.to_dict() if hasattr(element, 'to_dict') else element
                integrated += f"[{elem_dict.get('category_korean', '알 수 없음')}] {elem_dict.get('text', '')}\n"
            integrated += "\n"
        
        # 멀티페이지 분석
        if "multipage_analysis" in enhanced and enhanced["multipage_analysis"]["success"]:
            multipage = enhanced["multipage_analysis"]
            integrated += "=== 멀티페이지 분석 ===\n"
            integrated += f"총 페이지: {multipage['total_pages']}\n"
            integrated += f"분석된 페이지: {multipage['analyzed_pages']}\n"
            integrated += f"문서 유형: {multipage.get('document_type', '알 수 없음')}\n"
            integrated += f"총 요소: {multipage['total_elements']}\n\n"
            
            # 페이지별 요소
            for page_analysis in multipage["page_analyses"]:
                if page_analysis["success"]:
                    page_num = page_analysis["page_num"]
                    integrated += f"--- 페이지 {page_num} ---\n"
                    
                    for element in page_analysis["analysis"].get("elements", []):
                        elem_dict = element.to_dict() if hasattr(element, 'to_dict') else element
                        integrated += f"[{elem_dict.get('category_korean', '알 수 없음')}] {elem_dict.get('text', '')}\n"
                    integrated += "\n"
        
        return integrated

    def save_enhanced_results(self, results: Dict[str, Any], output_dir: str = "RAG_OCR/OCR_Output"):
        """업그레이드된 결과 저장"""
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = Path(results["file_path"]).stem
        
        # JSON 저장 (전체 분석 결과)
        json_path = f"{output_dir}/{filename}_enhanced_free_{timestamp}.json"
        
        # 객체를 딕셔너리로 변환
        json_results = self._prepare_json_data(results)
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_results, f, ensure_ascii=False, indent=2)
        
        # 텍스트 저장
        if results["final_result"]["success"]:
            txt_path = f"{output_dir}/{filename}_enhanced_free_{timestamp}.txt"
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write("=== 업그레이드된 무료 대안 OCR 결과 ===\n\n")
                f.write(results['final_result']['integrated_text'])
        
        print(f"\n💾 업그레이드된 결과 저장:")
        print(f"   📄 JSON: {json_path}")
        if results["final_result"]["success"]:
            print(f"   📝 TXT: {txt_path}")

    def _prepare_json_data(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """JSON 직렬화를 위한 데이터 준비"""
        json_results = results.copy()
        
        # LayoutElement 객체들을 딕셔너리로 변환
        def convert_elements(data):
            if isinstance(data, dict):
                for key, value in data.items():
                    if key == "layout_elements" and isinstance(value, list):
                        data[key] = [elem.to_dict() if hasattr(elem, 'to_dict') else elem for elem in value]
                    elif key == "elements" and isinstance(value, list):
                        data[key] = [elem.to_dict() if hasattr(elem, 'to_dict') else elem for elem in value]
                    elif key == "all_elements" and isinstance(value, list):
                        data[key] = [elem.to_dict() if hasattr(elem, 'to_dict') else elem for elem in value]
                    elif isinstance(value, dict):
                        convert_elements(value)
                    elif isinstance(value, list):
                        for item in value:
                            if isinstance(item, dict):
                                convert_elements(item)
        
        convert_elements(json_results)
        return json_results

def main():
    """메인 실행 함수"""
    try:
        # 업그레이드된 시스템 초기화
        enhanced_ocr = EnhancedFreeAlternativeOCR()
        
        # 테스트 파일들
        test_files = [
            "RAG_OCR/OCR_Input/real_korean_test.png",
            "RAG_OCR/OCR_Input/korean_sample.png", 
            "RAG_OCR/OCR_Input/ocr test.pdf"
        ]
        
        for file_path in test_files:
            if os.path.exists(file_path):
                print(f"\n{'='*60}")
                results = enhanced_ocr.enhanced_complete_process(file_path)
                enhanced_ocr.save_enhanced_results(results)
                print(f"{'='*60}")
            else:
                print(f"⚠️ 파일 없음: {file_path}")
        
        print("\n🎊 업그레이드된 OCR 시스템 테스트 완료!")
        
    except Exception as e:
        print(f"❌ 시스템 오류: {str(e)}")

if __name__ == "__main__":
    main()