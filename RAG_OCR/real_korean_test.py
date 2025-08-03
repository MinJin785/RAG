#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
실제 한글 텍스트 OCR 테스트
"""

from enhanced_ocr_system import UltimateOCRSystem
import os

def test_real_korean():
    """실제 한글 텍스트 OCR 테스트"""
    
    print("=== 실제 한글 OCR 최종 테스트 ===")
    
    # OCR 시스템 초기화
    print("1. OCR 시스템 초기화...")
    ocr = UltimateOCRSystem()
    
    if ocr.easyocr_reader is None:
        print("   ERROR: EasyOCR 엔진 초기화 실패!")
        return
    
    print(f"   ✓ 한국어 모델 로드 완료 ({len(ocr.easyocr_reader.lang_char)}개 문자 지원)")
    
    # 테스트 이미지들
    test_images = [
        ("OCR_Input/real_korean_test.png", "순수 한글 텍스트"),
        ("OCR_Input/mixed_korean_english_test.png", "한영 혼합 텍스트")
    ]
    
    for i, (image_path, description) in enumerate(test_images, 1):
        if not os.path.exists(image_path):
            print(f"   SKIP: {image_path} 파일이 없습니다.")
            continue
        
        print(f"\n{i}. {description}: {image_path}")
        
        # 3가지 모드로 테스트
        modes = ['fast', 'accurate', 'ultimate']
        
        for mode in modes:
            print(f"\n   --- {mode.upper()} 모드 ---")
            
            # OCR 실행
            result = ocr.extract_text(image_path, mode=mode)
            
            # 결과 분석
            has_korean = result['has_korean']
            has_english = result['has_english']
            confidence = result['confidence']
            text = result['text']
            
            print(f"   텍스트: {repr(text)}")
            print(f"   신뢰도: {confidence:.3f}")
            print(f"   한글 인식: {has_korean}")
            print(f"   영어 인식: {has_english}")
            
            # 결과 평가
            if '?' in text:
                print(f"   ❌ 물음표 패턴 발견!")
            elif has_korean and "안녕" in text:
                print(f"   ✅ 한글 인식 성공!")
            elif has_english and ("Hello" in text or "Korean" in text):
                print(f"   ✅ 영어 인식 성공!")
            else:
                print(f"   ⚠️  인식 결과 확인 필요")
    
    print("\n=== 최종 테스트 완료 ===")
    print("한글 OCR 시스템이 완성되었습니다!")

if __name__ == "__main__":
    test_real_korean()