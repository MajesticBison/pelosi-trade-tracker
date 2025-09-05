# PowerShell script to set up Windows Task Scheduler for Pelosi Trade Tracker
# Run this script as Administrator

param(
    [string]$TaskName = "Pelosi Trade Tracker",
    [string]$ProjectPath = (Get-Location).Path,
    [string]$PythonPath = "python",
    [string]$Time = "09:00"
)

Write-Host "🔧 Setting up Windows Task Scheduler for Pelosi Trade Tracker" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Green

# Check if running as Administrator
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "❌ This script must be run as Administrator!" -ForegroundColor Red
    Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    exit 1
}

# Verify project path
if (-not (Test-Path "$ProjectPath\pelosi_tracker.py")) {
    Write-Host "❌ pelosi_tracker.py not found in: $ProjectPath" -ForegroundColor Red
    Write-Host "Please run this script from the project directory" -ForegroundColor Yellow
    exit 1
}

# Check if Python is available
try {
    $pythonVersion = & $PythonPath --version 2>&1
    Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found. Please install Python and add it to PATH" -ForegroundColor Red
    exit 1
}

# Remove existing task if it exists
Write-Host "🗑️  Removing existing task (if any)..." -ForegroundColor Yellow
try {
    schtasks /delete /tn "$TaskName" /f 2>$null
    Write-Host "✅ Existing task removed" -ForegroundColor Green
} catch {
    Write-Host "ℹ️  No existing task to remove" -ForegroundColor Blue
}

# Create new task
Write-Host "📅 Creating new scheduled task..." -ForegroundColor Yellow

$action = New-ScheduledTaskAction -Execute $PythonPath -Argument "pelosi_tracker.py" -WorkingDirectory $ProjectPath
$trigger = New-ScheduledTaskTrigger -Daily -At $Time
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest

try {
    Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description "Automatically checks for new Nancy Pelosi trade filings and sends Discord notifications"
    Write-Host "✅ Task created successfully!" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to create task: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Verify task was created
Write-Host "🔍 Verifying task creation..." -ForegroundColor Yellow
try {
    $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction Stop
    Write-Host "✅ Task verified: $($task.TaskName)" -ForegroundColor Green
    Write-Host "📅 Next run time: $($task.NextRunTime)" -ForegroundColor Cyan
} catch {
    Write-Host "❌ Task verification failed" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "🎉 Setup Complete!" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Green
Write-Host "📋 Task Details:" -ForegroundColor Cyan
Write-Host "   Name: $TaskName" -ForegroundColor White
Write-Host "   Schedule: Daily at $Time" -ForegroundColor White
Write-Host "   Command: $PythonPath pelosi_tracker.py" -ForegroundColor White
Write-Host "   Working Directory: $ProjectPath" -ForegroundColor White
Write-Host ""
Write-Host "🧪 Test Commands:" -ForegroundColor Cyan
Write-Host "   python pelosi_tracker.py --dry-run" -ForegroundColor White
Write-Host "   python pelosi_tracker.py --test-discord" -ForegroundColor White
Write-Host ""
Write-Host "📊 Monitoring:" -ForegroundColor Cyan
Write-Host "   python check_status.py" -ForegroundColor White
Write-Host "   Get-Content pelosi_tracker.log -Tail 20" -ForegroundColor White
Write-Host ""
Write-Host "🗑️  To remove task: schtasks /delete /tn `"$TaskName`" /f" -ForegroundColor Yellow
