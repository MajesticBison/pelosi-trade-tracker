# Windows Deployment Guide - Pelosi Trade Tracker

This guide will help you deploy the Pelosi Trade Tracker on your Windows computer.

## Prerequisites

### 1. Install Python 3.7+
- Download from: https://www.python.org/downloads/
- **Important**: Check "Add Python to PATH" during installation
- Verify installation: Open Command Prompt and run `python --version`

### 2. Install Git (Optional but Recommended)
- Download from: https://git-scm.com/download/win
- This allows you to clone the repository easily

## Deployment Options

### Option A: Copy Files Manually
1. Copy all project files to your Windows computer
2. Place them in a folder like `C:\PelosiTracker\`

### Option B: Use Git (Recommended)
```cmd
# Open Command Prompt or PowerShell
cd C:\
git clone <your-repository-url> PelosiTracker
cd PelosiTracker
```

## Setup Steps

### 1. Install Dependencies
```cmd
# Navigate to project directory
cd C:\PelosiTracker

# Install required packages
pip install -r requirements.txt
```

### 2. Configure Environment
```cmd
# Copy the example environment file
copy env.example .env

# Edit .env file with your Discord webhook
notepad .env
```

### 3. Test the Installation
```cmd
# Test with dry run
python pelosi_tracker.py --dry-run

# Test Discord connection
python pelosi_tracker.py --test-discord
```

## Windows Task Scheduler Setup

Since Windows doesn't have cron, we'll use Task Scheduler:

### Method 1: Using Task Scheduler GUI
1. Open **Task Scheduler** (search in Start menu)
2. Click **"Create Basic Task"**
3. **Name**: "Pelosi Trade Tracker"
4. **Trigger**: Daily at 9:00 AM
5. **Action**: Start a program
   - **Program**: `python`
   - **Arguments**: `pelosi_tracker.py`
   - **Start in**: `C:\PelosiTracker`

### Method 2: Using PowerShell Script
I'll create a PowerShell script to set this up automatically.

## Monitoring and Logs

### View Logs
```cmd
# View recent logs
type pelosi_tracker.log | more

# View last 20 lines
powershell "Get-Content pelosi_tracker.log -Tail 20"
```

### Check Status
```cmd
# Run the status check script
python check_status.py
```

## Troubleshooting

### Common Issues
1. **"python is not recognized"**
   - Solution: Reinstall Python with "Add to PATH" checked

2. **Permission errors**
   - Solution: Run Command Prompt as Administrator

3. **Module not found errors**
   - Solution: Run `pip install -r requirements.txt` again

4. **Discord webhook not working**
   - Solution: Check .env file and webhook URL

### Getting Help
- Check logs: `type pelosi_tracker.log`
- Test manually: `python pelosi_tracker.py --dry-run`
- Verify setup: `python check_status.py`

## Files to Copy

Make sure you have these files on your Windows computer:
- `pelosi_tracker.py` (main script)
- `scraper.py`
- `pdf_parser.py`
- `database.py`
- `discord_notifier.py`
- `requirements.txt`
- `env.example`
- `README.md`
- `check_status.py` (Windows version)
- `setup_windows_task.ps1` (PowerShell setup script)

## Next Steps

1. Copy files to Windows computer
2. Install Python and dependencies
3. Configure .env file
4. Test the installation
5. Set up Task Scheduler
6. Monitor the first few runs

The system will automatically check for new Pelosi filings daily at 9 AM and send Discord notifications for any new trades found.
