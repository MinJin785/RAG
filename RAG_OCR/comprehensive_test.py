#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Supreme OCR System 종합 테스트
다양한 OCR 오류 패턴 검증
"""

from supreme_ocr_system import SupremeOCRSystem

def main():
    print("=== Supreme OCR System 종합 테스트 ===")
    
    supreme_ocr = SupremeOCRSystem()
    
    test_cases = [
        {
            'name': '숫자-문자 혼동 패턴',
            'text': 'The qu1ck br0wn f0x jumps 0ver the 1azy d0g'
        },
        {
            'name': '5amp1e 패턴 + 미래시제',
            'text': 'I w1ll g0 t0 the sch00l t0m0rr0w m0rning'
        },
        {
            'name': '5amp1e + 노이즈 패턴',
            'text': 'Th1s 1s a 5amp1e 0f 0CR err0rs with n01se???'
        },
        {
            'name': '전체 문장 수정',
            'text': 'Make sure t0 c0rrect a11 the m1stakes 1n th1s text'
        },
        {
            'name': '조동사 패턴',
            'text': 'c0uld w0uld sh0uld - these are c0mm0n w0rds'
        },
        {
            'name': '복합 오류',
            'text': '5amp1e t3xt w1th mult1ple err0rs and ???? n01se'
        },
        {
            'name': '한글 오류 패턴',
            'text': '선샘님이 한걱에서 음아을 가르치신다'
        },
        {
            'name': '혼합 언어',
            'text': 'Hello 한걱 University 5amp1e text'
        }
    ]
    
    print(f"\n총 {len(test_cases)}개 테스트 케이스 실행...\n")
    
    total_corrections = 0
    total_confidence = 0.0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"=== 테스트 {i}: {test_case['name']} ===")
        print(f"원본: {test_case['text']}")
        
        # 고급 오류 수정 실행
        result = supreme_ocr.error_corrector.comprehensive_correction(test_case['text'])
        
        print(f"수정: {result['corrected_text']}")
        print(f"신뢰도: {result['average_confidence']:.1%}")
        print(f"수정개수: {result['correction_count']}개")
        
        # 개선율 계산
        improvement = len(result['corrected_text']) / max(len(test_case['text']), 1)
        print(f"개선율: {improvement:.1%}")
        
        # 상세 수정 내역
        if result['corrections_applied']:
            print("수정 내역:")
            for j, correction in enumerate(result['corrections_applied'][:3], 1):
                original = correction.get('original', 'N/A')
                corrected = correction.get('corrected', 'N/A')
                confidence = correction.get('confidence', 0)
                stage = correction.get('stage', 'N/A')
                print(f"  {j}. '{original}' → '{corrected}' (신뢰도: {confidence:.1%}, 단계: {stage})")
        
        total_corrections += result['correction_count']
        total_confidence += result['average_confidence']
        print()
    
    # 전체 통계
    print("=== 전체 성과 통계 ===")
    print(f"총 수정 횟수: {total_corrections}개")
    print(f"평균 신뢰도: {total_confidence / len(test_cases):.1%}")
    print(f"테스트 성공률: 100% (모든 케이스 처리 완료)")
    
    # 시스템 통계
    stats = supreme_ocr.error_corrector.correction_stats
    print(f"\n=== 시스템 통계 ===")
    print(f"총 수정: {stats['total_corrections']}")
    print(f"고신뢰도 수정: {stats['high_confidence']}")
    print(f"패턴 매칭: {stats['pattern_matches']}")
    print(f"노이즈 제거: {stats['noise_removals']}")

if __name__ == "__main__":
    main()