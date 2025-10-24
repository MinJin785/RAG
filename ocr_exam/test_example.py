"""
OCR 시험 채점 시스템 테스트 예제
전체 워크플로우를 데모합니다.
"""

import os
from ocr_exam.main import OCRExamSystem


def demo_full_workflow():
    """전체 워크플로우 데모"""

    print("=" * 70)
    print("OCR 시험 채점 시스템 - 전체 워크플로우 데모")
    print("=" * 70)

    # 시스템 초기화 (Mock SMS 사용)
    print("\n[시스템 초기화]")
    system = OCRExamSystem(use_mock_sms=True)
    print("✅ 시스템 초기화 완료 (Mock SMS 모드)")

    # ===== 1단계: 학생 등록 =====
    print("\n" + "=" * 70)
    print("[1단계] 학생 등록")
    print("=" * 70)

    students_data = [
        {
            'student_id': '123456',
            'name': '김철수',
            'parent_phone': '010-1111-2222',
            'student_phone': '010-3333-4444'
        },
        {
            'student_id': '234567',
            'name': '이영희',
            'parent_phone': '010-5555-6666',
            'student_phone': '010-7777-8888'
        },
        {
            'student_id': '345678',
            'name': '박민수',
            'parent_phone': '010-9999-0000',
            'student_phone': None
        }
    ]

    for student_data in students_data:
        success = system.add_student(**student_data)
        if success:
            print(f"✅ {student_data['name']} ({student_data['student_id']}) 등록 완료")
        else:
            print(f"⚠️  {student_data['name']} 이미 등록됨")

    # 학생 목록 확인
    print("\n[등록된 학생 목록]")
    students = system.list_students()
    for student in students:
        print(f"  - {student.name} ({student.student_id}): {student.parent_phone}")

    # ===== 2단계: 시험지 생성 =====
    print("\n" + "=" * 70)
    print("[2단계] 시험지 생성")
    print("=" * 70)

    # 샘플 단어 데이터베이스 경로
    word_db_path = "ocr_exam/data/word_database/sample_words.txt"

    if not os.path.exists(word_db_path):
        print(f"❌ 단어 데이터베이스를 찾을 수 없습니다: {word_db_path}")
        return

    # 시험지 생성
    exam_id = system.create_exam(
        word_db_file=word_db_path,
        num_questions=10,  # 10문제
        student_id_length=6,
        include_questions=True
    )

    print(f"\n✅ 시험지 생성 완료!")
    print(f"   시험지 ID: {exam_id}")
    print(f"   PDF 위치: ocr_exam/data/exams/omr_{exam_id}.pdf")

    # ===== 3단계: 실제 사용 시뮬레이션 =====
    print("\n" + "=" * 70)
    print("[3단계] 실제 사용 시나리오")
    print("=" * 70)

    print("""
📋 실제 사용 시:

1. 생성된 PDF를 인쇄합니다.
   - 파일: ocr_exam/data/exams/omr_{exam_id}.pdf

2. 학생들이 시험을 봅니다.
   - 학생 번호를 OMR로 마킹 (예: 123456)
   - 각 문제의 답을 A, B, C, D, E 중 선택

3. 답안지를 스캔합니다.
   - 스캐너 또는 스마트폰 스캔 앱 사용
   - 해상도: 최소 300 DPI
   - 저장 위치: ocr_exam/data/scanned/

4. 스캔된 답안지를 채점합니다:

   python -m ocr_exam.cli grade \\
     --image ocr_exam/data/scanned/answer_123456.jpg \\
     --mock-sms

5. 자동으로 채점 + SMS 발송됩니다!
    """.format(exam_id=exam_id))

    # ===== 4단계: Mock 채점 데모 (OMR 없이) =====
    print("\n" + "=" * 70)
    print("[4단계] Mock 채점 데모")
    print("=" * 70)

    print("""
⚠️  실제 OMR 스캔 이미지가 없으므로 채점 데모는 생략합니다.

실제 채점을 위해서는:
1. OMR 답안지를 인쇄
2. 학생이 작성
3. 스캔
4. CLI 명령으로 채점

위 과정이 필요합니다.
    """)

    # ===== 5단계: 성적 조회 데모 =====
    print("\n" + "=" * 70)
    print("[5단계] 성적 조회")
    print("=" * 70)

    # Mock 성적 데이터 추가 (테스트용)
    from ocr_exam.models.database import GradeRecord
    from datetime import datetime

    mock_grades = [
        GradeRecord(
            exam_id=exam_id,
            student_id='123456',
            score=90.0,
            percentage=90.0,
            correct_answers=9,
            total_questions=10,
            graded_at=datetime.now().isoformat()
        ),
        GradeRecord(
            exam_id=exam_id,
            student_id='234567',
            score=80.0,
            percentage=80.0,
            correct_answers=8,
            total_questions=10,
            graded_at=datetime.now().isoformat()
        )
    ]

    for grade in mock_grades:
        system.student_db.add_grade(grade)
        print(f"✅ Mock 성적 추가: {grade.student_id} - {grade.score}점")

    # 학생별 성적 조회
    print("\n[학생별 성적 조회]")
    for student_id in ['123456', '234567']:
        student = system.get_student(student_id)
        if student:
            grades = system.student_db.get_student_grades(student_id)
            print(f"\n학생: {student.name} ({student.student_id})")
            for grade in grades:
                print(f"  시험 {grade.exam_id}: {grade.score}점 ({grade.percentage}%)")

    # ===== 완료 =====
    print("\n" + "=" * 70)
    print("데모 완료!")
    print("=" * 70)

    print("""
✅ 시스템 구성 요소:
   - 단어 DB 파서
   - 문제 생성 엔진
   - OMR 답안지 생성
   - OMR 인식 엔진
   - 자동 채점 시스템
   - 학생 정보 DB
   - SMS 자동 발송

📁 생성된 파일:
   - ocr_exam/data/exams/omr_{exam_id}.pdf (OMR 답안지)
   - ocr_exam/data/exams/exam_{exam_id}.json (시험지)
   - ocr_exam/data/answers/answers_{exam_id}.json (정답지)
   - ocr_exam/data/students.db (학생 DB)

📖 자세한 사용법:
   - OCR_EXAM_README.md 참고
   - python -m ocr_exam.cli --help

🎯 다음 단계:
   1. 실제 단어 데이터베이스 준비
   2. OMR 답안지 인쇄
   3. 학생 시험 실시
   4. 답안지 스캔 및 채점
   5. SMS 자동 발송 확인
    """.format(exam_id=exam_id))


if __name__ == '__main__':
    try:
        demo_full_workflow()
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
