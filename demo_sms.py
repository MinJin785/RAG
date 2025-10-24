"""
SMS 발송 데모
"""

from ocr_exam.sms.sms_sender import MockSMSSender, GradeNotificationSender

print("=" * 70)
print("SMS 자동 발송 데모 (Mock)")
print("=" * 70)

# Mock SMS 발송기 초기화
mock_sender = MockSMSSender()

notification_sender = GradeNotificationSender(
    sms_sender=mock_sender,
    from_number="010-9999-9999",
    academy_name="영어스타 학원"
)

# 학생 성적 데이터
students_results = [
    {
        'student_name': '김민준',
        'student_phone': '010-2222-2222',
        'parent_phone': '010-1111-1111',
        'exam_name': '영단어 동의어 시험 #1',
        'score': 95.0,
        'percentage': 95.0,
        'correct_answers': 14,
        'total_questions': 15
    },
    {
        'student_name': '박서연',
        'student_phone': None,
        'parent_phone': '010-3333-3333',
        'exam_name': '영단어 동의어 시험 #1',
        'score': 87.0,
        'percentage': 87.0,
        'correct_answers': 13,
        'total_questions': 15
    },
    {
        'student_name': '정하윤',
        'student_phone': '010-5555-5555',
        'parent_phone': '010-4444-4444',
        'exam_name': '영단어 동의어 시험 #1',
        'score': 73.0,
        'percentage': 73.0,
        'correct_answers': 11,
        'total_questions': 15
    }
]

print("\n각 학생 및 학부모에게 성적 문자 발송 중...\n")

for i, result in enumerate(students_results, 1):
    print(f"\n{'='*70}")
    print(f"[{i}번째 학생] {result['student_name']}")
    print(f"{'='*70}\n")

    results = notification_sender.send_grade_notification(**result)

    if results['student']:
        print(f"\n✅ 학생에게 발송 완료: {results['student'].success}")
    else:
        print(f"\n⚠️  학생 연락처 없음 - 발송 생략")

    print(f"✅ 학부모에게 발송 완료: {results['parent'].success}")

print("\n" + "=" * 70)
print("전체 SMS 발송 완료!")
print("=" * 70)
print("\n💡 참고:")
print("  - 실제 Coolsms API 사용 시 건당 8-12원")
print("  - 위 예시는 Mock SMS (실제 발송 안됨)")
print("  - 실제 사용 시 .env 파일에 API 키 설정 필요")
print("  - Mock → 실제: use_mock_sms=False 로 변경")
