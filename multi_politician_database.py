#!/usr/bin/env python3
"""
Multi-politician database manager for tracking processed filings and trades.
Supports multiple politicians with individual tracking.
"""

import sqlite3
import os
from typing import List, Dict, Optional
from datetime import datetime

class MultiPoliticianTradesDB:
    """Database manager for tracking processed filings from multiple politicians."""
    
    def __init__(self, db_path: str = "politician_trades.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create politicians table to track politician information
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS politicians (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    full_name TEXT NOT NULL,
                    search_name TEXT NOT NULL,
                    party TEXT,
                    state TEXT,
                    chamber TEXT,
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create filings table to track processed PTRs
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS filings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filing_id TEXT UNIQUE NOT NULL,
                    politician_name TEXT NOT NULL,
                    filing_type TEXT NOT NULL,
                    filing_date TEXT NOT NULL,
                    pdf_url TEXT NOT NULL,
                    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    trade_count INTEGER DEFAULT 0,
                    FOREIGN KEY (politician_name) REFERENCES politicians (name)
                )
            ''')
            
            # Create trades table to store extracted trade data
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filing_id TEXT NOT NULL,
                    politician_name TEXT NOT NULL,
                    asset_name TEXT NOT NULL,
                    ticker TEXT,
                    trade_type TEXT NOT NULL,
                    action TEXT NOT NULL,
                    amount_range TEXT NOT NULL,
                    transaction_date TEXT NOT NULL,
                    filing_date TEXT NOT NULL,
                    description TEXT,
                    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (filing_id) REFERENCES filings (filing_id),
                    FOREIGN KEY (politician_name) REFERENCES politicians (name)
                )
            ''')
            
            # Create indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_filings_politician ON filings (politician_name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_trades_politician ON trades (politician_name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_trades_filing ON trades (filing_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_filings_date ON filings (filing_date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_trades_date ON trades (transaction_date)')
            
            conn.commit()
    
    def add_politician(self, name: str, full_name: str, search_name: str, 
                      party: str = "", state: str = "", chamber: str = "House", 
                      status: str = "active") -> bool:
        """Add a politician to the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO politicians 
                    (name, full_name, search_name, party, state, chamber, status, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (name, full_name, search_name, party, state, chamber, status))
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Error adding politician: {e}")
            return False
    
    def get_politician(self, name: str) -> Optional[Dict]:
        """Get politician information."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM politicians WHERE name = ?', (name,))
                row = cursor.fetchone()
                if row:
                    columns = [description[0] for description in cursor.description]
                    return dict(zip(columns, row))
                return None
        except sqlite3.Error as e:
            print(f"Error getting politician: {e}")
            return None
    
    def list_politicians(self) -> List[Dict]:
        """List all politicians in the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM politicians ORDER BY name')
                rows = cursor.fetchall()
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in rows]
        except sqlite3.Error as e:
            print(f"Error listing politicians: {e}")
            return []
    
    def is_filing_processed(self, filing_id: str) -> bool:
        """Check if a filing has already been processed."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT 1 FROM filings WHERE filing_id = ?', (filing_id,))
                return cursor.fetchone() is not None
        except sqlite3.Error as e:
            print(f"Error checking filing: {e}")
            return False
    
    def add_filing(self, filing_id: str, politician_name: str, filing_type: str, 
                   filing_date: str, pdf_url: str) -> bool:
        """Add a processed filing to the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO filings 
                    (filing_id, politician_name, filing_type, filing_date, pdf_url, processed_at)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (filing_id, politician_name, filing_type, filing_date, pdf_url))
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Error adding filing: {e}")
            return False
    
    def add_trades(self, filing_id: str, politician_name: str, trades: List[Dict], 
                   filing_date: str) -> bool:
        """Add extracted trades to the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for trade in trades:
                    cursor.execute('''
                        INSERT INTO trades 
                        (filing_id, politician_name, asset_name, ticker, trade_type, 
                         action, amount_range, transaction_date, filing_date, description)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        filing_id, politician_name, trade.get('asset_name', ''),
                        trade.get('ticker', ''), trade.get('trade_type', ''),
                        trade.get('action', ''), trade.get('amount_range', ''),
                        trade.get('transaction_date', ''), filing_date,
                        trade.get('description', '')
                    ))
                
                # Update trade count in filings table
                cursor.execute('''
                    UPDATE filings SET trade_count = ? 
                    WHERE filing_id = ?
                ''', (len(trades), filing_id))
                
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Error adding trades: {e}")
            return False
    
    def get_politician_filings(self, politician_name: str) -> List[Dict]:
        """Get all filings for a specific politician."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM filings 
                    WHERE politician_name = ? 
                    ORDER BY filing_date DESC
                ''', (politician_name,))
                rows = cursor.fetchall()
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in rows]
        except sqlite3.Error as e:
            print(f"Error getting politician filings: {e}")
            return []
    
    def get_politician_trades(self, politician_name: str, limit: int = 50) -> List[Dict]:
        """Get recent trades for a specific politician."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM trades 
                    WHERE politician_name = ? 
                    ORDER BY transaction_date DESC, extracted_at DESC
                    LIMIT ?
                ''', (politician_name, limit))
                rows = cursor.fetchall()
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in rows]
        except sqlite3.Error as e:
            print(f"Error getting politician trades: {e}")
            return []
    
    def get_all_recent_trades(self, limit: int = 100) -> List[Dict]:
        """Get recent trades from all politicians."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT t.*, p.full_name, p.party, p.state 
                    FROM trades t
                    JOIN politicians p ON t.politician_name = p.name
                    ORDER BY t.transaction_date DESC, t.extracted_at DESC
                    LIMIT ?
                ''', (limit,))
                rows = cursor.fetchall()
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in rows]
        except sqlite3.Error as e:
            print(f"Error getting all recent trades: {e}")
            return []
    
    def get_statistics(self) -> Dict:
        """Get database statistics."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Count politicians
                cursor.execute('SELECT COUNT(*) FROM politicians')
                politician_count = cursor.fetchone()[0]
                
                # Count active politicians
                cursor.execute('SELECT COUNT(*) FROM politicians WHERE status = "active"')
                active_politician_count = cursor.fetchone()[0]
                
                # Count filings
                cursor.execute('SELECT COUNT(*) FROM filings')
                filing_count = cursor.fetchone()[0]
                
                # Count trades
                cursor.execute('SELECT COUNT(*) FROM trades')
                trade_count = cursor.fetchone()[0]
                
                # Count trades by politician
                cursor.execute('''
                    SELECT politician_name, COUNT(*) as trade_count
                    FROM trades
                    GROUP BY politician_name
                    ORDER BY trade_count DESC
                ''')
                trades_by_politician = cursor.fetchall()
                
                return {
                    'politician_count': politician_count,
                    'active_politician_count': active_politician_count,
                    'filing_count': filing_count,
                    'trade_count': trade_count,
                    'trades_by_politician': trades_by_politician
                }
        except sqlite3.Error as e:
            print(f"Error getting statistics: {e}")
            return {}
    
    def clear_politician_data(self, politician_name: str) -> bool:
        """Clear all data for a specific politician."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Delete trades
                cursor.execute('DELETE FROM trades WHERE politician_name = ?', (politician_name,))
                
                # Delete filings
                cursor.execute('DELETE FROM filings WHERE politician_name = ?', (politician_name,))
                
                # Delete politician
                cursor.execute('DELETE FROM politicians WHERE name = ?', (politician_name,))
                
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Error clearing politician data: {e}")
            return False

# Backward compatibility - create a wrapper for the old Pelosi-specific database
class PelosiTradesDB:
    """Backward compatibility wrapper for the original Pelosi database."""
    
    def __init__(self, db_path: str = "pelosi_trades.db"):
        # Use the new multi-politician database
        self.multi_db = MultiPoliticianTradesDB("politician_trades.db")
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
    
    def init_database(self):
        """Initialize database (backward compatibility)."""
        self.multi_db.init_database()
    
    def is_filing_processed(self, filing_id: str) -> bool:
        """Check if filing is processed (backward compatibility)."""
        return self.multi_db.is_filing_processed(filing_id)
    
    def add_filing(self, filing_id: str, filing_date: str, pdf_url: str) -> bool:
        """Add filing (backward compatibility)."""
        return self.multi_db.add_filing(filing_id, "pelosi", "PTR", filing_date, pdf_url)
    
    def add_trades(self, filing_id: str, trades: List[Dict], filing_date: str) -> bool:
        """Add trades (backward compatibility)."""
        return self.multi_db.add_trades(filing_id, "pelosi", trades, filing_date)

if __name__ == "__main__":
    # Test the multi-politician database
    db = MultiPoliticianTradesDB()
    
    print("Testing multi-politician database...")
    
    # Add a test politician
    db.add_politician("test", "Test Politician", "Test, Politician", "Independent", "XX", "House")
    
    # Get statistics
    stats = db.get_statistics()
    print(f"Statistics: {stats}")
    
    # List politicians
    politicians = db.list_politicians()
    print(f"Politicians: {politicians}")
