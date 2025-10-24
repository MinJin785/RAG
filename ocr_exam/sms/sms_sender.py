"""
SMS 자동 발송 시스템
Coolsms API를 사용하여 학생 및 학부모에게 성적 문자 발송
"""

import os
from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime

# Coolsms 라이브러리
try:
    from coolsms import Coolsms
except ImportError:
    print("Warning: coolsms-python이 설치되지 않았습니다.")
    print("pip install coolsms-python 으로 설치하세요.")


@dataclass
class SMSMessage:
    """SMS 메시지"""
    to: str  # 수신자 전화번호
    text: str  # 메시지 내용


@dataclass
class SMSResult:
    """SMS 발송 결과"""
    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None
    sent_at: Optional[str] = None


class SMSSender:
    """SMS 발송기 (Coolsms 사용)"""

    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        """
        Args:
            api_key: Coolsms API Key
            api_secret: Coolsms API Secret
        """
        self.api_key = api_key or os.getenv('COOLSMS_API_KEY')
        self.api_secret = api_secret or os.getenv('COOLSMS_API_SECRET')

        if not self.api_key or not self.api_secret:
            raise ValueError(
                "Coolsms API 키가 설정되지 않았습니다. "
                "환경변수 COOLSMS_API_KEY, COOLSMS_API_SECRET를 설정하거나 "
                "생성자에 직접 전달하세요."
            )

        try:
            self.client = Coolsms(self.api_key, self.api_secret)
        except Exception as e:
            raise ValueError(f"Coolsms 클라이언트 초기화 실패: {e}")

    def send_message(
        self,
        to: str,
        text: str,
        from_number: Optional[str] = None
    ) -> SMSResult:
        """
        단일 SMS 발송

        Args:
            to: 수신자 전화번호 (예: 010-1234-5678)
            text: 메시지 내용
            from_number: 발신자 번호 (등록된 번호)

        Returns:
            발송 결과
        """
        try:
            # 전화번호 포맷 정리 (하이픈 제거)
            to_clean = to.replace('-', '').replace(' ', '')

            params = {
                'to': to_clean,
                'text': text,
                'type': 'SMS'
            }

            if from_number:
                params['from'] = from_number.replace('-', '').replace(' ', '')

            response = self.client.send(params)

            # 성공 여부 확인
            if response.get('success_count', 0) > 0:
                return SMSResult(
                    success=True,
                    message_id=response.get('group_id'),
                    sent_at=datetime.now().isoformat()
                )
            else:
                return SMSResult(
                    success=False,
                    error=response.get('error_message', '알 수 없는 오류')
                )

        except Exception as e:
            return SMSResult(
                success=False,
                error=str(e)
            )

    def send_bulk(
        self,
        messages: List[SMSMessage],
        from_number: Optional[str] = None
    ) -> List[SMSResult]:
        """
        대량 SMS 발송

        Args:
            messages: 메시지 리스트
            from_number: 발신자 번호

        Returns:
            발송 결과 리스트
        """
        results = []

        for msg in messages:
            result = self.send_message(
                to=msg.to,
                text=msg.text,
                from_number=from_number
            )
            results.append(result)

        return results


class GradeNotificationSender:
    """성적 알림 발송기"""

    def __init__(
        self,
        sms_sender: SMSSender,
        from_number: str,
        academy_name: str = "학원"
    ):
        """
        Args:
            sms_sender: SMS 발송기
            from_number: 발신자 번호
            academy_name: 학원 이름
        """
        self.sms_sender = sms_sender
        self.from_number = from_number
        self.academy_name = academy_name

    def create_grade_message(
        self,
        student_name: str,
        exam_name: str,
        score: float,
        percentage: float,
        correct_answers: int,
        total_questions: int
    ) -> str:
        """
        성적 알림 메시지 생성

        Args:
            student_name: 학생 이름
            exam_name: 시험 이름
            score: 점수
            percentage: 정답률
            correct_answers: 정답 개수
            total_questions: 총 문제 수

        Returns:
            메시지 텍스트
        """
        message = f"""[{self.academy_name}] 시험 성적 알림

학생: {student_name}
시험: {exam_name}
점수: {score:.0f}점
정답률: {percentage:.1f}%
정답: {correct_answers}/{total_questions}문제

수고하셨습니다!"""

        return message

    def send_grade_notification(
        self,
        student_name: str,
        student_phone: Optional[str],
        parent_phone: str,
        exam_name: str,
        score: float,
        percentage: float,
        correct_answers: int,
        total_questions: int
    ) -> dict:
        """
        학생 및 학부모에게 성적 알림 발송

        Args:
            student_name: 학생 이름
            student_phone: 학생 전화번호
            parent_phone: 학부모 전화번호
            exam_name: 시험 이름
            score: 점수
            percentage: 정답률
            correct_answers: 정답 개수
            total_questions: 총 문제 수

        Returns:
            발송 결과 딕셔너리
        """
        # 메시지 생성
        message_text = self.create_grade_message(
            student_name=student_name,
            exam_name=exam_name,
            score=score,
            percentage=percentage,
            correct_answers=correct_answers,
            total_questions=total_questions
        )

        results = {
            'student': None,
            'parent': None
        }

        # 학생에게 발송
        if student_phone:
            student_result = self.sms_sender.send_message(
                to=student_phone,
                text=message_text,
                from_number=self.from_number
            )
            results['student'] = student_result

        # 학부모에게 발송
        parent_result = self.sms_sender.send_message(
            to=parent_phone,
            text=message_text,
            from_number=self.from_number
        )
        results['parent'] = parent_result

        return results


class MockSMSSender:
    """
    테스트용 Mock SMS 발송기
    실제로 문자를 보내지 않고 콘솔에 출력만 함
    """

    def send_message(
        self,
        to: str,
        text: str,
        from_number: Optional[str] = None
    ) -> SMSResult:
        """Mock SMS 발송"""
        print("=" * 50)
        print(f"[Mock SMS] 발송")
        print(f"발신: {from_number or '미지정'}")
        print(f"수신: {to}")
        print(f"내용:\n{text}")
        print("=" * 50)

        return SMSResult(
            success=True,
            message_id="MOCK-" + datetime.now().strftime("%Y%m%d%H%M%S"),
            sent_at=datetime.now().isoformat()
        )

    def send_bulk(
        self,
        messages: List[SMSMessage],
        from_number: Optional[str] = None
    ) -> List[SMSResult]:
        """Mock 대량 SMS 발송"""
        results = []

        for msg in messages:
            result = self.send_message(
                to=msg.to,
                text=msg.text,
                from_number=from_number
            )
            results.append(result)

        return results


if __name__ == '__main__':
    # 테스트 (Mock 사용)
    print("SMS 발송 테스트 (Mock)\n")

    mock_sender = MockSMSSender()

    notification_sender = GradeNotificationSender(
        sms_sender=mock_sender,
        from_number="010-1234-5678",
        academy_name="ABC학원"
    )

    # 성적 알림 발송
    results = notification_sender.send_grade_notification(
        student_name="김철수",
        student_phone="010-9999-8888",
        parent_phone="010-7777-6666",
        exam_name="영단어 동의어 시험 #1",
        score=85.0,
        percentage=85.0,
        correct_answers=17,
        total_questions=20
    )

    print("\n발송 결과:")
    print(f"학생: {results['student'].success if results['student'] else 'N/A'}")
    print(f"학부모: {results['parent'].success}")
