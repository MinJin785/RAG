#!/usr/bin/env python3
"""
MCP Enhanced OCR System 2025
Advanced OCR with Model Context Protocol Integration

주요 기능:
- MCP 기반 표준화된 OCR 서비스 통합
- Context-Aware 문서 처리
- 다중 모델 협업 (Claude + Gemini + Layout Analysis)
- 동적 도구 발견 및 적응형 처리
- TeddyFlow 스타일 워크플로우 통합
"""

import asyncio
import json
import time
import base64
import logging
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from pathlib import Path
import hashlib
import aiohttp
from abc import ABC, abstractmethod

# MCP 관련 임포트 (실제 구현에서는 MCP SDK 사용)
# from mcp import MCPClient, MCPServer, Tool, Resource

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class DocumentContext:
    """문서 처리 컨텍스트"""
    document_id: str
    file_path: str
    file_type: str
    processing_history: List[Dict]
    metadata: Dict[str, Any]
    layout_analysis: Optional[Dict] = None
    quality_metrics: Optional[Dict] = None

@dataclass 
class OCRResult:
    """OCR 처리 결과"""
    success: bool
    text: str
    confidence: float
    processing_time: float
    method: str
    context: DocumentContext
    error: Optional[str] = None

class MCPServer(ABC):
    """MCP 서버 추상 클래스"""
    
    def __init__(self, name: str, port: int):
        self.name = name
        self.port = port
        self.capabilities = {}
    
    @abstractmethod
    async def initialize(self):
        """서버 초기화"""
        pass
    
    @abstractmethod 
    async def process_request(self, action: str, params: Dict) -> Dict:
        """요청 처리"""
        pass

class ClaudeOCRServer(MCPServer):
    """Claude OCR MCP 서버"""
    
    def __init__(self):
        super().__init__("claude_ocr", 8001)
        self.api_key = None
        self.capabilities = {
            "extract_text": {
                "description": "한글/영어 텍스트 정확 추출",
                "supports": ["pdf", "png", "jpg", "jpeg"],
                "context_aware": True
            },
            "analyze_layout": {
                "description": "문서 레이아웃 구조 분석", 
                "supports": ["complex_documents"],
                "context_aware": True
            }
        }
    
    async def initialize(self):
        """Claude API 초기화"""
        self.api_key = "claude_api_key_here"  # 실제 구현에서는 환경변수
        logger.info(f"✅ {self.name} 서버 초기화 완료")
    
    async def process_request(self, action: str, params: Dict) -> Dict:
        """Claude OCR 요청 처리"""
        start_time = time.time()
        
        try:
            if action == "extract_text":
                return await self._extract_text_with_context(params)
            elif action == "analyze_layout":
                return await self._analyze_layout(params)
            else:
                raise ValueError(f"지원하지 않는 액션: {action}")
                
        except Exception as e:
            processing_time = time.time() - start_time
            return {
                "success": False,
                "error": str(e),
                "processing_time": processing_time
            }
    
    async def _extract_text_with_context(self, params: Dict) -> Dict:
        """컨텍스트 기반 텍스트 추출"""
        file_path = params.get("file_path")
        context = params.get("context", {})
        layout_context = params.get("layout_context", {})
        
        # 이미지 읽기 및 인코딩
        with open(file_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode()
        
        # 컨텍스트 기반 프롬프트 생성
        if layout_context:
            prompt = f"""
이 문서의 레이아웃 분석 결과: {json.dumps(layout_context, ensure_ascii=False)}

위 레이아웃 정보를 참고하여 다음 이미지의 한국어와 영어 텍스트를 정확히 추출해주세요:

처리 규칙:
1. 레이아웃 구조를 고려한 텍스트 순서 유지
2. 제목, 본문, 표, 목록 등 요소별 구분
3. 한글: 완성형 한글로 정확히 인식
4. 영어: 대소문자 구분하여 정확히 인식
5. 문서 흐름에 따른 논리적 텍스트 배치

텍스트만 출력해주세요:
"""
        else:
            prompt = """
이 이미지의 한국어와 영어 텍스트를 정확히 OCR 처리해주세요.

처리 규칙:
1. 한글: 완성형 한글로 정확히 인식
2. 영어: 대소문자 구분하여 정확히 인식  
3. 숫자: 아라비아 숫자로 변환
4. 특수문자: 원본 그대로 유지
5. 레이아웃: 줄바꿈과 단락 구조 보존

텍스트만 출력해주세요:
"""
        
        # Claude API 호출 시뮬레이션
        await asyncio.sleep(0.5)  # API 호출 시뮬레이션
        
        # 실제 구현에서는 여기서 Claude API 호출
        extracted_text = f"[Claude OCR] 추출된 텍스트 (파일: {Path(file_path).name})"
        confidence = 0.95
        
        processing_time = time.time() - time.time()
        
        return {
            "success": True,
            "text": extracted_text,
            "confidence": confidence,
            "processing_time": processing_time,
            "method": "claude_context_ocr",
            "context_used": bool(layout_context)
        }
    
    async def _analyze_layout(self, params: Dict) -> Dict:
        """문서 레이아웃 분석"""
        file_path = params.get("file_path")
        
        # 레이아웃 분석 시뮬레이션
        await asyncio.sleep(0.3)
        
        layout_result = {
            "elements": [
                {"type": "title", "bbox": [100, 50, 500, 100], "confidence": 0.98},
                {"type": "paragraph", "bbox": [100, 120, 500, 300], "confidence": 0.95},
                {"type": "table", "bbox": [100, 320, 500, 450], "confidence": 0.92}
            ],
            "reading_order": [0, 1, 2],
            "document_type": "article"
        }
        
        return {
            "success": True,
            "layout": layout_result,
            "processing_time": 0.3
        }

class GeminiVisionServer(MCPServer):
    """Gemini Vision MCP 서버"""
    
    def __init__(self):
        super().__init__("gemini_vision", 8002)
        self.api_key = None
        self.capabilities = {
            "analyze_image": {
                "description": "멀티모달 이미지 분석",
                "supports": ["visual_elements", "image_quality"],
                "context_aware": True
            },
            "enhance_quality": {
                "description": "이미지 품질 개선 분석",
                "supports": ["quality_metrics", "enhancement_suggestions"],
                "context_aware": False
            }
        }
    
    async def initialize(self):
        """Gemini API 초기화"""
        self.api_key = "gemini_api_key_here"
        logger.info(f"✅ {self.name} 서버 초기화 완료")
    
    async def process_request(self, action: str, params: Dict) -> Dict:
        """Gemini Vision 요청 처리"""
        start_time = time.time()
        
        try:
            if action == "analyze_image":
                return await self._analyze_image(params)
            elif action == "enhance_quality":
                return await self._enhance_quality(params)
            else:
                raise ValueError(f"지원하지 않는 액션: {action}")
                
        except Exception as e:
            processing_time = time.time() - start_time
            return {
                "success": False,
                "error": str(e),
                "processing_time": processing_time
            }
    
    async def _analyze_image(self, params: Dict) -> Dict:
        """이미지 멀티모달 분석"""
        file_path = params.get("file_path")
        
        # Gemini 분석 시뮬레이션
        await asyncio.sleep(0.4)
        
        analysis_result = {
            "visual_elements": {
                "has_images": True,
                "has_tables": True,
                "has_charts": False,
                "color_scheme": "black_and_white"
            },
            "quality_assessment": {
                "resolution": "high",
                "clarity": 0.92,
                "noise_level": "low"
            },
            "content_suggestions": [
                "이미지 품질이 우수하여 OCR에 적합",
                "테이블 구조가 명확하게 구분됨"
            ]
        }
        
        return {
            "success": True,
            "analysis": analysis_result,
            "processing_time": 0.4,
            "method": "gemini_vision"
        }
    
    async def _enhance_quality(self, params: Dict) -> Dict:
        """이미지 품질 개선 분석"""
        # 품질 개선 제안 생성
        return {
            "success": True,
            "enhancement_suggestions": [
                "대비 조정으로 텍스트 선명도 향상 가능",
                "노이즈 제거 필터 적용 권장"
            ],
            "processing_time": 0.2
        }

class LayoutAnalysisServer(MCPServer):
    """Layout Analysis MCP 서버"""
    
    def __init__(self):
        super().__init__("layout_analyzer", 8003)
        self.capabilities = {
            "detect_structure": {
                "description": "OmniDocBench 19개 카테고리 구조 분석",
                "supports": ["19_categories", "reading_order"],
                "context_aware": True
            },
            "classify_elements": {
                "description": "문서 요소 분류 및 라벨링",
                "supports": ["element_classification", "confidence_scoring"],
                "context_aware": True
            }
        }
    
    async def initialize(self):
        """Layout Analyzer 초기화"""
        logger.info(f"✅ {self.name} 서버 초기화 완료")
    
    async def process_request(self, action: str, params: Dict) -> Dict:
        """Layout Analysis 요청 처리"""
        if action == "detect_structure":
            return await self._detect_structure(params)
        elif action == "classify_elements":
            return await self._classify_elements(params)
        else:
            raise ValueError(f"지원하지 않는 액션: {action}")
    
    async def _detect_structure(self, params: Dict) -> Dict:
        """19개 카테고리 구조 분석"""
        file_path = params.get("file_path")
        
        # OmniDocBench 기반 분석 시뮬레이션
        await asyncio.sleep(0.6)
        
        structure_result = {
            "categories": {
                "title": {"count": 1, "confidence": 0.98},
                "text": {"count": 5, "confidence": 0.95},
                "table": {"count": 2, "confidence": 0.92},
                "figure": {"count": 1, "confidence": 0.89},
                "list": {"count": 3, "confidence": 0.94}
            },
            "reading_order": [
                {"type": "title", "bbox": [100, 50, 500, 100]},
                {"type": "text", "bbox": [100, 120, 500, 200]},
                {"type": "table", "bbox": [100, 220, 500, 350]},
                {"type": "text", "bbox": [100, 370, 500, 450]}
            ],
            "document_classification": "research_paper"
        }
        
        return {
            "success": True,
            "structure": structure_result,
            "processing_time": 0.6,
            "categories_detected": 5
        }
    
    async def _classify_elements(self, params: Dict) -> Dict:
        """문서 요소 분류"""
        return {
            "success": True,
            "elements": [
                {"id": 1, "type": "heading", "level": 1, "confidence": 0.98},
                {"id": 2, "type": "paragraph", "confidence": 0.95},
                {"id": 3, "type": "table", "rows": 5, "cols": 3, "confidence": 0.92}
            ],
            "processing_time": 0.3
        }

class MCPClient:
    """MCP 클라이언트"""
    
    def __init__(self):
        self.servers = {}
        self.session_id = self._generate_session_id()
    
    def _generate_session_id(self) -> str:
        """세션 ID 생성"""
        return hashlib.md5(f"{time.time()}".encode()).hexdigest()[:8]
    
    async def register_server(self, server: MCPServer):
        """MCP 서버 등록"""
        await server.initialize()
        self.servers[server.name] = server
        logger.info(f"🔗 MCP 서버 등록: {server.name}")
    
    async def discover_capabilities(self) -> Dict[str, Dict]:
        """서버 기능 탐색"""
        capabilities = {}
        for name, server in self.servers.items():
            capabilities[name] = server.capabilities
        
        logger.info(f"🔍 발견된 MCP 서버: {list(capabilities.keys())}")
        return capabilities
    
    async def call_tool(self, server_name: str, action: str, params: Dict) -> Dict:
        """MCP 도구 호출"""
        if server_name not in self.servers:
            raise ValueError(f"서버를 찾을 수 없음: {server_name}")
        
        server = self.servers[server_name]
        
        # 요청 로깅
        logger.info(f"📡 MCP 호출: {server_name}.{action}")
        
        # 서버 요청 처리
        result = await server.process_request(action, params)
        
        # 응답 로깅
        if result.get("success"):
            logger.info(f"✅ MCP 성공: {server_name}.{action} ({result.get('processing_time', 0):.2f}초)")
        else:
            logger.error(f"❌ MCP 실패: {server_name}.{action} - {result.get('error')}")
        
        return result

class MCPEnhancedOCRSystem:
    """MCP 기반 고급 OCR 시스템"""
    
    def __init__(self):
        self.mcp_client = MCPClient()
        self.context_cache = {}
        self.processing_stats = {
            "total_processed": 0,
            "success_rate": 0.0,
            "avg_processing_time": 0.0
        }
    
    async def initialize(self):
        """시스템 초기화"""
        logger.info("🚀 MCP Enhanced OCR System 초기화 시작")
        
        # MCP 서버 등록
        servers = [
            ClaudeOCRServer(),
            GeminiVisionServer(), 
            LayoutAnalysisServer()
        ]
        
        for server in servers:
            await self.mcp_client.register_server(server)
        
        # 기능 탐색
        capabilities = await self.mcp_client.discover_capabilities()
        logger.info("✅ MCP Enhanced OCR System 초기화 완료")
        
        return capabilities
    
    def _create_document_context(self, file_path: str) -> DocumentContext:
        """문서 컨텍스트 생성"""
        return DocumentContext(
            document_id=hashlib.md5(file_path.encode()).hexdigest()[:12],
            file_path=file_path,
            file_type=Path(file_path).suffix.lower(),
            processing_history=[],
            metadata={
                "created_at": time.time(),
                "file_size": Path(file_path).stat().st_size if Path(file_path).exists() else 0
            }
        )
    
    async def process_document(self, file_path: str, options: Dict = None) -> OCRResult:
        """문서 처리 (MCP 워크플로우)"""
        start_time = time.time()
        options = options or {}
        
        try:
            # 1. 컨텍스트 생성
            context = self._create_document_context(file_path)
            logger.info(f"📄 문서 처리 시작: {Path(file_path).name} (ID: {context.document_id})")
            
            # 2. 레이아웃 분석 (MCP)
            layout_result = await self.mcp_client.call_tool(
                "layout_analyzer",
                "detect_structure", 
                {"file_path": file_path, "context": context.__dict__}
            )
            
            if layout_result["success"]:
                context.layout_analysis = layout_result["structure"]
                context.processing_history.append({
                    "step": "layout_analysis",
                    "timestamp": time.time(),
                    "result": "success"
                })
            
            # 3. 이미지 품질 분석 (MCP)
            quality_result = await self.mcp_client.call_tool(
                "gemini_vision",
                "analyze_image",
                {"file_path": file_path, "context": context.__dict__}
            )
            
            if quality_result["success"]:
                context.quality_metrics = quality_result["analysis"]
                context.processing_history.append({
                    "step": "quality_analysis", 
                    "timestamp": time.time(),
                    "result": "success"
                })
            
            # 4. 컨텍스트 기반 OCR (MCP)
            ocr_result = await self.mcp_client.call_tool(
                "claude_ocr",
                "extract_text",
                {
                    "file_path": file_path,
                    "context": context.__dict__,
                    "layout_context": context.layout_analysis,
                    "quality_context": context.quality_metrics
                }
            )
            
            if not ocr_result["success"]:
                raise Exception(f"OCR 처리 실패: {ocr_result.get('error')}")
            
            # 5. 결과 종합
            processing_time = time.time() - start_time
            
            result = OCRResult(
                success=True,
                text=ocr_result["text"],
                confidence=ocr_result["confidence"],
                processing_time=processing_time,
                method="mcp_enhanced_ocr",
                context=context
            )
            
            # 6. 통계 업데이트
            self._update_stats(result)
            
            logger.info(f"✅ 문서 처리 완료: {Path(file_path).name} ({processing_time:.2f}초)")
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_result = OCRResult(
                success=False,
                text="",
                confidence=0.0,
                processing_time=processing_time,
                method="mcp_enhanced_ocr",
                context=context if 'context' in locals() else None,
                error=str(e)
            )
            
            logger.error(f"❌ 문서 처리 실패: {Path(file_path).name} - {str(e)}")
            return error_result
    
    async def batch_process(self, file_paths: List[str], max_concurrent: int = 3) -> List[OCRResult]:
        """배치 처리"""
        logger.info(f"📋 배치 처리 시작: {len(file_paths)}개 파일")
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_with_semaphore(file_path: str):
            async with semaphore:
                return await self.process_document(file_path)
        
        tasks = [process_with_semaphore(fp) for fp in file_paths]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 예외 처리
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                error_result = OCRResult(
                    success=False,
                    text="",
                    confidence=0.0,
                    processing_time=0.0,
                    method="mcp_enhanced_ocr",
                    context=None,
                    error=str(result)
                )
                processed_results.append(error_result)
            else:
                processed_results.append(result)
        
        successful = sum(1 for r in processed_results if r.success)
        logger.info(f"✅ 배치 처리 완료: {successful}/{len(file_paths)} 성공")
        
        return processed_results
    
    def _update_stats(self, result: OCRResult):
        """통계 업데이트"""
        self.processing_stats["total_processed"] += 1
        
        # 성공률 계산
        if hasattr(self, '_success_count'):
            self._success_count += 1 if result.success else 0
        else:
            self._success_count = 1 if result.success else 0
        
        self.processing_stats["success_rate"] = self._success_count / self.processing_stats["total_processed"]
        
        # 평균 처리 시간 계산
        if hasattr(self, '_total_time'):
            self._total_time += result.processing_time
        else:
            self._total_time = result.processing_time
        
        self.processing_stats["avg_processing_time"] = self._total_time / self.processing_stats["total_processed"]
    
    def get_stats(self) -> Dict:
        """처리 통계 조회"""
        return {
            **self.processing_stats,
            "active_servers": list(self.mcp_client.servers.keys()),
            "session_id": self.mcp_client.session_id
        }

# TeddyFlow 스타일 워크플로우 통합
class TeddyFlowOCRWorkflow:
    """TeddyFlow 스타일 OCR 워크플로우"""
    
    def __init__(self, ocr_system: MCPEnhancedOCRSystem):
        self.ocr_system = ocr_system
        self.workflows = {}
    
    def create_workflow(self, name: str, config: Dict) -> str:
        """워크플로우 생성"""
        workflow_id = hashlib.md5(f"{name}_{time.time()}".encode()).hexdigest()[:8]
        
        self.workflows[workflow_id] = {
            "name": name,
            "config": config,
            "created_at": time.time(),
            "executions": 0
        }
        
        logger.info(f"🔄 워크플로우 생성: {name} (ID: {workflow_id})")
        return workflow_id
    
    async def execute_workflow(self, workflow_id: str, inputs: Dict) -> Dict:
        """워크플로우 실행"""
        if workflow_id not in self.workflows:
            raise ValueError(f"워크플로우를 찾을 수 없음: {workflow_id}")
        
        workflow = self.workflows[workflow_id]
        workflow["executions"] += 1
        
        logger.info(f"▶️ 워크플로우 실행: {workflow['name']}")
        
        # OCR 처리
        file_path = inputs.get("file_path")
        if not file_path:
            raise ValueError("file_path가 필요합니다")
        
        result = await self.ocr_system.process_document(file_path, inputs.get("options", {}))
        
        return {
            "workflow_id": workflow_id,
            "workflow_name": workflow["name"],
            "execution_count": workflow["executions"],
            "result": {
                "success": result.success,
                "text": result.text,
                "confidence": result.confidence,
                "processing_time": result.processing_time,
                "context": result.context.__dict__ if result.context else None
            }
        }

# 메인 실행 함수
async def main():
    """메인 실행 함수"""
    logger.info("🎯 MCP Enhanced OCR System 데모 시작")
    
    # 시스템 초기화
    ocr_system = MCPEnhancedOCRSystem()
    capabilities = await ocr_system.initialize()
    
    print("\n🔧 발견된 MCP 서버 기능:")
    for server, caps in capabilities.items():
        print(f"  📡 {server}:")
        for action, details in caps.items():
            print(f"    - {action}: {details['description']}")
    
    # TeddyFlow 워크플로우 생성
    workflow_system = TeddyFlowOCRWorkflow(ocr_system)
    
    workflow_id = workflow_system.create_workflow(
        "고급_문서_OCR_처리",
        {
            "input_format": ["pdf", "png", "jpg"],
            "output_format": "structured_json",
            "quality_enhancement": True,
            "layout_analysis": True
        }
    )
    
    # 샘플 파일 처리 (실제 파일이 있다면)
    sample_files = [
        "RAG_OCR/OCR_Input/batch_sample_1.png",
        "RAG_OCR/OCR_Input/batch_sample_2.png"
    ]
    
    existing_files = [f for f in sample_files if Path(f).exists()]
    
    if existing_files:
        print(f"\n📄 {len(existing_files)}개 파일 처리 시작...")
        
        # 개별 처리 데모
        for file_path in existing_files[:1]:  # 첫 번째 파일만 처리
            result = await workflow_system.execute_workflow(
                workflow_id,
                {"file_path": file_path}
            )
            
            print(f"\n✅ 처리 결과:")
            print(f"  📁 파일: {Path(file_path).name}")
            print(f"  🎯 성공: {result['result']['success']}")
            print(f"  ⏱️ 처리시간: {result['result']['processing_time']:.2f}초")
            print(f"  🎯 신뢰도: {result['result']['confidence']:.2%}")
            
            if result['result']['success']:
                text_preview = result['result']['text'][:100] + "..." if len(result['result']['text']) > 100 else result['result']['text']
                print(f"  📝 텍스트: {text_preview}")
        
        # 배치 처리 데모
        if len(existing_files) > 1:
            print(f"\n📋 배치 처리 데모...")
            batch_results = await ocr_system.batch_process(existing_files)
            
            successful = sum(1 for r in batch_results if r.success)
            print(f"  ✅ 배치 결과: {successful}/{len(batch_results)} 성공")
    
    else:
        print("\n⚠️ 샘플 파일이 없어 시뮬레이션 모드로 실행")
        
        # 시뮬레이션 파일 경로
        sim_file = "demo_document.pdf"
        result = await workflow_system.execute_workflow(
            workflow_id,
            {"file_path": sim_file}
        )
        
        print(f"✅ 시뮬레이션 결과: {result['result']['success']}")
    
    # 시스템 통계
    stats = ocr_system.get_stats()
    print(f"\n📊 시스템 통계:")
    print(f"  📈 처리된 문서: {stats['total_processed']}개")
    print(f"  🎯 성공률: {stats['success_rate']:.1%}")
    print(f"  ⏱️ 평균 처리시간: {stats['avg_processing_time']:.2f}초")
    print(f"  🔗 활성 서버: {', '.join(stats['active_servers'])}")
    
    logger.info("🎉 MCP Enhanced OCR System 데모 완료")

if __name__ == "__main__":
    asyncio.run(main())