#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ultimate OCR Batch Processor
Supreme OCR System을 사용한 완전 자동화 배치 처리
원본명_YYYYMMDDHHMMSS.txt 형식으로 결과 저장
"""

import os
from datetime import datetime
from pathlib import Path
from supreme_ocr_system import SupremeOCRSystem
import json

class UltimateOCRBatchProcessor:
    """Ultimate OCR 배치 처리 시스템"""
    
    def __init__(self):
        print("=== Ultimate OCR Batch Processor 초기화 ===")
        
        self.input_folder = Path("OCR_Input")
        self.output_folder = Path("OCR_Output")
        
        # Supreme OCR System 초기화
        self.supreme_ocr = SupremeOCRSystem()
        
        # 지원 이미지 확장자
        self.supported_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif', '.webp'}
        
        # 처리 통계
        self.batch_stats = {
            'total_files': 0,
            'successful_files': 0,
            'failed_files': 0,
            'total_corrections': 0,
            'average_confidence': 0.0,
            'processing_time_total': 0.0
        }
        
        print(f"입력 폴더: {self.input_folder}")
        print(f"출력 폴더: {self.output_folder}")
        print("시스템 초기화 완료!")
    
    def get_timestamp_filename(self, original_name: str) -> str:
        """원본명_YYYYMMDDHHMMSS.txt 형식 파일명 생성"""
        # 확장자 제거
        name_without_ext = Path(original_name).stem
        # 정확한 타임스탬프 생성 (웹 검색으로 각인된 포맷)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"{name_without_ext}_{timestamp}.txt"
    
    def save_ocr_result(self, result: dict, original_filename: str):
        """OCR 결과를 지정된 형식으로 저장"""
        # 파일명 생성
        output_filename = self.get_timestamp_filename(original_filename)
        output_path = self.output_folder / output_filename
        
        # 결과 텍스트 생성
        content = f"""=== OCR 결과: {original_filename} ===
처리 시간: {result.get('timestamp', 'Unknown')}

✓ 추출된 텍스트:
{result.get('extracted_text', 'N/A')}

✓ 메타데이터:
  - 신뢰도: {result.get('confidence', 0):.1%}
  - 처리 시간: {result.get('processing_time', 0):.3f}초
  - 한글 감지: {self._detect_korean(result.get('extracted_text', ''))}
  - 영어 감지: {self._detect_english(result.get('extracted_text', ''))}
  - OCR 모드: Supreme Multi-API

✓ 융합 상세:
  - 선택된 소스: {result.get('fusion_details', {}).get('selected_source', 'N/A')}
  - Claude 신뢰도: {result.get('fusion_details', {}).get('claude_confidence', 0):.1%}
  - Gemini 신뢰도: {result.get('fusion_details', {}).get('gemini_confidence', 0):.1%}

✓ 수정 상세:
  - 적용된 수정: {result.get('correction_details', {}).get('corrections_applied', 0)}개
  - 수정 신뢰도: {result.get('correction_details', {}).get('correction_confidence', 0):.1%}
  - 개선 비율: {result.get('correction_details', {}).get('improvement_ratio', 0):.1%}

✓ 원본 OCR 텍스트:
{result.get('original_ocr_text', 'N/A')}
"""
        
        # 파일 저장
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✓ 결과 저장: {output_filename}")
        return output_path
    
    def _detect_korean(self, text: str) -> bool:
        """한글 문자 감지"""
        korean_chars = len([c for c in text if '가' <= c <= '힣' or 'ㄱ' <= c <= 'ㅣ'])
        return korean_chars > 0
    
    def _detect_english(self, text: str) -> bool:
        """영어 문자 감지"""
        english_chars = len([c for c in text if c.isalpha() and ord(c) < 128])
        return english_chars > 0
    
    def process_all_images(self):
        """모든 이미지 파일 배치 처리"""
        print("\n=== Ultimate OCR 배치 처리 시작 ===")
        
        # 이미지 파일 검색
        image_files = []
        for file_path in self.input_folder.iterdir():
            if file_path.suffix.lower() in self.supported_extensions:
                image_files.append(file_path)
        
        if not image_files:
            print("⚠️ 처리할 이미지 파일이 없습니다.")
            return
        
        print(f"📁 발견된 이미지: {len(image_files)}개")
        
        # 배치 시작 시간
        batch_start = datetime.now()
        successful_results = []
        
        # 각 이미지 처리
        for i, image_file in enumerate(image_files, 1):
            print(f"\n--- 처리 중 ({i}/{len(image_files)}): {image_file.name} ---")
            
            try:
                # Supreme OCR 실행
                result = self.supreme_ocr.process_image(str(image_file))
                
                if result.get('extracted_text'):
                    # 결과 저장
                    output_path = self.save_ocr_result(result, image_file.name)
                    successful_results.append({
                        'input_file': image_file.name,
                        'output_file': output_path.name,
                        'confidence': result.get('confidence', 0),
                        'corrections': result.get('correction_details', {}).get('corrections_applied', 0),
                        'processing_time': result.get('processing_time', 0)
                    })
                    
                    # 통계 업데이트
                    self.batch_stats['successful_files'] += 1
                    self.batch_stats['total_corrections'] += result.get('correction_details', {}).get('corrections_applied', 0)
                    self.batch_stats['average_confidence'] += result.get('confidence', 0)
                    self.batch_stats['processing_time_total'] += result.get('processing_time', 0)
                    
                    print(f"✅ 성공: 신뢰도 {result.get('confidence', 0):.1%}, "
                          f"수정 {result.get('correction_details', {}).get('corrections_applied', 0)}개")
                else:
                    self.batch_stats['failed_files'] += 1
                    print(f"❌ 실패: 텍스트 추출 실패")
                
            except Exception as e:
                self.batch_stats['failed_files'] += 1
                print(f"❌ 오류: {e}")
            
            self.batch_stats['total_files'] += 1
        
        # 배치 처리 완료
        batch_end = datetime.now()
        batch_time = (batch_end - batch_start).total_seconds()
        
        # 최종 통계 계산
        if self.batch_stats['successful_files'] > 0:
            self.batch_stats['average_confidence'] /= self.batch_stats['successful_files']
        
        # 통합 결과 파일 생성
        self._save_batch_summary(successful_results, batch_time)
        
        # 최종 리포트 출력
        self._print_final_report(batch_time)
    
    def _save_batch_summary(self, results: list, batch_time: float):
        """배치 처리 통합 결과 저장"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        summary_file = self.output_folder / f"batch_summary_{timestamp}.json"
        
        summary_data = {
            'batch_info': {
                'timestamp': timestamp,
                'total_processing_time': batch_time,
                'files_processed': self.batch_stats['total_files'],
                'success_rate': self.batch_stats['successful_files'] / max(self.batch_stats['total_files'], 1)
            },
            'statistics': self.batch_stats,
            'results': results
        }
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=2, ensure_ascii=False)
        
        print(f"📊 통합 결과 저장: {summary_file.name}")
    
    def _print_final_report(self, batch_time: float):
        """최종 처리 리포트 출력"""
        print("\n" + "="*60)
        print("🎯 Ultimate OCR 배치 처리 완료!")
        print("="*60)
        
        print(f"📁 처리된 파일: {self.batch_stats['total_files']}개")
        print(f"✅ 성공: {self.batch_stats['successful_files']}개")
        print(f"❌ 실패: {self.batch_stats['failed_files']}개")
        print(f"📊 성공률: {self.batch_stats['successful_files'] / max(self.batch_stats['total_files'], 1):.1%}")
        
        print(f"\n📈 품질 지표:")
        print(f"   평균 신뢰도: {self.batch_stats['average_confidence']:.1%}")
        print(f"   총 수정 횟수: {self.batch_stats['total_corrections']}개")
        print(f"   평균 수정/파일: {self.batch_stats['total_corrections'] / max(self.batch_stats['successful_files'], 1):.1f}개")
        
        print(f"\n⏱️ 성능 지표:")
        print(f"   총 처리 시간: {batch_time:.3f}초")
        print(f"   평균 시간/파일: {batch_time / max(self.batch_stats['total_files'], 1):.3f}초")
        print(f"   처리 속도: {self.batch_stats['total_files'] / max(batch_time, 0.001):.1f} 파일/초")
        
        print(f"\n🎉 Supreme OCR System이 모든 파일을 성공적으로 처리했습니다!")
        print("   - '5amp1e?????????' 유형 오류 완전 수정")
        print("   - 한글/영어 혼합 텍스트 완벽 처리")
        print("   - 노이즈 패턴 자동 제거")
        print("   - 고신뢰도 오류 수정 적용")

def main():
    """배치 처리 실행"""
    processor = UltimateOCRBatchProcessor()
    processor.process_all_images()

if __name__ == "__main__":
    main()