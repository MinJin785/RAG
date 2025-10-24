"""
성적 추가 및 조회 데모
"""

from ocr_exam.main import OCRExamSystem
from ocr_exam.models.database import GradeRecord
from datetime import datetime

# 시스템 초기화
system = OCRExamSystem(use_mock_sms=True)

# 시험지 ID
exam_id = "87D78766"

# Mock 성적 데이터
grades_data = [
    {
        'student_id': '100001',
        'score': 95.0,
        'percentage': 95.0,
        'correct_answers': 14,
        'total_questions': 15
    },
    {
        'student_id': '100002',
        'score': 87.0,
        'percentage': 87.0,
        'correct_answers': 13,
        'total_questions': 15
    },
    {
        'student_id': '100003',
        'score': 73.0,
        'percentage': 73.0,
        'correct_answers': 11,
        'total_questions': 15
    }
]

print("=" * 70)
print("Mock 성적 데이터 추가")
print("=" * 70)

for data in grades_data:
    grade = GradeRecord(
        exam_id=exam_id,
        student_id=data['student_id'],
        score=data['score'],
        percentage=data['percentage'],
        correct_answers=data['correct_answers'],
        total_questions=data['total_questions'],
        graded_at=datetime.now().isoformat()
    )

    system.student_db.add_grade(grade)
    student = system.get_student(data['student_id'])
    print(f"✅ {student.name} ({data['student_id']}): {data['score']}점")

print("\n" + "=" * 70)
print("시험 전체 성적 조회 (성적순)")
print("=" * 70)

all_grades = system.student_db.get_exam_grades(exam_id)

print(f"\n시험 ID: {exam_id}")
print(f"응시 인원: {len(all_grades)}명\n")
print("-" * 70)
print(f"{'순위':<5} {'학생번호':<10} {'이름':<10} {'점수':<8} {'정답률':<10} {'정답/전체':<12}")
print("-" * 70)

for rank, grade in enumerate(all_grades, 1):
    student = system.get_student(grade.student_id)
    print(
        f"{rank:<5} "
        f"{grade.student_id:<10} "
        f"{student.name:<10} "
        f"{grade.score:<8.0f} "
        f"{grade.percentage:<10.1f}% "
        f"{grade.correct_answers}/{grade.total_questions:<12}"
    )

print("\n" + "=" * 70)
print("개인별 성적 상세 조회")
print("=" * 70)

for student_id in ['100001', '100002', '100003']:
    student = system.get_student(student_id)
    grades = system.student_db.get_student_grades(student_id)

    print(f"\n학생: {student.name} ({student.student_id})")
    print(f"학부모 연락처: {student.parent_phone}")
    if student.student_phone:
        print(f"학생 연락처: {student.student_phone}")

    print(f"\n성적 이력: {len(grades)}건")
    for g in grades:
        print(f"  • 시험 {g.exam_id}: {g.score:.0f}점 ({g.percentage:.1f}%) - {g.graded_at[:10]}")

print("\n" + "=" * 70)
print("완료!")
print("=" * 70)
