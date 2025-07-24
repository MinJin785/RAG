# AI민진 Git 자동화 스크립트
# 모든 Git 작업을 비인터랙티브로 수행

param(
    [string]$Action = "sync",
    [string]$Message = "",
    [string]$Branch = "main",
    [switch]$Force,
    [switch]$Verbose
)

# 색상 출력 함수
function Write-ColorOutput {
    param([string]$Message, [string]$Color = "White")
    Write-Host $Message -ForegroundColor $Color
}

# Git 환경 설정
$env:GIT_PAGER = "cat"
$env:PAGER = "cat"
$env:GIT_TERMINAL_PROMPT = "0"
$env:GCM_INTERACTIVE = "never"

Write-ColorOutput "🚀 AI민진 Git 자동화 시작!" "Green"

# 현재 위치 확인
if (-not (Test-Path ".git")) {
    Write-ColorOutput "❌ Git 저장소가 아닙니다!" "Red"
    exit 1
}

# Git 설정 최적화
Write-ColorOutput "⚙️ Git 비인터랙티브 설정 중..." "Yellow"
git config core.pager cat
git config color.ui false
git config push.default simple
git config pull.rebase false

# 함수: Git 상태 확인
function Get-GitStatus {
    $status = git status --porcelain 2>$null
    $modified = @()
    $untracked = @()
    $staged = @()
    
    foreach ($line in $status) {
        if ($line) {
            $statusCode = $line.Substring(0, 2)
            $filename = $line.Substring(3)
            
            switch ($statusCode) {
                "??" { $untracked += $filename }
                { $_.Substring(0, 1) -ne " " } { $staged += $filename }
                { $_.Substring(1, 1) -ne " " } { $modified += $filename }
            }
        }
    }
    
    return @{
        Modified = $modified
        Untracked = $untracked
        Staged = $staged
        Total = $modified.Count + $untracked.Count + $staged.Count
        Clean = ($modified.Count + $untracked.Count + $staged.Count) -eq 0
    }
}

# 함수: 자동 커밋 메시지 생성
function New-AutoCommitMessage {
    param($Status)
    
    if ($Status.Clean) {
        return "Update: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    }
    
    $parts = @()
    
    if ($Status.Modified.Count -gt 0) {
        $fileList = $Status.Modified[0..2] -join ", "
        if ($Status.Modified.Count -gt 3) {
            $fileList += " (+$($Status.Modified.Count - 3) more)"
        }
        $parts += "Modified: $fileList"
    }
    
    if ($Status.Untracked.Count -gt 0) {
        $fileList = $Status.Untracked[0..2] -join ", "
        if ($Status.Untracked.Count -gt 3) {
            $fileList += " (+$($Status.Untracked.Count - 3) more)"
        }
        $parts += "Added: $fileList"
    }
    
    if ($parts.Count -eq 0) {
        return "Update: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    }
    
    return $parts -join " | "
}

# 메인 실행 로직
switch ($Action.ToLower()) {
    "status" {
        Write-ColorOutput "📊 Git 상태 확인 중..." "Cyan"
        $status = Get-GitStatus
        
        Write-ColorOutput "📁 저장소 상태:" "White"
        Write-ColorOutput "  • 수정된 파일: $($status.Modified.Count)개" "Yellow"
        Write-ColorOutput "  • 새 파일: $($status.Untracked.Count)개" "Green"
        Write-ColorOutput "  • 스테이징된 파일: $($status.Staged.Count)개" "Blue"
        
        if ($status.Clean) {
            Write-ColorOutput "✅ 깨끗한 상태입니다!" "Green"
        } else {
            Write-ColorOutput "📝 $($status.Total)개의 변경사항이 있습니다." "Yellow"
        }
    }
    
    "sync" {
        Write-ColorOutput "🔄 자동 동기화 시작..." "Cyan"
        
        # 1. 상태 확인
        $status = Get-GitStatus
        
        if ($status.Clean) {
            Write-ColorOutput "✅ 변경사항이 없습니다." "Green"
            exit 0
        }
        
        Write-ColorOutput "📝 $($status.Total)개의 변경사항 발견" "Yellow"
        
        # 2. 모든 파일 추가
        Write-ColorOutput "📁 파일 추가 중..." "Yellow"
        git add . 2>$null
        if ($LASTEXITCODE -ne 0) {
            Write-ColorOutput "❌ 파일 추가 실패!" "Red"
            exit 1
        }
        
        # 3. 커밋
        if (-not $Message) {
            $Message = New-AutoCommitMessage -Status $status
        }
        
        Write-ColorOutput "💬 커밋 중: $Message" "Yellow"
        git commit -m $Message 2>$null
        if ($LASTEXITCODE -ne 0) {
            Write-ColorOutput "❌ 커밋 실패!" "Red"
            exit 1
        }
        
        # 4. 푸시
        Write-ColorOutput "🚀 GitHub에 푸시 중..." "Yellow"
        
        # 업스트림 설정 확인
        $upstream = git rev-parse --abbrev-ref "$Branch@{upstream}" 2>$null
        if ($LASTEXITCODE -ne 0) {
            Write-ColorOutput "🔗 업스트림 설정 중..." "Yellow"
            git push --set-upstream origin $Branch 2>$null
        } else {
            git push 2>$null
        }
        
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "✅ 동기화 완료!" "Green"
        } else {
            Write-ColorOutput "❌ 푸시 실패!" "Red"
            exit 1
        }
    }
    
    "pull" {
        Write-ColorOutput "📥 최신 변경사항 가져오기..." "Cyan"
        git pull --no-edit --no-rebase 2>$null
        
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "✅ 풀 완료!" "Green"
        } else {
            Write-ColorOutput "❌ 풀 실패!" "Red"
            exit 1
        }
    }
    
    "branch" {
        Write-ColorOutput "🌿 브랜치 정보:" "Cyan"
        
        # 현재 브랜치
        $currentBranch = git branch --show-current 2>$null
        Write-ColorOutput "  현재 브랜치: $currentBranch" "Green"
        
        # 모든 브랜치
        Write-ColorOutput "  모든 브랜치:" "White"
        git branch --no-pager 2>$null | ForEach-Object {
            Write-ColorOutput "    $_" "Gray"
        }
    }
    
    "log" {
        Write-ColorOutput "📜 최근 커밋 로그:" "Cyan"
        git log --oneline --max-count=10 --no-pager 2>$null | ForEach-Object {
            Write-ColorOutput "  $_" "Gray"
        }
    }
    
    "clean" {
        Write-ColorOutput "🧹 저장소 정리 중..." "Cyan"
        
        if ($Force) {
            git clean -fd 2>$null
            git reset --hard HEAD 2>$null
            Write-ColorOutput "✅ 강제 정리 완료!" "Green"
        } else {
            Write-ColorOutput "⚠️ 강제 정리를 원하면 -Force 옵션을 사용하세요." "Yellow"
            git status --porcelain 2>$null | ForEach-Object {
                Write-ColorOutput "  정리될 파일: $_" "Red"
            }
        }
    }
    
    "help" {
        Write-ColorOutput "🆘 Git 자동화 스크립트 도움말:" "Cyan"
        Write-ColorOutput ""
        Write-ColorOutput "사용법: .\git_automation.ps1 [Action] [Options]" "White"
        Write-ColorOutput ""
        Write-ColorOutput "Actions:" "Yellow"
        Write-ColorOutput "  status  - Git 상태 확인" "White"
        Write-ColorOutput "  sync    - 자동 동기화 (add + commit + push)" "White"
        Write-ColorOutput "  pull    - 최신 변경사항 가져오기" "White"
        Write-ColorOutput "  branch  - 브랜치 정보 표시" "White"
        Write-ColorOutput "  log     - 커밋 로그 표시" "White"
        Write-ColorOutput "  clean   - 저장소 정리" "White"
        Write-ColorOutput "  help    - 이 도움말 표시" "White"
        Write-ColorOutput ""
        Write-ColorOutput "Options:" "Yellow"
        Write-ColorOutput "  -Message 'text' - 커밋 메시지 지정" "White"
        Write-ColorOutput "  -Branch 'name'  - 브랜치 지정 (기본: main)" "White"
        Write-ColorOutput "  -Force          - 강제 실행" "White"
        Write-ColorOutput "  -Verbose        - 상세 출력" "White"
        Write-ColorOutput ""
        Write-ColorOutput "예제:" "Yellow"
        Write-ColorOutput "  .\git_automation.ps1 sync -Message 'AI민진 업데이트'" "Green"
        Write-ColorOutput "  .\git_automation.ps1 status" "Green"
        Write-ColorOutput "  .\git_automation.ps1 pull" "Green"
    }
    
    default {
        Write-ColorOutput "❌ 알 수 없는 작업: $Action" "Red"
        Write-ColorOutput "💡 'help' 액션을 사용해 도움말을 확인하세요." "Yellow"
        exit 1
    }
}

Write-ColorOutput "🎉 작업 완료!" "Green" 