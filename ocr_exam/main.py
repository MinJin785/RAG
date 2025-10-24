"""
OCR 시험 채점 시스템 메인 프로그램
전체 워크플로우를 통합 관리합니다.
"""

import os
import sys
from typing import Optional

# 모듈 임포트
from ocr_exam.database.word_parser import WordDatabaseParser
from ocr_exam.generator.question_generator import QuestionGenerator
from ocr_exam.omr.answer_sheet_generator import OMRAnswerSheetGenerator
from ocr_exam.omr.omr_reader import OMRReader, OMRValidator
from ocr_exam.grading.grader import AutoGrader
from ocr_exam.models.database import StudentDatabase, Student, GradeRecord
from ocr_exam.sms.sms_sender import (
    SMSSender,
    GradeNotificationSender,
    MockSMSSender
)


class OCRExamSystem:
    """OCR 시험 채점 시스템"""

    def __init__(
        self,
        data_dir: str = "ocr_exam/data",
        use_mock_sms: bool = True
    ):
        """
        Args:
            data_dir: 데이터 저장 디렉토리
            use_mock_sms: Mock SMS 사용 여부 (테스트용)
        """
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)

        # 디렉토리 설정
        self.word_db_dir = os.path.join(data_dir, "word_database")
        self.exam_dir = os.path.join(data_dir, "exams")
        self.answer_dir = os.path.join(data_dir, "answers")
        self.scanned_dir = os.path.join(data_dir, "scanned")
        self.result_dir = os.path.join(data_dir, "results")
        self.student_db_path = os.path.join(data_dir, "students.db")

        for directory in [
            self.word_db_dir,
            self.exam_dir,
            self.answer_dir,
            self.scanned_dir,
            self.result_dir
        ]:
            os.makedirs(directory, exist_ok=True)

        # 컴포넌트 초기화
        self.student_db = StudentDatabase(self.student_db_path)
        self.grader = AutoGrader(self.answer_dir)

        # SMS 발송기 초기화
        if use_mock_sms:
            self.sms_sender = MockSMSSender()
        else:
            self.sms_sender = SMSSender()

    # ===== 1단계: 시험지 생성 =====

    def create_exam(
        self,
        word_db_file: str,
        num_questions: int,
        student_id_length: int = 6,
        include_questions: bool = True
    ) -> str:
        """
        시험지 생성

        Args:
            word_db_file: 단어 데이터베이스 파일 (txt, csv, xlsx)
            num_questions: 문제 개수
            student_id_length: 학생 번호 자릿수
            include_questions: 문제 내용 포함 여부

        Returns:
            생성된 시험지 ID
        """
        print(f"\n[1단계] 시험지 생성 중...")

        # 단어 데이터베이스 파싱
        print(f"  - 단어 데이터베이스 로드: {word_db_file}")
        parser = WordDatabaseParser()

        if word_db_file.endswith('.txt'):
            words = parser.parse_text_file(word_db_file)
        elif word_db_file.endswith('.csv'):
            words = parser.parse_csv_file(word_db_file)
        elif word_db_file.endswith('.xlsx'):
            words = parser.parse_excel_file(word_db_file)
        else:
            raise ValueError("지원하지 않는 파일 형식입니다. (txt, csv, xlsx만 가능)")

        print(f"  - 로드된 단어: {len(words)}개")

        # 문제 생성
        print(f"  - {num_questions}문제 생성 중...")
        generator = QuestionGenerator(words)
        exam = generator.generate_exam(num_questions=num_questions)

        print(f"  - 시험지 ID: {exam.exam_id}")

        # 시험지 저장
        generator.save_exam(exam, self.exam_dir)

        # 정답지 복사 (answer_dir에 별도 저장)
        import shutil
        answer_src = os.path.join(self.exam_dir, f"answers_{exam.exam_id}.json")
        answer_dst = os.path.join(self.answer_dir, f"answers_{exam.exam_id}.json")
        shutil.copy(answer_src, answer_dst)

        # OMR 답안지 PDF 생성
        print(f"  - OMR 답안지 PDF 생성 중...")
        omr_generator = OMRAnswerSheetGenerator(student_id_length=student_id_length)
        pdf_path = os.path.join(self.exam_dir, f"omr_{exam.exam_id}.pdf")

        omr_generator.generate_pdf(
            exam=exam,
            output_path=pdf_path,
            include_questions=include_questions
        )

        print(f"\n✅ 시험지 생성 완료!")
        print(f"   PDF: {pdf_path}")

        return exam.exam_id

    # ===== 2단계: 답안지 스캔 및 채점 =====

    def grade_scanned_answer_sheet(
        self,
        scanned_image_path: str,
        student_id_length: int = 6,
        send_sms: bool = True,
        from_number: Optional[str] = None,
        academy_name: str = "학원"
    ) -> dict:
        """
        스캔된 답안지 채점 및 SMS 발송

        Args:
            scanned_image_path: 스캔된 답안지 이미지 경로
            student_id_length: 학생 번호 자릿수
            send_sms: SMS 발송 여부
            from_number: 발신자 번호
            academy_name: 학원 이름

        Returns:
            채점 결과 딕셔너리
        """
        print(f"\n[2단계] 답안지 채점 중...")

        # OMR 인식
        print(f"  - 답안지 인식 중: {scanned_image_path}")
        omr_reader = OMRReader(student_id_length=student_id_length)
        omr_result = omr_reader.read_answer_sheet(scanned_image_path)

        print(f"  - 시험지 ID: {omr_result.exam_id}")
        print(f"  - 학생 번호: {omr_result.student_id}")
        print(f"  - 인식 신뢰도: {omr_result.confidence:.2%}")

        # 검증
        validator = OMRValidator()
        errors = validator.validate_result(omr_result)

        if errors:
            print("\n⚠️  검증 오류:")
            for error in errors:
                print(f"   - {error}")
            raise ValueError("OMR 인식 결과가 올바르지 않습니다.")

        # 채점
        print(f"  - 자동 채점 중...")
        grading_result = self.grader.grade(
            exam_id=omr_result.exam_id,
            student_id=omr_result.student_id,
            student_answers=omr_result.answers
        )

        print(f"\n  📊 채점 결과:")
        print(f"     점수: {grading_result.score:.0f}점")
        print(f"     정답률: {grading_result.percentage:.1f}%")
        print(f"     정답: {grading_result.correct_answers}/{grading_result.total_questions}문제")

        # 결과 저장
        self.grader.save_result(grading_result, self.result_dir)

        # 성적 DB에 저장
        grade_record = GradeRecord(
            exam_id=omr_result.exam_id,
            student_id=omr_result.student_id,
            score=grading_result.score,
            percentage=grading_result.percentage,
            correct_answers=grading_result.correct_answers,
            total_questions=grading_result.total_questions,
            graded_at=grading_result.graded_at
        )
        self.student_db.add_grade(grade_record)

        # SMS 발송
        if send_sms:
            print(f"\n  - SMS 발송 중...")
            student = self.student_db.get_student(omr_result.student_id)

            if not student:
                print(f"    ⚠️  학생 정보를 찾을 수 없습니다: {omr_result.student_id}")
            else:
                notification_sender = GradeNotificationSender(
                    sms_sender=self.sms_sender,
                    from_number=from_number or "010-0000-0000",
                    academy_name=academy_name
                )

                sms_results = notification_sender.send_grade_notification(
                    student_name=student.name,
                    student_phone=student.student_phone,
                    parent_phone=student.parent_phone,
                    exam_name=f"시험 {omr_result.exam_id}",
                    score=grading_result.score,
                    percentage=grading_result.percentage,
                    correct_answers=grading_result.correct_answers,
                    total_questions=grading_result.total_questions
                )

                print(f"    ✅ SMS 발송 완료")
                if sms_results['student']:
                    print(f"       학생: {sms_results['student'].success}")
                print(f"       학부모: {sms_results['parent'].success}")

        print(f"\n✅ 채점 완료!")

        return {
            'omr_result': omr_result,
            'grading_result': grading_result,
            'student': self.student_db.get_student(omr_result.student_id)
        }

    # ===== 학생 관리 =====

    def add_student(
        self,
        student_id: str,
        name: str,
        parent_phone: str,
        student_phone: Optional[str] = None
    ) -> bool:
        """학생 추가"""
        student = Student(
            student_id=student_id,
            name=name,
            parent_phone=parent_phone,
            student_phone=student_phone
        )
        return self.student_db.add_student(student)

    def get_student(self, student_id: str) -> Optional[Student]:
        """학생 조회"""
        return self.student_db.get_student(student_id)

    def list_students(self):
        """전체 학생 목록"""
        return self.student_db.list_students()


if __name__ == '__main__':
    print("=" * 60)
    print("OCR 시험 채점 시스템")
    print("=" * 60)

    # 시스템 초기화
    system = OCRExamSystem(use_mock_sms=True)

    print("\n테스트 모드: Mock SMS 사용")
    print("\n사용 가능한 기능:")
    print("  1. 시험지 생성")
    print("  2. 학생 등록")
    print("  3. 답안지 채점")
    print("\n자세한 사용법은 README.md를 참고하세요.")
