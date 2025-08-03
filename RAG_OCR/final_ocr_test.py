#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
완전한 OCR 워크플로우 테스트
입력 → 처리 → 출력 저장
"""

from enhanced_ocr_system import UltimateOCRSystem
import os
import json
from datetime import datetime

def process_all_images():
    """OCR_Input의 모든 이미지를 처리하고 결과를 OCR_Output에 저장"""
    
    print("=== 완전한 OCR 워크플로우 테스트 ===")
    
    # OCR 시스템 초기화
    ocr = UltimateOCRSystem()
    
    # 입력 폴더의 모든 이미지 처리
    input_folder = "OCR_Input"
    output_folder = "OCR_Output"
    
    # 이미지 파일 찾기
    image_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif']
    image_files = []
    
    for file in os.listdir(input_folder):
        if any(file.lower().endswith(ext) for ext in image_extensions):
            image_files.append(file)
    
    print(f"발견된 이미지 파일: {len(image_files)}개")
    
    # 전체 결과 저장
    all_results = []
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    for i, image_file in enumerate(image_files, 1):
        print(f"\n[{i}/{len(image_files)}] 처리 중: {image_file}")
        
        image_path = os.path.join(input_folder, image_file)
        
        # OCR 처리 (3가지 모드로)
        fast_result = ocr.extract_text(image_path, mode='fast')
        accurate_result = ocr.extract_text(image_path, mode='accurate')
        ultimate_result = ocr.extract_text(image_path, mode='ultimate')
        
        # 결과 정리
        result_data = {
            'file_name': image_file,
            'timestamp': datetime.now().isoformat(),
            'fast_mode': {
                'text': fast_result['text'],
                'confidence': float(fast_result['confidence']),
                'processing_time': fast_result['processing_time'],
                'has_korean': fast_result['has_korean'],
                'has_english': fast_result['has_english']
            },
            'accurate_mode': {
                'text': accurate_result['text'],
                'confidence': float(accurate_result['confidence']),
                'processing_time': accurate_result['processing_time']
            },
            'ultimate_mode': {
                'text': ultimate_result['text'],
                'confidence': float(ultimate_result['confidence']),
                'processing_time': ultimate_result['processing_time']
            }
        }
        
        all_results.append(result_data)
        
        # 개별 결과 텍스트 파일로 저장
        text_filename = f"{os.path.splitext(image_file)[0]}_ocr_result.txt"
        text_path = os.path.join(output_folder, text_filename)
        
        with open(text_path, 'w', encoding='utf-8') as f:
            f.write(f"=== OCR 결과: {image_file} ===\n")
            f.write(f"처리 시간: {timestamp}\n\n")
            
            f.write("--- FAST 모드 ---\n")
            f.write(f"텍스트: {fast_result['text']}\n")
            f.write(f"신뢰도: {fast_result['confidence']:.3f}\n")
            f.write(f"처리 시간: {fast_result['processing_time']:.3f}초\n\n")
            
            f.write("--- ACCURATE 모드 ---\n")
            f.write(f"텍스트: {accurate_result['text']}\n")
            f.write(f"신뢰도: {accurate_result['confidence']:.3f}\n")
            f.write(f"처리 시간: {accurate_result['processing_time']:.3f}초\n\n")
            
            f.write("--- ULTIMATE 모드 ---\n")
            f.write(f"텍스트: {ultimate_result['text']}\n")
            f.write(f"신뢰도: {ultimate_result['confidence']:.3f}\n")
            f.write(f"처리 시간: {ultimate_result['processing_time']:.3f}초\n\n")
        
        print(f"   → {text_filename} 저장 완료")
    
    # 전체 결과 JSON으로 저장
    json_filename = f"ocr_batch_results_{timestamp}.json"
    json_path = os.path.join(output_folder, json_filename)
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    
    print(f"\n=== 배치 처리 완료 ===")
    print(f"처리된 이미지: {len(image_files)}개")
    print(f"개별 결과 파일: {len(image_files)}개")
    print(f"통합 결과 JSON: {json_filename}")
    print(f"출력 폴더: {output_folder}")
    
    # 시스템 성능 통계
    final_status = ocr.get_system_status()
    print(f"\n--- 최종 성능 통계 ---")
    for operation, stats in final_status['performance_stats'].items():
        print(f"{operation}: 평균 {stats['avg_time']:.3f}초 (총 {stats['count']}회)")
    
    return all_results

if __name__ == "__main__":
    process_all_images()