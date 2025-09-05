#!/bin/bash

# Pelosi Trade Tracker - Cron Setup Script
# This script helps you set up automated execution

echo "🔧 Pelosi Trade Tracker - Cron Setup"
echo "====================================="
echo ""

# Get current directory
CURRENT_DIR=$(pwd)
PYTHON_PATH=$(which python3)

echo "📁 Project Directory: $CURRENT_DIR"
echo "🐍 Python Path: $PYTHON_PATH"
echo ""

echo "📋 Cron Job Options:"
echo ""
echo "1. Daily at 9:00 AM (recommended for most users)"
echo "   0 9 * * * cd $CURRENT_DIR && $PYTHON_PATH pelosi_tracker.py >> pelosi_tracker.log 2>&1"
echo ""
echo "2. Every 12 hours (9 AM and 9 PM)"
echo "   0 */12 * * * cd $CURRENT_DIR && $PYTHON_PATH pelosi_tracker.py >> pelosi_tracker.log 2>&1"
echo ""
echo "3. Every 6 hours (more frequent monitoring)"
echo "   0 */6 * * * cd $CURRENT_DIR && $PYTHON_PATH pelosi_tracker.py >> pelosi_tracker.log 2>&1"
echo ""
echo "4. Weekdays only at 9 AM (Monday-Friday)"
echo "   0 9 * * 1-5 cd $CURRENT_DIR && $PYTHON_PATH pelosi_tracker.py >> pelosi_tracker.log 2>&1"
echo ""

echo "🚀 To set up cron job:"
echo "1. Run: crontab -e"
echo "2. Add one of the lines above"
echo "3. Save and exit"
echo ""
echo "📊 To view current cron jobs: crontab -l"
echo "📝 Logs will be saved to: pelosi_tracker.log"
echo ""

# Test the command
echo "🧪 Testing the command (dry run):"
echo "cd $CURRENT_DIR && $PYTHON_PATH pelosi_tracker.py --dry-run"
echo ""
