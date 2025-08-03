#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
한글+영어 특화 Claude + Gemini API OCR 시스템
Reference_Codes 테디노트 자료 기반 최적화
"""

import os
import base64
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime

# API 클라이언트
import requests
from PIL import Image
import io

# Reference_Codes 기반 라이브러리 (테디노트 자료에서 학습)
try:
    from unstructured.partition.pdf import partition_pdf
    UNSTRUCTURED_AVAILABLE = True
except ImportError:
    UNSTRUCTURED_AVAILABLE = False
    print("unstructured 라이브러리가 없습니다. pip install unstructured[all-docs] 실행 권장")

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KoreanEnglishOCR:
    """한글+영어 특화 OCR 시스템"""
    
    def __init__(self, claude_key: str = None, gemini_key: str = None):
        self.claude_key = claude_key or os.getenv('ANTHROPIC_API_KEY')
        self.gemini_key = gemini_key or os.getenv('GOOGLE_API_KEY')
        
        if not self.claude_key or not self.gemini_key:
            raise ValueError("Claude와 Gemini API 키가 필요합니다")
        
        # Claude API 설정
        self.claude_headers = {
            "Content-Type": "application/json",
            "x-api-key": self.claude_key,
            "anthropic-version": "2023-06-01"
        }
        
        # Gemini API 설정
        self.gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={self.gemini_key}"
        
        # 한글+영어 최적화 프롬프트 (Reference_Codes 기반)
        self.korean_english_prompt = """
한국어와 영어가 섞인 문서를 정확히 OCR 처리해주세요.

처리 규칙:
1. 한글: 완성형 한글로 정확히 인식
2. 영어: 대소문자 구분하여 정확히 인식  
3. 숫자: 아라비아 숫자로 변환
4. 특수문자: 원본 그대로 유지
5. 레이아웃: 줄바꿈과 단락 구조 보존

출력 형식:
- 텍스트만 출력 (마크다운 불필요)
- 줄바꿈은 원본과 동일하게
- 테이블이 있다면 탭으로 구분

시작:
"""

    def encode_image(self, image_path: str) -> str:
        """이미지를 base64로 인코딩"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def claude_ocr(self, image_path: str) -> Dict[str, Any]:
        """Claude API로 OCR 처리"""
        try:
            base64_image = self.encode_image(image_path)
            
            payload = {
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 4000,
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
                        {
                            "type": "text",
                            "text": self.korean_english_prompt
                        }
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
                text = result['content'][0]['text']
                
                return {
                    "success": True,
                    "text": text,
                    "confidence": 0.95,  # Claude는 일반적으로 높은 품질
                    "processing_time": process_time,
                    "engine": "claude-3.5-sonnet"
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
                "error": f"Claude OCR 실패: {str(e)}",
                "processing_time": 0
            }

    def gemini_ocr_chunking(self, image_path: str) -> Dict[str, Any]:
        """Gemini 2.0 Flash로 OCR + 청킹 동시 처리 (웹 검색 기법)"""
        try:
            base64_image = self.encode_image(image_path)
            
            # Gemini 2.0 Flash 혁신 기법: OCR + 청킹 통합
            chunking_prompt = """
이 이미지의 한국어와 영어 텍스트를 OCR 처리하고 의미 단위로 청킹해주세요.

처리 요구사항:
1. 한글+영어 정확한 인식
2. 의미 단위별로 <chunk>...</chunk> 태그로 분할
3. 각 청크는 100-500자 내외
4. 제목, 단락, 표는 별도 청크로 분리

출력 형식:
<chunk>
첫 번째 의미 단위 텍스트
</chunk>

<chunk>
두 번째 의미 단위 텍스트
</chunk>
"""
            
            payload = {
                "contents": [{
                    "parts": [
                        {
                            "inline_data": {
                                "mime_type": "image/png",
                                "data": base64_image
                            }
                        },
                        {
                            "text": chunking_prompt
                        }
                    ]
                }],
                "generationConfig": {
                    "temperature": 0.1,
                    "maxOutputTokens": 4000
                }
            }
            
            start_time = time.time()
            response = requests.post(self.gemini_url, json=payload, timeout=30)
            process_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                text = result['candidates'][0]['content']['parts'][0]['text']
                
                # <chunk> 태그 파싱
                import re
                chunks = re.findall(r'<chunk>(.*?)</chunk>', text, re.DOTALL)
                if not chunks:
                    chunks = [text]  # 태그가 없으면 전체를 하나의 청크로
                
                return {
                    "success": True,
                    "text": text,
                    "chunks": [chunk.strip() for chunk in chunks],
                    "chunk_count": len(chunks),
                    "confidence": 0.92,
                    "processing_time": process_time,
                    "engine": "gemini-2.0-flash"
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
                "error": f"Gemini OCR 실패: {str(e)}",
                "processing_time": 0
            }

    def hybrid_process(self, image_path: str) -> Dict[str, Any]:
        """하이브리드 처리: Claude(품질) + Gemini(청킹)"""
        print(f"\n=== 한글+영어 OCR 처리 시작: {image_path} ===")
        
        results = {
            "file_path": image_path,
            "timestamp": datetime.now().isoformat(),
            "claude_result": None,
            "gemini_result": None,
            "hybrid_result": None
        }
        
        # 1. Claude OCR (높은 품질)
        print("1. Claude OCR 처리 중...")
        claude_result = self.claude_ocr(image_path)
        results["claude_result"] = claude_result
        
        if claude_result["success"]:
            print(f"   ✅ Claude 성공 ({claude_result['processing_time']:.2f}초)")
        else:
            print(f"   ❌ Claude 실패: {claude_result.get('error', '알 수 없는 오류')}")
        
        # 2. Gemini OCR + 청킹
        print("2. Gemini OCR + 청킹 처리 중...")
        gemini_result = self.gemini_ocr_chunking(image_path)
        results["gemini_result"] = gemini_result
        
        if gemini_result["success"]:
            print(f"   ✅ Gemini 성공 ({gemini_result['processing_time']:.2f}초)")
            print(f"   📋 청크 개수: {gemini_result.get('chunk_count', 0)}개")
        else:
            print(f"   ❌ Gemini 실패: {gemini_result.get('error', '알 수 없는 오류')}")
        
        # 3. 하이브리드 결과 생성
        if claude_result["success"] and gemini_result["success"]:
            hybrid_result = {
                "success": True,
                "primary_text": claude_result["text"],  # Claude 텍스트를 메인으로
                "chunked_text": gemini_result["chunks"],  # Gemini 청킹 결과
                "confidence": (claude_result["confidence"] + gemini_result["confidence"]) / 2,
                "total_processing_time": claude_result["processing_time"] + gemini_result["processing_time"],
                "method": "hybrid_claude_gemini"
            }
            print("   🎯 하이브리드 결과 생성 완료")
            
        elif claude_result["success"]:
            hybrid_result = {
                "success": True,
                "primary_text": claude_result["text"],
                "chunked_text": [claude_result["text"]],  # 단일 청크로
                "confidence": claude_result["confidence"],
                "total_processing_time": claude_result["processing_time"],
                "method": "claude_only"
            }
            print("   📝 Claude 결과만 사용")
            
        elif gemini_result["success"]:
            hybrid_result = {
                "success": True,
                "primary_text": gemini_result["text"],
                "chunked_text": gemini_result["chunks"],
                "confidence": gemini_result["confidence"],
                "total_processing_time": gemini_result["processing_time"],
                "method": "gemini_only"
            }
            print("   🔍 Gemini 결과만 사용")
            
        else:
            hybrid_result = {
                "success": False,
                "error": "모든 OCR 엔진 실패",
                "method": "none"
            }
            print("   ❌ 모든 엔진 실패")
        
        results["hybrid_result"] = hybrid_result
        return results

    def save_results(self, results: Dict[str, Any], output_dir: str = "RAG_OCR/OCR_Output"):
        """결과 저장"""
        os.makedirs(output_dir, exist_ok=True)
        
        # 파일명 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = Path(results["file_path"]).stem
        
        # JSON 결과 저장
        json_path = f"{output_dir}/{filename}_korean_english_{timestamp}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        # 텍스트 결과 저장
        if results["hybrid_result"]["success"]:
            txt_path = f"{output_dir}/{filename}_korean_english_{timestamp}.txt"
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write("=== 한글+영어 OCR 결과 ===\n\n")
                f.write(f"처리 방식: {results['hybrid_result']['method']}\n")
                f.write(f"신뢰도: {results['hybrid_result']['confidence']:.2f}\n")
                f.write(f"처리 시간: {results['hybrid_result']['total_processing_time']:.2f}초\n\n")
                f.write("=== 메인 텍스트 ===\n")
                f.write(results['hybrid_result']['primary_text'])
                f.write("\n\n=== 청크별 분할 ===\n")
                for i, chunk in enumerate(results['hybrid_result']['chunked_text'], 1):
                    f.write(f"\n[청크 {i}]\n{chunk}\n")
        
        print(f"\n💾 결과 저장 완료:")
        print(f"   📄 JSON: {json_path}")
        if results["hybrid_result"]["success"]:
            print(f"   📝 TXT: {txt_path}")

def main():
    """메인 실행 함수"""
    try:
        # OCR 시스템 초기화
        ocr_system = KoreanEnglishOCR()
        print("🚀 한글+영어 OCR 시스템 초기화 완료")
        
        # 테스트 이미지 자동 처리
        input_dir = "RAG_OCR/OCR_Input"
        image_files = [
            "mixed_korean_english_test.png",
            "real_korean_test.png", 
            "korean_sample.png"
        ]
        
        for image_file in image_files:
            image_path = f"{input_dir}/{image_file}"
            if os.path.exists(image_path):
                results = ocr_system.hybrid_process(image_path)
                ocr_system.save_results(results)
                print("-" * 50)
            else:
                print(f"⚠️ 파일이 존재하지 않습니다: {image_path}")
        
        print("\n🎉 한글+영어 OCR 처리 완료!")
        
    except Exception as e:
        print(f"❌ 시스템 오류: {str(e)}")

if __name__ == "__main__":
    main()