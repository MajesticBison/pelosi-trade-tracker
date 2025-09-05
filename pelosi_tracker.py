#!/usr/bin/env python3
"""
Nancy Pelosi Trade Tracker

Scrapes the U.S. House Clerk's financial disclosure site for new Periodic Transaction Reports (PTRs)
filed by Nancy Pelosi, downloads PDFs, extracts trades, and sends notifications to Slack.

Usage:
    python pelosi_tracker.py [--test] [--verbose] [--dry-run]
"""

import argparse
import logging
import os
import sys
import tempfile
from datetime import datetime
from typing import List, Dict
from dotenv import load_dotenv

# Import our modules
from database import PelosiTradesDB
from scraper import HouseClerkScraper
from pdf_parser import PelosiPTRParser
from discord_notifier import DiscordNotifier

class PelosiTradeTracker:
    """Main orchestrator for tracking Nancy Pelosi's trades."""
    
    def __init__(self, test_mode: bool = False, dry_run: bool = False):
        # Load environment variables
        load_dotenv()
        
        # Setup logging
        self._setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # Configuration
        self.test_mode = test_mode
        self.dry_run = dry_run
        
        # Initialize components
        self.db = PelosiTradesDB()
        self.scraper = HouseClerkScraper()
        self.parser = PelosiPTRParser()
        
        # Discord integration (only if not in test mode and webhook is configured)
        self.discord = None
        if not test_mode:
            webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
            channel_name = os.getenv('DISCORD_CHANNEL_NAME', '#pelosi-trades')
            
            if webhook_url:
                try:
                    self.discord = DiscordNotifier(webhook_url, channel_name)
                    self.logger.info("Discord integration enabled")
                except ValueError as e:
                    self.logger.error(f"Invalid Discord configuration: {e}")
                    self.logger.info("Continuing without Discord integration")
            else:
                self.logger.info("No DISCORD_WEBHOOK_URL found - continuing without Discord integration")
        
        self.logger.info("Pelosi Trade Tracker initialized")
        if test_mode:
            self.logger.info("Running in TEST MODE - no Discord notifications will be sent")
        if dry_run:
            self.logger.info("Running in DRY RUN MODE - no files will be downloaded or saved")
    
    def _setup_logging(self):
        """Setup logging configuration."""
        log_level = logging.INFO
        if '--verbose' in sys.argv:
            log_level = logging.DEBUG
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler('pelosi_tracker.log')
            ]
        )
    
    def run(self):
        """Main execution flow."""
        try:
            self.logger.info("Starting Pelosi trade tracking process...")
            
            # Step 1: Search for new filings
            new_filings = self._find_new_filings()
            if not new_filings:
                self.logger.info("No new Pelosi filings found")
                return
            
            self.logger.info(f"Found {len(new_filings)} new filings to process")
            
            # Step 2: Process each new filing
            for filing in new_filings:
                self._process_filing(filing)
            
            # Step 3: Display summary
            self._display_summary()
            
        except Exception as e:
            self.logger.error(f"Unexpected error in main execution: {e}")
            raise
    
    def _find_new_filings(self) -> List[Dict]:
        """Find new Pelosi filings that haven't been processed yet."""
        try:
            # Scrape the House Clerk site
            all_filings = self.scraper.search_pelosi_filings()
            
            # Filter for new filings, but limit to most recent ones
            new_filings = []
            processed_count = 0
            
            for filing in all_filings:
                filing_id = filing['filing_id']
                if not self.db.is_filing_processed(filing_id):
                    new_filings.append(filing)
                    self.logger.info(f"New filing found: {filing_id} ({filing.get('filing_date', 'Unknown date')})")
                else:
                    processed_count += 1
                    self.logger.debug(f"Filing already processed: {filing_id}")
                    # If we find a processed filing, we can stop looking for more
                    # since filings are sorted by newest first
                    break
            
            # If no filings are processed yet (fresh database), limit to first 2 most recent
            if processed_count == 0 and len(new_filings) > 2:
                self.logger.info(f"Fresh database detected. Limiting to first 2 most recent filings out of {len(new_filings)} found.")
                new_filings = new_filings[:2]
            
            return new_filings
            
        except Exception as e:
            self.logger.error(f"Error finding new filings: {e}")
            return []
    
    def _process_filing(self, filing: Dict):
        """Process a single filing: download, parse, and notify."""
        filing_id = filing['filing_id']
        
        try:
            self.logger.info(f"Processing filing: {filing_id}")
            
            # Download PDF
            pdf_path = self._download_filing_pdf(filing)
            if not pdf_path:
                self.logger.error(f"Failed to download PDF for filing: {filing_id}")
                return
            
            # Parse PDF for trades
            trades = self.parser.extract_trades(pdf_path)
            self.logger.info(f"Extracted {len(trades)} trades from filing: {filing_id}")
            
            # Store in database
            self.db.add_filing(
                filing_id=filing_id,
                filing_date=filing.get('filing_date', 'Unknown'),
                pdf_url=filing['pdf_url'],
                trade_count=len(trades)
            )
            
            if trades:
                self.db.add_trades(filing_id, trades, filing.get('filing_date', 'Unknown'))
                
                # Send Discord notifications
                if not self.test_mode and self.discord:
                    self._send_discord_notifications(trades, filing)
                elif self.test_mode:
                    self.logger.info(f"[TEST MODE] Would send {len(trades)} trade notifications to Discord")
                elif not self.discord:
                    self.logger.info(f"[NO DISCORD] Would send {len(trades)} trade notifications to Discord")
            
            # Clean up downloaded PDF
            if not self.dry_run and os.path.exists(pdf_path):
                os.remove(pdf_path)
                self.logger.debug(f"Cleaned up temporary PDF: {pdf_path}")
            
        except Exception as e:
            self.logger.error(f"Error processing filing {filing_id}: {e}")
    
    def _download_filing_pdf(self, filing: Dict) -> str:
        """Download a filing PDF to a temporary location."""
        if self.dry_run:
            # In dry run mode, create a dummy path
            return f"/tmp/dry_run_{filing['filing_id']}.pdf"
        
        try:
            # Create temporary file
            temp_dir = tempfile.gettempdir()
            filename = f"pelosi_filing_{filing['filing_id']}.pdf"
            pdf_path = os.path.join(temp_dir, filename)
            
            # Download the PDF
            if self.scraper.download_pdf(filing['pdf_url'], pdf_path):
                return pdf_path
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"Error downloading PDF: {e}")
            return None
    
    def _send_discord_notifications(self, trades: List[Dict], filing: Dict):
        """Send Discord notifications for extracted trades."""
        try:
            if not trades:
                return
            
            # Send filing summary
            self.discord.send_filing_summary(filing, len(trades))
            
            # Send individual trade notifications for each trade
            for trade in trades:
                self.discord.send_trade_notification(trade, filing['pdf_url'])
            
            self.logger.info(f"Discord notifications sent for {len(trades)} trades")
            
        except Exception as e:
            self.logger.error(f"Error sending Discord notifications: {e}")
    
    def _display_summary(self):
        """Display a summary of the current run."""
        try:
            stats = self.db.get_filing_stats()
            
            print("\n" + "="*50)
            print("PELOSI TRADE TRACKER - EXECUTION SUMMARY")
            print("="*50)
            print(f"Total filings processed: {stats['total_filings']}")
            print(f"Total trades extracted: {stats['total_trades']}")
            print(f"Filings in last 7 days: {stats['recent_filings_7d']}")
            print(f"Test mode: {'Yes' if self.test_mode else 'No'}")
            print(f"Dry run mode: {'Yes' if self.dry_run else 'No'}")
            print("="*50)
            
        except Exception as e:
            self.logger.error(f"Error displaying summary: {e}")
    
    def test_discord_connection(self):
        """Test the Discord webhook connection."""
        if not self.discord:
            print("No Discord configuration available")
            return False
        
        print("Testing Discord connection...")
        if self.discord.test_connection():
            print("✅ Discord connection successful!")
            return True
        else:
            print("❌ Discord connection failed!")
            return False

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Track Nancy Pelosi's financial disclosures and trades",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python pelosi_tracker.py                    # Normal run
  python pelosi_tracker.py --test            # Test mode (no Slack)
  python pelosi_tracker.py --dry-run         # Dry run (no downloads)
  python pelosi_tracker.py --verbose         # Verbose logging
  python pelosi_tracker.py --test-discord    # Test Discord connection only
        """
    )
    
    parser.add_argument(
        '--test',
        action='store_true',
        help='Run in test mode (no Discord notifications)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Dry run mode (no file downloads or saves)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--test-discord',
        action='store_true',
        help='Test Discord connection and exit'
    )
    
    args = parser.parse_args()
    
    try:
        # Create tracker instance
        tracker = PelosiTradeTracker(
            test_mode=args.test,
            dry_run=args.dry_run
        )
        
        # Test Discord connection if requested
        if args.test_discord:
            tracker.test_discord_connection()
            return
        
        # Run the main process
        tracker.run()
        
    except KeyboardInterrupt:
        print("\nProcess interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
