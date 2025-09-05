#!/bin/bash

# Pelosi Trade Tracker - Status Check Script
echo "🔍 Pelosi Trade Tracker - Status Check"
echo "======================================"
echo ""

# Check if cron job is set up
echo "📅 Cron Job Status:"
if crontab -l | grep -q "pelosi_tracker.py"; then
    echo "✅ Cron job is active"
    crontab -l | grep "pelosi_tracker.py"
else
    echo "❌ No cron job found"
fi
echo ""

# Check if log file exists and show recent activity
echo "📝 Recent Activity:"
if [ -f "pelosi_tracker.log" ]; then
    echo "✅ Log file exists"
    echo "📊 Last 5 log entries:"
    tail -5 pelosi_tracker.log
    echo ""
    echo "📈 Total log size: $(wc -l < pelosi_tracker.log) lines"
else
    echo "ℹ️  No log file yet (cron job hasn't run or no activity)"
fi
echo ""

# Check database status
echo "🗄️  Database Status:"
if [ -f "pelosi_trades.db" ]; then
    echo "✅ Database exists"
    # Count processed filings
    FILING_COUNT=$(sqlite3 pelosi_trades.db "SELECT COUNT(*) FROM filings;" 2>/dev/null || echo "0")
    TRADE_COUNT=$(sqlite3 pelosi_trades.db "SELECT COUNT(*) FROM trades;" 2>/dev/null || echo "0")
    echo "📊 Processed filings: $FILING_COUNT"
    echo "📊 Total trades found: $TRADE_COUNT"
else
    echo "ℹ️  No database yet (no filings processed)"
fi
echo ""

# Check environment setup
echo "🔧 Environment Check:"
if [ -f ".env" ]; then
    echo "✅ .env file exists"
    if grep -q "DISCORD_WEBHOOK_URL" .env; then
        echo "✅ Discord webhook configured"
    else
        echo "❌ Discord webhook not found in .env"
    fi
else
    echo "❌ .env file missing"
fi
echo ""

# Show next scheduled run
echo "⏰ Next Scheduled Run:"
echo "Daily at 9:00 AM"
echo ""

echo "🧪 To test manually: python3 pelosi_tracker.py --dry-run"
echo "📊 To view live logs: tail -f pelosi_tracker.log"
echo "🗑️  To remove cron job: crontab -r"
