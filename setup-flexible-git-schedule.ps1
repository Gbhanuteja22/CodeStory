# Flexible Git Auto Push Setup Script
# Provides multiple scheduling options including startup and wake-from-sleep

param(
    [string]$RepoUrl = "",
    [ValidateSet("Daily", "Startup", "Both", "Manual")]
    [string]$ScheduleType = "Both",
    [string]$DailyTime = "10:00",
    [int]$FilesPerDay = 2
)

Write-Host "🚀 CodeStory Flexible Auto Git Push Setup" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green

# Check if running as administrator
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "❌ This script must be run as Administrator" -ForegroundColor Red
    Write-Host "Right-click PowerShell and 'Run as Administrator'" -ForegroundColor Yellow
    exit 1
}

$ProjectPath = "e:\CodeStory"
$TaskName = "CodeStory-AutoGitPush"
$StartupTaskName = "CodeStory-AutoGitPush-Startup"
$BatFilePath = Join-Path $ProjectPath "run-auto-push.bat"

Set-Location $ProjectPath

Write-Host "📋 Schedule Options:" -ForegroundColor Cyan
Write-Host "  1. Daily: Runs at $DailyTime every day (only if computer is on)" -ForegroundColor White
Write-Host "  2. Startup: Runs every time you start your computer" -ForegroundColor White
Write-Host "  3. Both: Runs daily AND on startup (recommended)" -ForegroundColor White
Write-Host "  4. Manual: Only when you double-click the .bat file" -ForegroundColor White
Write-Host ""
Write-Host "Selected: $ScheduleType" -ForegroundColor Green
Write-Host ""

# Remove existing tasks
Write-Host "🧹 Removing any existing tasks..." -ForegroundColor Yellow
try {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
    Unregister-ScheduledTask -TaskName $StartupTaskName -Confirm:$false -ErrorAction SilentlyContinue
    Write-Host "✅ Cleaned up existing tasks" -ForegroundColor Green
} catch {
    Write-Host "ℹ️  No existing tasks to remove" -ForegroundColor Gray
}

# Create tasks based on selection
if ($ScheduleType -eq "Daily" -or $ScheduleType -eq "Both") {
    Write-Host "📅 Creating daily scheduled task..." -ForegroundColor Yellow
    
    $DailyAction = New-ScheduledTaskAction -Execute $BatFilePath -WorkingDirectory $ProjectPath
    $DailyTrigger = New-ScheduledTaskTrigger -Daily -At $DailyTime
    $DailySettings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -WakeToRun
    $DailyPrincipal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive
    
    $DailyTask = New-ScheduledTask -Action $DailyAction -Trigger $DailyTrigger -Settings $DailySettings -Principal $DailyPrincipal -Description "CodeStory Auto Git Push - Daily at $DailyTime"
    
    Register-ScheduledTask -TaskName $TaskName -InputObject $DailyTask
    Write-Host "✅ Daily task created successfully" -ForegroundColor Green
}

if ($ScheduleType -eq "Startup" -or $ScheduleType -eq "Both") {
    Write-Host "🔄 Creating startup task..." -ForegroundColor Yellow
    
    $StartupAction = New-ScheduledTaskAction -Execute $BatFilePath -WorkingDirectory $ProjectPath
    $StartupTrigger = New-ScheduledTaskTrigger -AtStartup
    $StartupSettings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -Delay (New-TimeSpan -Minutes 2)
    $StartupPrincipal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive
    
    $StartupTask = New-ScheduledTask -Action $StartupAction -Trigger $StartupTrigger -Settings $StartupSettings -Principal $StartupPrincipal -Description "CodeStory Auto Git Push - On System Startup"
    
    Register-ScheduledTask -TaskName $StartupTaskName -InputObject $StartupTask
    Write-Host "✅ Startup task created successfully" -ForegroundColor Green
}

if ($ScheduleType -eq "Manual") {
    Write-Host "📝 Manual mode selected - no scheduled tasks created" -ForegroundColor Yellow
    Write-Host "Double-click 'run-auto-push.bat' whenever you want to push files" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "🎯 Setup Complete!" -ForegroundColor Green
Write-Host "=================" -ForegroundColor Green

switch ($ScheduleType) {
    "Daily" {
        Write-Host "📅 Your files will be automatically pushed daily at $DailyTime" -ForegroundColor White
        Write-Host "⚠️  Note: Computer must be ON at $DailyTime for this to work" -ForegroundColor Yellow
    }
    "Startup" {
        Write-Host "🔄 Your files will be automatically pushed every time you start your computer" -ForegroundColor White
        Write-Host "✅ Works even if you don't turn on your computer daily" -ForegroundColor Green
    }
    "Both" {
        Write-Host "📅 Daily pushes at $DailyTime (if computer is on)" -ForegroundColor White
        Write-Host "🔄 Startup pushes every time you boot your computer" -ForegroundColor White
        Write-Host "✅ Maximum coverage - recommended option!" -ForegroundColor Green
    }
    "Manual" {
        Write-Host "👆 Run manually by double-clicking 'run-auto-push.bat'" -ForegroundColor White
    }
}

Write-Host ""
Write-Host "🔧 Additional Options:" -ForegroundColor Cyan
Write-Host "  • View tasks: taskschd.msc" -ForegroundColor White
Write-Host "  • Test now: Double-click run-auto-push.bat" -ForegroundColor White
Write-Host "  • Check logs: Check logs/ folder for execution history" -ForegroundColor White

Write-Host ""
Write-Host "💡 Recommendations based on your usage:" -ForegroundColor Yellow
Write-Host "  • If you use your computer daily: Choose 'Both'" -ForegroundColor White
Write-Host "  • If you use it sporadically: Choose 'Startup'" -ForegroundColor White
Write-Host "  • If you want full control: Choose 'Manual'" -ForegroundColor White
