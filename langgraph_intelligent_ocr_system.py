#!/usr/bin/env python3
"""
LangGraph 기반 지능형 OCR 시스템
동적 문서 처리 워크플로우와 품질 기반 자동 최적화

주요 혁신사항:
- 문서 타입별 적응형 처리 파이프라인
- 다중 OCR 엔진 협업 및 품질 기반 선택
- 실시간 품질 평가 및 재처리 로직
- Claude + Gemini + Free Tools 하이브리드 시스템
"""

import asyncio
import json
import time
import base64
import requests
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Literal
from dataclasses import dataclass, asdict
from typing_extensions import TypedDict, Annotated
import logging
import hashlib
import fitz  # PyMuPDF

# LangGraph 임포트
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver

# 기존 OCR 도구들
try:
    from unstructured.partition.auto import partition
    UNSTRUCTURED_AVAILABLE = True
except ImportError:
    UNSTRUCTURED_AVAILABLE = False

try:
    from pdftext import plain_text_output
    PDFTEXT_AVAILABLE = True
except ImportError:
    PDFTEXT_AVAILABLE = False

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ============================================================================
# LangGraph State 정의
# ============================================================================

class OCRWorkflowState(TypedDict):
    """OCR 워크플로우 상태"""
    document_id: str
    file_path: str
    file_type: str
    document_analysis: Dict[str, Any]
    ocr_results: Dict[str, Any]
    quality_scores: Dict[str, float]
    messages: Annotated[List[str], add_messages]
    processing_methods: List[str]
    retry_count: int
    final_text: str
    layout_elements: List[Dict]
    confidence_score: float
    processing_metadata: Dict[str, Any]
    requires_human_review: bool
    optimization_suggestions: List[str]

# ============================================================================
# 데이터 모델
# ============================================================================

@dataclass
class DocumentMetrics:
    """문서 메트릭"""
    page_count: int
    text_density: float
    image_count: int
    table_count: int
    complexity_score: float
    language_detected: str

@dataclass
class OCRQualityMetrics:
    """OCR 품질 메트릭"""
    text_confidence: float
    layout_accuracy: float
    character_error_rate: float
    completeness_score: float
    overall_quality: float

@dataclass
class LayoutElement:
    """레이아웃 요소"""
    category: str
    text: str
    bbox: List[float]
    confidence: float
    page_num: int

# ============================================================================
# LangGraph 노드 함수들
# ============================================================================

class OCRWorkflowNodes:
    """OCR 워크플로우 노드 구현"""
    
    def __init__(self, ocr_system):
        self.ocr_system = ocr_system
        self.claude_api_key = os.getenv('ANTHROPIC_API_KEY')
        self.gemini_api_key = os.getenv('GOOGLE_API_KEY')
        
        if not self.claude_api_key:
            logger.warning("ANTHROPIC_API_KEY가 설정되지 않았습니다")
        if not self.gemini_api_key:
            logger.warning("GOOGLE_API_KEY가 설정되지 않았습니다")
    
    def analyze_document(self, state: OCRWorkflowState) -> OCRWorkflowState:
        """문서 분석 노드"""
        file_path = state["file_path"]
        file_type = state["file_type"]
        
        # 문서 기본 분석
        document_analysis = self._analyze_document_structure(file_path, file_type)
        
        # 처리 방법 결정
        processing_methods = self._determine_processing_methods(document_analysis)
        
        return {
            **state,
            "document_analysis": document_analysis,
            "processing_methods": processing_methods,
            "processing_metadata": {
                "analysis_timestamp": datetime.now().isoformat(),
                "suggested_methods": processing_methods,
                "complexity_level": document_analysis.get("complexity", "medium")
            },
            "messages": [f"문서 분석 완료: {document_analysis['type']} 타입, 복잡도 {document_analysis['complexity']}"]
        }
    
    def execute_free_tools_ocr(self, state: OCRWorkflowState) -> OCRWorkflowState:
        """무료 도구 OCR 실행 노드"""
        file_path = state["file_path"]
        file_type = state["file_type"]
        
        ocr_results = {}
        quality_scores = {}
        
        # 1. unstructured 처리
        if UNSTRUCTURED_AVAILABLE and "unstructured" in state["processing_methods"]:
            try:
                unstructured_result = self._process_with_unstructured(file_path)
                ocr_results["unstructured"] = unstructured_result
                quality_scores["unstructured"] = self._evaluate_text_quality(unstructured_result.get("text", ""))
                logger.info(f"unstructured 처리 완료: 품질 {quality_scores['unstructured']:.2f}")
            except Exception as e:
                logger.error(f"unstructured 처리 실패: {e}")
                ocr_results["unstructured"] = {"success": False, "error": str(e)}
                quality_scores["unstructured"] = 0.0
        
        # 2. pdftext 처리 (PDF만)
        if PDFTEXT_AVAILABLE and file_type.lower() == "pdf" and "pdftext" in state["processing_methods"]:
            try:
                pdftext_result = self._process_with_pdftext(file_path)
                ocr_results["pdftext"] = pdftext_result
                quality_scores["pdftext"] = self._evaluate_text_quality(pdftext_result.get("text", ""))
                logger.info(f"pdftext 처리 완료: 품질 {quality_scores['pdftext']:.2f}")
            except Exception as e:
                logger.error(f"pdftext 처리 실패: {e}")
                ocr_results["pdftext"] = {"success": False, "error": str(e)}
                quality_scores["pdftext"] = 0.0
        
        return {
            **state,
            "ocr_results": {**state.get("ocr_results", {}), **ocr_results},
            "quality_scores": {**state.get("quality_scores", {}), **quality_scores},
            "messages": [f"무료 도구 OCR 완료: {len(ocr_results)}개 방법 시도"]
        }
    
    def execute_claude_ocr(self, state: OCRWorkflowState) -> OCRWorkflowState:
        """Claude OCR 실행 노드"""
        file_path = state["file_path"]
        
        if not self.claude_api_key:
            return {
                **state,
                "messages": ["Claude API 키가 없어 건너뜀"]
            }
        
        try:
            claude_result = self._process_with_claude(file_path)
            
            # 결과 저장
            ocr_results = state.get("ocr_results", {})
            ocr_results["claude"] = claude_result
            
            quality_scores = state.get("quality_scores", {})
            quality_scores["claude"] = self._evaluate_text_quality(claude_result.get("text", ""))
            
            logger.info(f"Claude OCR 완료: 품질 {quality_scores['claude']:.2f}")
            
            return {
                **state,
                "ocr_results": ocr_results,
                "quality_scores": quality_scores,
                "messages": [f"Claude OCR 완료: 품질 {quality_scores['claude']:.2f}"]
            }
            
        except Exception as e:
            logger.error(f"Claude OCR 실패: {e}")
            return {
                **state,
                "messages": [f"Claude OCR 실패: {str(e)}"]
            }
    
    def execute_gemini_ocr(self, state: OCRWorkflowState) -> OCRWorkflowState:
        """Gemini OCR 실행 노드"""
        file_path = state["file_path"]
        
        if not self.gemini_api_key:
            return {
                **state,
                "messages": ["Gemini API 키가 없어 건너뜀"]
            }
        
        try:
            gemini_result = self._process_with_gemini(file_path)
            
            # 결과 저장
            ocr_results = state.get("ocr_results", {})
            ocr_results["gemini"] = gemini_result
            
            quality_scores = state.get("quality_scores", {})
            quality_scores["gemini"] = self._evaluate_text_quality(gemini_result.get("text", ""))
            
            logger.info(f"Gemini OCR 완료: 품질 {quality_scores['gemini']:.2f}")
            
            return {
                **state,
                "ocr_results": ocr_results,
                "quality_scores": quality_scores,
                "messages": [f"Gemini OCR 완료: 품질 {quality_scores['gemini']:.2f}"]
            }
            
        except Exception as e:
            logger.error(f"Gemini OCR 실패: {e}")
            return {
                **state,
                "messages": [f"Gemini OCR 실패: {str(e)}"]
            }
    
    def evaluate_results_quality(self, state: OCRWorkflowState) -> OCRWorkflowState:
        """결과 품질 평가 노드"""
        ocr_results = state.get("ocr_results", {})
        quality_scores = state.get("quality_scores", {})
        
        if not quality_scores:
            return {
                **state,
                "confidence_score": 0.0,
                "requires_human_review": True,
                "messages": ["OCR 결과가 없어 품질 평가 불가"]
            }
        
        # 최고 품질 결과 선택
        best_method = max(quality_scores.keys(), key=lambda k: quality_scores[k])
        best_quality = quality_scores[best_method]
        best_result = ocr_results.get(best_method, {})
        
        # 전체 품질 평가
        overall_quality = self._calculate_overall_quality(quality_scores)
        
        # 인간 리뷰 필요성 판단
        requires_review = overall_quality < 0.7 or best_quality < 0.6
        
        # 개선 제안 생성
        optimization_suggestions = self._generate_optimization_suggestions(
            quality_scores, state["document_analysis"], state["retry_count"]
        )
        
        return {
            **state,
            "final_text": best_result.get("text", ""),
            "confidence_score": best_quality,
            "requires_human_review": requires_review,
            "optimization_suggestions": optimization_suggestions,
            "processing_metadata": {
                **state.get("processing_metadata", {}),
                "best_method": best_method,
                "overall_quality": overall_quality,
                "quality_breakdown": quality_scores
            },
            "messages": [f"품질 평가 완료: 최고 {best_method} ({best_quality:.2f}), 전체 {overall_quality:.2f}"]
        }
    
    def optimize_processing_strategy(self, state: OCRWorkflowState) -> OCRWorkflowState:
        """처리 전략 최적화 노드"""
        optimization_suggestions = state["optimization_suggestions"]
        retry_count = state["retry_count"]
        
        # 최적화 전략 적용
        updated_methods = []
        
        if "try_different_engines" in optimization_suggestions:
            # 다른 엔진 시도
            current_methods = state["processing_methods"]
            all_methods = ["unstructured", "pdftext", "claude", "gemini"]
            updated_methods = [m for m in all_methods if m not in current_methods]
        
        if "enhance_preprocessing" in optimization_suggestions:
            # 전처리 향상
            updated_methods.append("enhanced_preprocessing")
        
        if "try_multimodal" in optimization_suggestions:
            # 멀티모달 접근
            updated_methods.extend(["claude", "gemini"])
        
        return {
            **state,
            "processing_methods": updated_methods or state["processing_methods"],
            "retry_count": retry_count + 1,
            "processing_metadata": {
                **state.get("processing_metadata", {}),
                "optimization_applied": True,
                "optimization_strategies": optimization_suggestions,
                "retry_attempt": retry_count + 1
            },
            "messages": [f"처리 전략 최적화: {len(optimization_suggestions)}개 제안 적용"]
        }
    
    def extract_layout_elements(self, state: OCRWorkflowState) -> OCRWorkflowState:
        """레이아웃 요소 추출 노드"""
        file_path = state["file_path"]
        best_text = state["final_text"]
        
        # 레이아웃 분석 실행
        layout_elements = self._analyze_document_layout(file_path, best_text)
        
        # 구조화된 결과 생성
        structured_result = self._create_structured_result(layout_elements, best_text)
        
        return {
            **state,
            "layout_elements": [elem.to_dict() if hasattr(elem, 'to_dict') else elem for elem in layout_elements],
            "final_text": structured_result,
            "processing_metadata": {
                **state.get("processing_metadata", {}),
                "layout_elements_count": len(layout_elements),
                "structure_extracted": True
            },
            "messages": [f"레이아웃 분석 완료: {len(layout_elements)}개 요소 추출"]
        }
    
    def save_results(self, state: OCRWorkflowState) -> OCRWorkflowState:
        """결과 저장 노드"""
        document_id = state["document_id"]
        final_text = state["final_text"]
        
        # 결과 파일 저장
        saved_files = self._save_ocr_results(state)
        
        # 성능 메트릭 계산
        performance_metrics = self._calculate_performance_metrics(state)
        
        return {
            **state,
            "processing_metadata": {
                **state.get("processing_metadata", {}),
                "results_saved": saved_files,
                "performance_metrics": performance_metrics,
                "processing_completed": True,
                "completion_timestamp": datetime.now().isoformat()
            },
            "messages": [f"결과 저장 완료: {len(saved_files)}개 파일 생성"]
        }
    
    # ========================================================================
    # 헬퍼 메서드들
    # ========================================================================
    
    def _analyze_document_structure(self, file_path: str, file_type: str) -> Dict:
        """문서 구조 분석"""
        analysis = {
            "type": file_type,
            "complexity": "medium",
            "page_count": 1,
            "has_images": False,
            "has_tables": False,
            "language": "korean",
            "estimated_processing_time": 30
        }
        
        if file_type.lower() == "pdf":
            try:
                doc = fitz.open(file_path)
                analysis["page_count"] = len(doc)
                
                # 이미지와 테이블 감지
                for page in doc:
                    if page.get_images():
                        analysis["has_images"] = True
                    # 간단한 테이블 감지 (실제로는 더 정교한 방법 사용)
                    text = page.get_text()
                    if text.count('\t') > 10 or text.count('|') > 5:
                        analysis["has_tables"] = True
                
                doc.close()
                
                # 복잡도 계산
                complexity_score = 0
                complexity_score += min(analysis["page_count"] / 10, 1.0) * 0.3
                complexity_score += (1.0 if analysis["has_images"] else 0.0) * 0.3
                complexity_score += (1.0 if analysis["has_tables"] else 0.0) * 0.4
                
                if complexity_score < 0.3:
                    analysis["complexity"] = "low"
                elif complexity_score > 0.7:
                    analysis["complexity"] = "high"
                
            except Exception as e:
                logger.error(f"PDF 분석 오류: {e}")
        
        return analysis
    
    def _determine_processing_methods(self, document_analysis: Dict) -> List[str]:
        """처리 방법 결정"""
        methods = []
        
        complexity = document_analysis.get("complexity", "medium")
        file_type = document_analysis.get("type", "").lower()
        has_images = document_analysis.get("has_images", False)
        has_tables = document_analysis.get("has_tables", False)
        
        # 기본 무료 도구들
        if UNSTRUCTURED_AVAILABLE:
            methods.append("unstructured")
        
        if PDFTEXT_AVAILABLE and file_type == "pdf":
            methods.append("pdftext")
        
        # 복잡한 문서나 이미지가 있는 경우 AI 모델 추가
        if complexity == "high" or has_images or has_tables:
            methods.extend(["claude", "gemini"])
        
        # 간단한 문서도 하나의 AI 모델은 사용
        if complexity == "low" and len(methods) == 0:
            methods.append("claude")
        
        return methods
    
    def _process_with_unstructured(self, file_path: str) -> Dict:
        """unstructured 처리"""
        start_time = time.time()
        
        try:
            elements = partition(file_path)
            text = "\n".join([str(element) for element in elements])
            
            return {
                "success": True,
                "text": text,
                "processing_time": time.time() - start_time,
                "method": "unstructured",
                "elements_count": len(elements)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "processing_time": time.time() - start_time,
                "method": "unstructured"
            }
    
    def _process_with_pdftext(self, file_path: str) -> Dict:
        """pdftext 처리"""
        start_time = time.time()
        
        try:
            text = plain_text_output(file_path)
            
            return {
                "success": True,
                "text": text,
                "processing_time": time.time() - start_time,
                "method": "pdftext"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "processing_time": time.time() - start_time,
                "method": "pdftext"
            }
    
    def _process_with_claude(self, file_path: str) -> Dict:
        """Claude 처리"""
        start_time = time.time()
        
        try:
            # 이미지를 base64로 인코딩
            with open(file_path, "rb") as f:
                file_data = f.read()
                base64_data = base64.b64encode(file_data).decode('utf-8')
            
            # 파일 타입 결정
            file_ext = Path(file_path).suffix.lower()
            if file_ext == '.pdf':
                media_type = "application/pdf"
            elif file_ext in ['.png', '.jpg', '.jpeg']:
                media_type = f"image/{file_ext[1:]}"
            else:
                media_type = "application/octet-stream"
            
            payload = {
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 4000,
                "messages": [{
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": """이 문서의 한국어와 영어 텍스트를 정확히 OCR 처리해주세요.

처리 규칙:
1. 한글: 완성형 한글로 정확히 인식
2. 영어: 대소문자 구분하여 정확히 인식  
3. 숫자: 아라비아 숫자로 변환
4. 특수문자: 원본 그대로 유지
5. 레이아웃: 줄바꿈과 단락 구조 보존

텍스트만 출력해주세요:"""
                        },
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": base64_data
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
            
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                text = result['content'][0]['text']
                
                return {
                    "success": True,
                    "text": text,
                    "processing_time": time.time() - start_time,
                    "method": "claude"
                }
            else:
                return {
                    "success": False,
                    "error": f"Claude API 오류: {response.status_code}",
                    "processing_time": time.time() - start_time,
                    "method": "claude"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "processing_time": time.time() - start_time,
                "method": "claude"
            }
    
    def _process_with_gemini(self, file_path: str) -> Dict:
        """Gemini 처리"""
        start_time = time.time()
        
        try:
            # 이미지를 base64로 인코딩
            with open(file_path, "rb") as f:
                file_data = f.read()
                base64_data = base64.b64encode(file_data).decode('utf-8')
            
            # 파일 타입 결정
            file_ext = Path(file_path).suffix.lower()
            if file_ext in ['.png', '.jpg', '.jpeg']:
                mime_type = f"image/{file_ext[1:] if file_ext != '.jpg' else 'jpeg'}"
            else:
                mime_type = "image/png"  # 기본값
            
            payload = {
                "contents": [{
                    "parts": [
                        {
                            "text": """이 문서의 한국어와 영어 텍스트를 정확히 OCR 처리해주세요.

처리 규칙:
1. 한글: 완성형 한글로 정확히 인식
2. 영어: 대소문자 구분하여 정확히 인식  
3. 숫자: 아라비아 숫자로 변환
4. 특수문자: 원본 그대로 유지
5. 레이아웃: 줄바꿈과 단락 구조 보존

텍스트만 출력해주세요:"""
                        },
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": base64_data
                            }
                        }
                    ]
                }]
            }
            
            response = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={self.gemini_api_key}",
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                text = result['candidates'][0]['content']['parts'][0]['text']
                
                return {
                    "success": True,
                    "text": text,
                    "processing_time": time.time() - start_time,
                    "method": "gemini"
                }
            else:
                return {
                    "success": False,
                    "error": f"Gemini API 오류: {response.status_code}",
                    "processing_time": time.time() - start_time,
                    "method": "gemini"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "processing_time": time.time() - start_time,
                "method": "gemini"
            }
    
    def _evaluate_text_quality(self, text: str) -> float:
        """텍스트 품질 평가"""
        if not text or not text.strip():
            return 0.0
        
        quality_score = 0.0
        
        # 1. 길이 점수 (너무 짧지 않고 너무 길지 않음)
        length = len(text.strip())
        if 10 <= length <= 10000:
            quality_score += 0.3
        elif length > 10000:
            quality_score += 0.2
        else:
            quality_score += 0.1
        
        # 2. 문자 다양성 점수
        unique_chars = len(set(text))
        if unique_chars > 50:
            quality_score += 0.2
        elif unique_chars > 20:
            quality_score += 0.15
        else:
            quality_score += 0.1
        
        # 3. 구조 점수 (줄바꿈, 문장 부호 등)
        has_structure = any(char in text for char in ['\n', '.', '!', '?'])
        if has_structure:
            quality_score += 0.2
        
        # 4. 한글/영어 혼재 점수
        has_korean = any('\uac00' <= char <= '\ud7af' for char in text)
        has_english = any(char.isalpha() and ord(char) < 128 for char in text)
        
        if has_korean and has_english:
            quality_score += 0.2
        elif has_korean or has_english:
            quality_score += 0.15
        
        # 5. 노이즈 감점
        noise_chars = sum(1 for char in text if not (char.isalnum() or char.isspace() or char in '.,!?;:\n\t()[]{}'))
        noise_ratio = noise_chars / len(text) if text else 0
        
        if noise_ratio < 0.1:
            quality_score += 0.1
        elif noise_ratio > 0.3:
            quality_score -= 0.1
        
        return min(quality_score, 1.0)
    
    def _calculate_overall_quality(self, quality_scores: Dict[str, float]) -> float:
        """전체 품질 계산"""
        if not quality_scores:
            return 0.0
        
        # 최고 점수와 평균 점수의 가중 평균
        max_score = max(quality_scores.values())
        avg_score = sum(quality_scores.values()) / len(quality_scores)
        
        return max_score * 0.7 + avg_score * 0.3
    
    def _generate_optimization_suggestions(self, quality_scores: Dict, document_analysis: Dict, retry_count: int) -> List[str]:
        """최적화 제안 생성"""
        suggestions = []
        
        max_quality = max(quality_scores.values()) if quality_scores else 0
        avg_quality = sum(quality_scores.values()) / len(quality_scores) if quality_scores else 0
        
        # 품질이 낮은 경우 제안
        if max_quality < 0.5:
            suggestions.append("try_different_engines")
        
        if avg_quality < 0.3:
            suggestions.append("enhance_preprocessing")
        
        # 복잡한 문서인 경우
        if document_analysis.get("complexity") == "high" and max_quality < 0.7:
            suggestions.append("try_multimodal")
        
        # 재시도 횟수가 적은 경우
        if retry_count < 2 and max_quality < 0.6:
            suggestions.append("retry_with_optimization")
        
        return suggestions
    
    def _analyze_document_layout(self, file_path: str, text: str) -> List[LayoutElement]:
        """문서 레이아웃 분석"""
        layout_elements = []
        
        # 간단한 레이아웃 분석 (실제로는 더 정교한 분석 필요)
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            if not line.strip():
                continue
            
            # 간단한 카테고리 분류
            category = "paragraph"
            
            if len(line) < 50 and i == 0:
                category = "title"
            elif len(line) < 100 and line.isupper():
                category = "heading"
            elif line.strip().startswith(('•', '-', '*', '1.', '2.')):
                category = "list"
            elif '\t' in line or '|' in line:
                category = "table"
            
            element = LayoutElement(
                category=category,
                text=line.strip(),
                bbox=[0, 0, 0, 0],  # 실제로는 좌표 정보 필요
                confidence=0.8,
                page_num=1
            )
            
            layout_elements.append(element)
        
        return layout_elements
    
    def _create_structured_result(self, layout_elements: List[LayoutElement], text: str) -> str:
        """구조화된 결과 생성"""
        structured_parts = []
        
        for element in layout_elements:
            if hasattr(element, 'category'):
                category = element.category
                text_content = element.text
            else:
                category = element.get('category', 'paragraph')
                text_content = element.get('text', '')
            
            if category == "title":
                structured_parts.append(f"# {text_content}")
            elif category == "heading":
                structured_parts.append(f"## {text_content}")
            elif category == "list":
                structured_parts.append(f"- {text_content}")
            else:
                structured_parts.append(text_content)
        
        return '\n\n'.join(structured_parts) if structured_parts else text
    
    def _save_ocr_results(self, state: OCRWorkflowState) -> List[str]:
        """OCR 결과 저장"""
        document_id = state["document_id"]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        output_dir = Path("C:/Users/user/Dropbox/_RAG/RAG_OCR/OCR_Output")
        output_dir.mkdir(exist_ok=True)
        
        saved_files = []
        
        # 1. 텍스트 결과 저장
        text_file = output_dir / f"{document_id}_{timestamp}_text.txt"
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write(state["final_text"])
        saved_files.append(str(text_file))
        
        # 2. 메타데이터 저장
        metadata_file = output_dir / f"{document_id}_{timestamp}_metadata.json"
        metadata = {
            "document_id": document_id,
            "file_path": state["file_path"],
            "processing_timestamp": timestamp,
            "confidence_score": state["confidence_score"],
            "quality_scores": state["quality_scores"],
            "processing_methods": state["processing_methods"],
            "retry_count": state["retry_count"],
            "layout_elements_count": len(state.get("layout_elements", [])),
            "processing_metadata": state.get("processing_metadata", {})
        }
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        saved_files.append(str(metadata_file))
        
        # 3. 레이아웃 정보 저장 (있는 경우)
        if state.get("layout_elements"):
            layout_file = output_dir / f"{document_id}_{timestamp}_layout.json"
            with open(layout_file, 'w', encoding='utf-8') as f:
                json.dump(state["layout_elements"], f, ensure_ascii=False, indent=2)
            saved_files.append(str(layout_file))
        
        return saved_files
    
    def _calculate_performance_metrics(self, state: OCRWorkflowState) -> Dict:
        """성능 메트릭 계산"""
        return {
            "total_processing_time": "실시간 측정 필요",
            "confidence_score": state["confidence_score"],
            "retry_count": state["retry_count"],
            "methods_attempted": len(state["processing_methods"]),
            "success_rate": 1.0 if state["confidence_score"] > 0.6 else 0.0,
            "layout_elements_extracted": len(state.get("layout_elements", [])),
            "requires_human_review": state["requires_human_review"]
        }

# ============================================================================
# 조건부 판단 함수들
# ============================================================================

def decide_after_analysis(state: OCRWorkflowState) -> str:
    """문서 분석 후 다음 단계 결정"""
    processing_methods = state["processing_methods"]
    
    # 무료 도구 먼저 시도
    if any(method in processing_methods for method in ["unstructured", "pdftext"]):
        return "free_tools"
    else:
        return "ai_models"

def decide_after_free_tools(state: OCRWorkflowState) -> str:
    """무료 도구 후 다음 단계 결정"""
    quality_scores = state.get("quality_scores", {})
    processing_methods = state["processing_methods"]
    
    # 무료 도구 품질 확인
    free_tool_quality = max([
        quality_scores.get("unstructured", 0),
        quality_scores.get("pdftext", 0)
    ])
    
    # 품질이 좋으면 AI 모델 건너뛰기, 나쁘면 AI 모델 사용
    if free_tool_quality >= 0.8:
        return "evaluate"
    elif any(method in processing_methods for method in ["claude", "gemini"]):
        return "ai_models"
    else:
        return "evaluate"

def decide_ai_model_sequence(state: OCRWorkflowState) -> str:
    """AI 모델 순서 결정"""
    processing_methods = state["processing_methods"]
    ocr_results = state.get("ocr_results", {})
    
    # Claude 먼저, 그 다음 Gemini
    if "claude" in processing_methods and "claude" not in ocr_results:
        return "claude"
    elif "gemini" in processing_methods and "gemini" not in ocr_results:
        return "gemini"
    else:
        return "evaluate"

def decide_after_quality_evaluation(state: OCRWorkflowState) -> str:
    """품질 평가 후 다음 단계 결정"""
    confidence_score = state["confidence_score"]
    retry_count = state["retry_count"]
    requires_review = state["requires_human_review"]
    optimization_suggestions = state["optimization_suggestions"]
    
    # 품질이 좋으면 레이아웃 분석으로
    if confidence_score >= 0.7:
        return "layout_analysis"
    
    # 재시도 가능하고 제안이 있으면 최적화
    elif retry_count < 3 and optimization_suggestions:
        return "optimize"
    
    # 인간 리뷰가 필요하면 일단 저장
    elif requires_review:
        return "save_with_review"
    
    # 그 외에는 레이아웃 분석 진행
    else:
        return "layout_analysis"

def decide_after_optimization(state: OCRWorkflowState) -> str:
    """최적화 후 다음 단계 결정"""
    retry_count = state["retry_count"]
    
    if retry_count >= 3:
        return "layout_analysis"  # 재시도 한계 도달
    else:
        return "retry_processing"  # 재처리 실행

# ============================================================================
# LangGraph 워크플로우 구성
# ============================================================================

class LangGraphIntelligentOCRSystem:
    """LangGraph 기반 지능형 OCR 시스템"""
    
    def __init__(self, base_path: str = "C:/Users/user/Dropbox/_RAG"):
        self.base_path = Path(base_path)
        self.ocr_output_dir = self.base_path / "RAG_OCR" / "OCR_Output"
        self.ocr_output_dir.mkdir(parents=True, exist_ok=True)
        
        # LangGraph 설정
        self.memory = MemorySaver()
        self.workflow_nodes = OCRWorkflowNodes(self)
        self.workflow = self._create_workflow()
        
        logger.info("LangGraph Intelligent OCR System 초기화 완료")
    
    def _create_workflow(self) -> StateGraph:
        """LangGraph 워크플로우 생성"""
        workflow = StateGraph(OCRWorkflowState)
        
        # 노드 추가
        workflow.add_node("analyze", self.workflow_nodes.analyze_document)
        workflow.add_node("free_tools", self.workflow_nodes.execute_free_tools_ocr)
        workflow.add_node("claude", self.workflow_nodes.execute_claude_ocr)
        workflow.add_node("gemini", self.workflow_nodes.execute_gemini_ocr)
        workflow.add_node("evaluate", self.workflow_nodes.evaluate_results_quality)
        workflow.add_node("optimize", self.workflow_nodes.optimize_processing_strategy)
        workflow.add_node("layout_analysis", self.workflow_nodes.extract_layout_elements)
        workflow.add_node("save_results", self.workflow_nodes.save_results)
        
        # 시작점 설정
        workflow.set_entry_point("analyze")
        
        # 엣지 연결
        workflow.add_conditional_edges(
            "analyze",
            decide_after_analysis,
            {
                "free_tools": "free_tools",
                "ai_models": "claude"  # AI 모델부터 시작
            }
        )
        
        workflow.add_conditional_edges(
            "free_tools",
            decide_after_free_tools,
            {
                "ai_models": "claude",
                "evaluate": "evaluate"
            }
        )
        
        workflow.add_conditional_edges(
            "claude",
            decide_ai_model_sequence,
            {
                "gemini": "gemini",
                "evaluate": "evaluate"
            }
        )
        
        workflow.add_edge("gemini", "evaluate")
        
        workflow.add_conditional_edges(
            "evaluate",
            decide_after_quality_evaluation,
            {
                "layout_analysis": "layout_analysis",
                "optimize": "optimize",
                "save_with_review": "save_results"
            }
        )
        
        workflow.add_conditional_edges(
            "optimize",
            decide_after_optimization,
            {
                "retry_processing": "free_tools",  # 재처리는 무료 도구부터
                "layout_analysis": "layout_analysis"
            }
        )
        
        workflow.add_edge("layout_analysis", "save_results")
        workflow.add_edge("save_results", END)
        
        return workflow.compile(checkpointer=self.memory)
    
    async def process_document(self, file_path: str, document_id: str = None, thread_id: str = None) -> Dict:
        """문서 처리 실행"""
        if document_id is None:
            document_id = f"doc_{hashlib.md5(file_path.encode()).hexdigest()[:8]}"
        
        if thread_id is None:
            thread_id = f"ocr_{document_id}_{int(datetime.now().timestamp())}"
        
        # 파일 타입 확인
        file_ext = Path(file_path).suffix.lower()
        file_type = file_ext[1:] if file_ext else "unknown"
        
        # 초기 상태 설정
        initial_state = {
            "document_id": document_id,
            "file_path": file_path,
            "file_type": file_type,
            "document_analysis": {},
            "ocr_results": {},
            "quality_scores": {},
            "messages": [],
            "processing_methods": [],
            "retry_count": 0,
            "final_text": "",
            "layout_elements": [],
            "confidence_score": 0.0,
            "processing_metadata": {},
            "requires_human_review": False,
            "optimization_suggestions": []
        }
        
        # 워크플로우 실행
        config = {
            "configurable": {
                "thread_id": thread_id,
                "recursion_limit": 30
            }
        }
        
        try:
            result = await self.workflow.ainvoke(initial_state, config)
            
            logger.info(f"OCR 처리 완료: {file_path} - 품질 {result['confidence_score']:.2f}")
            
            return result
            
        except Exception as e:
            logger.error(f"OCR 워크플로우 실행 오류: {e}")
            return {"error": str(e), "file_path": file_path}

# ============================================================================
# 사용 예제
# ============================================================================

async def main():
    """사용 예제"""
    ocr_system = LangGraphIntelligentOCRSystem()
    
    # 테스트 파일들
    test_files = [
        "C:/Users/user/Dropbox/_RAG/RAG_OCR/OCR_Input/batch_sample_1.png",
        "C:/Users/user/Dropbox/_RAG/RAG_OCR/OCR_Input/test_document.pdf"
    ]
    
    for file_path in test_files:
        if Path(file_path).exists():
            print(f"\n=== OCR 처리 시작: {Path(file_path).name} ===")
            
            result = await ocr_system.process_document(file_path)
            
            if "error" not in result:
                print(f"최종 텍스트 길이: {len(result.get('final_text', ''))}")
                print(f"신뢰도 점수: {result['confidence_score']:.2f}")
                print(f"재시도 횟수: {result['retry_count']}")
                print(f"레이아웃 요소: {len(result.get('layout_elements', []))}개")
                print(f"인간 리뷰 필요: {result['requires_human_review']}")
                
                # 저장된 파일들
                saved_files = result.get('processing_metadata', {}).get('results_saved', [])
                print(f"저장된 파일: {len(saved_files)}개")
                
            else:
                print(f"오류: {result['error']}")
        else:
            print(f"파일 없음: {file_path}")

if __name__ == "__main__":
    asyncio.run(main())