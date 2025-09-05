#!/usr/bin/env python3
"""
Windows-compatible status check script for Pelosi Trade Tracker
"""

import os
import sqlite3
import subprocess
import sys
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible."""
    print("🐍 Python Version Check:")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 7:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} (Compatible)")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} (Requires 3.7+)")
        return False

def check_dependencies():
    """Check if required packages are installed."""
    print("\n📦 Dependencies Check:")
    required_packages = [
        'requests', 'beautifulsoup4', 'pdfplumber', 'python-dotenv'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        print("Run: pip install -r requirements.txt")
        return False
    return True

def check_environment():
    """Check environment configuration."""
    print("\n🔧 Environment Check:")
    
    # Check .env file
    if os.path.exists('.env'):
        print("✅ .env file exists")
        with open('.env', 'r') as f:
            content = f.read()
            if 'DISCORD_WEBHOOK_URL' in content:
                print("✅ Discord webhook configured")
                return True
            else:
                print("❌ Discord webhook not found in .env")
                return False
    else:
        print("❌ .env file missing")
        print("Run: copy env.example .env")
        return False

def check_database():
    """Check database status."""
    print("\n🗄️  Database Status:")
    
    if os.path.exists('pelosi_trades.db'):
        print("✅ Database exists")
        try:
            conn = sqlite3.connect('pelosi_trades.db')
            cursor = conn.cursor()
            
            # Count filings
            cursor.execute("SELECT COUNT(*) FROM filings")
            filing_count = cursor.fetchone()[0]
            
            # Count trades
            cursor.execute("SELECT COUNT(*) FROM trades")
            trade_count = cursor.fetchone()[0]
            
            print(f"📊 Processed filings: {filing_count}")
            print(f"📊 Total trades found: {trade_count}")
            
            conn.close()
            return True
        except Exception as e:
            print(f"❌ Database error: {e}")
            return False
    else:
        print("ℹ️  No database yet (no filings processed)")
        return True

def check_logs():
    """Check log file status."""
    print("\n📝 Log Status:")
    
    if os.path.exists('pelosi_tracker.log'):
        print("✅ Log file exists")
        try:
            with open('pelosi_tracker.log', 'r', encoding='utf-8') as f:
                lines = f.readlines()
                print(f"📈 Total log lines: {len(lines)}")
                
                if lines:
                    print("📊 Last 3 log entries:")
                    for line in lines[-3:]:
                        print(f"   {line.strip()}")
        except Exception as e:
            print(f"❌ Log file error: {e}")
    else:
        print("ℹ️  No log file yet (script hasn't run)")

def check_task_scheduler():
    """Check if Windows Task Scheduler is set up."""
    print("\n⏰ Task Scheduler Check:")
    
    try:
        # Try to query task scheduler
        result = subprocess.run(
            ['schtasks', '/query', '/tn', 'Pelosi Trade Tracker'],
            capture_output=True,
            text=True,
            shell=True
        )
        
        if result.returncode == 0:
            print("✅ Task Scheduler job found")
            print("📅 Scheduled: Daily at 9:00 AM")
        else:
            print("ℹ️  No Task Scheduler job found")
            print("💡 Use setup_windows_task.ps1 to create one")
    except Exception as e:
        print(f"ℹ️  Could not check Task Scheduler: {e}")

def main():
    """Main status check function."""
    print("🔍 Pelosi Trade Tracker - Windows Status Check")
    print("=" * 50)
    
    # Run all checks
    python_ok = check_python_version()
    deps_ok = check_dependencies()
    env_ok = check_environment()
    db_ok = check_database()
    check_logs()
    check_task_scheduler()
    
    print("\n" + "=" * 50)
    print("📋 Summary:")
    
    if python_ok and deps_ok and env_ok and db_ok:
        print("✅ System is ready to run!")
        print("\n🧪 Test commands:")
        print("   python pelosi_tracker.py --dry-run")
        print("   python pelosi_tracker.py --test-discord")
    else:
        print("⚠️  Some issues found. Please fix them before running.")
        print("\n🔧 Setup commands:")
        print("   pip install -r requirements.txt")
        print("   copy env.example .env")
        print("   # Edit .env with your Discord webhook URL")

if __name__ == "__main__":
    main()
