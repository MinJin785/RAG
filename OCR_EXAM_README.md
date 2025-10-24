# OCR 시험 채점 시스템

학원용 자동 시험 채점 및 성적 문자 발송 시스템입니다.

## 주요 기능

### ✅ 완성된 기능

1. **시험지 자동 생성**
   - 단어 데이터베이스 기반 문제 생성
   - 동의어 찾기 5지선다형
   - 시험지마다 고유 ID 부여
   - 정답지 자동 생성

2. **OMR 답안지 생성**
   - A4 용지 PDF 생성
   - QR 코드 (시험지 ID)
   - 학생 고유번호 마킹 영역
   - 5지선다 답안 마킹 영역
   - 문제 내용 포함 옵션

3. **스캔 이미지 인식**
   - QR 코드 인식 → 시험지 ID
   - 학생 번호 OMR 인식
   - 답안 OMR 인식 (A-E)

4. **자동 채점**
   - 시험지 ID로 정답지 자동 매칭
   - 정답률 및 점수 계산
   - 상세 채점 결과 저장

5. **학생 정보 관리**
   - SQLite 데이터베이스
   - 학생 정보 CRUD
   - 성적 기록 관리

6. **SMS 자동 발송**
   - Coolsms API 연동
   - 학생 및 학부모에게 자동 발송
   - Mock SMS (테스트용)

## 시스템 구조

```
ocr_exam/
├── database/           # 단어 데이터베이스 파싱
│   └── word_parser.py
├── generator/          # 문제 생성 엔진
│   └── question_generator.py
├── omr/               # OMR 답안지 생성 및 인식
│   ├── answer_sheet_generator.py
│   └── omr_reader.py
├── grading/           # 자동 채점 시스템
│   └── grader.py
├── models/            # 데이터베이스 모델
│   └── database.py
├── sms/               # SMS 발송
│   └── sms_sender.py
├── data/              # 데이터 저장소
│   ├── word_database/ # 단어 DB
│   ├── exams/         # 시험지
│   ├── answers/       # 정답지
│   ├── scanned/       # 스캔 이미지
│   ├── results/       # 채점 결과
│   └── students.db    # 학생 DB
├── main.py            # 메인 시스템
└── cli.py             # CLI 인터페이스
```

## 설치 방법

### 1. 패키지 설치

```bash
pip install -r requirements.txt
```

### 2. Tesseract OCR 설치 (선택)

Ubuntu/Debian:
```bash
sudo apt-get install tesseract-ocr
```

macOS:
```bash
brew install tesseract
```

Windows:
- https://github.com/UB-Mannheim/tesseract/wiki 에서 설치

### 3. Coolsms API 설정 (실제 SMS 사용 시)

환경변수 설정:
```bash
export COOLSMS_API_KEY="your_api_key"
export COOLSMS_API_SECRET="your_api_secret"
```

또는 `.env` 파일 생성:
```
COOLSMS_API_KEY=your_api_key
COOLSMS_API_SECRET=your_api_secret
```

## 사용 방법

### CLI 명령어

#### 1. 시험지 생성

```bash
python -m ocr_exam.cli create-exam \
  --word-db ocr_exam/data/word_database/sample_words.txt \
  --num 20
```

옵션:
- `--word-db`: 단어 데이터베이스 파일 (txt, csv, xlsx)
- `--num`: 문제 개수
- `--student-id-length`: 학생번호 자릿수 (기본: 6)
- `--no-questions`: 문제 내용 제외 (답안지만)

생성되는 파일:
- `ocr_exam/data/exams/omr_XXXXXXXX.pdf` - OMR 답안지
- `ocr_exam/data/exams/exam_XXXXXXXX.json` - 시험지 데이터
- `ocr_exam/data/answers/answers_XXXXXXXX.json` - 정답지

#### 2. 학생 등록

```bash
python -m ocr_exam.cli add-student \
  --id 123456 \
  --name "김철수" \
  --parent "010-1234-5678" \
  --student "010-9876-5432"
```

#### 3. 학생 목록 조회

```bash
python -m ocr_exam.cli list-students
```

#### 4. 답안지 채점

```bash
python -m ocr_exam.cli grade \
  --image ocr_exam/data/scanned/answer_sheet.jpg \
  --mock-sms
```

옵션:
- `--image`: 스캔된 답안지 이미지
- `--mock-sms`: Mock SMS 사용 (테스트)
- `--no-sms`: SMS 발송 안함
- `--from`: 발신자 번호
- `--academy`: 학원 이름

#### 5. 학생 성적 조회

```bash
python -m ocr_exam.cli student-grades --id 123456
```

### Python 코드 사용

```python
from ocr_exam.main import OCRExamSystem

# 시스템 초기화
system = OCRExamSystem(use_mock_sms=True)

# 1. 시험지 생성
exam_id = system.create_exam(
    word_db_file="ocr_exam/data/word_database/sample_words.txt",
    num_questions=20,
    student_id_length=6
)

# 2. 학생 등록
system.add_student(
    student_id="123456",
    name="김철수",
    parent_phone="010-1234-5678",
    student_phone="010-9876-5432"
)

# 3. 답안지 채점
result = system.grade_scanned_answer_sheet(
    scanned_image_path="scanned.jpg",
    send_sms=True,
    from_number="010-0000-0000",
    academy_name="ABC학원"
)

print(f"점수: {result['grading_result'].score}점")
```

## 단어 데이터베이스 형식

### 텍스트 형식 (.txt)

```
01 accelerate
[ək|seləreɪt]

v
 가속화되다, 속도를 높이다
syn   speed up  /  move faster  /  hasten
           속도를 높이다      더 빠르게 움직이다        재촉하다

02 acquire
[ə|kwaɪə(r)]

v
 습득하다, 얻다
syn   earn   /   gain   /   get
            얻다             얻다          얻다
```

### CSV 형식 (.csv)

```csv
number,word,pronunciation,pos,meaning,synonyms
1,accelerate,[ək|seləreɪt],v,가속화되다,"speed up / 속도를 높이다, move faster / 더 빠르게 움직이다"
```

### Excel 형식 (.xlsx)

컬럼:
- number: 번호
- word: 단어
- pronunciation: 발음
- pos: 품사
- meaning: 의미
- synonyms: 동의어 (/ 구분)

## 워크플로우

### 전체 프로세스

```
1. 단어 DB 준비
   └─> 텍스트/CSV/엑셀 파일

2. 시험지 생성
   ├─> 문제 자동 생성 (동의어 5지선다)
   ├─> 시험지 ID 부여
   ├─> OMR 답안지 PDF 생성
   └─> 정답지 저장

3. 학생 등록
   └─> 학생번호, 이름, 연락처 등록

4. 시험 실시
   ├─> OMR 답안지 인쇄
   ├─> 학생들이 학생번호 + 답안 마킹
   └─> 답안지 스캔

5. 자동 채점
   ├─> QR 코드로 시험지 ID 인식
   ├─> 학생 번호 OMR 인식
   ├─> 답안 OMR 인식
   ├─> 정답지 매칭 및 채점
   └─> 결과 저장

6. SMS 자동 발송
   ├─> 학생 DB 조회 (연락처)
   ├─> 성적 메시지 생성
   └─> 학생 + 학부모에게 발송
```

## 주의사항

### 학생 고유번호

- 사용자가 지정한 자릿수로 설정 (기본: 6자리)
- 예: 123456, 000001, 999999
- 학생들은 매번 동일한 번호 사용

### OMR 스캔

- 해상도: 최소 300 DPI 권장
- 형식: JPG, PNG
- 정렬: 답안지가 평평하고 정확히 스캔되어야 함
- 마킹: 진하게 칠하되 번지지 않게

### SMS 발송

- Coolsms 가입 필요: https://coolsms.co.kr
- API 키 발급 후 환경변수 설정
- 가격: 건당 8~12원 (2024년 기준)
- 테스트 시 Mock SMS 사용 권장

## 문제 해결

### OMR 인식 실패

1. 이미지 품질 확인 (해상도, 선명도)
2. 답안지 정렬 확인
3. 마킹이 진하고 명확한지 확인

### SMS 발송 실패

1. API 키 확인
2. 잔액 확인
3. 발신자 번호 등록 확인

### 시험지 ID 인식 불가

1. QR 코드가 선명한지 확인
2. QR 코드 영역이 잘리지 않았는지 확인

## 라이선스

MIT License

## 지원

문의사항이나 버그 리포트는 GitHub Issues에 등록해주세요.

---

**개발 완료 일시**: 2024년 10월

**주요 기술 스택**:
- Python 3.8+
- OpenCV (이미지 처리)
- ReportLab (PDF 생성)
- QRCode (QR 코드)
- Pyzbar (QR 인식)
- Coolsms (SMS 발송)
- SQLite (데이터베이스)
