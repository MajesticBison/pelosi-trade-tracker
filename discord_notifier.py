import requests
import json
import logging
from typing import List, Dict, Optional
from datetime import datetime
import os
import time

class DiscordNotifier:
    """Discord integration for sending Pelosi trade notifications."""
    
    def __init__(self, webhook_url: str, channel_name: str = "#pelosi-trades"):
        self.webhook_url = webhook_url
        self.channel_name = channel_name
        self.logger = logging.getLogger(__name__)
        
        # Validate webhook URL
        if not webhook_url or not webhook_url.startswith('https://discord.com/api/webhooks/'):
            raise ValueError("Invalid Discord webhook URL")
    
    def send_trade_notification(self, trade: Dict, filing_url: str) -> bool:
        """
        Send a single trade notification to Discord.
        Returns True if successful, False otherwise.
        """
        try:
            message = self._format_trade_message(trade, filing_url)
            return self._send_discord_message(message)
            
        except Exception as e:
            self.logger.error(f"Error sending trade notification: {e}")
            return False
    
    def send_bulk_trade_notification(self, trades: List[Dict], filing_url: str) -> bool:
        """
        Send a bulk notification for multiple trades from the same filing.
        Returns True if successful, False otherwise.
        """
        try:
            if not trades:
                return True
            
            if len(trades) == 1:
                return self.send_trade_notification(trades[0], filing_url)
            
            # For multiple trades, send a summary message
            message = self._format_bulk_trade_message(trades, filing_url)
            return self._send_discord_message(message)
            
        except Exception as e:
            self.logger.error(f"Error sending bulk trade notification: {e}")
            return False
    
    def send_filing_summary(self, filing_info: Dict, trade_count: int) -> bool:
        """
        Send a summary message about a new filing.
        Returns True if successful, False otherwise.
        """
        try:
            message = self._format_filing_summary(filing_info, trade_count)
            return self._send_discord_message(message)
            
        except Exception as e:
            self.logger.error(f"Error sending filing summary: {e}")
            return False
    
    def _format_trade_message(self, trade: Dict, filing_url: str) -> Dict:
        """Format a single trade for Discord notification."""
        # Determine emoji, trade type display, and colors based on action and type
        action = trade['action'].upper()
        
        if trade['trade_type'] == 'option_call':
            emoji = "📢"
            trade_type_display = "Option Trade (**CALL**)"
            color = 0x800080  # Purple for options
        elif trade['trade_type'] == 'option_put':
            emoji = "📢"
            trade_type_display = "Option Trade (**PUT**)"
            color = 0x800080  # Purple for options
        else:
            emoji = "📢"
            trade_type_display = "Stock Trade"
            # Color based on action
            if action == 'BUY':
                color = 0x00ff00  # Green for BUY
            elif action == 'SELL':
                color = 0xff8000  # Orange for SELL
            else:
                color = 0x0099ff  # Blue for other actions
        
        # Format ticker info
        ticker_info = f" ({trade['ticker']})" if trade.get('ticker') else ""
        
        # Create fields list
        fields = [
            {
                "name": "Stock",
                "value": f"{trade['asset_name']}{ticker_info}",
                "inline": True
            },
            {
                "name": "Type",
                "value": trade['trade_type'].title(),
                "inline": True
            },
            {
                "name": "Action",
                "value": f"**{trade['action']}**",
                "inline": True
            },
            {
                "name": "Amount",
                "value": self._format_amount_range(trade['amount_range']),
                "inline": True
            },
            {
                "name": "Date",
                "value": trade['transaction_date'],
                "inline": True
            },
            {
                "name": "PDF",
                "value": f"[View Filing]({filing_url})",
                "inline": True
            }
        ]
        
        # Add description field for options trades
        if trade.get('description') and trade['trade_type'] in ['option_call', 'option_put']:
            fields.append({
                "name": "Option Details",
                "value": trade['description'],
                "inline": False
            })
        
        # Get politician name from trade data
        politician_name = trade.get('politician_full_name', 'Unknown Politician')
        
        # Create Discord embed
        embed = {
            "title": f"{emoji} {politician_name} {trade_type_display}!",
            "color": color,
            "fields": fields,
            "footer": {
                "text": "Congressional Trade Bot",
                "icon_url": "https://cdn.discordapp.com/emojis/📈.png"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return {
            "username": "Congressional Trade Bot",
            "avatar_url": "https://cdn.discordapp.com/emojis/📈.png",
            "embeds": [embed]
        }
    
    def _format_bulk_trade_message(self, trades: List[Dict], filing_url: str) -> Dict:
        """Format multiple trades for a single Discord notification."""
        emoji = "📢"
        
        # Create description with trade list
        description = f"**{len(trades)} new trades** found in latest filing\n\n"
        
        # List each trade briefly
        for i, trade in enumerate(trades[:5], 1):  # Show first 5 trades
            ticker_info = f" ({trade['ticker']})" if trade.get('ticker') else ""
            description += f"{i}. {trade['action']} {trade['trade_type'].title()} - {trade['asset_name']}{ticker_info} - {trade['amount_range']}\n"
        
        if len(trades) > 5:
            description += f"\n... and {len(trades) - 5} more trades"
        
        embed = {
            "title": f"{emoji} Nancy Pelosi Multiple Trades Alert!",
            "description": description,
            "color": 0xff9900,  # Orange for multiple trades
            "fields": [
                {
                    "name": "PDF",
                    "value": f"[View Full Filing]({filing_url})",
                    "inline": False
                }
            ],
            "footer": {
                "text": "Congressional Trade Bot",
                "icon_url": "https://cdn.discordapp.com/emojis/📈.png"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return {
            "username": "Congressional Trade Bot",
            "avatar_url": "https://cdn.discordapp.com/emojis/📈.png",
            "embeds": [embed]
        }
    
    def _format_filing_summary(self, filing_info: Dict, trade_count: int) -> Dict:
        """Format a filing summary message."""
        emoji = "📄"
        
        embed = {
            "title": f"{emoji} New Pelosi Filing Detected!",
            "color": 0x0099ff,  # Blue for filing summary
            "fields": [
                {
                    "name": "Filing Date",
                    "value": filing_info.get('filing_date', 'Unknown'),
                    "inline": True
                },
                {
                    "name": "Trades Found",
                    "value": str(trade_count),
                    "inline": True
                },
                {
                    "name": "PDF",
                    "value": f"[View Filing]({filing_info.get('pdf_url', '')})",
                    "inline": True
                }
            ],
            "footer": {
                "text": "Congressional Trade Bot",
                "icon_url": "https://cdn.discordapp.com/emojis/📈.png"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return {
            "username": "Congressional Trade Bot",
            "avatar_url": "https://cdn.discordapp.com/emojis/📈.png",
            "embeds": [embed]
        }
    
    def _format_amount_range(self, amount_range: str) -> str:
        """Convert amount range to cleaner format like 1M-5M or 100K-500K."""
        try:
            # Remove dollar signs and clean up the string
            clean_amount = amount_range.replace('$', '').replace(',', '').strip()
            
            # Split by dash to get min and max
            if ' - ' in clean_amount:
                min_str, max_str = clean_amount.split(' - ')
            elif '-' in clean_amount:
                min_str, max_str = clean_amount.split('-')
            else:
                return amount_range  # Return original if we can't parse
            
            # Convert to numbers
            min_val = int(min_str.strip())
            max_val = int(max_str.strip())
            
            # Format based on size
            def format_amount(val):
                if val >= 1_000_000:
                    return f"{val // 1_000_000}M"
                elif val >= 1_000:
                    return f"{val // 1_000}K"
                else:
                    return str(val)
            
            return f"${format_amount(min_val)}-${format_amount(max_val)}"
            
        except (ValueError, IndexError):
            # If parsing fails, return original
            return amount_range
    
    def _send_discord_message(self, message: Dict, max_retries: int = 3) -> bool:
        """Send a message to Discord via webhook with rate limiting handling."""
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    self.webhook_url,
                    json=message,
                    headers={'Content-Type': 'application/json'},
                    timeout=10
                )
                
                if response.status_code in [200, 204]:
                    self.logger.info("Discord message sent successfully")
                    return True
                elif response.status_code == 429:
                    # Rate limited - parse retry_after from response
                    try:
                        error_data = response.json()
                        retry_after = error_data.get('retry_after', 1.0)
                        self.logger.warning(f"Discord rate limited. Waiting {retry_after} seconds before retry {attempt + 1}/{max_retries}")
                        time.sleep(retry_after)
                        continue
                    except (json.JSONDecodeError, KeyError):
                        # Fallback if we can't parse the response
                        wait_time = (attempt + 1) * 2  # Exponential backoff: 2, 4, 6 seconds
                        self.logger.warning(f"Discord rate limited. Waiting {wait_time} seconds before retry {attempt + 1}/{max_retries}")
                        time.sleep(wait_time)
                        continue
                else:
                    self.logger.error(f"Discord API error: {response.status_code} - {response.text}")
                    return False
                    
            except requests.RequestException as e:
                self.logger.error(f"Network error sending Discord message (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)  # Wait 2 seconds before retry
                    continue
                return False
            except Exception as e:
                self.logger.error(f"Unexpected error sending Discord message: {e}")
                return False
        
        self.logger.error(f"Failed to send Discord message after {max_retries} attempts")
        return False
    
    def test_connection(self) -> bool:
        """Test the Discord webhook connection."""
        try:
            test_embed = {
                "title": "🧪 Congressional Trade Bot Connection Test",
                "description": "Connection test successful!",
                "color": 0x00ff00,  # Green for success
                "footer": {
                    "text": "Congressional Trade Bot",
                    "icon_url": "https://cdn.discordapp.com/emojis/📈.png"
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
            test_message = {
                "username": "Congressional Trade Bot",
                "avatar_url": "https://cdn.discordapp.com/emojis/📈.png",
                "embeds": [test_embed]
            }
            
            return self._send_discord_message(test_message)
            
        except Exception as e:
            self.logger.error(f"Discord connection test failed: {e}")
            return False
