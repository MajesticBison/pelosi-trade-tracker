#!/usr/bin/env python3
"""
Multi-politician trade tracker that monitors financial disclosures
from multiple members of Congress and sends Discord notifications.
"""

import argparse
import logging
import os
import tempfile
from typing import List, Dict
from dotenv import load_dotenv

from politicians_config import PoliticiansManager, get_all_active_politicians
from multi_politician_scraper import MultiPoliticianScraper
from multi_politician_database import MultiPoliticianTradesDB
from pdf_parser import PelosiPTRParser
from discord_notifier import DiscordNotifier

class MultiPoliticianTracker:
    """Main tracker for multiple politicians' financial disclosures."""
    
    def __init__(self, dry_run: bool = False, verbose: bool = False):
        self.dry_run = dry_run
        self.verbose = verbose
        
        # Setup logging
        log_level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Load environment variables
        load_dotenv()
        
        # Initialize components
        self.politicians_manager = PoliticiansManager()
        self.scraper = MultiPoliticianScraper()
        self.database = MultiPoliticianTradesDB()
        self.pdf_parser = PelosiPTRParser()
        
        # Initialize Discord notifiers for each politician
        self.discord_notifiers = {}
        self._setup_discord_notifiers()
        
        self.logger.info("Multi-Politician Trade Tracker initialized")
    
    def _setup_discord_notifiers(self):
        """Set up Discord notifiers for each active politician using shared webhook."""
        active_politicians = get_all_active_politicians()
        
        # Get shared Discord webhook from environment
        webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
        channel_name = os.getenv('DISCORD_CHANNEL_NAME', '#congressional-trades')
        
        if webhook_url:
            for politician in active_politicians:
                try:
                    self.discord_notifiers[politician.name] = DiscordNotifier(webhook_url, channel_name)
                    self.logger.info(f"Discord integration enabled for {politician.full_name}")
                except Exception as e:
                    self.logger.error(f"Failed to setup Discord for {politician.full_name}: {e}")
        else:
            self.logger.warning("No Discord webhook configured in environment variables")
    
    def run(self):
        """Run the main tracking process."""
        self.logger.info("Starting multi-politician trade tracking process...")
        
        if self.dry_run:
            self.logger.info("Running in DRY RUN MODE - no files will be downloaded or saved")
        
        try:
            # Get all active politicians
            active_politicians = get_all_active_politicians()
            if not active_politicians:
                self.logger.warning("No active politicians configured")
                return
            
            self.logger.info(f"Tracking {len(active_politicians)} active politicians")
            
            # Search for new filings from all politicians
            all_filings = self.scraper.search_all_active_politicians()
            
            total_new_filings = 0
            total_new_trades = 0
            
            # Process filings for each politician
            for politician_name, filings in all_filings.items():
                politician = self.politicians_manager.get_politician(politician_name)
                if not politician:
                    self.logger.error(f"Politician configuration not found: {politician_name}")
                    continue
                
                self.logger.info(f"Processing {len(filings)} filings for {politician.full_name}")
                
                new_filings, new_trades = self._process_politician_filings(politician, filings)
                total_new_filings += new_filings
                total_new_trades += new_trades
            
            self.logger.info(f"Processing complete: {total_new_filings} new filings, {total_new_trades} new trades")
            
        except Exception as e:
            self.logger.error(f"Error in main tracking process: {e}")
            raise
    
    def _process_politician_filings(self, politician, filings: List[Dict]) -> tuple[int, int]:
        """Process filings for a specific politician."""
        new_filings = 0
        new_trades = 0
        
        # Always limit to most recent 1 PTR filing per politician
        if len(filings) > 1:
            self.logger.info(f"Limiting to 1 most recent PTR filing for {politician.full_name} out of {len(filings)} found.")
            filings = filings[:1]
        
        for filing in filings:
            filing_id = filing['filing_id']
            
            # Only process PTR filings (Periodic Transaction Reports)
            if not filing.get('is_ptr', False):
                self.logger.debug(f"Skipping non-PTR filing {filing_id} ({filing.get('filing_type', 'Unknown')}) for {politician.full_name}")
                continue
            
            # Check if already processed
            if self.database.is_filing_processed(filing_id):
                self.logger.debug(f"Filing {filing_id} already processed for {politician.full_name}")
                continue
            
            self.logger.info(f"Processing new PTR filing {filing_id} for {politician.full_name}")
            
            try:
                # Download and parse PDF
                trades = self._process_filing_pdf(filing, politician)
                
                if not self.dry_run:
                    # Save to database
                    self.database.add_filing(
                        filing_id, politician.name, filing['filing_type'],
                        filing['filing_date'], filing['pdf_url']
                    )
                    
                    if trades:
                        self.database.add_trades(filing_id, politician.name, trades, filing['filing_date'])
                    
                    # Send Discord notifications
                    self._send_discord_notifications(politician, trades, filing)
                
                new_filings += 1
                new_trades += len(trades)
                
                self.logger.info(f"Processed filing {filing_id}: {len(trades)} trades found")
                
            except Exception as e:
                self.logger.error(f"Error processing filing {filing_id}: {e}")
                continue
        
        return new_filings, new_trades
    
    def _process_filing_pdf(self, filing: Dict, politician) -> List[Dict]:
        """Download and parse a PDF filing."""
        if self.dry_run:
            self.logger.info(f"DRY RUN: Would download PDF from {filing['pdf_url']}")
            return []
        
        # Download PDF to temporary file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_filename = temp_file.name
        
        try:
            # Download PDF
            if not self.scraper.download_pdf(filing['pdf_url'], temp_filename):
                self.logger.error(f"Failed to download PDF: {filing['pdf_url']}")
                return []
            
            # Parse PDF
            trades = self.pdf_parser.extract_trades(temp_filename)
            
            # Add politician information to trades
            for trade in trades:
                trade['politician_name'] = politician.name
                trade['politician_full_name'] = politician.full_name
            
            return trades
            
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_filename)
            except OSError:
                pass
    
    def _send_discord_notifications(self, politician, trades: List[Dict], filing: Dict):
        """Send Discord notifications for new trades."""
        if not trades:
            return
        
        notifier = self.discord_notifiers.get(politician.name)
        if not notifier:
            self.logger.warning(f"No Discord notifier configured for {politician.full_name}")
            return
        
        try:
            # Send individual notifications for each trade
            for trade in trades:
                success = notifier.send_trade_notification(trade, filing['pdf_url'])
                if success:
                    self.logger.info(f"Discord notification sent for {politician.full_name} trade: {trade.get('asset_name', 'Unknown')}")
                else:
                    self.logger.error(f"Failed to send Discord notification for {politician.full_name}")
        
        except Exception as e:
            self.logger.error(f"Error sending Discord notifications for {politician.full_name}: {e}")
    
    def test_discord_connection(self, politician_name: str = None):
        """Test Discord connection for a specific politician or all politicians."""
        if politician_name:
            politicians = [self.politicians_manager.get_politician(politician_name)]
            if not politicians[0]:
                self.logger.error(f"Politician not found: {politician_name}")
                return
        else:
            politicians = get_all_active_politicians()
        
        for politician in politicians:
            if not politician:
                continue
                
            notifier = self.discord_notifiers.get(politician.name)
            if notifier:
                success = notifier.test_connection()
                if success:
                    self.logger.info(f"✅ Discord connection test successful for {politician.full_name}")
                else:
                    self.logger.error(f"❌ Discord connection test failed for {politician.full_name}")
            else:
                self.logger.warning(f"⚠️  No Discord notifier configured for {politician.full_name}")
    
    def show_statistics(self):
        """Show database statistics."""
        stats = self.database.get_statistics()
        
        print("\n📊 Multi-Politician Tracker Statistics")
        print("=" * 50)
        print(f"Politicians: {stats.get('politician_count', 0)} total, {stats.get('active_politician_count', 0)} active")
        print(f"Filings: {stats.get('filing_count', 0)}")
        print(f"Trades: {stats.get('trade_count', 0)}")
        
        if stats.get('trades_by_politician'):
            print("\nTrades by Politician:")
            for politician_name, trade_count in stats['trades_by_politician']:
                politician = self.politicians_manager.get_politician(politician_name)
                full_name = politician.full_name if politician else politician_name
                print(f"  {full_name}: {trade_count} trades")

def main():
    parser = argparse.ArgumentParser(description="Multi-Politician Trade Tracker")
    parser.add_argument('--dry-run', action='store_true', 
                       help='Run without downloading files or sending notifications')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    parser.add_argument('--test-discord', metavar='POLITICIAN',
                       help='Test Discord connection for a specific politician')
    parser.add_argument('--stats', action='store_true',
                       help='Show database statistics')
    
    args = parser.parse_args()
    
    try:
        tracker = MultiPoliticianTracker(dry_run=args.dry_run, verbose=args.verbose)
        
        if args.stats:
            tracker.show_statistics()
        elif args.test_discord:
            tracker.test_discord_connection(args.test_discord)
        else:
            tracker.run()
            
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
