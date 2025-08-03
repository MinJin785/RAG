#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Claude + Gemini API 기반 OCR 시스템
단순하고 효과적인 멀티모달 OCR 처리
"""

import os
import base64
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime

# API 클라이언트
import requests
from PIL import Image
import io

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ClaudeOCR:
    """Claude API 기반 OCR 처리"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.api_url = "https://api.anthropic.com/v1/messages"
        self.headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01"
        }
    
    def encode_image(self, image_path: str) -> str:
        """이미지를 base64로 인코딩"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def extract_text(self, image_path: str) -> Dict[str, Any]:
        """Claude API로 텍스트 추출"""
        try:
            start_time = time.time()
            
            # 이미지 인코딩
            base64_image = self.encode_image(image_path)
            
            # API 요청 데이터
            payload = {
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 4000,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/jpeg",
                                    "data": base64_image
                                }
                            },
                            {
                                "type": "text",
                                "text": "이 이미지에서 모든 텍스트를 정확하게 추출해주세요. 한글과 영어 모두 정확히 인식해주시고, 줄바꿈과 레이아웃을 최대한 보존해주세요."
                            }
                        ]
                    }
                ]
            }
            
            # API 호출
            response = requests.post(self.api_url, headers=self.headers, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                extracted_text = result['content'][0]['text']
                processing_time = time.time() - start_time
                
                return {
                    "success": True,
                    "text": extracted_text,
                    "confidence": 0.95,  # Claude는 일반적으로 높은 신뢰도
                    "processing_time": processing_time,
                    "engine": "claude-3.5-sonnet"
                }
            else:
                logger.error(f"Claude API 오류: {response.status_code}, {response.text}")
                return {
                    "success": False,
                    "error": f"API 오류: {response.status_code}",
                    "text": "",
                    "processing_time": time.time() - start_time
                }
                
        except Exception as e:
            logger.error(f"Claude OCR 처리 오류: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "text": "",
                "processing_time": time.time() - start_time
            }

class GeminiOCR:
    """Gemini API 기반 OCR 처리"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent?key={api_key}"
    
    def encode_image(self, image_path: str) -> str:
        """이미지를 base64로 인코딩"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def extract_text(self, image_path: str) -> Dict[str, Any]:
        """Gemini API로 텍스트 추출"""
        try:
            start_time = time.time()
            
            # 이미지 인코딩
            base64_image = self.encode_image(image_path)
            
            # API 요청 데이터
            payload = {
                "contents": [{
                    "parts": [
                        {
                            "text": "이 이미지에서 모든 텍스트를 정확하게 추출해주세요. 한글과 영어 모두 정확히 인식해주시고, 줄바꿈과 레이아웃을 최대한 보존해주세요."
                        },
                        {
                            "inline_data": {
                                "mime_type": "image/jpeg",
                                "data": base64_image
                            }
                        }
                    ]
                }]
            }
            
            # API 호출
            response = requests.post(self.api_url, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and len(result['candidates']) > 0:
                    extracted_text = result['candidates'][0]['content']['parts'][0]['text']
                    processing_time = time.time() - start_time
                    
                    return {
                        "success": True,
                        "text": extracted_text,
                        "confidence": 0.90,  # Gemini 신뢰도
                        "processing_time": processing_time,
                        "engine": "gemini-1.5-pro"
                    }
                else:
                    return {
                        "success": False,
                        "error": "응답에서 텍스트를 찾을 수 없음",
                        "text": "",
                        "processing_time": time.time() - start_time
                    }
            else:
                logger.error(f"Gemini API 오류: {response.status_code}, {response.text}")
                return {
                    "success": False,
                    "error": f"API 오류: {response.status_code}",
                    "text": "",
                    "processing_time": time.time() - start_time
                }
                
        except Exception as e:
            logger.error(f"Gemini OCR 처리 오류: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "text": "",
                "processing_time": time.time() - start_time
            }

class ClaudeGeminiOCRSystem:
    """Claude + Gemini 하이브리드 OCR 시스템"""
    
    def __init__(self):
        # API 키 가져오기
        claude_key = os.getenv('ANTHROPIC_API_KEY')
        gemini_key = os.getenv('GOOGLE_API_KEY')
        
        if not claude_key:
            raise ValueError("ANTHROPIC_API_KEY 환경변수가 설정되지 않았습니다.")
        if not gemini_key:
            raise ValueError("GOOGLE_API_KEY 환경변수가 설정되지 않았습니다.")
        
        # OCR 엔진 초기화
        self.claude_ocr = ClaudeOCR(claude_key)
        self.gemini_ocr = GeminiOCR(gemini_key)
        
        # 통계
        self.total_processed = 0
        self.results_history = []
        
        logger.info("Claude + Gemini OCR 시스템 초기화 완료!")
    
    def process_image(self, image_path: str, use_both: bool = True) -> Dict[str, Any]:
        """이미지 OCR 처리"""
        if not os.path.exists(image_path):
            return {"error": "이미지 파일을 찾을 수 없습니다."}
        
        logger.info(f"OCR 처리 시작: {image_path}")
        start_time = time.time()
        
        results = {
            "image_path": image_path,
            "timestamp": datetime.now().isoformat(),
            "claude_result": None,
            "gemini_result": None,
            "final_result": None
        }
        
        if use_both:
            # 두 API 모두 사용
            logger.info("Claude API로 처리 중...")
            results["claude_result"] = self.claude_ocr.extract_text(image_path)
            
            logger.info("Gemini API로 처리 중...")
            results["gemini_result"] = self.gemini_ocr.extract_text(image_path)
            
            # 결과 통합
            results["final_result"] = self._merge_results(
                results["claude_result"], 
                results["gemini_result"]
            )
        else:
            # Claude만 사용 (더 정확함)
            logger.info("Claude API로 처리 중...")
            results["claude_result"] = self.claude_ocr.extract_text(image_path)
            results["final_result"] = results["claude_result"]
        
        total_time = time.time() - start_time
        results["total_processing_time"] = total_time
        
        # 통계 업데이트
        self.total_processed += 1
        self.results_history.append(results)
        
        logger.info(f"OCR 처리 완료! 총 처리 시간: {total_time:.2f}초")
        
        return results
    
    def _merge_results(self, claude_result: Dict, gemini_result: Dict) -> Dict[str, Any]:
        """두 API 결과 통합"""
        # Claude 결과를 우선으로 하되, 실패시 Gemini 사용
        if claude_result.get("success", False):
            final_text = claude_result["text"]
            confidence = claude_result["confidence"]
            engine = "claude-primary"
        elif gemini_result.get("success", False):
            final_text = gemini_result["text"]
            confidence = gemini_result["confidence"] 
            engine = "gemini-fallback"
        else:
            final_text = ""
            confidence = 0.0
            engine = "both-failed"
        
        return {
            "success": len(final_text) > 0,
            "text": final_text,
            "confidence": confidence,
            "engine": engine,
            "claude_success": claude_result.get("success", False),
            "gemini_success": gemini_result.get("success", False)
        }
    
    def save_result(self, result: Dict, output_dir: str = "OCR_Output") -> str:
        """결과를 파일로 저장"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # 파일명 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        image_name = Path(result["image_path"]).stem
        
        # 텍스트 파일 저장
        txt_file = output_path / f"{image_name}_ocr_{timestamp}.txt"
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write("=== Claude + Gemini OCR 결과 ===\n\n")
            f.write(f"이미지: {result['image_path']}\n")
            f.write(f"처리 시간: {result['timestamp']}\n")
            f.write(f"총 소요 시간: {result.get('total_processing_time', 0):.2f}초\n\n")
            
            if result.get("final_result"):
                f.write("=== 최종 결과 ===\n")
                f.write(f"엔진: {result['final_result']['engine']}\n")
                f.write(f"신뢰도: {result['final_result']['confidence']:.2f}\n\n")
                f.write("추출된 텍스트:\n")
                f.write(result['final_result']['text'])
        
        # JSON 파일 저장 (상세 정보)
        json_file = output_path / f"{image_name}_ocr_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        logger.info(f"결과 저장 완료: {txt_file}")
        return str(txt_file)
    
    def get_statistics(self) -> Dict[str, Any]:
        """처리 통계 반환"""
        if not self.results_history:
            return {"message": "처리된 이미지가 없습니다."}
        
        total_time = sum(r.get("total_processing_time", 0) for r in self.results_history)
        claude_success = sum(1 for r in self.results_history 
                           if r.get("claude_result", {}).get("success", False))
        gemini_success = sum(1 for r in self.results_history 
                           if r.get("gemini_result", {}).get("success", False))
        
        return {
            "total_processed": self.total_processed,
            "average_time": total_time / self.total_processed,
            "claude_success_rate": claude_success / self.total_processed * 100,
            "gemini_success_rate": gemini_success / self.total_processed * 100,
            "total_processing_time": total_time
        }

def main():
    """메인 실행 함수"""
    try:
        # OCR 시스템 초기화
        ocr_system = ClaudeGeminiOCRSystem()
        
        # 테스트 이미지 경로
        test_image = "OCR_Input/test_image.jpg"  # 기본 테스트 이미지
        
        # 사용자에게 이미지 경로 입력 받기
        image_path = input(f"OCR 할 이미지 경로를 입력하세요 (기본값: {test_image}): ").strip()
        if not image_path:
            image_path = test_image
        
        if not os.path.exists(image_path):
            print(f"오류: 이미지 파일을 찾을 수 없습니다: {image_path}")
            return
        
        # OCR 처리
        print("OCR 처리 중...")
        result = ocr_system.process_image(image_path, use_both=True)
        
        # 결과 출력
        if result.get("final_result", {}).get("success", False):
            print("\n=== OCR 결과 ===")
            print(f"엔진: {result['final_result']['engine']}")
            print(f"신뢰도: {result['final_result']['confidence']:.2f}")
            print(f"처리 시간: {result.get('total_processing_time', 0):.2f}초")
            print("\n추출된 텍스트:")
            print("-" * 50)
            print(result['final_result']['text'])
            print("-" * 50)
            
            # 결과 저장
            output_file = ocr_system.save_result(result)
            print(f"\n결과가 저장되었습니다: {output_file}")
            
        else:
            print("OCR 처리에 실패했습니다.")
            if result.get("claude_result", {}).get("error"):
                print(f"Claude 오류: {result['claude_result']['error']}")
            if result.get("gemini_result", {}).get("error"):
                print(f"Gemini 오류: {result['gemini_result']['error']}")
        
        # 통계 출력
        stats = ocr_system.get_statistics()
        print(f"\n=== 통계 ===")
        print(f"처리된 이미지: {stats['total_processed']}개")
        print(f"평균 처리 시간: {stats['average_time']:.2f}초")
        print(f"Claude 성공률: {stats['claude_success_rate']:.1f}%")
        print(f"Gemini 성공률: {stats['gemini_success_rate']:.1f}%")
        
    except Exception as e:
        print(f"오류 발생: {str(e)}")
        logger.error(f"메인 실행 오류: {str(e)}")

if __name__ == "__main__":
    main()