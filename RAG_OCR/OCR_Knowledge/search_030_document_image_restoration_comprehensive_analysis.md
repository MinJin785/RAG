# 문서 이미지 복원 - 종합 분석

## 생성일: 2025-01-10
## 주제: OCR 성능 향상을 위한 문서 이미지 복원 기술

## 핵심 요약

### 주요 발견사항
- **2단계 파이프라인**: 이미지 복원 + 의미 기반 후처리로 최적화
- **합성 데이터 활용**: 다양한 폰트와 레이아웃으로 현실적 문서 합성
- **성능 대폭 향상**: Character Error Rate 63.9-70.3% 감소
- **역사 문서 특화**: 열화된 고문서에 특히 효과적

### 기술적 혁신
- **다방향 패치 처리**: 대형 이미지의 효율적 복원
- **적응적 이진화**: CLAHE 기반 조명 균등화
- **Un-sharp 마스킹**: 텍스트 세부사항 강화
- **통합 파이프라인**: 복원과 OCR의 완전한 통합

## 1. PreP-OCR 파이프라인

### 1.1 전체 아키텍처
```python
class PrePOCRPipeline:
    def __init__(self):
        self.image_restorer = DocumentImageRestorer()
        self.ocr_engine = EnhancedOCREngine()
        self.post_processor = ByT5PostProcessor()
    
    def process_document(self, degraded_image):
        # Stage 1: 이미지 복원
        restored_image = self.image_restorer.restore(degraded_image)
        
        # Stage 2: OCR 수행
        raw_text = self.ocr_engine.extract_text(restored_image)
        
        # Stage 3: 의미 기반 후처리
        corrected_text = self.post_processor.correct_errors(raw_text)
        
        return corrected_text, restored_image
```

### 1.2 성능 지표
- **영어**: 70.3% 오류율 감소
- **프랑스어**: 65.1% 오류율 감소
- **스페인어**: 63.9% 오류율 감소
- **처리량**: 13,831 페이지 실험 완료

## 2. 이미지 복원 기술

### 2.1 조명 보정 기법
```python
class IlluminationCorrection:
    def __init__(self):
        self.clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8,8))
    
    def correct_illumination(self, image):
        # HSV 색공간으로 변환
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # V 채널에 CLAHE 적용
        hsv[:,:,2] = self.clahe.apply(hsv[:,:,2])
        
        # RGB로 재변환
        corrected = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
        return corrected
    
    def estimate_brightness(self, image):
        """YUV 색공간의 Y 채널로 밝기 추정"""
        yuv = cv2.cvtColor(image, cv2.COLOR_BGR2YUV)
        return np.mean(yuv[:,:,0])
```

### 2.2 노이즈 제거 및 선명화
```python
class DocumentEnhancer:
    def __init__(self):
        self.unsharp_kernel = self.create_unsharp_kernel()
    
    def remove_degradation(self, image):
        """다양한 열화 요소 제거"""
        # 1. 여우화 효과 제거
        defoxed = self.remove_foxing_effect(image)
        
        # 2. 얼룩 제거
        destained = self.remove_stain_marks(defoxed)
        
        # 3. 잉크 번짐 제거
        deblurred = self.remove_ink_bleed(destained)
        
        # 4. 긁힌 자국 제거
        descratched = self.remove_scratch_marks(deblurred)
        
        return descratched
    
    def unsharp_masking(self, image, amount=1.5, radius=0.5):
        """텍스트 세부사항 강화"""
        gaussian = cv2.GaussianBlur(image, (0, 0), radius)
        unsharp = cv2.addWeighted(image, 1 + amount, gaussian, -amount, 0)
        return unsharp
```

### 2.3 적응적 이진화
```python
class AdaptiveBinarization:
    def otsu_with_preprocessing(self, image):
        """전처리가 적용된 Otsu 이진화"""
        # 1. 밝기 및 대비 조정
        adjusted = self.adjust_brightness_contrast(image)
        
        # 2. 그레이스케일 변환 (Luminance 방법)
        gray = self.luminance_conversion(adjusted)
        
        # 3. Un-sharp 마스킹
        sharpened = self.unsharp_masking(gray)
        
        # 4. Otsu 이진화
        _, binary = cv2.threshold(sharpened, 0, 255, 
                                 cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return binary
    
    def luminance_conversion(self, bgr_image):
        """인간 시각 인지에 최적화된 그레이스케일 변환"""
        b, g, r = cv2.split(bgr_image)
        gray = 0.11 * b + 0.59 * g + 0.30 * r
        return gray.astype(np.uint8)
```

## 3. 합성 데이터 생성

### 3.1 현실적 문서 합성
```python
class SyntheticDocumentGenerator:
    def __init__(self):
        self.fonts = self.load_diverse_fonts()
        self.layouts = self.create_layout_templates()
        self.degradation_ops = self.setup_degradation_pipeline()
    
    def generate_document_pair(self, text_content):
        """텍스트에서 문서-이미지 쌍 생성"""
        # 1. 다양한 폰트와 레이아웃으로 렌더링
        clean_image = self.render_with_layout(text_content)
        
        # 2. 무작위 순서로 열화 효과 적용
        degraded_image = self.apply_random_degradations(clean_image)
        
        # 3. Ground truth 마스크 생성
        gt_mask = self.generate_ground_truth_mask(clean_image)
        
        return degraded_image, clean_image, gt_mask
    
    def apply_random_degradations(self, image):
        """무작위 순서의 열화 효과"""
        operations = random.sample(self.degradation_ops, 
                                  k=random.randint(3, 7))
        
        degraded = image.copy()
        for op in operations:
            degraded = op.apply(degraded)
        
        return degraded
```

### 3.2 다방향 패치 처리
```python
class MultiDirectionalPatchProcessor:
    def __init__(self, patch_size=256, overlap=64):
        self.patch_size = patch_size
        self.overlap = overlap
    
    def extract_patches(self, large_image):
        """대형 이미지에서 중복되는 패치 추출"""
        h, w = large_image.shape[:2]
        patches = []
        positions = []
        
        for y in range(0, h - self.overlap, self.patch_size - self.overlap):
            for x in range(0, w - self.overlap, self.patch_size - self.overlap):
                patch = large_image[y:y+self.patch_size, x:x+self.patch_size]
                patches.append(patch)
                positions.append((x, y))
        
        return patches, positions
    
    def fuse_patches(self, restored_patches, positions, original_shape):
        """복원된 패치들을 원본 크기로 융합"""
        fused_image = np.zeros(original_shape, dtype=np.uint8)
        weight_map = np.zeros(original_shape[:2], dtype=np.float32)
        
        for patch, (x, y) in zip(restored_patches, positions):
            # 가중치 기반 블렌딩
            weights = self.create_blend_weights(patch.shape[:2])
            
            patch_h, patch_w = patch.shape[:2]
            fused_image[y:y+patch_h, x:x+patch_w] += patch * weights[:,:,None]
            weight_map[y:y+patch_h, x:x+patch_w] += weights
        
        # 정규화
        weight_map = np.maximum(weight_map, 1e-6)
        fused_image = fused_image / weight_map[:,:,None]
        
        return fused_image.astype(np.uint8)
```

## 4. 의미 기반 후처리

### 4.1 ByT5 기반 오류 보정
```python
class SemanticPostProcessor:
    def __init__(self):
        self.byt5_model = self.load_byt5_model()
        self.historical_text_adapter = HistoricalTextAdapter()
    
    def correct_ocr_errors(self, raw_ocr_text, context_window=512):
        """의미를 고려한 OCR 오류 보정"""
        # 1. 텍스트를 청크로 분할
        chunks = self.split_into_chunks(raw_ocr_text, context_window)
        
        corrected_chunks = []
        for chunk in chunks:
            # 2. 역사적 텍스트 패턴 적용
            historical_adapted = self.historical_text_adapter.adapt(chunk)
            
            # 3. ByT5로 오류 보정
            corrected = self.byt5_model.correct(historical_adapted)
            
            corrected_chunks.append(corrected)
        
        return self.merge_chunks(corrected_chunks)
    
    def create_synthetic_error_pairs(self, clean_text):
        """합성 오류 쌍 생성으로 모델 훈련"""
        common_errors = [
            ('m', 'rn'), ('cl', 'd'), ('li', 'h'),
            ('o', 'c'), ('e', 'c'), ('s', '5')
        ]
        
        noisy_text = clean_text
        for correct, wrong in common_errors:
            if random.random() < 0.1:  # 10% 확률로 오류 삽입
                noisy_text = noisy_text.replace(correct, wrong)
        
        return noisy_text, clean_text
```

## 5. 실험 결과 및 성능

### 5.1 데이터셋별 성능
```python
def evaluate_restoration_pipeline():
    """문서 복원 파이프라인 평가"""
    datasets = {
        'English': {'pages': 4521, 'baseline_cer': 0.234, 'improved_cer': 0.070},
        'French': {'pages': 4892, 'baseline_cer': 0.267, 'improved_cer': 0.093},
        'Spanish': {'pages': 4418, 'baseline_cer': 0.245, 'improved_cer': 0.088}
    }
    
    for language, stats in datasets.items():
        improvement = (stats['baseline_cer'] - stats['improved_cer']) / stats['baseline_cer']
        print(f"{language}: {improvement:.1%} CER reduction")
    
    return datasets
```

### 5.2 처리 시간 최적화
- **패치 기반 처리**: 메모리 효율성 극대화
- **병렬 처리**: GPU 가속으로 실시간 처리 가능
- **점진적 복원**: 우선순위 기반 영역별 처리

## 6. 통합 구현 예제

### 6.1 완전한 복원 파이프라인
```python
class CompleteRestorationPipeline:
    def __init__(self):
        self.preprocessor = DocumentPreprocessor()
        self.restorer = DocumentImageRestorer()
        self.ocr_engine = TesseractOCREngine()
        self.post_processor = SemanticPostProcessor()
    
    def process_historical_document(self, image_path):
        """역사 문서 완전 처리"""
        # 1. 이미지 로드 및 전처리
        original = cv2.imread(image_path)
        preprocessed = self.preprocessor.preprocess(original)
        
        # 2. 이미지 복원
        restored = self.restorer.restore(preprocessed)
        
        # 3. OCR 수행
        raw_text = self.ocr_engine.extract_text(restored)
        
        # 4. 의미 기반 후처리
        final_text = self.post_processor.correct_ocr_errors(raw_text)
        
        return {
            'original_image': original,
            'restored_image': restored,
            'raw_ocr_text': raw_text,
            'corrected_text': final_text
        }
```

## 7. 실용적 적용 방안

### 7.1 역사 문서 디지털화
- **도서관 아카이브**: 고문서의 대규모 디지털화
- **박물관 컬렉션**: 유물 텍스트의 자동 인식
- **학술 연구**: 역사 텍스트의 검색 가능한 데이터베이스 구축

### 7.2 상업적 응용
- **법률 문서**: 오래된 계약서 및 법적 문서 처리
- **의료 기록**: 수기 의료 기록의 디지털 변환
- **보험 서류**: 손상된 보험 문서 복원 및 처리

## 결론

문서 이미지 복원 기술은 OCR 성능 향상의 핵심 요소로, 특히 열화된 역사 문서에서 탁월한 효과를 보여줍니다. 이미지 복원과 의미적 후처리의 통합적 접근법이 미래 OCR 시스템의 표준이 될 것으로 예상됩니다.