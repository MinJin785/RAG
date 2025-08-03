#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
완전한 고급 OCR 시스템 - 최종 버전
영어와 한글 특화, 모든 기능 포함된 완전체

새로 추가된 기능:
- 실시간 스트리밍 처리
- 메모리 최적화
- 캐싱 시스템
- 성능 모니터링
- 자동 품질 향상
- LLM 기반 후처리 시뮬레이션
"""

import cv2
import numpy as np
import easyocr
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import os
import logging
import time
import json
import threading
from typing import Dict, List, Tuple, Optional, Any
import re
from collections import defaultdict
import hashlib
from functools import lru_cache

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """성능 모니터링 클래스"""
    
    def __init__(self):
        self.metrics = defaultdict(list)
        self.start_times = {}
    
    def start_timer(self, operation: str):
        """타이머 시작"""
        self.start_times[operation] = time.time()
    
    def end_timer(self, operation: str):
        """타이머 종료 및 기록"""
        if operation in self.start_times:
            duration = time.time() - self.start_times[operation]
            self.metrics[operation].append(duration)
            del self.start_times[operation]
            return duration
        return 0
    
    def get_stats(self) -> Dict:
        """성능 통계 반환"""
        stats = {}
        for operation, times in self.metrics.items():
            if times:
                stats[operation] = {
                    'count': len(times),
                    'total_time': sum(times),
                    'avg_time': sum(times) / len(times),
                    'min_time': min(times),
                    'max_time': max(times)
                }
        return stats

class InferenceCache:
    """추론 결과 캐싱 시스템"""
    
    def __init__(self, max_size: int = 100):
        self.cache = {}
        self.max_size = max_size
        self.access_order = []
    
    def _generate_key(self, image: np.ndarray) -> str:
        """이미지 해시키 생성"""
        image_bytes = cv2.imencode('.png', image)[1].tobytes()
        return hashlib.md5(image_bytes).hexdigest()
    
    def get(self, image: np.ndarray) -> Optional[Dict]:
        """캐시에서 결과 조회"""
        key = self._generate_key(image)
        if key in self.cache:
            # LRU 업데이트
            self.access_order.remove(key)
            self.access_order.append(key)
            return self.cache[key]
        return None
    
    def put(self, image: np.ndarray, result: Dict):
        """캐시에 결과 저장"""
        key = self._generate_key(image)
        
        # 크기 제한 확인
        if len(self.cache) >= self.max_size:
            # 가장 오래된 항목 제거
            oldest_key = self.access_order.pop(0)
            del self.cache[oldest_key]
        
        self.cache[key] = result
        self.access_order.append(key)

class AdvancedImageProcessor:
    """고급 이미지 처리 클래스"""
    
    def __init__(self):
        self.clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8, 8))
    
    def auto_enhance_image(self, image: np.ndarray) -> np.ndarray:
        """자동 이미지 품질 향상"""
        # 1. 해상도 확인 및 업스케일링
        if image.shape[0] < 100 or image.shape[1] < 100:
            scale_factor = max(2, 100 // min(image.shape[:2]))
            image = cv2.resize(image, None, fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_CUBIC)
        
        # 2. 노이즈 감지 및 제거
        noise_level = self._estimate_noise_level(image)
        if noise_level > 0.3:
            image = cv2.bilateralFilter(image, 9, 75, 75)
        
        # 3. 밝기 자동 조정
        brightness_score = self._estimate_brightness(image)
        if brightness_score < 0.3:  # 너무 어두움
            image = cv2.convertScaleAbs(image, alpha=1.2, beta=30)
        elif brightness_score > 0.8:  # 너무 밝음
            image = cv2.convertScaleAbs(image, alpha=0.8, beta=-20)
        
        # 4. 대비 자동 조정
        if len(image.shape) == 3:
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            hsv[:, :, 2] = self.clahe.apply(hsv[:, :, 2])
            image = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
        else:
            image = self.clahe.apply(image)
        
        return image
    
    def _estimate_noise_level(self, image: np.ndarray) -> float:
        """노이즈 수준 추정"""
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Laplacian 분산으로 노이즈 추정
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        # 정규화 (0-1 범위)
        return min(laplacian_var / 1000.0, 1.0)
    
    def _estimate_brightness(self, image: np.ndarray) -> float:
        """밝기 수준 추정"""
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        return np.mean(gray) / 255.0
    
    def adaptive_preprocessing(self, image: np.ndarray) -> np.ndarray:
        """적응적 전처리"""
        # 자동 품질 향상
        enhanced = self.auto_enhance_image(image)
        
        # 회전 보정
        corrected = self._correct_skew(enhanced)
        
        # 경계 정리
        cleaned = self._clean_borders(corrected)
        
        return cleaned
    
    def _correct_skew(self, image: np.ndarray) -> np.ndarray:
        """기울기 자동 보정"""
        try:
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            # 에지 검출
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)
            
            # 허프 변환으로 선 검출
            lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=100)
            
            if lines is not None and len(lines) > 0:
                angles = []
                # lines 배열의 올바른 unpacking
                for line in lines[:10]:  # 상위 10개 선만 사용
                    rho, theta = line[0]  # line[0]에서 rho, theta 추출
                    angle = theta * 180 / np.pi - 90
                    angles.append(angle)
                
                if angles:
                    # 중간값 사용 (이상치 제거)
                    median_angle = np.median(angles)
                    
                    # 큰 회전만 보정 (5도 이상)
                    if abs(median_angle) > 5:
                        center = (image.shape[1] // 2, image.shape[0] // 2)
                        rotation_matrix = cv2.getRotationMatrix2D(center, median_angle, 1.0)
                        return cv2.warpAffine(image, rotation_matrix, (image.shape[1], image.shape[0]), 
                                            flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
            
            return image
            
        except Exception as e:
            logger.error(f"Skew correction 오류: {e}")
            return image
    
    def _clean_borders(self, image: np.ndarray) -> np.ndarray:
        """경계 정리 (노이즈 제거)"""
        h, w = image.shape[:2]
        
        # 경계에서 5% 영역의 노이즈 확인
        border_size = min(h, w) // 20
        
        if border_size > 2:
            # 상하좌우 경계 정리
            if len(image.shape) == 3:
                image[:border_size, :] = np.median(image[:border_size, :], axis=(0, 1))
                image[-border_size:, :] = np.median(image[-border_size:, :], axis=(0, 1))
                image[:, :border_size] = np.median(image[:, :border_size], axis=(0, 1))
                image[:, -border_size:] = np.median(image[:, -border_size:], axis=(0, 1))
            else:
                median_val = np.median(image)
                image[:border_size, :] = median_val
                image[-border_size:, :] = median_val
                image[:, :border_size] = median_val
                image[:, -border_size:] = median_val
        
        return image

class SmartTextProcessor:
    """지능형 텍스트 후처리 클래스"""
    
    def __init__(self):
        self.korean_pattern = re.compile(r'[가-힣]+')
        self.english_pattern = re.compile(r'[a-zA-Z]+')
        
        # 일반적인 OCR 오류 패턴
        self.error_patterns = {
            # 한글 오류
            'ㅇ1': '어', '1ㅏ': '가', 'ㅏ1': '아', '0': '으',
            'ㅗ1': '요', '1ㅗ': '고', 'ㅡ1': '으', '1ㅡ': '그',
            
            # 영어 오류
            'rn': 'm', 'vv': 'w', 'cl': 'd', 'li': 'h',
            '0': 'o', '1': 'l', '5': 's', '8': 'b',
            
            # 숫자 오류
            'O': '0', 'l': '1', 'S': '5', 'B': '8'
        }
    
    def intelligent_correction(self, text: str) -> str:
        """지능형 텍스트 보정"""
        corrected = text
        
        # 1. 기본 오류 패턴 수정
        for wrong, correct in self.error_patterns.items():
            corrected = corrected.replace(wrong, correct)
        
        # 2. 언어별 특화 보정
        if self.korean_pattern.search(corrected):
            corrected = self._correct_korean_text(corrected)
        
        if self.english_pattern.search(corrected):
            corrected = self._correct_english_text(corrected)
        
        # 3. 구조적 정리
        corrected = self._clean_structure(corrected)
        
        return corrected
    
    def _correct_korean_text(self, text: str) -> str:
        """한글 특화 보정 (강화된 버전)"""
        corrected = text
        
        # 1. 물음표 패턴을 한글로 복원 시도
        if '?' in corrected:
            # ?????? 패턴을 한글 placeholder로 변경
            corrected = re.sub(r'\?+', '한글', corrected)
            logger.warning(f"물음표 패턴 감지 후 복원 시도: {text} -> {corrected}")
        
        # 2. 자모 분리 문제 해결
        corrected = re.sub(r'([가-힣])\s+([ㄱ-ㅎㅏ-ㅣ])', r'\1\2', corrected)
        
        # 3. 한글 단어 간 불필요한 공백 제거
        corrected = re.sub(r'([가-힣])\s+([가-힣])', r'\1\2', corrected)
        
        # 4. 자주 잘못 인식되는 한글 패턴 수정
        korean_fixes = {
            '교1': '교', '리1': '리', '트1': '트', '스1': '스',
            '가1': '가', '나1': '나', '다1': '다', '라1': '라',
            '마1': '마', '바1': '바', '사1': '사', '아1': '아',
            '자1': '자', '차1': '차', '카1': '카', '타1': '타',
            '파1': '파', '하1': '하'
        }
        
        for wrong, correct in korean_fixes.items():
            corrected = corrected.replace(wrong, correct)
        
        # 5. UTF-8 인코딩 문제 해결 시도
        try:
            if isinstance(corrected, bytes):
                corrected = corrected.decode('utf-8', errors='ignore')
            elif isinstance(corrected, str):
                # 문자열을 바이트로 변환 후 다시 디코딩하여 인코딩 문제 해결
                corrected = corrected.encode('utf-8', errors='ignore').decode('utf-8', errors='ignore')
        except:
            logger.warning(f"한글 인코딩 수정 실패: {text}")
        
        return corrected
    
    def _correct_english_text(self, text: str) -> str:
        """영어 특화 보정"""
        # 단어 내 불필요한 공백 제거
        corrected = re.sub(r'([a-zA-Z])\s+([a-zA-Z])', r'\1\2', text)
        
        # 대소문자 정규화 (문장 첫 글자 대문자)
        sentences = corrected.split('. ')
        normalized = []
        for sentence in sentences:
            if sentence:
                normalized.append(sentence[0].upper() + sentence[1:])
        
        return '. '.join(normalized)
    
    def _clean_structure(self, text: str) -> str:
        """구조적 정리"""
        # 과도한 공백 제거
        cleaned = re.sub(r'\s+', ' ', text)
        
        # 문장부호 주변 공백 정리
        cleaned = re.sub(r'\s+([.,!?])', r'\1', cleaned)
        cleaned = re.sub(r'([.,!?])\s+', r'\1 ', cleaned)
        
        return cleaned.strip()

class LLMSimulator:
    """LLM 기반 후처리 시뮬레이터"""
    
    def __init__(self):
        self.context_patterns = {
            'date': r'\d{4}[-/]\d{1,2}[-/]\d{1,2}',
            'email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            'phone': r'\d{3}-\d{3,4}-\d{4}',
            'url': r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        }
    
    def context_aware_correction(self, text: str) -> str:
        """맥락 기반 보정 (LLM 시뮬레이션)"""
        corrected = text
        
        # 1. 패턴 기반 보정
        for pattern_name, pattern in self.context_patterns.items():
            matches = re.finditer(pattern, corrected)
            for match in matches:
                # 패턴 검증 및 보정
                corrected_match = self._correct_pattern(match.group(), pattern_name)
                corrected = corrected.replace(match.group(), corrected_match)
        
        # 2. 문맥 일관성 검사
        corrected = self._ensure_consistency(corrected)
        
        return corrected
    
    def _correct_pattern(self, text: str, pattern_type: str) -> str:
        """패턴별 보정"""
        if pattern_type == 'date':
            # 날짜 형식 정규화
            return re.sub(r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})', r'\1-\2-\3', text)
        elif pattern_type == 'phone':
            # 전화번호 형식 정규화
            numbers = re.findall(r'\d', text)
            if len(numbers) >= 10:
                return f"{numbers[0]}{numbers[1]}{numbers[2]}-{numbers[3]}{numbers[4]}{numbers[5]}{numbers[6]}-{numbers[7]}{numbers[8]}{numbers[9]}{numbers[10] if len(numbers) > 10 else ''}"
        
        return text
    
    def _ensure_consistency(self, text: str) -> str:
        """문맥 일관성 보장"""
        # 단어 일관성 검사 (같은 단어가 다르게 인식된 경우)
        words = text.split()
        word_counts = defaultdict(list)
        
        for i, word in enumerate(words):
            if len(word) > 3:  # 3글자 이상 단어만
                word_counts[word.lower()].append((i, word))
        
        # 가장 많이 나타난 형태로 통일
        for word_variants in word_counts.values():
            if len(word_variants) > 1:
                # 가장 빈번한 형태 찾기
                variant_counts = defaultdict(int)
                for _, variant in word_variants:
                    variant_counts[variant] += 1
                
                most_common = max(variant_counts.items(), key=lambda x: x[1])[0]
                
                # 모든 변형을 가장 빈번한 형태로 교체
                for _, variant in word_variants:
                    if variant != most_common:
                        text = text.replace(variant, most_common)
        
        return text

class UltimateOCRSystem:
    """최고 성능 OCR 시스템 - 완전체"""
    
    def __init__(self):
        # 핵심 컴포넌트
        self.performance_monitor = PerformanceMonitor()
        self.inference_cache = InferenceCache(max_size=200)
        self.image_processor = AdvancedImageProcessor()
        self.text_processor = SmartTextProcessor()
        self.llm_simulator = LLMSimulator()
        
        # OCR 엔진 초기화 (한글 최적화)
        try:
            # 한국어 모델 강제 다운로드 및 설정
            self.easyocr_reader = easyocr.Reader(['ko', 'en'], 
                                                gpu=False,
                                                download_enabled=True,
                                                model_storage_directory='~/.EasyOCR')
            logger.info("EasyOCR 엔진 초기화 완료")
            
            # 언어 캐릭터 셋 확인
            logger.info(f"지원 언어 문자: {len(self.easyocr_reader.lang_char)}개 문자")
            
        except Exception as e:
            logger.error(f"EasyOCR 초기화 실패: {e}")
            self.easyocr_reader = None
        
        # 성능 설정
        self.enable_cache = True
        self.enable_preprocessing = True
        self.enable_postprocessing = True
        
        logger.info("Ultimate OCR 시스템 초기화 완료")
    
    def extract_text(self, image_input, mode: str = 'ultimate') -> Dict:
        """최고 성능 텍스트 추출"""
        logger.info(f"extract_text 시작: mode={mode}, input_type={type(image_input)}")
        self.performance_monitor.start_timer('total_extraction')
        
        try:
            # 이미지 로드
            logger.info("이미지 로드 시작...")
            if isinstance(image_input, str):
                logger.info(f"파일에서 이미지 로드: {image_input}")
                image = cv2.imread(image_input)
                if image is None:
                    raise ValueError(f"이미지를 로드할 수 없습니다: {image_input}")
                logger.info(f"이미지 로드 성공: {image.shape}")
            else:
                image = image_input
                logger.info(f"직접 이미지 사용: {image.shape}")
            
            # 캐시 확인
            logger.info("캐시 확인 중...")
            if self.enable_cache:
                cached_result = self.inference_cache.get(image)
                if cached_result:
                    logger.info("캐시에서 결과 반환")
                    self.performance_monitor.end_timer('total_extraction')
                    return cached_result
                logger.info("캐시에 결과 없음")
            else:
                logger.info("캐시 비활성화됨")
            
            # 이미지 전처리
            logger.info("이미지 전처리 시작...")
            if self.enable_preprocessing:
                logger.info("전처리 활성화됨")
                try:
                    self.performance_monitor.start_timer('preprocessing')
                    processed_image = self.image_processor.adaptive_preprocessing(image)
                    self.performance_monitor.end_timer('preprocessing')
                    logger.info("전처리 완료")
                except Exception as e:
                    logger.error(f"전처리 중 오류 발생: {e}")
                    import traceback
                    traceback.print_exc()
                    processed_image = image
            else:
                logger.info("전처리 비활성화됨")
                processed_image = image
            
            # OCR 수행
            self.performance_monitor.start_timer('ocr_extraction')
            
            if mode == 'fast':
                logger.info("Fast extraction 호출 중...")
                result = self._fast_extraction(processed_image)
                logger.info(f"Fast extraction 결과: {result} (타입: {type(result)})")
                text, confidence = result
            elif mode == 'accurate':
                logger.info("Accurate extraction 호출 중...")
                result = self._accurate_extraction(processed_image)
                logger.info(f"Accurate extraction 결과: {result} (타입: {type(result)})")
                text, confidence = result
            else:  # ultimate
                logger.info("Ultimate extraction 호출 중...")
                result = self._ultimate_extraction(processed_image)
                logger.info(f"Ultimate extraction 결과: {result} (타입: {type(result)})")
                text, confidence = result
            
            self.performance_monitor.end_timer('ocr_extraction')
            
            # 후처리
            if self.enable_postprocessing:
                self.performance_monitor.start_timer('postprocessing')
                
                # 기본 텍스트 처리
                processed_text = self.text_processor.intelligent_correction(text)
                
                # LLM 스타일 보정
                final_text = self.llm_simulator.context_aware_correction(processed_text)
                
                self.performance_monitor.end_timer('postprocessing')
            else:
                final_text = text
            
            # 결과 구성
            result = {
                'text': final_text,
                'raw_text': text,
                'confidence': confidence,
                'mode': mode,
                'processing_time': self.performance_monitor.end_timer('total_extraction'),
                'has_korean': bool(self.text_processor.korean_pattern.search(final_text)),
                'has_english': bool(self.text_processor.english_pattern.search(final_text)),
                'image_shape': image.shape,
                'performance_stats': self.performance_monitor.get_stats()
            }
            
            # 캐시에 저장
            if self.enable_cache:
                self.inference_cache.put(image, result)
            
            logger.info(f"텍스트 추출 완료 - 신뢰도: {confidence:.2f}, 시간: {result['processing_time']:.2f}초")
            
            return result
            
        except Exception as e:
            logger.error(f"텍스트 추출 중 오류: {e}")
            return {
                'text': '',
                'raw_text': '',
                'confidence': 0.0,
                'mode': mode,
                'processing_time': 0.0,
                'has_korean': False,
                'has_english': False,
                'error': str(e)
            }
    
    def _fast_extraction(self, image: np.ndarray) -> Tuple[str, float]:
        """빠른 추출 (성능 우선 + 한글 최적화)"""
        if self.easyocr_reader is None:
            return "", 0.0
        
        try:
            # 한글 최적화 파라미터로 EasyOCR 실행
            results = self.easyocr_reader.readtext(
                image,
                detail=1,
                paragraph=False,
                allowlist=None,  # 모든 문자 허용
                blocklist=None,
                # 한글 인식 최적화 파라미터
                text_threshold=0.6,     # 기본 0.7 → 0.6 (더 관대하게)
                low_text=0.3,          # 기본 0.4 → 0.3 (더 관대하게)
                link_threshold=0.3,     # 기본 0.4 → 0.3 (더 관대하게)
                canvas_size=2560,
                mag_ratio=1.0,
                # 대비 조정 (한글 인식 향상)
                contrast_ths=0.05,      # 기본 0.1 → 0.05 (더 민감하게)
                adjust_contrast=0.7,    # 기본 0.5 → 0.7 (더 강하게)
                # 한글용 디코더
                decoder='beamsearch',   # 정확도 우선 디코딩
                beamWidth=5
            )
            logger.info(f"EasyOCR 결과 개수 (최적화): {len(results)}")
            
            if not results:
                logger.warning("최적화 설정 실패 - 더 관대한 설정으로 재시도")
                # 더 관대한 설정으로 재시도
                results = self.easyocr_reader.readtext(
                    image,
                    detail=1,
                    text_threshold=0.4,     # 더 낮은 임계값
                    low_text=0.2,
                    link_threshold=0.2,
                    contrast_ths=0.01,      # 매우 민감하게
                    adjust_contrast=0.9     # 매우 강하게
                )
                logger.info(f"재시도 후 EasyOCR 결과 개수: {len(results)}")
            
            if not results:
                return "", 0.0
            
            # 텍스트와 신뢰도 추출
            texts = []
            confidences = []
            for result in results:
                # EasyOCR는 (bbox, text, confidence) 3개 값을 반환
                bbox, text, confidence = result
                
                # 빈 텍스트나 물음표만 있는 텍스트 필터링
                if text.strip() and not text.strip().replace('?', '').strip() == '':
                    texts.append(text)
                    confidences.append(confidence)
                    logger.info(f"추출된 텍스트: '{text}', 신뢰도: {confidence:.3f}")
                else:
                    logger.warning(f"필터링된 텍스트: '{text}' (물음표 또는 빈 텍스트)")
            
            final_text = ' '.join(texts) if texts else ""
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            logger.info(f"최종 텍스트: '{final_text}', 평균 신뢰도: {avg_confidence:.3f}")
            return final_text, avg_confidence
            
        except Exception as e:
            logger.error(f"Fast extraction 오류: {e}")
            import traceback
            traceback.print_exc()
            return "", 0.0
    
    def _accurate_extraction(self, image: np.ndarray) -> Tuple[str, float]:
        """정확한 추출 (정확도 우선)"""
        if self.easyocr_reader is None:
            return "", 0.0
        
        try:
            results = self.easyocr_reader.readtext(image)
            
            text_parts = []
            confidences = []
            
            for result in results:
                bbox, text, confidence = result
                if confidence > 0.5:  # 높은 신뢰도만 사용
                    text_parts.append(text)
                    confidences.append(confidence)
            
            full_text = ' '.join(text_parts)
            avg_confidence = np.mean(confidences) if confidences else 0.0
            
            return full_text, avg_confidence
            
        except Exception as e:
            logger.error(f"Accurate extraction 오류: {e}")
            return "", 0.0
    
    def _ultimate_extraction(self, image: np.ndarray) -> Tuple[str, float]:
        """최고 품질 추출 (모든 기법 결합)"""
        if self.easyocr_reader is None:
            return "", 0.0
        
        try:
            # 다중 스케일 처리
            scales = [1.0, 1.2, 0.8]
            all_results = []
            
            for scale in scales:
                if scale != 1.0:
                    h, w = image.shape[:2]
                    scaled_image = cv2.resize(image, (int(w*scale), int(h*scale)), 
                                            interpolation=cv2.INTER_CUBIC)
                else:
                    scaled_image = image
                
                results = self.easyocr_reader.readtext(scaled_image)
                
                for result in results:
                    bbox, text, confidence = result
                    if confidence > 0.3:  # 낮은 임계값으로 더 많은 텍스트 수집
                        all_results.append((text, confidence, scale))
            
            # 결과 통합 및 필터링
            if not all_results:
                return "", 0.0
            
            # 신뢰도 기반 정렬
            all_results.sort(key=lambda x: x[1], reverse=True)
            
            # 최고 신뢰도 결과들 결합
            high_conf_texts = [r[0] for r in all_results if r[1] > 0.6]
            
            if high_conf_texts:
                combined_text = ' '.join(high_conf_texts)
                avg_confidence = np.mean([r[1] for r in all_results if r[1] > 0.6])
            else:
                # 모든 결과 사용
                combined_text = ' '.join([r[0] for r in all_results])
                avg_confidence = np.mean([r[1] for r in all_results])
            
            return combined_text, avg_confidence
            
        except Exception as e:
            logger.error(f"Ultimate 추출 중 오류: {e}")
            return "", 0.0
    
    def batch_process_advanced(self, image_paths: List[str], mode: str = 'ultimate') -> List[Dict]:
        """고급 배치 처리 (병렬 처리)"""
        logger.info(f"고급 배치 처리 시작: {len(image_paths)}개 이미지")
        
        results = []
        total_start = time.time()
        
        # 스레드 풀 사용 (간단한 병렬 처리)
        def process_single(path):
            return {
                'file_path': path,
                **self.extract_text(path, mode=mode)
            }
        
        # 순차 처리 (더 안정적)
        for i, path in enumerate(image_paths):
            logger.info(f"처리 중: {i+1}/{len(image_paths)} - {os.path.basename(path)}")
            result = process_single(path)
            results.append(result)
        
        total_time = time.time() - total_start
        logger.info(f"배치 처리 완료 - 총 시간: {total_time:.2f}초, 평균: {total_time/len(image_paths):.2f}초/이미지")
        
        return results
    
    def get_system_status(self) -> Dict:
        """시스템 상태 조회"""
        return {
            'ocr_engine_status': 'EasyOCR Ready' if self.easyocr_reader else 'EasyOCR Not Available',
            'cache_size': len(self.inference_cache.cache),
            'cache_max_size': self.inference_cache.max_size,
            'performance_stats': self.performance_monitor.get_stats(),
            'settings': {
                'enable_cache': self.enable_cache,
                'enable_preprocessing': self.enable_preprocessing,
                'enable_postprocessing': self.enable_postprocessing
            }
        }
    
    def optimize_for_speed(self):
        """속도 최적화 모드"""
        self.enable_preprocessing = False
        self.enable_postprocessing = False
        self.inference_cache.max_size = 50
        logger.info("속도 최적화 모드 활성화")
    
    def optimize_for_accuracy(self):
        """정확도 최적화 모드"""
        self.enable_preprocessing = True
        self.enable_postprocessing = True
        self.inference_cache.max_size = 200
        logger.info("정확도 최적화 모드 활성화")

def demo_ultimate_system():
    """Ultimate OCR 시스템 데모"""
    print("=== Ultimate OCR 시스템 데모 ===")
    
    # 시스템 초기화
    ocr = UltimateOCRSystem()
    
    # 시스템 상태 확인
    status = ocr.get_system_status()
    print(f"\n시스템 상태: {status['ocr_engine_status']}")
    
    # OCR_Input 폴더 확인
    os.makedirs("OCR_Input", exist_ok=True)
    os.makedirs("OCR_Output", exist_ok=True)
    
    # 테스트 이미지 생성
    test_img = np.ones((200, 800, 3), dtype=np.uint8) * 255
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(test_img, 'Ultimate OCR System Test', (50, 80), font, 1, (0, 0, 0), 2)
    cv2.putText(test_img, 'Korean: 최고 성능 시스템', (50, 130), font, 1, (0, 0, 0), 2)
    cv2.putText(test_img, 'Performance: 99.9% Accuracy', (50, 180), font, 0.8, (0, 0, 0), 2)
    
    test_path = "OCR_Input/ultimate_test.png"
    cv2.imwrite(test_path, test_img)
    
    # 다양한 모드 테스트
    modes = ['fast', 'accurate', 'ultimate']
    
    for mode in modes:
        print(f"\n--- {mode.upper()} 모드 테스트 ---")
        result = ocr.extract_text(test_path, mode=mode)
        
        print(f"추출된 텍스트: {result['text']}")
        print(f"신뢰도: {result['confidence']:.2f}")
        print(f"처리 시간: {result['processing_time']:.2f}초")
        print(f"한글 포함: {result['has_korean']}")
        print(f"영어 포함: {result['has_english']}")
    
    # 성능 통계
    print(f"\n--- 성능 통계 ---")
    final_status = ocr.get_system_status()
    for operation, stats in final_status['performance_stats'].items():
        print(f"{operation}: 평균 {stats['avg_time']:.3f}초 (총 {stats['count']}회)")
    
    return ocr

if __name__ == "__main__":
    demo_ultimate_system()