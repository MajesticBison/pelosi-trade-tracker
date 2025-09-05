import sqlite3
import os
from typing import List, Dict, Optional
from datetime import datetime

class PelosiTradesDB:
    """Database manager for tracking processed Pelosi filings."""
    
    def __init__(self, db_path: str = "pelosi_trades.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create filings table to track processed PTRs
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS filings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filing_id TEXT UNIQUE NOT NULL,
                    filing_date TEXT NOT NULL,
                    pdf_url TEXT NOT NULL,
                    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    trade_count INTEGER DEFAULT 0
                )
            ''')
            
            # Create trades table to store extracted trade data
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filing_id TEXT NOT NULL,
                    asset_name TEXT NOT NULL,
                    ticker TEXT,
                    trade_type TEXT NOT NULL,
                    action TEXT NOT NULL,
                    amount_range TEXT NOT NULL,
                    transaction_date TEXT NOT NULL,
                    filing_date TEXT NOT NULL,
                    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (filing_id) REFERENCES filings (filing_id)
                )
            ''')
            
            conn.commit()
    
    def is_filing_processed(self, filing_id: str) -> bool:
        """Check if a filing has already been processed."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT 1 FROM filings WHERE filing_id = ?', (filing_id,))
            return cursor.fetchone() is not None
    
    def add_filing(self, filing_id: str, filing_date: str, pdf_url: str, trade_count: int = 0):
        """Add a new filing to the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO filings (filing_id, filing_date, pdf_url, trade_count)
                VALUES (?, ?, ?, ?)
            ''', (filing_id, filing_date, pdf_url, trade_count))
            conn.commit()
    
    def add_trades(self, filing_id: str, trades: List[Dict], filing_date: str = None):
        """Add extracted trades for a filing."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for trade in trades:
                cursor.execute('''
                    INSERT INTO trades (
                        filing_id, asset_name, ticker, trade_type, action,
                        amount_range, transaction_date, filing_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    filing_id,
                    trade['asset_name'],
                    trade.get('ticker'),
                    trade['trade_type'],
                    trade['action'],
                    trade['amount_range'],
                    trade['transaction_date'],
                    filing_date or 'Unknown'
                ))
            
            # Update trade count in filings table
            cursor.execute('''
                UPDATE filings SET trade_count = ? WHERE filing_id = ?
            ''', (len(trades), filing_id))
            
            conn.commit()
    
    def get_recent_filings(self, limit: int = 10) -> List[Dict]:
        """Get recent filings for debugging/monitoring."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT filing_id, filing_date, pdf_url, processed_at, trade_count
                FROM filings ORDER BY processed_at DESC LIMIT ?
            ''', (limit,))
            
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_filing_stats(self) -> Dict:
        """Get statistics about processed filings."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Total filings
            cursor.execute('SELECT COUNT(*) FROM filings')
            total_filings = cursor.fetchone()[0]
            
            # Total trades
            cursor.execute('SELECT COUNT(*) FROM trades')
            total_trades = cursor.fetchone()[0]
            
            # Recent activity
            cursor.execute('''
                SELECT COUNT(*) FROM filings 
                WHERE processed_at >= datetime('now', '-7 days')
            ''')
            recent_filings = cursor.fetchone()[0]
            
            return {
                'total_filings': total_filings,
                'total_trades': total_trades,
                'recent_filings_7d': recent_filings
            }
