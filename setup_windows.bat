@echo off
REM Windows setup script for Pelosi Trade Tracker
echo 🔧 Pelosi Trade Tracker - Windows Setup
echo ======================================
echo.

REM Check if Python is installed
echo 🐍 Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python not found! Please install Python 3.7+ from https://python.org
    echo    Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)
echo ✅ Python is installed
echo.

REM Install dependencies
echo 📦 Installing dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ❌ Failed to install dependencies
    pause
    exit /b 1
)
echo ✅ Dependencies installed
echo.

REM Setup environment file
echo 🔧 Setting up environment...
if not exist .env (
    copy env.example .env
    echo ✅ Created .env file
    echo ⚠️  Please edit .env file with your Discord webhook URL
    echo    Open .env in notepad and add your webhook URL
    pause
) else (
    echo ✅ .env file already exists
)
echo.

REM Test the installation
echo 🧪 Testing installation...
python pelosi_tracker.py --dry-run
if %errorlevel% neq 0 (
    echo ❌ Test failed! Please check the error messages above
    pause
    exit /b 1
)
echo ✅ Installation test passed
echo.

echo 🎉 Setup Complete!
echo =================
echo.
echo 📋 Next Steps:
echo 1. Edit .env file with your Discord webhook URL
echo 2. Test Discord connection: python pelosi_tracker.py --test-discord
echo 3. Set up Task Scheduler: Run setup_windows_task.ps1 as Administrator
echo.
echo 🧪 Test Commands:
echo    python pelosi_tracker.py --dry-run
echo    python pelosi_tracker.py --test-discord
echo    python check_status.py
echo.
pause
