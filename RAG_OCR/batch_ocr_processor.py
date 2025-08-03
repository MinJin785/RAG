#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR 배치 처리 시스템
OCR_Input 폴더의 모든 이미지를 처리하고 결과를 OCR_Output에 저장
파일명 형식: 원본명_YYYYMMDDHHMMSS.txt
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from enhanced_ocr_system import UltimateOCRSystem

class BatchOCRProcessor:
    def __init__(self):
        """배치 OCR 프로세서 초기화"""
        print("=== OCR 배치 처리 시스템 초기화 ===")
        
        # 폴더 경로 설정
        self.input_folder = Path("OCR_Input")
        self.output_folder = Path("OCR_Output")
        
        # OCR 시스템 초기화
        self.ocr_system = UltimateOCRSystem()
        
        # 지원하는 이미지 확장자
        self.supported_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif', '.webp'}
        
        print(f"입력 폴더: {self.input_folder}")
        print(f"출력 폴더: {self.output_folder}")
        print("시스템 초기화 완료!")
    
    def get_timestamp_filename(self, original_filename: str) -> str:
        """웹 검색으로 확인된 정확한 날짜/시간 포맷 사용"""
        # 정확한 포맷: %Y%m%d%H%M%S (웹 검색 결과 적용)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        name_without_ext = Path(original_filename).stem
        return f"{name_without_ext}_{timestamp}.txt"
    
    def scan_input_files(self) -> list:
        """OCR_Input 폴더에서 처리할 이미지 파일들을 스캔"""
        image_files = []
        
        if not self.input_folder.exists():
            print(f"ERROR: {self.input_folder} 폴더가 없습니다!")
            return image_files
        
        for file_path in self.input_folder.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in self.supported_extensions:
                image_files.append(file_path)
        
        print(f"발견된 이미지 파일: {len(image_files)}개")
        for file_path in image_files:
            print(f"  - {file_path.name}")
        
        return image_files
    
    def process_single_image(self, image_path: Path) -> dict:
        """단일 이미지 OCR 처리"""
        print(f"\n📄 처리 중: {image_path.name}")
        
        try:
            # OCR 실행 (ULTIMATE 모드 사용)
            result = self.ocr_system.extract_text(str(image_path), mode='ultimate')
            
            # 결과 출력
            print(f"  ✓ 텍스트 추출 완료")
            print(f"  ✓ 신뢰도: {result.get('confidence', 0):.1%}")
            print(f"  ✓ 처리 시간: {result.get('processing_time', 0):.3f}초")
            print(f"  ✓ 한글 감지: {result.get('has_korean', False)}")
            print(f"  ✓ 영어 감지: {result.get('has_english', False)}")
            
            return result
            
        except Exception as e:
            print(f"  ❌ 처리 실패: {e}")
            return {
                'text': '',
                'confidence': 0.0,
                'processing_time': 0.0,
                'has_korean': False,
                'has_english': False,
                'error': str(e)
            }
    
    def save_result(self, image_path: Path, ocr_result: dict) -> Path:
        """OCR 결과를 지정된 파일명 형식으로 저장"""
        # 정확한 날짜/시간 포맷으로 파일명 생성
        output_filename = self.get_timestamp_filename(image_path.name)
        output_path = self.output_folder / output_filename
        
        # 출력 폴더 확인/생성
        self.output_folder.mkdir(exist_ok=True)
        
        # 결과 내용 구성
        content = []
        content.append(f"=== OCR 결과: {image_path.name} ===")
        content.append(f"처리 시간: {datetime.now().strftime('%Y%m%d_%H%M%S')}")
        content.append("")
        
        # OCR 결과
        if 'error' in ocr_result:
            content.append(f"❌ 오류 발생: {ocr_result['error']}")
        else:
            content.append(f"✓ 추출된 텍스트:")
            content.append(f"{ocr_result.get('text', '').strip()}")
            content.append("")
            content.append(f"✓ 메타데이터:")
            content.append(f"  - 신뢰도: {ocr_result.get('confidence', 0):.1%}")
            content.append(f"  - 처리 시간: {ocr_result.get('processing_time', 0):.3f}초")
            content.append(f"  - 한글 감지: {ocr_result.get('has_korean', False)}")
            content.append(f"  - 영어 감지: {ocr_result.get('has_english', False)}")
            content.append(f"  - OCR 모드: {ocr_result.get('mode', 'unknown')}")
        
        # 파일 저장
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(content))
            
            print(f"  💾 결과 저장: {output_filename}")
            return output_path
            
        except Exception as e:
            print(f"  ❌ 저장 실패: {e}")
            return None
    
    def process_all_images(self) -> dict:
        """모든 이미지를 배치 처리"""
        print("\n" + "="*50)
        print("🚀 OCR 배치 처리 시작")
        print("="*50)
        
        # 이미지 파일 스캔
        image_files = self.scan_input_files()
        
        if not image_files:
            print("처리할 이미지 파일이 없습니다.")
            return {'total': 0, 'success': 0, 'failed': 0, 'results': []}
        
        # 처리 결과 추적
        results = {
            'total': len(image_files),
            'success': 0,
            'failed': 0,
            'results': []
        }
        
        # 각 이미지 처리
        for i, image_path in enumerate(image_files, 1):
            print(f"\n[{i}/{len(image_files)}] 처리 중...")
            
            # OCR 실행
            ocr_result = self.process_single_image(image_path)
            
            # 결과 저장
            output_path = self.save_result(image_path, ocr_result)
            
            # 통계 업데이트
            if output_path and 'error' not in ocr_result:
                results['success'] += 1
            else:
                results['failed'] += 1
            
            # 결과 기록
            results['results'].append({
                'input_file': str(image_path),
                'output_file': str(output_path) if output_path else None,
                'success': 'error' not in ocr_result,
                'confidence': ocr_result.get('confidence', 0),
                'processing_time': ocr_result.get('processing_time', 0)
            })
        
        return results
    
    def print_summary(self, results: dict):
        """처리 결과 요약 출력"""
        print("\n" + "="*50)
        print("📊 OCR 배치 처리 완료!")
        print("="*50)
        
        print(f"총 파일 수: {results['total']}")
        print(f"성공: {results['success']}")
        print(f"실패: {results['failed']}")
        print(f"성공률: {results['success']/results['total']*100:.1f}%" if results['total'] > 0 else "성공률: 0%")
        
        if results['success'] > 0:
            avg_confidence = sum(r['confidence'] for r in results['results'] if r['success']) / results['success']
            avg_time = sum(r['processing_time'] for r in results['results'] if r['success']) / results['success']
            print(f"평균 신뢰도: {avg_confidence:.1%}")
            print(f"평균 처리 시간: {avg_time:.3f}초")
        
        print(f"\n결과 파일 위치: {self.output_folder}/")
        print("파일명 형식: 원본명_YYYYMMDDHHMMSS.txt (웹 검색 확인된 정확한 포맷)")


def main():
    """메인 실행 함수"""
    try:
        # 배치 프로세서 초기화
        processor = BatchOCRProcessor()
        
        # 모든 이미지 처리
        results = processor.process_all_images()
        
        # 결과 요약 출력
        processor.print_summary(results)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 시스템 오류: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()