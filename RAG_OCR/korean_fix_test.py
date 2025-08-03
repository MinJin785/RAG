#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
한글 OCR 문제 해결 테스트
"""

from enhanced_ocr_system import UltimateOCRSystem
import os

def test_korean_ocr():
    """한글 OCR 테스트"""
    
    print("=== 한글 OCR 문제 해결 테스트 ===")
    
    # OCR 시스템 초기화
    print("1. OCR 시스템 초기화 중...")
    ocr = UltimateOCRSystem()
    
    if ocr.easyocr_reader is None:
        print("   ERROR: EasyOCR 엔진 초기화 실패!")
        return
    
    print("   ✓ OCR 시스템 초기화 완료")
    
    # 지원 언어 확인
    print(f"   ✓ 지원 언어 문자 수: {len(ocr.easyocr_reader.lang_char)}개")
    
    # 테스트 이미지들
    test_images = [
        "OCR_Input/batch_sample_1.png",
        "OCR_Input/korean_sample.png",
        "OCR_Input/sample_test.png"
    ]
    
    for i, image_path in enumerate(test_images, 1):
        if not os.path.exists(image_path):
            print(f"   SKIP: {image_path} 파일이 없습니다.")
            continue
        
        print(f"\n{i}. 테스트 이미지: {image_path}")
        
        # OCR 실행
        result = ocr.extract_text(image_path, mode='fast')
        
        # 결과 출력
        print(f"   원본 텍스트: {repr(result['raw_text'])}")
        print(f"   후처리된 텍스트: {repr(result['text'])}")
        print(f"   신뢰도: {result['confidence']:.3f}")
        print(f"   한글 포함: {result['has_korean']}")
        print(f"   영어 포함: {result['has_english']}")
        
        # 물음표 검사
        if '?' in result['text']:
            print(f"   WARNING: 물음표 패턴 감지됨!")
        else:
            print(f"   ✓ 물음표 문제 없음")
    
    print("\n=== 테스트 완료 ===")

if __name__ == "__main__":
    test_korean_ocr()