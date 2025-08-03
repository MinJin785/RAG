#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced OCR 시스템 디버깅 테스트
"""

from enhanced_ocr_system import UltimateOCRSystem

def debug_test():
    print("=== Enhanced OCR 시스템 디버깅 ===")
    
    try:
        # OCR 시스템 초기화
        print("1. OCR 시스템 초기화...")
        ocr = UltimateOCRSystem()
        print("   초기화 완료!")
        
        # 이미지 경로
        test_image = "OCR_Input/korean_sample.png"
        print(f"2. 테스트 이미지: {test_image}")
        
        # FAST 모드 테스트
        print("3. FAST 모드 테스트...")
        try:
            result = ocr.extract_text(test_image, mode='fast')
            print(f"   성공: {result}")
        except Exception as e:
            print(f"   FAST 모드 에러: {e}")
            import traceback
            traceback.print_exc()
        
        # ULTIMATE 모드 테스트
        print("4. ULTIMATE 모드 테스트...")
        try:
            result = ocr.extract_text(test_image, mode='ultimate')
            print(f"   성공: {result}")
        except Exception as e:
            print(f"   ULTIMATE 모드 에러: {e}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"초기화 에러: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_test()