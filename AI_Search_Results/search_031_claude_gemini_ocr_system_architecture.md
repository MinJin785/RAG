# Claude + Gemini API 기반 OCR 시스템 아키텍처

## 시스템 방향 수정 (2025-01-03)

### 기존 방식 대신 새로운 접근
- **제거**: PaddleOCR, EasyOCR, Tesseract, GPT-4o
- **핵심**: Claude API + Gemini API만 활용
- **발전 방식**: 코딩 학습 자료 기반 점진적 개선

### 새로운 OCR 시스템 구조

#### 1. 메인 OCR 엔진
```python
핵심 구조:
├── Claude API (주력 OCR 엔진)
├── Gemini API (보조/검증 엔진)
└── 코딩 지식 기반 전처리/후처리 모듈
```

#### 2. 처리 파이프라인
1. **전처리**: 코딩 학습으로 얻는 지식 적용
2. **OCR 처리**: Claude + Gemini 멀티모달 API
3. **후처리**: 학습한 코딩 기법으로 점진적 개선
4. **검증**: 두 API 결과 비교 및 최적화

#### 3. 발전 전략
- 코딩 지식 하나씩 습득할 때마다 OCR 시스템에 적용 검토
- 유용한 기법은 즉시 통합, 불필요한 것은 무시
- 점진적 성능 향상 방식

## 하드웨어 환경 정보

### 노트북 (서브 시스템)
- **모델**: MSI 알파 17 C7VG-R9 QHD WIN11 (SSD 3TB)
- **OS**: Microsoft Windows 11 Pro (빌드 26100)
- **CPU**: AMD Ryzen 9 7945HX (16코어, 32논리적 프로세서)
- **RAM**: 64GB (실제 사용 가능 47.2GB)
- **모니터**: 3개 (노트북 + 비옵스 보조모니터 2개)

### 데스크탑 (메인 시스템) 🔥
- **CPU**: Intel Core Ultra 9 285K (24코어, 3.70 GHz)
- **마더보드**: ASUS ROG STRIX Z890-F GAMING WIFI
- **RAM**: 192GB DDR5-5200 (Corsair Vengeance RGB)
  - 물리적 메모리: 128GB
  - 사용 가능한 실제 메모리: 107GB
  - 총 가상 메모리: 136GB
  - 사용 가능한 가상 메모리: 111GB
- **GPU**: AMD Radeon RX 6600 8GB VRAM
- **Storage**: 
  - Samsung 9100 PRO M.2 NVMe 4TB
  - 총 저장 공간: 3.64TB (351GB 사용됨)
- **쿨러**: NZXT Kraken Plus 360mm 수냉
- **파워**: Maxwell Duke 1000W 80Plus 플래티넘
- **모니터**: 6개 (본체 2개 + 내장그래픽 4개)

### 성능 활용 최적화
- **메모리 집약적 작업**: 192GB RAM 활용한 대용량 이미지 배치 처리
- **멀티코어 활용**: 24코어로 병렬 API 호출 최적화
- **GPU 가속**: AMD RX 6600으로 이미지 전처리 가속
- **스토리지**: NVMe 4TB로 고속 임시 파일 처리

## 구현 방향

### 즉시 적용 가능한 구조
```python
class ClaudeGeminiOCRSystem:
    """Claude + Gemini API 기반 OCR 시스템"""
    
    def __init__(self):
        self.claude_api = ClaudeAPI()
        self.gemini_api = GeminiAPI()
        self.preprocessing_modules = []  # 코딩 학습으로 점진적 추가
        self.postprocessing_modules = [] # 코딩 학습으로 점진적 추가
    
    def process_image(self, image_data):
        # 1. 동적 전처리 (학습한 기법 적용)
        processed_image = self.apply_preprocessing(image_data)
        
        # 2. 멀티 API OCR
        claude_result = self.claude_api.extract_text(processed_image)
        gemini_result = self.gemini_api.extract_text(processed_image)
        
        # 3. 결과 통합 및 후처리
        final_result = self.merge_and_postprocess(claude_result, gemini_result)
        
        return final_result
```

### 학습 기반 발전 프로세스
1. **코딩 지식 입수** → **OCR 적용성 검토** → **유용시 통합** → **성능 테스트**
2. 불필요한 기법은 과감히 제외
3. 효과적인 기법만 선별적 적용

이제 모든 OCR 작업은 Claude + Gemini API 기반으로 진행하고, 점진적 학습을 통해 발전시키겠습니다.