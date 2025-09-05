#!/usr/bin/env python3
"""
Test script to demonstrate how multiple politicians look in the same Discord channel.
"""

from discord_notifier import DiscordNotifier
from politicians_config import get_politician_config

def test_same_channel_notifications():
    """Test how notifications look from different politicians in the same channel."""
    
    # Get the webhook URL (same for all politicians now)
    pelosi_config = get_politician_config("pelosi")
    webhook_url = pelosi_config.discord_webhook
    
    # Create notifier
    notifier = DiscordNotifier(webhook_url, "#pelosi-trades")
    
    # Test trades from different politicians
    test_trades = [
        {
            'politician_name': 'pelosi',
            'politician_full_name': 'Nancy Pelosi',
            'asset_name': 'Apple Inc',
            'ticker': 'AAPL',
            'trade_type': 'stock trade',
            'action': 'BUY',
            'amount_range': '$1M-$5M',
            'transaction_date': '2025-01-15',
            'description': ''
        },
        {
            'politician_name': 'mccarthy',
            'politician_full_name': 'Kevin McCarthy',
            'asset_name': 'Microsoft Corporation',
            'ticker': 'MSFT',
            'trade_type': 'stock trade',
            'action': 'SELL',
            'amount_range': '$500K-$1M',
            'transaction_date': '2025-01-15',
            'description': ''
        },
        {
            'politician_name': 'jeffries',
            'politician_full_name': 'Hakeem Jeffries',
            'asset_name': 'Tesla Inc',
            'ticker': 'TSLA',
            'trade_type': 'option_call',
            'action': 'BUY',
            'amount_range': '$100K-$250K',
            'transaction_date': '2025-01-15',
            'description': 'Call option expiring 2025-03-21'
        }
    ]
    
    print("🧪 Testing same-channel notifications...")
    print("=" * 50)
    
    for i, trade in enumerate(test_trades, 1):
        print(f"📤 Sending test trade {i}: {trade['politician_full_name']} - {trade['action']} {trade['asset_name']}")
        
        # Create a mock filing for the test
        mock_filing = {
            'pdf_url': f"https://example.com/filing_{i}.pdf"
        }
        
        success = notifier.send_trade_notification(trade, mock_filing['pdf_url'])
        
        if success:
            print(f"✅ Sent successfully")
        else:
            print(f"❌ Failed to send")
        
        print()
    
    print("🎯 All test notifications sent!")
    print("Check your Discord channel to see how they look together.")

if __name__ == "__main__":
    test_same_channel_notifications()
