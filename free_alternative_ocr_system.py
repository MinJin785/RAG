#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
무료 대안 OCR 시스템: unstructured + pdftext + Claude + Gemini
Reference_Codes 테디노트 기법 기반
"""

import os
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime

# 무료 대안 라이브러리들
try:
    from unstructured.partition.pdf import partition_pdf
    from unstructured.partition.image import partition_image
    UNSTRUCTURED_AVAILABLE = True
except ImportError:
    UNSTRUCTURED_AVAILABLE = False

try:
    from pdftext.extraction import plain_text_output, dictionary_output
    PDFTEXT_AVAILABLE = True
except ImportError:
    PDFTEXT_AVAILABLE = False

# Claude + Gemini API
import requests
import base64
from PIL import Image
import io

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FreeAlternativeOCR:
    """무료 대안 OCR 시스템"""
    
    def __init__(self, claude_key: str = None, gemini_key: str = None):
        self.claude_key = claude_key or os.getenv('ANTHROPIC_API_KEY')
        self.gemini_key = gemini_key or os.getenv('GOOGLE_API_KEY')
        
        # API 설정
        if self.claude_key:
            self.claude_headers = {
                "Content-Type": "application/json",
                "x-api-key": self.claude_key,
                "anthropic-version": "2023-06-01"
            }
        
        if self.gemini_key:
            self.gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={self.gemini_key}"
        
        print(f"🔧 시스템 초기화:")
        print(f"   📚 unstructured: {'✅' if UNSTRUCTURED_AVAILABLE else '❌'}")
        print(f"   📄 pdftext: {'✅' if PDFTEXT_AVAILABLE else '❌'}")
        print(f"   🤖 Claude API: {'✅' if self.claude_key else '❌'}")
        print(f"   🔍 Gemini API: {'✅' if self.gemini_key else '❌'}")

    def unstructured_process(self, file_path: str) -> Dict[str, Any]:
        """unstructured로 PDF/이미지 처리 (테디노트 기법)"""
        if not UNSTRUCTURED_AVAILABLE:
            return {"success": False, "error": "unstructured 라이브러리 없음"}
        
        try:
            start_time = time.time()
            file_ext = Path(file_path).suffix.lower()
            
            if file_ext == '.pdf':
                # PDF 처리 (테디노트 Reference_Codes 기법)
                elements = partition_pdf(
                    filename=file_path,
                    extract_images_in_pdf=True,      # 이미지 추출
                    infer_table_structure=True,      # 테이블 구조 추론
                    chunking_strategy="by_title",    # 제목별 청킹
                    max_characters=1000,             # 최대 문자 수
                    new_after_n_chars=800,           # 새 청크 생성 기준
                    combine_text_under_n_chars=200   # 짧은 텍스트 결합
                )
            else:
                # 이미지 처리
                elements = partition_image(filename=file_path)
            
            process_time = time.time() - start_time
            
            # 요소별 분류 (테디노트 기법)
            texts = []
            tables = []
            images = []
            
            for element in elements:
                element_type = str(type(element))
                if "Table" in element_type:
                    tables.append(str(element))
                elif "Image" in element_type:
                    images.append(str(element))
                else:
                    texts.append(str(element))
            
            combined_text = "\n\n".join(texts)
            
            return {
                "success": True,
                "text": combined_text,
                "tables": tables,
                "images": images,
                "total_elements": len(elements),
                "processing_time": process_time,
                "method": "unstructured_partition"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"unstructured 처리 실패: {str(e)}",
                "processing_time": 0
            }

    def pdftext_process(self, file_path: str) -> Dict[str, Any]:
        """pdftext로 PDF 처리 (PyMuPDF보다 빠름)"""
        if not PDFTEXT_AVAILABLE or not file_path.lower().endswith('.pdf'):
            return {"success": False, "error": "pdftext PDF 전용 또는 라이브러리 없음"}
        
        try:
            start_time = time.time()
            
            # 단순 텍스트 추출
            plain_text = plain_text_output(file_path, sort=True)
            
            # 구조화된 블록/라인 정보
            structured_data = dictionary_output(file_path, sort=True)
            
            process_time = time.time() - start_time
            
            # 페이지별 통계
            page_stats = []
            for page_data in structured_data:
                blocks = page_data.get('blocks', [])
                page_stats.append({
                    "page": page_data.get('page', 0),
                    "blocks": len(blocks),
                    "bbox": page_data.get('bbox', [])
                })
            
            return {
                "success": True,
                "text": plain_text,
                "structured_data": structured_data,
                "page_stats": page_stats,
                "total_pages": len(structured_data),
                "processing_time": process_time,
                "method": "pdftext_extraction"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"pdftext 처리 실패: {str(e)}",
                "processing_time": 0
            }

    def claude_verify(self, image_path: str, extracted_text: str) -> Dict[str, Any]:
        """Claude로 추출된 텍스트 검증"""
        if not self.claude_key:
            return {"success": False, "error": "Claude API 키 없음"}
        
        try:
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
            if extracted_text.strip():
                verify_prompt = f"""
다음은 무료 도구로 추출한 텍스트입니다:

{extracted_text}

이미지와 비교해서 누락되거나 잘못된 부분이 있다면 수정해주세요.
특히 한글과 영어 정확성을 중점적으로 검토해주세요.

수정된 텍스트만 출력해주세요:
"""
            else:
                verify_prompt = """
이 이미지의 한국어와 영어 텍스트를 정확히 OCR 처리해주세요.

처리 규칙:
1. 한글: 완성형 한글로 정확히 인식
2. 영어: 대소문자 구분하여 정확히 인식  
3. 숫자: 아라비아 숫자로 변환
4. 특수문자: 원본 그대로 유지
5. 레이아웃: 줄바꿈과 단락 구조 보존

텍스트만 출력해주세요:
"""
            
            payload = {
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 2000,
                "messages": [{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": base64_image
                            }
                        },
                        {"type": "text", "text": verify_prompt}
                    ]
                }]
            }
            
            start_time = time.time()
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers=self.claude_headers,
                json=payload,
                timeout=30
            )
            process_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                verified_text = result['content'][0]['text']
                
                return {
                    "success": True,
                    "verified_text": verified_text,
                    "processing_time": process_time,
                    "method": "claude_verification"
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
                "error": f"Claude 검증 실패: {str(e)}",
                "processing_time": 0
            }

    def gemini_enhance(self, extracted_text: str) -> Dict[str, Any]:
        """Gemini로 텍스트 품질 향상 및 청킹"""
        if not self.gemini_key:
            return {"success": False, "error": "Gemini API 키 없음"}
        
        try:
            enhance_prompt = f"""
다음 텍스트를 더 읽기 쉽고 구조화된 형태로 개선해주세요:

{extracted_text}

개선 요구사항:
1. 맞춤법과 띄어쓰기 정리
2. 문단 구조 정리
3. 의미 단위별로 <chunk>...</chunk> 태그로 분할
4. 한글과 영어 정확성 검토

개선된 텍스트를 출력해주세요:
"""
            
            payload = {
                "contents": [{
                    "parts": [{"text": enhance_prompt}]
                }],
                "generationConfig": {
                    "temperature": 0.1,
                    "maxOutputTokens": 2000
                }
            }
            
            start_time = time.time()
            response = requests.post(self.gemini_url, json=payload, timeout=30)
            process_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                enhanced_text = result['candidates'][0]['content']['parts'][0]['text']
                
                # 청크 추출
                import re
                chunks = re.findall(r'<chunk>(.*?)</chunk>', enhanced_text, re.DOTALL)
                if not chunks:
                    chunks = [enhanced_text]
                
                return {
                    "success": True,
                    "enhanced_text": enhanced_text,
                    "chunks": [chunk.strip() for chunk in chunks],
                    "chunk_count": len(chunks),
                    "processing_time": process_time,
                    "method": "gemini_enhancement"
                }
            else:
                return {
                    "success": False,
                    "error": f"Gemini API 오류: {response.status_code}",
                    "processing_time": process_time
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Gemini 향상 실패: {str(e)}",
                "processing_time": 0
            }

    def complete_process(self, file_path: str) -> Dict[str, Any]:
        """완전한 무료 대안 처리 파이프라인"""
        print(f"\n🚀 무료 대안 OCR 시작: {file_path}")
        
        results = {
            "file_path": file_path,
            "timestamp": datetime.now().isoformat(),
            "unstructured_result": None,
            "pdftext_result": None,
            "claude_verification": None,
            "gemini_enhancement": None,
            "final_result": None
        }
        
        # 1. unstructured 처리
        print("1️⃣ unstructured 처리 중...")
        unstructured_result = self.unstructured_process(file_path)
        results["unstructured_result"] = unstructured_result
        
        if unstructured_result["success"]:
            print(f"   ✅ 성공 ({unstructured_result['processing_time']:.2f}초)")
            print(f"   📊 요소: {unstructured_result.get('total_elements', 0)}개")
        else:
            print(f"   ❌ 실패: {unstructured_result.get('error', '알 수 없음')}")
        
        # 2. pdftext 처리 (PDF인 경우)
        pdftext_result = None
        if file_path.lower().endswith('.pdf'):
            print("2️⃣ pdftext 처리 중...")
            pdftext_result = self.pdftext_process(file_path)
            results["pdftext_result"] = pdftext_result
            
            if pdftext_result["success"]:
                print(f"   ✅ 성공 ({pdftext_result['processing_time']:.2f}초)")
                print(f"   📄 페이지: {pdftext_result.get('total_pages', 0)}개")
            else:
                print(f"   ❌ 실패: {pdftext_result.get('error', '알 수 없음')}")
        else:
            print("2️⃣ pdftext: PDF 파일이 아니므로 건너뜀")
        
        # 최고 품질 텍스트 선택
        best_text = ""
        best_method = "none"
        
        if unstructured_result["success"]:
            best_text = unstructured_result["text"]
            best_method = "unstructured"
        elif pdftext_result and pdftext_result["success"]:
            best_text = pdftext_result["text"]
            best_method = "pdftext"
        
        if not best_text:
            print("⚠️ 무료 도구 실패, Claude/Gemini로 대체 시도")
            
            # 무료 도구 실패 시 Claude/Gemini 직접 사용
            if file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
                print("🔄 Claude 직접 OCR 시도...")
                claude_direct = self.claude_verify(file_path, "")  # 빈 텍스트로 직접 OCR
                if claude_direct["success"]:
                    best_text = claude_direct["verified_text"]
                    best_method = "claude_direct"
                    print(f"   ✅ Claude 직접 성공")
                else:
                    print(f"   ❌ Claude 직접 실패")
            
            if not best_text:
                print("❌ 모든 방법 실패")
                results["final_result"] = {"success": False, "error": "모든 방법 실패"}
                return results
        
        # 3. Claude 검증 (이미지 파일인 경우)
        if file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
            print("3️⃣ Claude 검증 중...")
            claude_verification = self.claude_verify(file_path, best_text)
            results["claude_verification"] = claude_verification
            
            if claude_verification["success"]:
                print(f"   ✅ 검증 완료 ({claude_verification['processing_time']:.2f}초)")
                best_text = claude_verification["verified_text"]
                best_method += "+claude"
            else:
                print(f"   ⚠️ 검증 실패: {claude_verification.get('error', '알 수 없음')}")
        
        # 4. Gemini 품질 향상
        print("4️⃣ Gemini 품질 향상 중...")
        gemini_enhancement = self.gemini_enhance(best_text)
        results["gemini_enhancement"] = gemini_enhancement
        
        if gemini_enhancement["success"]:
            print(f"   ✅ 향상 완료 ({gemini_enhancement['processing_time']:.2f}초)")
            print(f"   📋 청크: {gemini_enhancement.get('chunk_count', 0)}개")
            final_text = gemini_enhancement["enhanced_text"]
            chunks = gemini_enhancement["chunks"]
            best_method += "+gemini"
        else:
            print(f"   ⚠️ 향상 실패: {gemini_enhancement.get('error', '알 수 없음')}")
            final_text = best_text
            chunks = [best_text]
        
        # 5. 최종 결과
        total_time = sum([
            unstructured_result.get("processing_time", 0),
            pdftext_result.get("processing_time", 0) if pdftext_result else 0,
            claude_verification.get("processing_time", 0) if results["claude_verification"] else 0,
            gemini_enhancement.get("processing_time", 0)
        ])
        
        results["final_result"] = {
            "success": True,
            "final_text": final_text,
            "chunks": chunks,
            "chunk_count": len(chunks),
            "processing_method": best_method,
            "total_processing_time": total_time,
            "cost_estimate": "무료" if "claude" not in best_method and "gemini" not in best_method else "매우 저렴"
        }
        
        print(f"🎉 완료! 방식: {best_method}, 시간: {total_time:.2f}초")
        return results

    def save_results(self, results: Dict[str, Any], output_dir: str = "OCR_Output"):
        """결과 저장"""
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = Path(results["file_path"]).stem
        
        # JSON 저장
        json_path = f"{output_dir}/{filename}_free_alternative_{timestamp}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        # 텍스트 저장
        if results["final_result"]["success"]:
            txt_path = f"{output_dir}/{filename}_free_alternative_{timestamp}.txt"
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write("=== 무료 대안 OCR 결과 ===\n\n")
                f.write(f"처리 방식: {results['final_result']['processing_method']}\n")
                f.write(f"총 처리 시간: {results['final_result']['total_processing_time']:.2f}초\n")
                f.write(f"비용: {results['final_result']['cost_estimate']}\n\n")
                f.write("=== 최종 텍스트 ===\n")
                f.write(results['final_result']['final_text'])
                f.write("\n\n=== 청크별 분할 ===\n")
                for i, chunk in enumerate(results['final_result']['chunks'], 1):
                    f.write(f"\n[청크 {i}]\n{chunk}\n")
        
        print(f"\n💾 결과 저장:")
        print(f"   📄 JSON: {json_path}")
        if results["final_result"]["success"]:
            print(f"   📝 TXT: {txt_path}")

def main():
    """메인 실행"""
    try:
        # 무료 대안 시스템 초기화
        ocr_system = FreeAlternativeOCR()
        
        # 테스트 파일들
        test_files = [
            "RAG_OCR/OCR_Input/real_korean_test.png",
            "RAG_OCR/OCR_Input/korean_sample.png",
            "RAG_OCR/OCR_Input/ocr test.pdf"
        ]
        
        for file_path in test_files:
            if os.path.exists(file_path):
                results = ocr_system.complete_process(file_path)
                ocr_system.save_results(results)
                print("-" * 60)
            else:
                print(f"⚠️ 파일 없음: {file_path}")
        
        print("\n🎊 무료 대안 OCR 시스템 테스트 완료!")
        
    except Exception as e:
        print(f"❌ 시스템 오류: {str(e)}")

if __name__ == "__main__":
    main()