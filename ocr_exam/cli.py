"""
OCR 시험 채점 시스템 CLI
커맨드라인 인터페이스
"""

import argparse
import sys
import os

from ocr_exam.main import OCRExamSystem
from ocr_exam.models.database import Student


def cmd_create_exam(args):
    """시험지 생성 명령"""
    system = OCRExamSystem()

    exam_id = system.create_exam(
        word_db_file=args.word_db,
        num_questions=args.num_questions,
        student_id_length=args.student_id_length,
        include_questions=not args.no_questions
    )

    print(f"\n시험지 ID: {exam_id}")
    print(f"PDF 파일: ocr_exam/data/exams/omr_{exam_id}.pdf")


def cmd_add_student(args):
    """학생 등록 명령"""
    system = OCRExamSystem()

    success = system.add_student(
        student_id=args.student_id,
        name=args.name,
        parent_phone=args.parent_phone,
        student_phone=args.student_phone
    )

    if success:
        print(f"✅ 학생 등록 완료: {args.name} ({args.student_id})")
    else:
        print(f"❌ 학생 등록 실패 (이미 존재하는 학생번호)")


def cmd_list_students(args):
    """학생 목록 조회 명령"""
    system = OCRExamSystem()

    students = system.list_students()

    if not students:
        print("등록된 학생이 없습니다.")
        return

    print(f"\n등록된 학생 목록 ({len(students)}명):")
    print("-" * 80)
    print(f"{'학생번호':<10} {'이름':<10} {'학부모 연락처':<15} {'학생 연락처':<15}")
    print("-" * 80)

    for student in students:
        print(
            f"{student.student_id:<10} "
            f"{student.name:<10} "
            f"{student.parent_phone:<15} "
            f"{student.student_phone or 'N/A':<15}"
        )


def cmd_grade(args):
    """답안지 채점 명령"""
    system = OCRExamSystem(use_mock_sms=args.mock_sms)

    result = system.grade_scanned_answer_sheet(
        scanned_image_path=args.image,
        student_id_length=args.student_id_length,
        send_sms=not args.no_sms,
        from_number=args.from_number,
        academy_name=args.academy_name
    )

    print("\n채점 완료!")


def cmd_student_grades(args):
    """학생 성적 조회 명령"""
    system = OCRExamSystem()

    student = system.get_student(args.student_id)
    if not student:
        print(f"학생을 찾을 수 없습니다: {args.student_id}")
        return

    grades = system.student_db.get_student_grades(args.student_id)

    print(f"\n학생: {student.name} ({student.student_id})")
    print(f"성적 기록: {len(grades)}건")
    print("-" * 80)
    print(f"{'시험 ID':<10} {'점수':<8} {'정답률':<10} {'정답/전체':<12} {'일시':<20}")
    print("-" * 80)

    for grade in grades:
        print(
            f"{grade.exam_id:<10} "
            f"{grade.score:<8.0f} "
            f"{grade.percentage:<10.1f}% "
            f"{grade.correct_answers}/{grade.total_questions:<12} "
            f"{grade.graded_at[:19]:<20}"
        )


def main():
    """메인 CLI 진입점"""
    parser = argparse.ArgumentParser(
        description='OCR 시험 채점 시스템',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  # 시험지 생성
  python -m ocr_exam.cli create-exam --word-db data.txt --num 20

  # 학생 등록
  python -m ocr_exam.cli add-student --id 123456 --name "김철수" --parent "010-1234-5678"

  # 학생 목록
  python -m ocr_exam.cli list-students

  # 답안지 채점
  python -m ocr_exam.cli grade --image scanned.jpg

  # 학생 성적 조회
  python -m ocr_exam.cli student-grades --id 123456
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='명령')

    # create-exam 명령
    parser_create = subparsers.add_parser('create-exam', help='시험지 생성')
    parser_create.add_argument(
        '--word-db',
        required=True,
        help='단어 데이터베이스 파일 (txt, csv, xlsx)'
    )
    parser_create.add_argument(
        '--num',
        dest='num_questions',
        type=int,
        required=True,
        help='문제 개수'
    )
    parser_create.add_argument(
        '--student-id-length',
        type=int,
        default=6,
        help='학생번호 자릿수 (기본: 6)'
    )
    parser_create.add_argument(
        '--no-questions',
        action='store_true',
        help='문제 내용 제외 (답안지만 생성)'
    )
    parser_create.set_defaults(func=cmd_create_exam)

    # add-student 명령
    parser_add = subparsers.add_parser('add-student', help='학생 등록')
    parser_add.add_argument('--id', dest='student_id', required=True, help='학생 고유번호')
    parser_add.add_argument('--name', required=True, help='학생 이름')
    parser_add.add_argument('--parent', dest='parent_phone', required=True, help='학부모 연락처')
    parser_add.add_argument('--student', dest='student_phone', help='학생 연락처')
    parser_add.set_defaults(func=cmd_add_student)

    # list-students 명령
    parser_list = subparsers.add_parser('list-students', help='학생 목록')
    parser_list.set_defaults(func=cmd_list_students)

    # grade 명령
    parser_grade = subparsers.add_parser('grade', help='답안지 채점')
    parser_grade.add_argument('--image', required=True, help='스캔된 답안지 이미지')
    parser_grade.add_argument(
        '--student-id-length',
        type=int,
        default=6,
        help='학생번호 자릿수 (기본: 6)'
    )
    parser_grade.add_argument('--no-sms', action='store_true', help='SMS 발송 안함')
    parser_grade.add_argument('--mock-sms', action='store_true', help='Mock SMS 사용 (테스트)')
    parser_grade.add_argument('--from', dest='from_number', help='발신자 번호')
    parser_grade.add_argument('--academy', dest='academy_name', default='학원', help='학원 이름')
    parser_grade.set_defaults(func=cmd_grade)

    # student-grades 명령
    parser_student_grades = subparsers.add_parser('student-grades', help='학생 성적 조회')
    parser_student_grades.add_argument('--id', dest='student_id', required=True, help='학생 고유번호')
    parser_student_grades.set_defaults(func=cmd_student_grades)

    # 인자 파싱
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # 명령 실행
    try:
        args.func(args)
    except Exception as e:
        print(f"❌ 오류: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
