# Auto Git Push Script - Pushes 2 files per day to repository
# Usage: Run this script daily via Task Scheduler

param(
    [string]$TargetRepo = "origin",
    [string]$TargetBranch = "main",
    [int]$FilesPerDay = 2
)

# Configuration
$ProjectPath = "e:\CodeStory"
$LogFile = "$ProjectPath\logs\git-push-log.txt"

# Ensure logs directory exists
$LogDir = Split-Path $LogFile -Parent
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force
}

# Function to log messages
function Write-Log {
    param([string]$Message)
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogEntry = "[$Timestamp] $Message"
    Write-Host $LogEntry
    Add-Content -Path $LogFile -Value $LogEntry
}

try {
    Set-Location $ProjectPath
    Write-Log "Starting automated git push process..."
    
    # Check if we're in a git repository
    if (-not (Test-Path ".git")) {
        Write-Log "ERROR: Not a git repository. Please run 'git init' first."
        exit 1
    }
    
    # Get list of modified/new files (excluding logs and cache)
    $GitStatus = git status --porcelain
    $ModifiedFiles = @()
    
    foreach ($Line in $GitStatus) {
        if ($Line -match "^\s*[AM\?]\s+(.+)$") {
            $FilePath = $Matches[1].Trim('"')
            # Exclude log files, cache files, automation files, and other temporary files
            if ($FilePath -notmatch "(logs/|__pycache__|\.pyc$|\.log$|cache\.json$|\.tmp$|auto-git-push\.ps1$|setup-git-schedule\.ps1$|run-auto-push\.bat$|git-schedule-setup-guide\.md$)") {
                $ModifiedFiles += $FilePath
            }
        }
    }
    
    if ($ModifiedFiles.Count -eq 0) {
        Write-Log "No files to commit and push."
        exit 0
    }
    
    # Limit to specified number of files per day
    $FilesToCommit = $ModifiedFiles | Select-Object -First $FilesPerDay
    
    Write-Log "Found $($ModifiedFiles.Count) modified files, committing $($FilesToCommit.Count) files today:"
    foreach ($File in $FilesToCommit) {
        Write-Log "  - $File"
    }
    
    # Add files to git
    foreach ($File in $FilesToCommit) {
        git add $File
        if ($LASTEXITCODE -ne 0) {
            Write-Log "ERROR: Failed to add file: $File"
            continue
        }
    }
    
    # Check if there are staged changes
    $StagedChanges = git diff --cached --name-only
    if (-not $StagedChanges) {
        Write-Log "No staged changes to commit."
        exit 0
    }
    
    # Create commit message
    $CommitMessage = "Daily auto-commit: $(Get-Date -Format 'yyyy-MM-dd') - $($FilesToCommit.Count) files"
    
    # Commit changes
    git commit -m $CommitMessage
    if ($LASTEXITCODE -ne 0) {
        Write-Log "ERROR: Failed to create commit"
        exit 1
    }
    
    Write-Log "Created commit: $CommitMessage"
    
    # Push to remote repository
    Write-Log "Pushing to $TargetRepo $TargetBranch..."
    git push $TargetRepo $TargetBranch
    if ($LASTEXITCODE -eq 0) {
        Write-Log "Successfully pushed to remote repository!"
    } else {
        Write-Log "ERROR: Failed to push to remote repository"
        exit 1
    }
    
} catch {
    Write-Log "ERROR: Script execution failed - $($_.Exception.Message)"
    exit 1
}
