#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Claude 멀티모달 OCR 시스템
Claude API를 활용한 최고 성능 OCR + 전처리/후처리 파이프라인
"""

import cv2
import numpy as np
import base64
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import logging
from PIL import Image
import requests

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ClaudeOCRSystem:
    """Claude 기반 최고 성능 OCR 시스템"""
    
    def __init__(self):
        """시스템 초기화"""
        logger.info("=== Claude OCR 시스템 초기화 ===")
        
        # Claude API 설정 (실제 환경에서는 환경변수 사용)
        self.claude_api_key = os.getenv('ANTHROPIC_API_KEY', '')
        self.claude_api_url = "https://api.anthropic.com/v1/messages"
        
        # 성능 지표
        self.total_processed = 0
        self.total_time = 0.0
        
        logger.info("Claude OCR 시스템 초기화 완료!")
    
    def _scale_to_300_dpi(self, image: np.ndarray, target_dpi: int = 300) -> np.ndarray:
        """300 DPI로 이미지 스케일링 (웹 검색 해결책)"""
        height, width = image.shape[:2]
        
        # 현재 DPI 추정 (일반적으로 72 DPI로 가정)
        current_dpi = 72
        scale_factor = target_dpi / current_dpi
        
        # 스케일링
        new_width = int(width * scale_factor)
        new_height = int(height * scale_factor)
        
        # 고품질 스케일링
        scaled = cv2.resize(image, (new_width, new_height), 
                          interpolation=cv2.INTER_CUBIC)
        
        logger.info(f"이미지 스케일링: {width}x{height} -> {new_width}x{new_height} (300 DPI)")
        return scaled
    
    def _advanced_preprocessing(self, image: np.ndarray) -> np.ndarray:
        """고급 전처리 파이프라인 (웹 검색 기반 최적화)"""
        processed = image.copy()
        
        # 1. 300 DPI 스케일링
        processed = self._scale_to_300_dpi(processed)
        
        # 2. 그레이스케일 변환
        if len(processed.shape) == 3:
            processed = cv2.cvtColor(processed, cv2.COLOR_BGR2GRAY)
        
        # 3. CLAHE 적응형 대비 향상
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        processed = clahe.apply(processed)
        
        # 4. 양방향 필터링 (에지 보존 노이즈 제거)
        processed = cv2.bilateralFilter(processed, 9, 75, 75)
        
        # 5. 샤프닝 (텍스트 에지 강화)
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        processed = cv2.filter2D(processed, -1, kernel)
        
        # 6. 적응형 이진화
        processed = cv2.adaptiveThreshold(processed, 255, 
                                        cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                        cv2.THRESH_BINARY, 15, 4)
        
        # 7. 모폴로지 연산 (텍스트 정리)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        processed = cv2.morphologyEx(processed, cv2.MORPH_CLOSE, kernel)
        
        return processed
    
    def _image_to_base64(self, image: np.ndarray) -> str:
        """이미지를 base64로 인코딩"""
        # PIL Image로 변환
        if len(image.shape) == 3:
            image_pil = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        else:
            image_pil = Image.fromarray(image)
        
        # 메모리에서 인코딩
        import io
        buffer = io.BytesIO()
        image_pil.save(buffer, format='PNG')
        image_data = buffer.getvalue()
        
        # base64 인코딩
        encoded = base64.b64encode(image_data).decode('utf-8')
        return encoded
    
    def _claude_ocr_extract(self, image_base64: str) -> Dict:
        """Claude API를 통한 OCR 추출"""
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.claude_api_key,
            "anthropic-version": "2023-06-01"
        }
        
        payload = {
            "model": "claude-3-sonnet-20240229",
            "max_tokens": 4000,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": image_base64
                            }
                        },
                        {
                            "type": "text",
                            "text": """이미지에서 모든 텍스트를 정확히 추출해주세요. 

요구사항:
1. 한글과 영어 모두 정확히 인식
2. 레이아웃과 순서 유지
3. 특수문자, 숫자 포함
4. 불명확한 문자는 [?]로 표시

다음 JSON 형식으로 응답:
{
  "extracted_text": "추출된 텍스트",
  "confidence": 0.95,
  "language_detected": ["korean", "english"],
  "layout_preserved": true,
  "special_notes": "추가 정보"
}"""
                        }
                    ]
                }
            ]
        }
        
        try:
            # API 키가 없으면 시뮬레이션
            if not self.claude_api_key:
                logger.warning("Claude API 키가 없습니다. 시뮬레이션 모드로 실행...")
                return {
                    "extracted_text": "Claude API 시뮬레이션 결과 - 실제 키 설정시 정확한 OCR 수행",
                    "confidence": 0.98,
                    "language_detected": ["korean", "english"],
                    "layout_preserved": True,
                    "special_notes": "API 키 설정 필요"
                }
            
            response = requests.post(self.claude_api_url, headers=headers, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                content = result['content'][0]['text']
                
                # JSON 파싱 시도
                try:
                    return json.loads(content)
                except:
                    # JSON이 아니면 텍스트 그대로 반환
                    return {
                        "extracted_text": content,
                        "confidence": 0.90,
                        "language_detected": ["unknown"],
                        "layout_preserved": True,
                        "special_notes": "Raw text response"
                    }
            else:
                raise Exception(f"Claude API 오류: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Claude OCR 오류: {e}")
            return {
                "extracted_text": "",
                "confidence": 0.0,
                "language_detected": [],
                "layout_preserved": False,
                "special_notes": f"오류: {str(e)}"
            }
    
    def _post_process_text(self, claude_result: Dict) -> Dict:
        """후처리: Claude 결과 정제 및 향상"""
        text = claude_result.get('extracted_text', '')
        
        # 1. 한글 자모 분리 문제 해결
        text = self._fix_korean_separation(text)
        
        # 2. 공백 정규화
        text = ' '.join(text.split())
        
        # 3. 특수문자 정리
        text = text.replace('[?]', '').strip()
        
        # 4. 신뢰도 계산
        confidence = claude_result.get('confidence', 0.0)
        if len(text) > 0 and '[?]' not in claude_result.get('extracted_text', ''):
            confidence = min(confidence + 0.05, 1.0)  # 보정
        
        return {
            **claude_result,
            'extracted_text': text,
            'confidence': confidence,
            'post_processed': True
        }
    
    def _fix_korean_separation(self, text: str) -> str:
        """한글 자모 분리 문제 해결"""
        import re
        
        # 자모 분리된 패턴 복원
        text = re.sub(r'([가-힣])\s+([ㄱ-ㅎㅏ-ㅣ])', r'\1\2', text)
        text = re.sub(r'([가-힣])\s+([가-힣])', r'\1\2', text)
        
        return text
    
    def extract_text(self, image_input, use_preprocessing: bool = True) -> Dict:
        """최고 성능 Claude OCR 실행"""
        start_time = datetime.now()
        
        logger.info("=== Claude OCR 시작 ===")
        
        try:
            # 이미지 로드
            if isinstance(image_input, str):
                image = cv2.imread(image_input)
                if image is None:
                    raise ValueError(f"이미지 로드 실패: {image_input}")
            else:
                image = image_input.copy()
            
            logger.info(f"원본 이미지 크기: {image.shape}")
            
            # 전처리 적용
            if use_preprocessing:
                logger.info("고급 전처리 적용 중...")
                processed_image = self._advanced_preprocessing(image)
                logger.info("전처리 완료")
            else:
                processed_image = image
            
            # base64 인코딩
            logger.info("Claude API 요청 준비 중...")
            image_base64 = self._image_to_base64(processed_image)
            
            # Claude OCR 실행
            logger.info("Claude OCR 실행 중...")
            claude_result = self._claude_ocr_extract(image_base64)
            
            # 후처리
            logger.info("후처리 적용 중...")
            final_result = self._post_process_text(claude_result)
            
            # 성능 통계
            processing_time = (datetime.now() - start_time).total_seconds()
            self.total_processed += 1
            self.total_time += processing_time
            
            # 최종 결과
            result = {
                **final_result,
                'processing_time': processing_time,
                'preprocessing_applied': use_preprocessing,
                'total_processed': self.total_processed,
                'average_time': self.total_time / self.total_processed,
                'timestamp': datetime.now().strftime("%Y%m%d%H%M%S")
            }
            
            logger.info(f"Claude OCR 완료! 신뢰도: {result['confidence']:.1%}, 시간: {processing_time:.3f}초")
            return result
            
        except Exception as e:
            logger.error(f"Claude OCR 시스템 오류: {e}")
            return {
                'extracted_text': '',
                'confidence': 0.0,
                'error': str(e),
                'processing_time': (datetime.now() - start_time).total_seconds(),
                'preprocessing_applied': use_preprocessing,
                'timestamp': datetime.now().strftime("%Y%m%d%H%M%S")
            }

def main():
    """테스트 실행"""
    print("=== Claude OCR 시스템 테스트 ===")
    
    # 시스템 초기화
    claude_ocr = ClaudeOCRSystem()
    
    # 테스트 이미지들
    test_images = [
        "OCR_Input/batch_sample_1.png",
        "OCR_Input/korean_sample.png",
        "OCR_Input/real_korean_test.png"
    ]
    
    for image_path in test_images:
        if os.path.exists(image_path):
            print(f"\n--- 테스트: {image_path} ---")
            
            # Claude OCR 실행
            result = claude_ocr.extract_text(image_path)
            
            print(f"추출된 텍스트: {result['extracted_text']}")
            print(f"신뢰도: {result['confidence']:.1%}")
            print(f"처리 시간: {result['processing_time']:.3f}초")
            print(f"감지 언어: {result.get('language_detected', [])}")
            
if __name__ == "__main__":
    main()