import subprocess
import os
import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

class GitAutomation:
    """Git 작업 완전 자동화 시스템"""
    
    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path)
        self.logger = logging.getLogger(__name__)
        
        # Git 설정 최적화
        self._setup_git_config()
    
    def _setup_git_config(self):
        """Git 비인터랙티브 설정"""
        configs = [
            ("core.pager", "cat"),  # 페이저 비활성화 (q 키 방지)
            ("log.decorate", "short"),
            ("color.ui", "false"),  # 컬러 출력 비활성화
            ("core.autocrlf", "true"),  # Windows 호환성
            ("push.default", "simple"),
            ("pull.rebase", "false")
        ]
        
        for key, value in configs:
            try:
                subprocess.run(
                    ["git", "config", key, value],
                    cwd=self.repo_path,
                    capture_output=True,
                    check=True
                )
            except subprocess.CalledProcessError:
                self.logger.warning(f"Git 설정 실패: {key}={value}")

    async def run_git_command(self, command: List[str], timeout: int = 30) -> Dict[str, any]:
        """비인터랙티브 Git 명령 실행"""
        try:
            # 환경 변수 설정 (인터랙티브 방지)
            env = os.environ.copy()
            env.update({
                "GIT_PAGER": "cat",           # 페이저 비활성화
                "PAGER": "cat",               # 시스템 페이저 비활성화  
                "GIT_TERMINAL_PROMPT": "0",   # 터미널 프롬프트 비활성화
                "GIT_ASKPASS": "echo",        # 패스워드 프롬프트 비활성화
                "SSH_ASKPASS": "echo",        # SSH 패스워드 프롬프트 비활성화
                "GCM_INTERACTIVE": "never"    # Git Credential Manager 비활성화
            })
            
            # 명령 실행
            result = subprocess.run(
                ["git"] + command,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
                "returncode": result.returncode,
                "command": " ".join(["git"] + command)
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"명령 시간 초과 ({timeout}초)",
                "command": " ".join(["git"] + command)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "command": " ".join(["git"] + command)
            }

    async def get_status(self) -> Dict[str, any]:
        """Git 상태 확인 (비인터랙티브)"""
        result = await self.run_git_command(["status", "--porcelain"])
        
        if not result["success"]:
            return result
        
        # 상태 파싱
        modified_files = []
        untracked_files = []
        staged_files = []
        
        for line in result["stdout"].split("\n"):
            if not line.strip():
                continue
                
            status = line[:2]
            filename = line[3:]
            
            if status == "??":
                untracked_files.append(filename)
            elif status[0] != " ":
                staged_files.append(filename)
            elif status[1] != " ":
                modified_files.append(filename)
        
        return {
            "success": True,
            "modified_files": modified_files,
            "untracked_files": untracked_files,
            "staged_files": staged_files,
            "total_changes": len(modified_files) + len(untracked_files) + len(staged_files),
            "clean": len(modified_files) + len(untracked_files) + len(staged_files) == 0
        }

    async def auto_add_all(self) -> Dict[str, any]:
        """모든 변경사항 자동 추가"""
        return await self.run_git_command(["add", "."])

    async def auto_commit(self, message: str = None) -> Dict[str, any]:
        """자동 커밋"""
        if not message:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            message = f"Auto commit: {timestamp}"
        
        return await self.run_git_command(["commit", "-m", message])

    async def auto_push(self, branch: str = "main") -> Dict[str, any]:
        """자동 푸시"""
        # 먼저 업스트림 설정 확인
        upstream_result = await self.run_git_command(["rev-parse", "--abbrev-ref", f"{branch}@{{upstream}}"])
        
        if not upstream_result["success"]:
            # 업스트림 설정
            set_upstream = await self.run_git_command(["push", "--set-upstream", "origin", branch])
            if not set_upstream["success"]:
                return set_upstream
        
        # 푸시 실행
        return await self.run_git_command(["push"])

    async def auto_pull(self) -> Dict[str, any]:
        """자동 풀 (비인터랙티브)"""
        return await self.run_git_command(["pull", "--no-edit", "--no-rebase"])

    async def create_branch(self, branch_name: str) -> Dict[str, any]:
        """새 브랜치 생성 및 체크아웃"""
        return await self.run_git_command(["checkout", "-b", branch_name])

    async def switch_branch(self, branch_name: str) -> Dict[str, any]:
        """브랜치 전환"""
        return await self.run_git_command(["checkout", branch_name])

    async def get_log(self, limit: int = 10) -> Dict[str, any]:
        """Git 로그 조회 (비인터랙티브)"""
        result = await self.run_git_command([
            "log", 
            f"--max-count={limit}",
            "--oneline",
            "--no-pager"
        ])
        
        if result["success"]:
            commits = []
            for line in result["stdout"].split("\n"):
                if line.strip():
                    parts = line.split(" ", 1)
                    if len(parts) == 2:
                        commits.append({
                            "hash": parts[0],
                            "message": parts[1]
                        })
            result["commits"] = commits
        
        return result

    async def auto_sync(self, commit_message: str = None) -> Dict[str, any]:
        """완전 자동 동기화: add → commit → push"""
        steps = []
        
        # 1. 상태 확인
        status = await self.get_status()
        steps.append(("status", status))
        
        if not status["success"] or status["clean"]:
            return {
                "success": True,
                "message": "변경사항이 없습니다.",
                "steps": steps
            }
        
        # 2. 모든 파일 추가
        add_result = await self.auto_add_all()
        steps.append(("add", add_result))
        
        if not add_result["success"]:
            return {
                "success": False,
                "error": "파일 추가 실패",
                "steps": steps
            }
        
        # 3. 커밋
        commit_result = await self.auto_commit(commit_message)
        steps.append(("commit", commit_result))
        
        if not commit_result["success"]:
            return {
                "success": False,
                "error": "커밋 실패",
                "steps": steps
            }
        
        # 4. 푸시
        push_result = await self.auto_push()
        steps.append(("push", push_result))
        
        return {
            "success": push_result["success"],
            "message": "자동 동기화 완료" if push_result["success"] else "푸시 실패",
            "steps": steps,
            "changes_count": status["total_changes"]
        }

    async def create_gitignore_if_missing(self) -> bool:
        """gitignore 파일이 없으면 생성"""
        gitignore_path = self.repo_path / ".gitignore"
        
        if not gitignore_path.exists():
            default_gitignore = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Environment
.env
.env.local
.env.production
.env.staging
*.env

# AI/ML
data/
*.bin
*.pkl
*.faiss
*.db
*.sqlite
*.sqlite3

# Logs
*.log
logs/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# AI민진 전용
AI_Minjin_To_Do.md
AI_Minjin_To_Do.lock
ai_minjin_context.json
"""
            
            with open(gitignore_path, 'w', encoding='utf-8') as f:
                f.write(default_gitignore)
            
            return True
        
        return False

    async def check_remote_connection(self) -> Dict[str, any]:
        """원격 저장소 연결 상태 확인"""
        return await self.run_git_command(["remote", "-v"])

    async def get_current_branch(self) -> Dict[str, any]:
        """현재 브랜치 확인"""
        result = await self.run_git_command(["branch", "--show-current"])
        if result["success"]:
            result["current_branch"] = result["stdout"].strip()
        return result

    async def create_commit_template(self) -> str:
        """커밋 메시지 템플릿 생성"""
        status = await self.get_status()
        
        if not status["success"]:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return f"Update: {timestamp}"
        
        parts = []
        
        if status["modified_files"]:
            parts.append(f"Modified: {', '.join(status['modified_files'][:3])}")
            if len(status["modified_files"]) > 3:
                parts[-1] += f" (+{len(status['modified_files'])-3} more)"
        
        if status["untracked_files"]:
            parts.append(f"Added: {', '.join(status['untracked_files'][:3])}")
            if len(status["untracked_files"]) > 3:
                parts[-1] += f" (+{len(status['untracked_files'])-3} more)"
        
        if not parts:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return f"Update: {timestamp}"
        
        return " | ".join(parts)

# Cursor IDE Git GUI 활용 가이드
class CursorGitGuide:
    """Cursor IDE의 내장 Git GUI 기능 활용 가이드"""
    
    @staticmethod
    def get_cursor_git_shortcuts() -> Dict[str, str]:
        """Cursor Git 단축키 모음"""
        return {
            "Ctrl+Shift+G": "Git 패널 열기",
            "Ctrl+Shift+P → git": "Git 명령 팔레트",
            "Ctrl+K Ctrl+C": "변경사항 커밋",
            "Ctrl+K Ctrl+P": "Git 푸시",
            "Ctrl+K Ctrl+F": "Git 페치",
            "Ctrl+K Ctrl+L": "Git 로그 보기",
            "Ctrl+K Ctrl+B": "브랜치 관리",
            "Ctrl+K Ctrl+S": "Git 상태 보기"
        }
    
    @staticmethod
    def get_cursor_git_features() -> List[str]:
        """Cursor IDE Git 기능 목록"""
        return [
            "🔍 사이드바 Git 패널 - 변경사항 실시간 확인",
            "📝 인라인 Git 정보 - 각 줄의 마지막 수정자/시간",
            "🌿 브랜치 관리 - 하단 상태바에서 브랜치 전환",
            "📊 Git 그래프 - 커밋 히스토리 시각화",
            "🔄 자동 동기화 - 설정에서 auto-fetch 활성화",
            "📋 스테이징 영역 - 파일별 개별 스테이징",
            "💬 커밋 메시지 - 템플릿 및 히스토리 지원",
            "🔀 머지 충돌 해결 - 시각적 머지 툴 제공"
        ] 