"""
OMR 인식 엔진
스캔된 답안지 이미지에서 QR코드, 학생번호, 답안을 인식합니다.
"""

import cv2
import numpy as np
from pyzbar.pyzbar import decode
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class OMRResult:
    """OMR 인식 결과"""
    exam_id: str
    student_id: str
    answers: Dict[int, str]  # {문제번호: 답(A-E)}
    confidence: float  # 인식 신뢰도 (0-1)


class OMRReader:
    """OMR 인식기"""

    def __init__(self, student_id_length: int = 6):
        """
        Args:
            student_id_length: 학생 고유번호 자릿수
        """
        self.student_id_length = student_id_length

    def read_answer_sheet(self, image_path: str) -> OMRResult:
        """
        답안지 이미지에서 데이터 읽기

        Args:
            image_path: 스캔된 답안지 이미지 경로

        Returns:
            OMR 인식 결과
        """
        # 이미지 로드
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"이미지를 불러올 수 없습니다: {image_path}")

        # 전처리
        processed = self._preprocess_image(image)

        # QR 코드 인식 (시험지 ID)
        exam_id = self._read_qr_code(image)
        if not exam_id:
            raise ValueError("시험지 ID(QR 코드)를 인식할 수 없습니다.")

        # 학생 번호 인식
        student_id = self._read_student_id(processed)

        # 답안 인식
        answers = self._read_answers(processed)

        # 신뢰도 계산
        confidence = self._calculate_confidence(processed, answers)

        return OMRResult(
            exam_id=exam_id,
            student_id=student_id,
            answers=answers,
            confidence=confidence
        )

    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        이미지 전처리 (회전 보정, 이진화 등)

        Args:
            image: 원본 이미지

        Returns:
            전처리된 이미지
        """
        # 그레이스케일 변환
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # 가우시안 블러 (노이즈 제거)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # 적응형 이진화
        binary = cv2.adaptiveThreshold(
            blurred,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            11,
            2
        )

        return binary

    def _read_qr_code(self, image: np.ndarray) -> Optional[str]:
        """
        QR 코드에서 시험지 ID 읽기

        Args:
            image: 원본 이미지

        Returns:
            시험지 ID
        """
        decoded_objects = decode(image)

        for obj in decoded_objects:
            if obj.type == 'QRCODE':
                return obj.data.decode('utf-8')

        return None

    def _read_student_id(self, binary_image: np.ndarray) -> str:
        """
        학생 번호 마킹 영역에서 번호 읽기

        Args:
            binary_image: 전처리된 이진 이미지

        Returns:
            학생 번호
        """
        # 실제 구현에서는 이미지 좌표를 정확히 계산해야 합니다
        # 여기서는 간단한 버전으로 구현

        height, width = binary_image.shape

        # 학생 번호 영역 대략적인 위치 (상단 좌측)
        # 실제로는 답안지 레이아웃에 맞게 조정 필요
        x_start = int(width * 0.05)
        y_start = int(height * 0.15)

        student_id_digits = []

        # 각 자릿수 읽기
        for digit_idx in range(self.student_id_length):
            x_offset = x_start + int(digit_idx * width * 0.05)

            # 0-9까지 마킹 체크
            digit = self._detect_marked_bubble(
                binary_image,
                x_offset,
                y_start,
                num_options=10,
                vertical_spacing=int(height * 0.015)
            )

            student_id_digits.append(str(digit))

        return ''.join(student_id_digits)

    def _read_answers(self, binary_image: np.ndarray) -> Dict[int, str]:
        """
        답안 마킹 영역에서 답안 읽기

        Args:
            binary_image: 전처리된 이진 이미지

        Returns:
            답안 딕셔너리 {문제번호: 답}
        """
        height, width = binary_image.shape

        # 답안 영역 대략적인 위치
        x_start = int(width * 0.05)
        y_start = int(height * 0.45)

        answers = {}
        choices = ['A', 'B', 'C', 'D', 'E']

        # 문제별로 답 읽기 (최대 50문제)
        for q_num in range(1, 51):
            # 25문제마다 다음 컬럼
            if q_num > 25:
                column = 1
                q_idx = q_num - 26
            else:
                column = 0
                q_idx = q_num - 1

            x_offset = x_start + int(column * width * 0.45)
            y_offset = y_start + int(q_idx * height * 0.025)

            # 답안 위치 조정 (A-E 버블 시작 위치)
            answer_x = x_offset + int(width * 0.05)

            # A, B, C, D, E 중 마킹된 것 찾기
            marked_idx = self._detect_marked_bubble(
                binary_image,
                answer_x,
                y_offset,
                num_options=5,
                vertical_spacing=0,
                horizontal_spacing=int(width * 0.035)
            )

            if marked_idx is not None:
                answers[q_num] = choices[marked_idx]

        return answers

    def _detect_marked_bubble(
        self,
        binary_image: np.ndarray,
        x_start: int,
        y_start: int,
        num_options: int,
        vertical_spacing: int = 0,
        horizontal_spacing: int = 0
    ) -> Optional[int]:
        """
        마킹된 버블 감지

        Args:
            binary_image: 전처리된 이진 이미지
            x_start: 시작 X 좌표
            y_start: 시작 Y 좌표
            num_options: 선택지 개수
            vertical_spacing: 수직 간격 (세로 배치)
            horizontal_spacing: 수평 간격 (가로 배치)

        Returns:
            마킹된 선택지 인덱스 (0부터 시작)
        """
        bubble_radius = 10  # 픽셀 단위
        marked_threshold = 0.6  # 60% 이상 채워졌으면 마킹으로 판단

        max_fill_ratio = 0
        marked_idx = None

        for i in range(num_options):
            # 버블 중심 좌표
            if horizontal_spacing > 0:
                # 가로 배치 (답안용)
                cx = x_start + i * horizontal_spacing
                cy = y_start
            else:
                # 세로 배치 (학생번호용)
                cx = x_start
                cy = y_start + i * vertical_spacing

            # 버블 영역 추출
            y1 = max(0, cy - bubble_radius)
            y2 = min(binary_image.shape[0], cy + bubble_radius)
            x1 = max(0, cx - bubble_radius)
            x2 = min(binary_image.shape[1], cx + bubble_radius)

            bubble_region = binary_image[y1:y2, x1:x2]

            # 채워진 비율 계산
            if bubble_region.size > 0:
                fill_ratio = np.sum(bubble_region > 0) / bubble_region.size

                if fill_ratio > max_fill_ratio:
                    max_fill_ratio = fill_ratio
                    marked_idx = i

        # 임계값 이상이면 마킹으로 판단
        if max_fill_ratio >= marked_threshold:
            return marked_idx

        return None

    def _calculate_confidence(
        self,
        binary_image: np.ndarray,
        answers: Dict[int, str]
    ) -> float:
        """
        인식 신뢰도 계산

        Args:
            binary_image: 전처리된 이미지
            answers: 인식된 답안

        Returns:
            신뢰도 (0-1)
        """
        # 간단한 신뢰도 계산
        # 실제로는 더 정교한 방법 필요

        # 이미지 품질 체크
        mean_intensity = np.mean(binary_image)
        quality_score = min(1.0, mean_intensity / 128.0)

        # 답안 개수 체크
        answer_ratio = len(answers) / 50.0  # 최대 50문제 가정
        answer_score = min(1.0, answer_ratio)

        # 종합 신뢰도
        confidence = (quality_score + answer_score) / 2.0

        return confidence


class OMRValidator:
    """OMR 인식 결과 검증기"""

    @staticmethod
    def validate_result(result: OMRResult) -> List[str]:
        """
        OMR 인식 결과 검증

        Args:
            result: OMR 인식 결과

        Returns:
            검증 오류 메시지 리스트 (비어있으면 정상)
        """
        errors = []

        # 시험지 ID 검증
        if not result.exam_id or len(result.exam_id) != 8:
            errors.append("시험지 ID가 올바르지 않습니다.")

        # 학생 번호 검증
        if not result.student_id or not result.student_id.isdigit():
            errors.append("학생 번호가 올바르지 않습니다.")

        # 답안 검증
        if not result.answers:
            errors.append("답안이 인식되지 않았습니다.")

        for q_num, answer in result.answers.items():
            if answer not in ['A', 'B', 'C', 'D', 'E']:
                errors.append(f"문제 {q_num}의 답안이 올바르지 않습니다: {answer}")

        # 신뢰도 검증
        if result.confidence < 0.5:
            errors.append(
                f"인식 신뢰도가 낮습니다 ({result.confidence:.2%}). "
                "이미지를 다시 스캔해주세요."
            )

        return errors


if __name__ == '__main__':
    # 테스트
    reader = OMRReader(student_id_length=6)

    try:
        result = reader.read_answer_sheet("sample_scanned_answer_sheet.jpg")

        print(f"시험지 ID: {result.exam_id}")
        print(f"학생 번호: {result.student_id}")
        print(f"신뢰도: {result.confidence:.2%}")
        print(f"\n답안:")
        for q_num, answer in sorted(result.answers.items()):
            print(f"  {q_num}. {answer}")

        # 검증
        validator = OMRValidator()
        errors = validator.validate_result(result)

        if errors:
            print("\n검증 오류:")
            for error in errors:
                print(f"  - {error}")
        else:
            print("\n검증 성공!")

    except Exception as e:
        print(f"오류: {e}")
