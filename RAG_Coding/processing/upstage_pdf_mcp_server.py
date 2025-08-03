"""
Upstage PDF 전처리 MCP 서버
PDF 문서의 레이아웃 분석, 요소 분리, 배치 처리를 통한 고급 전처리 시스템
"""

import os
import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
import logging

# MCP 및 FastAPI 관련
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
import uvicorn

# LangChain Upstage 통합
try:
    from langchain_upstage import UpstageDocumentParseLoader
except ImportError:
    print("langchain-upstage가 설치되지 않았습니다. pip install langchain-upstage 를 실행하세요.")
    UpstageDocumentParseLoader = None

# PDF 처리 관련
import PyMuPDF as fitz  # PDF 처리
from PIL import Image
import io
import base64

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UpstageLayoutAnalyzer:
    """Upstage API를 사용한 레이아웃 분석기"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.loader = None
        if UpstageDocumentParseLoader:
            os.environ["UPSTAGE_API_KEY"] = api_key
    
    async def analyze_layout(self, file_path: str, split: str = "page") -> List[Dict]:
        """PDF 레이아웃 분석 수행"""
        try:
            if not UpstageDocumentParseLoader:
                raise Exception("UpstageDocumentParseLoader가 설치되지 않았습니다.")
            
            loader = UpstageDocumentParseLoader(file_path, split=split)
            docs = loader.load()
            
            results = []
            for i, doc in enumerate(docs):
                results.append({
                    "page": i + 1,
                    "content": doc.page_content,
                    "metadata": doc.metadata
                })
            
            logger.info(f"레이아웃 분석 완료: {len(results)} 페이지")
            return results
            
        except Exception as e:
            logger.error(f"레이아웃 분석 실패: {str(e)}")
            raise HTTPException(status_code=500, detail=f"레이아웃 분석 실패: {str(e)}")

class ElementExtractor:
    """요소별 추출기 (텍스트, 이미지, 테이블)"""
    
    def __init__(self):
        self.current_id = 0
    
    def extract_elements(self, layout_data: List[Dict]) -> Dict[str, Any]:
        """레이아웃 데이터에서 요소별 추출"""
        elements = {
            "texts": [],
            "images": [],
            "tables": [],
            "metadata": {}
        }
        
        for page_data in layout_data:
            page_num = page_data["page"]
            content = page_data["content"]
            metadata = page_data.get("metadata", {})
            
            # 텍스트 요소 추출
            if metadata.get("type") == "text" or not metadata.get("type"):
                elements["texts"].append({
                    "id": self._get_next_id(),
                    "page": page_num,
                    "content": content,
                    "type": "text",
                    "metadata": metadata
                })
            
            # 테이블 요소 처리
            elif metadata.get("type") == "table":
                elements["tables"].append({
                    "id": self._get_next_id(),
                    "page": page_num,
                    "content": content,
                    "type": "table",
                    "metadata": metadata
                })
            
            # 이미지 요소 처리 (메타데이터 기반)
            elif metadata.get("type") == "image":
                elements["images"].append({
                    "id": self._get_next_id(),
                    "page": page_num,
                    "content": content,
                    "type": "image",
                    "metadata": metadata
                })
        
        elements["metadata"] = {
            "total_pages": len(layout_data),
            "total_elements": len(elements["texts"]) + len(elements["images"]) + len(elements["tables"]),
            "processed_at": datetime.now().isoformat()
        }
        
        logger.info(f"요소 추출 완료: 텍스트 {len(elements['texts'])}, 이미지 {len(elements['images'])}, 테이블 {len(elements['tables'])}")
        return elements
    
    def _get_next_id(self) -> int:
        """연속 ID 생성"""
        self.current_id += 1
        return self.current_id

class BatchProcessor:
    """배치 처리 시스템"""
    
    def __init__(self, batch_size: int = 100):
        self.batch_size = batch_size
    
    async def process_large_pdf(self, file_path: str, analyzer: UpstageLayoutAnalyzer, extractor: ElementExtractor) -> Dict[str, Any]:
        """대용량 PDF 배치 처리"""
        try:
            # PDF 페이지 수 확인
            doc = fitz.open(file_path)
            total_pages = len(doc)
            doc.close()
            
            logger.info(f"PDF 총 페이지 수: {total_pages}")
            
            if total_pages <= self.batch_size:
                # 작은 파일은 일괄 처리
                layout_data = await analyzer.analyze_layout(file_path)
                elements = extractor.extract_elements(layout_data)
                return elements
            
            # 대용량 파일 배치 처리
            all_elements = {"texts": [], "images": [], "tables": [], "metadata": {}}
            
            for start_page in range(0, total_pages, self.batch_size):
                end_page = min(start_page + self.batch_size, total_pages)
                logger.info(f"배치 처리 중: 페이지 {start_page+1}-{end_page}")
                
                # 페이지 범위별 임시 파일 생성 필요시 구현
                # 현재는 전체 파일로 처리
                layout_data = await analyzer.analyze_layout(file_path)
                batch_elements = extractor.extract_elements(layout_data)
                
                # 결과 병합
                all_elements["texts"].extend(batch_elements["texts"])
                all_elements["images"].extend(batch_elements["images"])
                all_elements["tables"].extend(batch_elements["tables"])
            
            all_elements["metadata"] = {
                "total_pages": total_pages,
                "batch_size": self.batch_size,
                "total_elements": len(all_elements["texts"]) + len(all_elements["images"]) + len(all_elements["tables"]),
                "processed_at": datetime.now().isoformat()
            }
            
            logger.info(f"배치 처리 완료: 총 {len(all_elements['texts']) + len(all_elements['images']) + len(all_elements['tables'])} 요소")
            return all_elements
            
        except Exception as e:
            logger.error(f"배치 처리 실패: {str(e)}")
            raise HTTPException(status_code=500, detail=f"배치 처리 실패: {str(e)}")

class PDFPreprocessorMCPServer:
    """PDF 전처리 MCP 서버 메인 클래스"""
    
    def __init__(self, upstage_api_key: str, batch_size: int = 100):
        self.app = FastAPI(title="PDF Preprocessor MCP Server", version="1.0.0")
        self.analyzer = UpstageLayoutAnalyzer(upstage_api_key)
        self.extractor = ElementExtractor()
        self.batch_processor = BatchProcessor(batch_size)
        
        # 라우트 설정
        self._setup_routes()
        
        # 디렉토리 설정
        self.in_box = Path("C:/Users/user/Dropbox/_RAG/RAG_Coding/in_box")
        self.processing = Path("C:/Users/user/Dropbox/_RAG/RAG_Coding/processing")
        self.out_box = Path("C:/Users/user/Dropbox/_RAG/RAG_Coding/out_box")
        self.archive = Path("C:/Users/user/Dropbox/_RAG/RAG_Coding/archive")
        
        # 디렉토리 생성
        for dir_path in [self.in_box, self.processing, self.out_box, self.archive]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def _setup_routes(self):
        """FastAPI 라우트 설정"""
        
        @self.app.get("/")
        async def health_check():
            return {"status": "healthy", "service": "PDF Preprocessor MCP Server"}
        
        @self.app.post("/process_pdf")
        async def process_pdf_endpoint(file_path: str, batch_size: Optional[int] = None):
            """PDF 처리 엔드포인트"""
            if batch_size:
                self.batch_processor.batch_size = batch_size
            
            try:
                # 파일 존재 확인
                if not os.path.exists(file_path):
                    raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")
                
                # PDF 처리 실행
                result = await self.batch_processor.process_large_pdf(
                    file_path, self.analyzer, self.extractor
                )
                
                # 결과 저장
                output_path = self._save_results(file_path, result)
                
                return {
                    "status": "success",
                    "message": "PDF 처리 완료",
                    "input_file": file_path,
                    "output_file": str(output_path),
                    "elements_count": result["metadata"]["total_elements"],
                    "processing_time": result["metadata"]["processed_at"]
                }
                
            except Exception as e:
                logger.error(f"PDF 처리 오류: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/process_inbox")
        async def process_inbox_endpoint():
            """in_box 폴더의 모든 PDF 처리"""
            try:
                pdf_files = list(self.in_box.glob("*.pdf"))
                results = []
                
                for pdf_file in pdf_files:
                    logger.info(f"처리 중: {pdf_file.name}")
                    
                    # processing 폴더로 이동
                    processing_file = self.processing / pdf_file.name
                    pdf_file.rename(processing_file)
                    
                    # PDF 처리
                    result = await self.batch_processor.process_large_pdf(
                        str(processing_file), self.analyzer, self.extractor
                    )
                    
                    # 결과 저장
                    output_path = self._save_results(str(processing_file), result)
                    
                    # archive로 원본 이동
                    archive_file = self.archive / pdf_file.name
                    processing_file.rename(archive_file)
                    
                    results.append({
                        "file": pdf_file.name,
                        "status": "completed",
                        "output": str(output_path),
                        "elements": result["metadata"]["total_elements"]
                    })
                
                return {
                    "status": "success",
                    "processed_files": len(results),
                    "results": results
                }
                
            except Exception as e:
                logger.error(f"in_box 처리 오류: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
    
    def _save_results(self, input_file: str, result: Dict[str, Any]) -> Path:
        """처리 결과를 out_box에 저장"""
        input_path = Path(input_file)
        output_name = f"{input_path.stem}_processed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        output_path = self.out_box / output_name
        
        # 결과에 원본 파일 정보 추가
        result["source_file"] = str(input_path)
        result["output_file"] = str(output_path)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        logger.info(f"결과 저장 완료: {output_path}")
        return output_path
    
    def run(self, host: str = "localhost", port: int = 8000):
        """서버 실행"""
        logger.info(f"PDF Preprocessor MCP Server 시작: http://{host}:{port}")
        uvicorn.run(self.app, host=host, port=port)

def main():
    """메인 실행 함수"""
    # 환경 변수에서 API 키 가져오기
    upstage_api_key = os.getenv("UPSTAGE_API_KEY")
    
    if not upstage_api_key:
        logger.error("UPSTAGE_API_KEY 환경변수가 설정되지 않았습니다.")
        print("사용법:")
        print("1. Upstage API 키를 환경변수에 설정하세요:")
        print("   set UPSTAGE_API_KEY=your_api_key_here")
        print("2. 서버를 실행하세요:")
        print("   python upstage_pdf_mcp_server.py")
        return
    
    # MCP 서버 생성 및 실행
    server = PDFPreprocessorMCPServer(upstage_api_key, batch_size=100)
    server.run()

if __name__ == "__main__":
    main()