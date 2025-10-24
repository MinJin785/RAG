"""
OMR 답안지 생성기
A4 용지에 QR코드, 학생번호, 5지선다 마킹 영역이 포함된 PDF를 생성합니다.
"""

import qrcode
import io
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import black, white
from typing import Optional

from ocr_exam.generator.question_generator import ExamPaper


class OMRAnswerSheetGenerator:
    """OMR 답안지 생성기"""

    # A4 용지 크기 (mm)
    PAGE_WIDTH = 210 * mm
    PAGE_HEIGHT = 297 * mm

    # 마킹 원 크기
    BUBBLE_RADIUS = 3 * mm

    # 여백
    MARGIN_LEFT = 15 * mm
    MARGIN_RIGHT = 15 * mm
    MARGIN_TOP = 15 * mm
    MARGIN_BOTTOM = 15 * mm

    def __init__(self, student_id_length: int = 6):
        """
        Args:
            student_id_length: 학생 고유번호 자릿수
        """
        self.student_id_length = student_id_length

    def generate_pdf(
        self,
        exam: ExamPaper,
        output_path: str,
        include_questions: bool = True
    ):
        """
        OMR 답안지 PDF 생성

        Args:
            exam: 시험지 데이터
            output_path: 출력 PDF 파일 경로
            include_questions: 문제 내용 포함 여부
        """
        c = canvas.Canvas(output_path, pagesize=A4)

        # 제목
        self._draw_title(c, exam)

        # QR 코드 (시험지 ID)
        self._draw_qr_code(c, exam.exam_id)

        # 학생 번호 마킹 영역
        self._draw_student_id_section(c)

        # 답안 마킹 영역
        self._draw_answer_section(c, exam)

        # 문제 내용 (선택적)
        if include_questions:
            self._draw_questions(c, exam)

        # 페이지 저장
        c.save()
        print(f"OMR 답안지 생성 완료: {output_path}")

    def _draw_title(self, c: canvas.Canvas, exam: ExamPaper):
        """제목 그리기"""
        y_pos = self.PAGE_HEIGHT - self.MARGIN_TOP

        # 제목
        c.setFont("Helvetica-Bold", 16)
        c.drawString(self.MARGIN_LEFT, y_pos, "OMR Answer Sheet")

        # 시험지 정보
        c.setFont("Helvetica", 10)
        y_pos -= 20
        c.drawString(self.MARGIN_LEFT, y_pos, f"Exam ID: {exam.exam_id}")
        y_pos -= 15
        c.drawString(self.MARGIN_LEFT, y_pos, f"Questions: {exam.num_questions}")

    def _draw_qr_code(self, c: canvas.Canvas, exam_id: str):
        """QR 코드 그리기 (시험지 ID)"""
        from reportlab.lib.utils import ImageReader

        # QR 코드 생성
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(exam_id)
        qr.make(fit=True)

        # 이미지로 변환
        img = qr.make_image(fill_color="black", back_color="white")

        # 메모리 버퍼에 저장
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)

        # ImageReader로 감싸기
        img_reader = ImageReader(img_buffer)

        # PDF에 그리기 (우측 상단)
        qr_size = 25 * mm
        x_pos = self.PAGE_WIDTH - self.MARGIN_RIGHT - qr_size
        y_pos = self.PAGE_HEIGHT - self.MARGIN_TOP - qr_size

        c.drawImage(
            img_reader,
            x_pos,
            y_pos,
            width=qr_size,
            height=qr_size
        )

        # QR 코드 설명
        c.setFont("Helvetica", 8)
        c.drawString(x_pos, y_pos - 10, f"ID: {exam_id}")

    def _draw_student_id_section(self, c: canvas.Canvas):
        """학생 번호 마킹 영역 그리기"""
        x_start = self.MARGIN_LEFT
        y_start = self.PAGE_HEIGHT - self.MARGIN_TOP - 60 * mm

        c.setFont("Helvetica-Bold", 10)
        c.drawString(x_start, y_start + 5, "Student ID (학생 번호)")

        # 각 자릿수마다 0-9 마킹 영역
        digit_spacing = 15 * mm
        y_current = y_start - 5 * mm

        for digit_idx in range(self.student_id_length):
            x_pos = x_start + (digit_idx * digit_spacing)

            # 자릿수 표시
            c.setFont("Helvetica", 8)
            c.drawString(x_pos + 2 * mm, y_current + 8 * mm, f"Digit {digit_idx + 1}")

            # 0-9 버블
            for num in range(10):
                bubble_x = x_pos + self.BUBBLE_RADIUS + 2 * mm
                bubble_y = y_current - (num * 5 * mm)

                # 숫자 표시
                c.setFont("Helvetica", 8)
                c.drawString(x_pos - 3 * mm, bubble_y - 2, str(num))

                # 마킹 원
                c.circle(
                    bubble_x,
                    bubble_y,
                    self.BUBBLE_RADIUS,
                    stroke=1,
                    fill=0
                )

    def _draw_answer_section(self, c: canvas.Canvas, exam: ExamPaper):
        """답안 마킹 영역 그리기"""
        x_start = self.MARGIN_LEFT
        y_start = self.PAGE_HEIGHT - self.MARGIN_TOP - 160 * mm

        c.setFont("Helvetica-Bold", 10)
        c.drawString(x_start, y_start + 5, "Answers (답안)")

        # 5지선다 (A, B, C, D, E)
        choices = ['A', 'B', 'C', 'D', 'E']
        choice_spacing = 10 * mm
        question_spacing = 8 * mm

        y_current = y_start - 5 * mm

        # 문제 번호별로 그리기 (최대 50문제까지 한 페이지에)
        questions_per_column = 25
        num_questions = exam.num_questions

        for q_num in range(1, num_questions + 1):
            # 25문제마다 다음 컬럼으로
            if q_num > questions_per_column:
                column = 1
                q_idx = q_num - questions_per_column - 1
            else:
                column = 0
                q_idx = q_num - 1

            x_pos = x_start + (column * 90 * mm)
            bubble_y = y_current - (q_idx * question_spacing)

            # 문제 번호
            c.setFont("Helvetica", 9)
            c.drawString(x_pos, bubble_y - 2, f"{q_num:2d}.")

            # A, B, C, D, E 버블
            for i, choice in enumerate(choices):
                bubble_x = x_pos + 15 * mm + (i * choice_spacing)

                # 선택지 라벨
                c.setFont("Helvetica", 8)
                c.drawString(bubble_x - 1.5, bubble_y + 4 * mm, choice)

                # 마킹 원
                c.circle(
                    bubble_x,
                    bubble_y,
                    self.BUBBLE_RADIUS,
                    stroke=1,
                    fill=0
                )

    def _draw_questions(self, c: canvas.Canvas, exam: ExamPaper):
        """문제 내용 그리기 (별도 페이지)"""
        # 새 페이지 시작
        c.showPage()

        y_pos = self.PAGE_HEIGHT - self.MARGIN_TOP

        # 제목
        c.setFont("Helvetica-Bold", 14)
        c.drawString(self.MARGIN_LEFT, y_pos, f"Exam Questions - {exam.exam_id}")
        y_pos -= 20

        c.setFont("Helvetica", 8)
        c.drawString(self.MARGIN_LEFT, y_pos, "다음 단어의 동의어를 고르시오.")
        y_pos -= 15

        # 문제 출력
        for question in exam.questions:
            # 페이지 넘김 체크
            if y_pos < self.MARGIN_BOTTOM + 50 * mm:
                c.showPage()
                y_pos = self.PAGE_HEIGHT - self.MARGIN_TOP

            # 문제 번호 및 대상 단어
            c.setFont("Helvetica-Bold", 10)
            c.drawString(
                self.MARGIN_LEFT,
                y_pos,
                f"{question.number}. {question.target_word} [{question.target_pronunciation}]"
            )
            y_pos -= 12

            c.setFont("Helvetica", 9)
            c.drawString(
                self.MARGIN_LEFT + 10 * mm,
                y_pos,
                f"의미: {question.target_meaning}"
            )
            y_pos -= 15

            # 선택지
            c.setFont("Helvetica", 9)
            for choice in question.choices:
                choice_text = f"   {choice.label}) {choice.word}"
                if choice.meaning:
                    choice_text += f" ({choice.meaning})"

                c.drawString(self.MARGIN_LEFT + 10 * mm, y_pos, choice_text)
                y_pos -= 12

            y_pos -= 10  # 문제 간 간격


if __name__ == '__main__':
    # 테스트
    from ocr_exam.database.word_parser import WordDatabaseParser
    from ocr_exam.generator.question_generator import QuestionGenerator

    sample_text = """01 accelerate
[ək|seləreɪt]

v
 가속화되다, 속도를 높이다
syn   speed up  /  move faster  /  hasten  /  quicken  /  expedite
           속도를 높이다      더 빠르게 움직이다        재촉하다          빨라지다      더 신속히 처리하다

02 acquire
[ə|kwaɪə(r)]

v
 습득하다, 얻다
syn   earn   /   gain   /   get   /   receive   /   win
            얻다             얻다          얻다      받다, 받아들이다       얻다

03 advance
[əd|vӕns]

n
전진, 발전
syn   boost  /  development  /  growth  /  improvement  /  progress
             증대                  발전                      성장                  향상, 개선                진전, 진척

04 allow
[ə|laʊ]

v
 허락하다, 허용하다
syn   admit   /   authorize   /   permit   /   let    /   grant
           허락하다        권한을 부여하다          허락하다        허락하다       승인하다

05 bond
[bɑ:nd]

n
유대, 끈
syn   connection  /  link  /  tie  /  relation  /  relationship
            연결, 연관성          관련성       유대      관계, 관련성          관계, 관련성
"""

    # 파싱 및 문제 생성
    parser = WordDatabaseParser()
    words = parser.parse_text(sample_text)

    generator = QuestionGenerator(words)
    exam = generator.generate_exam(num_questions=5)

    # OMR 답안지 생성
    omr_generator = OMRAnswerSheetGenerator(student_id_length=6)
    omr_generator.generate_pdf(
        exam=exam,
        output_path="sample_omr_answer_sheet.pdf",
        include_questions=True
    )
