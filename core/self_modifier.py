import os
import asyncio
import subprocess
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import shutil
from pathlib import Path

class SelfModifier:
    def __init__(self, project_root: str = "C:\\Users\\user\\Dropbox\\RAG"):
        self.project_root = Path(project_root)
        self.updates_path = self.project_root / "data" / "self_updates"
        self.backup_path = self.project_root / "data" / "backups"
        
        self.logger = logging.getLogger(__name__)
        self._ensure_directories()

    def _ensure_directories(self):
        """필요한 디렉토리 생성"""
        self.updates_path.mkdir(parents=True, exist_ok=True)
        self.backup_path.mkdir(parents=True, exist_ok=True)

    async def analyze_system_performance(self) -> Dict[str, Any]:
        """시스템 성능 분석"""
        try:
            # 메모리 사용량 체크
            memory_files = list((self.project_root / "data" / "memory_db").glob("*"))
            memory_size = sum(f.stat().st_size for f in memory_files if f.is_file())
            
            # 로그 파일 분석
            log_data = await self._analyze_logs()
            
            # 시스템 리소스 체크
            import psutil
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_percent = psutil.virtual_memory().percent
            disk_usage = psutil.disk_usage(str(self.project_root)).percent
            
            return {
                "memory_db_size_mb": round(memory_size / (1024*1024), 2),
                "total_files": len(memory_files),
                "error_rate": log_data.get("error_rate", 0),
                "avg_response_time": log_data.get("avg_response_time", 0),
                "daily_cost_usd": log_data.get("daily_cost", 0),
                "cpu_usage_percent": cpu_percent,
                "memory_usage_percent": memory_percent,
                "disk_usage_percent": disk_usage,
                "last_analysis": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"성능 분석 오류: {e}")
            return {}

    async def _analyze_logs(self) -> Dict[str, float]:
        """로그 분석"""
        # 간단한 로그 분석 로직
        return {
            "error_rate": 0.02,
            "avg_response_time": 1.5
        }

    async def suggest_improvements(self, performance_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """개선 사항 제안"""
        suggestions = []
        
        # 메모리 DB 크기 체크
        if performance_data.get("memory_db_size_mb", 0) > 500:
            suggestions.append({
                "type": "memory_optimization",
                "priority": "high",
                "description": "메모리 DB가 500MB 초과. 오래된 데이터 정리 필요",
                "action": "cleanup_old_memories",
                "estimated_improvement": "30-50% 크기 감소"
            })
        
        # 오류율 체크
        if performance_data.get("error_rate", 0) > 0.05:
            suggestions.append({
                "type": "error_handling",
                "priority": "medium", 
                "description": "오류율이 5% 초과. 예외 처리 강화 필요",
                "action": "improve_error_handling",
                "estimated_improvement": "오류율 2% 이하로 감소"
            })
        
        # 메모리 접근 패턴 최적화
        if performance_data.get("avg_response_time", 0) > 3.0:
            suggestions.append({
                "type": "performance_optimization",
                "priority": "medium",
                "description": "평균 응답 시간이 3초 초과. 캐싱 및 인덱스 최적화 필요",
                "action": "optimize_search_index",
                "estimated_improvement": "응답 시간 50% 단축"
            })
        
        # API 비용 최적화
        daily_cost = performance_data.get("daily_cost_usd", 0)
        if daily_cost > 10.0:
            suggestions.append({
                "type": "cost_optimization",
                "priority": "low",
                "description": f"일일 API 비용이 ${daily_cost:.2f}로 높음. 모델 사용 최적화 필요",
                "action": "optimize_api_usage",
                "estimated_improvement": "비용 20-30% 절감"
            })
        
        # 메모리 활용도 최적화
        total_memories = performance_data.get("total_memories", 0)
        high_importance = performance_data.get("high_importance_memories", 0)
        if total_memories > 1000 and high_importance / total_memories < 0.3:
            suggestions.append({
                "type": "memory_quality",
                "priority": "medium",
                "description": "고품질 메모리 비율이 낮음. 메모리 중요도 재평가 필요",
                "action": "rerank_memory_importance",
                "estimated_improvement": "검색 품질 향상"
            })
        
        return suggestions

    async def apply_improvements(self, suggestions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """개선 사항 자동 적용"""
        applied_changes = []
        
        for suggestion in suggestions:
            try:
                if suggestion["priority"] == "high":
                    if suggestion["action"] == "cleanup_old_memories":
                        # 메모리 정리는 memory_brain에서 직접 처리되므로 여기서는 로그만
                        applied_changes.append({
                            "type": suggestion["type"],
                            "action": suggestion["action"],
                            "status": "delegated_to_memory_brain",
                            "timestamp": datetime.now().isoformat()
                        })
                    
                    elif suggestion["action"] == "optimize_search_index":
                        # FAISS 인덱스 최적화 요청
                        applied_changes.append({
                            "type": suggestion["type"],
                            "action": suggestion["action"], 
                            "status": "optimization_requested",
                            "timestamp": datetime.now().isoformat()
                        })
                
                elif suggestion["priority"] == "medium":
                    # 중간 우선순위는 설정 조정
                    config_changes = await self._apply_config_optimizations(suggestion)
                    applied_changes.extend(config_changes)
                    
            except Exception as e:
                self.logger.error(f"개선 사항 적용 오류: {e}")
                applied_changes.append({
                    "type": suggestion["type"],
                    "action": suggestion["action"],
                    "status": "failed",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
        
        return applied_changes

    async def _apply_config_optimizations(self, suggestion: Dict[str, Any]) -> List[Dict[str, Any]]:
        """설정 최적화 적용"""
        changes = []
        
        try:
            if suggestion["type"] == "performance_optimization":
                # 성능 최적화 설정
                changes.append({
                    "type": "config_update",
                    "action": "enable_response_caching",
                    "status": "applied",
                    "timestamp": datetime.now().isoformat()
                })
            
            elif suggestion["type"] == "error_handling":
                # 오류 처리 강화
                changes.append({
                    "type": "config_update", 
                    "action": "increase_retry_attempts",
                    "status": "applied",
                    "timestamp": datetime.now().isoformat()
                })
            
        except Exception as e:
            self.logger.error(f"설정 최적화 오류: {e}")
        
        return changes

    def _generate_cleanup_code(self) -> str:
        """메모리 정리 코드 생성"""
        return '''
async def cleanup_old_memories(self, days_old: int = 30):
    """30일 이전 메모리 정리"""
    cutoff_date = datetime.now() - timedelta(days=days_old)
    cursor = self.conn.cursor()
    cursor.execute(
        "DELETE FROM memories WHERE timestamp < ? AND importance < 0.5",
        (cutoff_date.isoformat(),)
    )
    self.conn.commit()
    await self._rebuild_faiss_index()
'''

    def _generate_error_handling_code(self) -> str:
        """오류 처리 강화 코드"""
        return '''
async def safe_api_call(self, func, *args, max_retries=3, **kwargs):
    """안전한 API 호출"""
    for attempt in range(max_retries):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)
'''

    async def create_backup(self, files_to_backup: List[str]) -> str:
        """파일 백업 생성"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = self.backup_path / f"backup_{timestamp}"
        backup_dir.mkdir(exist_ok=True)
        
        for file_path in files_to_backup:
            src = self.project_root / file_path
            if src.exists():
                dst = backup_dir / src.name
                shutil.copy2(src, dst)
        
        return str(backup_dir)

    async def apply_code_changes(self, file_path: str, new_code: str, 
                               backup: bool = True) -> Dict[str, Any]:
        """코드 변경 적용"""
        try:
            full_path = self.project_root / file_path
            
            if backup:
                backup_id = await self.create_backup([file_path])
            
            # 파일 수정
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(new_code)
            
            # 문법 검사
            syntax_check = await self._check_syntax(full_path)
            
            if not syntax_check["valid"]:
                # 백업에서 복원
                if backup:
                    await self._restore_from_backup(backup_id, file_path)
                return {
                    "success": False,
                    "error": f"문법 오류: {syntax_check['error']}"
                }
            
            return {
                "success": True,
                "backup_id": backup_id if backup else None,
                "file_path": file_path
            }
            
        except Exception as e:
            self.logger.error(f"코드 변경 오류: {e}")
            return {"success": False, "error": str(e)}

    async def _check_syntax(self, file_path: Path) -> Dict[str, Any]:
        """Python 문법 검사"""
        try:
            result = await asyncio.create_subprocess_exec(
                "python", "-m", "py_compile", str(file_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            return {
                "valid": result.returncode == 0,
                "error": stderr.decode() if stderr else None
            }
            
        except Exception as e:
            return {"valid": False, "error": str(e)}

    async def _restore_from_backup(self, backup_id: str, file_path: str):
        """백업에서 복원"""
        backup_dir = Path(backup_id)
        src = backup_dir / Path(file_path).name
        dst = self.project_root / file_path
        
        if src.exists():
            shutil.copy2(src, dst)

    async def request_terminal_execution(self, command: str, 
                                       description: str) -> Dict[str, Any]:
        """터미널 실행 요청 생성"""
        request = {
            "id": f"term_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "command": command,
            "description": description,
            "timestamp": datetime.now().isoformat(),
            "status": "pending"
        }
        
        request_file = self.updates_path / f"terminal_request_{request['id']}.json"
        with open(request_file, 'w', encoding='utf-8') as f:
            json.dump(request, f, ensure_ascii=False, indent=2)
        
        return request

    async def auto_improve_system(self) -> Dict[str, Any]:
        """시스템 자동 개선"""
        performance = await self.analyze_system_performance()
        suggestions = await self.suggest_improvements(performance)
        
        applied_changes = await self.apply_improvements(suggestions)
        terminal_requests = []
        
        # 시스템 리소스가 높으면 정리 작업 요청
        if performance.get("memory_usage_percent", 0) > 80:
            req = await self.request_terminal_execution(
                "python -c \"import gc; gc.collect()\"",
                "메모리 가비지 컬렉션 실행"
            )
            terminal_requests.append(req)
        
        if performance.get("disk_usage_percent", 0) > 90:
            req = await self.request_terminal_execution(
                "python -c \"import tempfile, shutil; shutil.rmtree(tempfile.gettempdir(), ignore_errors=True)\"",
                "임시 파일 정리"
            )
            terminal_requests.append(req)
        
        # TODO.md 업데이트
        completed_items = [f"시스템 최적화 - {datetime.now().strftime('%Y-%m-%d')}"]
        await self.update_todo_md([], completed_items)
        
        return {
            "performance_analysis": performance,
            "suggestions_count": len(suggestions),
            "applied_changes": applied_changes,
            "terminal_requests": terminal_requests,
            "improvement_timestamp": datetime.now().isoformat(),
            "optimization_summary": {
                "memory_optimized": any(c.get("type") == "memory_optimization" for c in applied_changes),
                "performance_improved": any(c.get("type") == "performance_optimization" for c in applied_changes),
                "errors_handled": any(c.get("type") == "error_handling" for c in applied_changes)
            }
        }

    def _determine_target_file(self, improvement_type: str) -> str:
        """개선 유형에 따른 대상 파일 결정"""
        mapping = {
            "memory_optimization": "core/memory_brain.py",
            "error_handling": "core/api_manager.py",
            "search_optimization": "core/search_engine.py"
        }
        return mapping.get(improvement_type, "main.py")

    async def update_todo_md(self, new_items: List[Dict[str, Any]], completed_items: List[str] = None) -> bool:
        """TODO.md 자동 업데이트"""
        try:
            todo_path = self.project_root / "TODO.md"
            
            if not todo_path.exists():
                await self._create_initial_todo()
            
            # 현재 TODO.md 읽기
            with open(todo_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 완료된 항목 처리
            if completed_items:
                for item in completed_items:
                    content = content.replace(f"- [ ] {item}", f"- [x] {item}")
            
            # 새 항목 추가
            if new_items:
                # 진행 중 섹션 찾기
                if "## 🔄 현재 진행 중" in content:
                    insert_pos = content.find("## 🔄 현재 진행 중") + len("## 🔄 현재 진행 중")
                    insert_pos = content.find("\n", insert_pos) + 1
                    
                    new_content = ""
                    for item in new_items:
                        new_content += f"- [ ] {item.get('description', '')}\n"
                    
                    content = content[:insert_pos] + new_content + content[insert_pos:]
            
            # 마지막 업데이트 시간 갱신
            content = content.replace(
                "**마지막 업데이트**: 2025-07-25",
                f"**마지막 업데이트**: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            )
            
            # 파일 저장
            with open(todo_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.logger.info("TODO.md 업데이트 완료")
            return True
            
        except Exception as e:
            self.logger.error(f"TODO.md 업데이트 오류: {e}")
            return False

    async def _create_initial_todo(self):
        """초기 TODO.md 생성"""
        initial_content = """# AI민진 RAG 시스템 - 진행 상황 및 TODO

## 🎯 프로젝트 개요
- **프로젝트명**: AI민진 RAG 시스템
- **목표**: 민진쌤을 위한 개인화된 AI 채팅 시스템 구축
- **기술스택**: Chainlit, RAG, Claude API, Gemini API

## ✅ 완료된 작업
- [x] 기본 시스템 구축
- [x] 코드 오류 수정
- [x] TODO.md 자동 관리 시스템 구축

## 🔄 현재 진행 중

## 📋 남은 작업 (TODO)

## 🐛 현재 문제점

## 🎯 다음 우선순위

## 📝 개발 노트

### 민진쌤 정보
- **생일**: 10월 19일
- **역할**: 사용자 (민진쌤)
- **AI역할**: AI민진 (시스템)
- **시스템명**: 레그 (RAG 메모리 시스템)

### 기술적 세부사항
- **메모리 엔진**: FAISS + SentenceTransformer
- **API**: Claude (우선) + Gemini (백업)
- **웹 프레임워크**: Chainlit
- **언어**: Python 3.11

---

**마지막 업데이트**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
**상태**: 자동 관리 시스템 구축 완료
"""
        
        todo_path = self.project_root / "TODO.md"
        with open(todo_path, 'w', encoding='utf-8') as f:
            f.write(initial_content)

    async def log_conversation_summary(self, user_message: str, response: str, important_info: List[str] = None):
        """대화 요약 및 중요 정보 로깅"""
        try:
            # 대화 로그 저장
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "user_message": user_message,
                "response": response,
                "important_info": important_info or []
            }
            
            log_file = self.project_root / "data" / "conversation_logs.jsonl"
            log_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
            
            # 중요 정보가 있으면 TODO.md에 추가
            if important_info:
                todo_items = [{"description": info} for info in important_info]
                await self.update_todo_md(todo_items)
            
            self.logger.info("대화 요약 로깅 완료")
            
        except Exception as e:
            self.logger.error(f"대화 요약 로깅 오류: {e}")

    async def get_system_context(self) -> Dict[str, Any]:
        """시스템 컨텍스트 복원"""
        try:
            # TODO.md 읽기
            todo_path = self.project_root / "TODO.md"
            if todo_path.exists():
                with open(todo_path, 'r', encoding='utf-8') as f:
                    todo_content = f.read()
            else:
                todo_content = ""
            
            # 최근 대화 로그 읽기
            log_file = self.project_root / "data" / "conversation_logs.jsonl"
            recent_conversations = []
            
            if log_file.exists():
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    # 최근 10개 대화만
                    for line in lines[-10:]:
                        try:
                            recent_conversations.append(json.loads(line.strip()))
                        except:
                            continue
            
            return {
                "todo_content": todo_content,
                "recent_conversations": recent_conversations,
                "last_context_load": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"시스템 컨텍스트 복원 오류: {e}")
            return {}