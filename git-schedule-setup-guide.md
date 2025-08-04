# Windows Task Scheduler Setup Guide for Auto Git Push

## Method 1: Using Task Scheduler GUI

1. **Open Task Scheduler**:
   - Press `Win + R`, type `taskschd.msc`, press Enter
   - Or search "Task Scheduler" in Start menu

2. **Create Basic Task**:
   - Click "Create Basic Task..." in right panel
   - Name: "CodeStory Auto Git Push"
   - Description: "Daily automated git push for CodeStory project"

3. **Set Trigger**:
   - Choose "Daily"
   - Set start date and time (e.g., 10:00 AM every day)
   - Recur every 1 day

4. **Set Action**:
   - Choose "Start a program"
   - Program/script: `e:\CodeStory\run-auto-push.bat`
   - Start in: `e:\CodeStory`

5. **Finish and Test**:
   - Review settings and click "Finish"
   - Right-click the task and "Run" to test

## Method 2: Using PowerShell to Create Task

Run this PowerShell command as Administrator:

```powershell
# Create scheduled task via PowerShell
$Action = New-ScheduledTaskAction -Execute "e:\CodeStory\run-auto-push.bat" -WorkingDirectory "e:\CodeStory"
$Trigger = New-ScheduledTaskTrigger -Daily -At "10:00AM"
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive

Register-ScheduledTask -TaskName "CodeStory Auto Git Push" -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal -Description "Daily automated git push for CodeStory project"
```

## Method 3: Manual XML Import

Save this as `CodeStory-AutoPush-Task.xml` and import via Task Scheduler:

```xml
<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.4" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Date>2025-07-30T10:00:00</Date>
    <Author>User</Author>
    <Description>Daily automated git push for CodeStory project</Description>
  </RegistrationInfo>
  <Triggers>
    <CalendarTrigger>
      <StartBoundary>2025-07-30T10:00:00</StartBoundary>
      <Enabled>true</Enabled>
      <ScheduleByDay>
        <DaysInterval>1</DaysInterval>
      </ScheduleByDay>
    </CalendarTrigger>
  </Triggers>
  <Actions>
    <Exec>
      <Command>e:\CodeStory\run-auto-push.bat</Command>
      <WorkingDirectory>e:\CodeStory</WorkingDirectory>
    </Exec>
  </Actions>
</Task>
```

## Configuration Options

### Customize Files Per Day
Edit the PowerShell script and change:
```powershell
[int]$FilesPerDay = 2  # Change to desired number
```

### Change Schedule
- Modify the trigger time in Task Scheduler
- For multiple times per day, create additional triggers

### Custom File Selection
The script automatically excludes:
- Log files (`logs/`, `*.log`)
- Cache files (`__pycache__/`, `*.pyc`, `*cache.json`)
- Temporary files (`*.tmp`)

To customize, edit the exclusion pattern in the script:
```powershell
if ($FilePath -notmatch "(logs/|__pycache__|\.pyc$|\.log$|cache\.json$|\.tmp$)") {
```

## Prerequisites

Before setting up the schedule, ensure:

1. **Git repository is initialized**:
   ```bash
   git init
   git remote add origin <your-repo-url>
   ```

2. **Git credentials are configured**:
   ```bash
   git config --global user.name "Your Name"
   git config --global user.email "your.email@example.com"
   ```

3. **Authentication is set up** (choose one):
   - SSH keys configured
   - Git credential manager
   - Personal access token

## Testing

Test the setup manually:
```powershell
# Run the PowerShell script directly
.\auto-git-push.ps1

# Or run the batch file
.\run-auto-push.bat
```

## Monitoring

Check the log file for execution history:
```
e:\CodeStory\logs\git-push-log.txt
```

The log will contain timestamps and details of each execution.
