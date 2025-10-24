"""
자동 채점 시스템
OMR 인식 결과와 정답지를 비교하여 채점합니다.
"""

import json
from typing import Dict, List
from dataclasses import dataclass
from datetime import datetime


@dataclass
class GradingResult:
    """채점 결과"""
    exam_id: str
    student_id: str
    total_questions: int
    correct_answers: int
    wrong_answers: int
    score: float  # 점수 (0-100)
    percentage: float  # 정답률 (0-100)
    details: Dict[int, Dict[str, str]]  # {문제번호: {student_answer, correct_answer, is_correct}}
    graded_at: str

    def to_dict(self) -> Dict:
        return {
            'exam_id': self.exam_id,
            'student_id': self.student_id,
            'total_questions': self.total_questions,
            'correct_answers': self.correct_answers,
            'wrong_answers': self.wrong_answers,
            'score': self.score,
            'percentage': self.percentage,
            'details': self.details,
            'graded_at': self.graded_at
        }


class AutoGrader:
    """자동 채점기"""

    def __init__(self, answer_keys_dir: str):
        """
        Args:
            answer_keys_dir: 정답지 JSON 파일들이 저장된 디렉토리
        """
        self.answer_keys_dir = answer_keys_dir
        self.answer_keys_cache = {}

    def load_answer_key(self, exam_id: str) -> Dict[int, str]:
        """
        정답지 로드

        Args:
            exam_id: 시험지 ID

        Returns:
            정답 딕셔너리 {문제번호: 정답}
        """
        # 캐시 확인
        if exam_id in self.answer_keys_cache:
            return self.answer_keys_cache[exam_id]

        # 정답지 파일 로드
        import os
        answer_file = os.path.join(
            self.answer_keys_dir,
            f"answers_{exam_id}.json"
        )

        if not os.path.exists(answer_file):
            raise FileNotFoundError(
                f"시험지 ID '{exam_id}'의 정답지를 찾을 수 없습니다: {answer_file}"
            )

        with open(answer_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 정답 딕셔너리 변환 (문자열 키를 정수로)
        answer_key = {int(k): v for k, v in data['answer_key'].items()}

        # 캐시에 저장
        self.answer_keys_cache[exam_id] = answer_key

        return answer_key

    def grade(
        self,
        exam_id: str,
        student_id: str,
        student_answers: Dict[int, str]
    ) -> GradingResult:
        """
        답안 채점

        Args:
            exam_id: 시험지 ID
            student_id: 학생 번호
            student_answers: 학생 답안 {문제번호: 답}

        Returns:
            채점 결과
        """
        # 정답지 로드
        answer_key = self.load_answer_key(exam_id)

        # 채점
        correct_count = 0
        wrong_count = 0
        details = {}

        for q_num in answer_key.keys():
            correct_answer = answer_key[q_num]
            student_answer = student_answers.get(q_num)

            is_correct = student_answer == correct_answer

            if is_correct:
                correct_count += 1
            else:
                wrong_count += 1

            details[q_num] = {
                'student_answer': student_answer or 'N/A',
                'correct_answer': correct_answer,
                'is_correct': is_correct
            }

        # 점수 계산
        total_questions = len(answer_key)
        percentage = (correct_count / total_questions) * 100 if total_questions > 0 else 0
        score = percentage  # 100점 만점

        return GradingResult(
            exam_id=exam_id,
            student_id=student_id,
            total_questions=total_questions,
            correct_answers=correct_count,
            wrong_answers=wrong_count,
            score=score,
            percentage=percentage,
            details=details,
            graded_at=datetime.now().isoformat()
        )

    def save_result(self, result: GradingResult, output_dir: str):
        """
        채점 결과 저장

        Args:
            result: 채점 결과
            output_dir: 출력 디렉토리
        """
        import os

        os.makedirs(output_dir, exist_ok=True)

        # 파일명: results_<exam_id>_<student_id>.json
        filename = f"result_{result.exam_id}_{result.student_id}.json"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)

        print(f"채점 결과 저장 완료: {filepath}")

    @staticmethod
    def load_result(filepath: str) -> GradingResult:
        """
        채점 결과 로드

        Args:
            filepath: 결과 JSON 파일 경로

        Returns:
            채점 결과
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return GradingResult(**data)

    def generate_report(self, result: GradingResult) -> str:
        """
        채점 결과 리포트 생성 (텍스트)

        Args:
            result: 채점 결과

        Returns:
            리포트 텍스트
        """
        report = []
        report.append("=" * 50)
        report.append("시험 채점 결과")
        report.append("=" * 50)
        report.append(f"시험지 ID: {result.exam_id}")
        report.append(f"학생 번호: {result.student_id}")
        report.append(f"채점 일시: {result.graded_at}")
        report.append("")
        report.append(f"총 문제 수: {result.total_questions}문제")
        report.append(f"정답 개수: {result.correct_answers}문제")
        report.append(f"오답 개수: {result.wrong_answers}문제")
        report.append(f"정답률: {result.percentage:.1f}%")
        report.append(f"점수: {result.score:.1f}점")
        report.append("")

        # 오답 문제 표시
        wrong_questions = [
            q_num for q_num, detail in result.details.items()
            if not detail['is_correct']
        ]

        if wrong_questions:
            report.append("오답 문제:")
            for q_num in sorted(wrong_questions):
                detail = result.details[q_num]
                report.append(
                    f"  {q_num}번: "
                    f"학생답안({detail['student_answer']}) "
                    f"→ 정답({detail['correct_answer']})"
                )
        else:
            report.append("모든 문제를 맞췄습니다! 🎉")

        report.append("=" * 50)

        return '\n'.join(report)


if __name__ == '__main__':
    # 테스트
    import os

    # 가상의 정답지 생성
    os.makedirs("test_answers", exist_ok=True)

    answer_key_data = {
        'exam_id': 'ABC12345',
        'answer_key': {
            '1': 'A',
            '2': 'B',
            '3': 'C',
            '4': 'D',
            '5': 'E'
        }
    }

    with open("test_answers/answers_ABC12345.json", 'w') as f:
        json.dump(answer_key_data, f)

    # 채점 테스트
    grader = AutoGrader(answer_keys_dir="test_answers")

    student_answers = {
        1: 'A',  # 정답
        2: 'B',  # 정답
        3: 'A',  # 오답
        4: 'D',  # 정답
        5: 'E'   # 정답
    }

    result = grader.grade(
        exam_id='ABC12345',
        student_id='123456',
        student_answers=student_answers
    )

    # 결과 출력
    print(grader.generate_report(result))

    # 결과 저장
    os.makedirs("test_results", exist_ok=True)
    grader.save_result(result, output_dir="test_results")
