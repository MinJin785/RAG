#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
간단한 OCR 테스트 스크립트
"""

import easyocr
import cv2
import numpy as np
import os

# 테스트용 간단한 OCR
def simple_ocr_test():
    print("=== 간단한 EasyOCR 테스트 ===")
    
    # EasyOCR 초기화
    print("EasyOCR 초기화 중...")
    reader = easyocr.Reader(['en', 'ko'])
    print("EasyOCR 초기화 완료!")
    
    # 테스트 이미지 경로
    test_image = "OCR_Input/korean_sample.png"
    
    if not os.path.exists(test_image):
        print(f"테스트 이미지가 없습니다: {test_image}")
        return
    
    # 이미지 로드
    print(f"이미지 로드: {test_image}")
    image = cv2.imread(test_image)
    
    if image is None:
        print("이미지 로드 실패!")
        return
    
    print(f"이미지 크기: {image.shape}")
    
    # OCR 수행
    print("OCR 수행 중...")
    try:
        # detail=0 (텍스트만)
        print("detail=0 테스트...")
        results_0 = reader.readtext(image, detail=0)
        print(f"detail=0 결과: {results_0}")
        print(f"결과 타입: {type(results_0)}")
        
        # detail=1 (기본값, 좌표+텍스트+신뢰도)
        print("\ndetail=1 테스트...")
        results_1 = reader.readtext(image, detail=1)
        print(f"detail=1 결과 개수: {len(results_1)}")
        
        for i, result in enumerate(results_1):
            print(f"결과 {i}: {result}")
            bbox, text, confidence = result
            print(f"  텍스트: {text}")
            print(f"  신뢰도: {confidence}")
        
    except Exception as e:
        print(f"OCR 오류: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    simple_ocr_test()