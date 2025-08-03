#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
실제 한글 텍스트 이미지 생성기
"""

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os

def create_korean_test_image():
    """한글 테스트 이미지 생성"""
    
    # 텍스트 내용
    korean_texts = [
        "안녕하세요",
        "한글 OCR 테스트",
        "대한민국",
        "인공지능 시스템",
        "텍스트 인식 성공"
    ]
    
    # 이미지 크기
    width, height = 600, 400
    
    # 이미지 생성 (흰 배경)
    image = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(image)
    
    # 기본 폰트 사용 (시스템에 있는 폰트)
    try:
        # Windows 기본 한글 폰트
        font_size = 30
        font = ImageFont.truetype("malgun.ttf", font_size)
    except:
        try:
            # 다른 한글 폰트
            font = ImageFont.truetype("gulim.ttc", font_size)
        except:
            # 기본 폰트
            font = ImageFont.load_default()
    
    # 텍스트 그리기
    y_position = 50
    for text in korean_texts:
        draw.text((50, y_position), text, fill='black', font=font)
        y_position += 60
    
    # 이미지 저장
    output_path = "OCR_Input/real_korean_test.png"
    image.save(output_path)
    print(f"한글 테스트 이미지 생성 완료: {output_path}")
    
    return output_path

def create_mixed_test_image():
    """한영 혼합 테스트 이미지 생성"""
    
    # 텍스트 내용
    mixed_texts = [
        "Hello 안녕하세요",
        "Korean OCR 한글 인식",
        "English 영어 Test 테스트",
        "AI System 인공지능 시스템",
        "Success 성공적인 Recognition 인식"
    ]
    
    # 이미지 크기
    width, height = 700, 400
    
    # 이미지 생성 (흰 배경)
    image = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(image)
    
    # 폰트 설정
    try:
        font_size = 28
        font = ImageFont.truetype("malgun.ttf", font_size)
    except:
        font = ImageFont.load_default()
    
    # 텍스트 그리기
    y_position = 50
    for text in mixed_texts:
        draw.text((50, y_position), text, fill='black', font=font)
        y_position += 60
    
    # 이미지 저장
    output_path = "OCR_Input/mixed_korean_english_test.png"
    image.save(output_path)
    print(f"한영 혼합 테스트 이미지 생성 완료: {output_path}")
    
    return output_path

if __name__ == "__main__":
    print("=== 한글 테스트 이미지 생성 ===")
    
    # OCR_Input 폴더 확인
    if not os.path.exists("OCR_Input"):
        os.makedirs("OCR_Input")
    
    # 이미지 생성
    korean_path = create_korean_test_image()
    mixed_path = create_mixed_test_image()
    
    print(f"생성된 파일:")
    print(f"1. {korean_path}")
    print(f"2. {mixed_path}")
    print("=== 생성 완료 ===")