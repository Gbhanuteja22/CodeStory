# Quick Setup Script for Git Auto Push Scheduling
# Run this as Administrator to set up the scheduled task

param(
    [string]$RepoUrl = "",
    [string]$ScheduleTime = "10:00",
    [int]$FilesPerDay = 2
)

Write-Host "🚀 CodeStory Auto Git Push Setup" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green

# Check if running as administrator
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "❌ This script must be run as Administrator" -ForegroundColor Red
    Write-Host "Right-click PowerShell and 'Run as Administrator'" -ForegroundColor Yellow
    exit 1
}

$ProjectPath = "e:\CodeStory"
Set-Location $ProjectPath

# Initialize git repository if needed
if (-not (Test-Path ".git")) {
    Write-Host "🔧 Initializing git repository..." -ForegroundColor Yellow
    git init
    
    if ($RepoUrl) {
        Write-Host "🔗 Adding remote origin: $RepoUrl" -ForegroundColor Yellow
        git remote add origin $RepoUrl
    } else {
        Write-Host "⚠️  No repository URL provided. You'll need to add remote manually:" -ForegroundColor Yellow
        Write-Host "   git remote add origin <your-repo-url>" -ForegroundColor Cyan
    }
}

# Check git configuration
$GitUser = git config user.name
$GitEmail = git config user.email

if (-not $GitUser -or -not $GitEmail) {
    Write-Host "⚠️  Git user configuration missing. Please run:" -ForegroundColor Yellow
    Write-Host "   git config --global user.name 'Your Name'" -ForegroundColor Cyan
    Write-Host "   git config --global user.email 'your.email@example.com'" -ForegroundColor Cyan
}

# Create scheduled task
Write-Host "📅 Creating scheduled task..." -ForegroundColor Yellow

try {
    $Action = New-ScheduledTaskAction -Execute "$ProjectPath\run-auto-push.bat" -WorkingDirectory $ProjectPath
    $Trigger = New-ScheduledTaskTrigger -Daily -At $ScheduleTime
    $Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
    $Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive

    # Remove existing task if it exists
    $ExistingTask = Get-ScheduledTask -TaskName "CodeStory Auto Git Push" -ErrorAction SilentlyContinue
    if ($ExistingTask) {
        Unregister-ScheduledTask -TaskName "CodeStory Auto Git Push" -Confirm:$false
        Write-Host "🗑️  Removed existing task" -ForegroundColor Yellow
    }

    Register-ScheduledTask -TaskName "CodeStory Auto Git Push" -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal -Description "Daily automated git push for CodeStory project ($FilesPerDay files/day)"
    
    Write-Host "✅ Scheduled task created successfully!" -ForegroundColor Green
    Write-Host "   Task Name: CodeStory Auto Git Push" -ForegroundColor Cyan
    Write-Host "   Schedule: Daily at $ScheduleTime" -ForegroundColor Cyan
    Write-Host "   Files per day: $FilesPerDay" -ForegroundColor Cyan
    
} catch {
    Write-Host "❌ Failed to create scheduled task: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Test the setup
Write-Host "🧪 Testing the setup..." -ForegroundColor Yellow
& "$ProjectPath\run-auto-push.bat"

Write-Host "`n🎉 Setup complete!" -ForegroundColor Green
Write-Host "📋 Next steps:" -ForegroundColor Yellow
Write-Host "   1. Ensure your git credentials are configured" -ForegroundColor Cyan
Write-Host "   2. Test push manually: git push origin main" -ForegroundColor Cyan
Write-Host "   3. Check logs at: $ProjectPath\logs\git-push-log.txt" -ForegroundColor Cyan
Write-Host "   4. Monitor scheduled task in Task Scheduler" -ForegroundColor Cyan
