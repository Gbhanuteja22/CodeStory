@echo off
REM Auto Git Push - Daily execution wrapper
REM This batch file calls the PowerShell script for automated git pushes

cd /d "e:\CodeStory"

REM Run PowerShell script with execution policy bypass
powershell.exe -ExecutionPolicy Bypass -File "auto-git-push.ps1"

REM Optional: Add pause to see output when run manually
REM pause
