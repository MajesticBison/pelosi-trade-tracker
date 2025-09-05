import re
import pdfplumber
from typing import List, Dict, Optional
from enum import Enum
import logging
import os

class TradeType(Enum):
    STOCK = "stock"
    OPTION_CALL = "option_call"
    OPTION_PUT = "option_put"

class PelosiPTRParser:
    """Parser for Nancy Pelosi's Periodic Transaction Reports (PTRs)."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def extract_trades(self, pdf_path: str) -> List[Dict]:
        """
        Extract trade information from Nancy Pelosi's PTR PDFs.
        Handles stocks, ETFs, and options (calls/puts).
        """
        try:
            if not os.path.exists(pdf_path):
                self.logger.error(f"PDF file not found: {pdf_path}")
                return []
            
            self.logger.info(f"Parsing PDF: {pdf_path}")
            
            with pdfplumber.open(pdf_path) as pdf:
                text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            
            if not text.strip():
                self.logger.warning("No text extracted from PDF")
                return []
            
            # Parse the extracted text for trades
            trades = self._parse_text_for_trades(text)
            
            self.logger.info(f"Extracted {len(trades)} trades from PDF")
            return trades
            
        except Exception as e:
            self.logger.error(f"Error parsing PDF {pdf_path}: {e}")
            return []
    
    def _parse_text_for_trades(self, text: str) -> List[Dict]:
        """Parse extracted text to find trade information."""
        trades = []
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            # Look for lines that might contain trade info
            if self._is_trade_line(line):
                trade = self._parse_trade_line(line, lines, i)
                if trade:
                    trades.append(trade)
        
        return trades
    
    def _is_trade_line(self, line: str) -> bool:
        """Check if a line might contain trade information."""
        line_upper = line.upper()
        
        # Look for PTR-specific patterns first
        # Pattern 1: Asset (Ticker) P/S Date Date Amount
        ptr_pattern1 = r'[A-Z].*?\s*\([A-Z]{1,5}\)\s*[PS]\s+\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}/\d{1,2}/\d{4}\s+\$[\d,]+(?:\s*-)?'
        if re.search(ptr_pattern1, line):
            return True
        
        # Pattern 2: SP Asset Name P/S (partial) Date Date Amount (ticker on next line)
        ptr_pattern2 = r'SP\s+[A-Z][^P]*?\s+[PS](?:\s+\(partial\))?\s+\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}/\d{1,2}/\d{4}\s+\$[\d,]+(?:\s*-)?'
        if re.search(ptr_pattern2, line):
            return True
        
        # Pattern 3: SP Asset Name P/S Date Date Amount (with [OT] or other codes on next line)
        ptr_pattern3 = r'SP\s+[A-Z][^P]*?\s+[PS]\s+\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}/\d{1,2}/\d{4}\s+\$[\d,]+(?:\s*-)?'
        if re.search(ptr_pattern3, line):
            return True
        
        # Look for action keywords
        action_keywords = ['BUY', 'SELL', 'PURCHASE', 'SALE', 'ACQUIRED', 'DISPOSED']
        
        # Look for asset indicators
        asset_indicators = ['INC', 'CORP', 'LLC', 'ETF', 'STOCK', 'SHARES']
        
        # Line should have both action and asset indicators
        has_action = any(keyword in line_upper for keyword in action_keywords)
        has_asset = any(indicator in line_upper for indicator in asset_indicators)
        
        # Skip if this looks like a header or non-trade line
        skip_keywords = ['DATE', 'ASSET', 'ACTION', 'AMOUNT', '---', 'TOTAL', 'SUMMARY']
        is_header = any(skip in line_upper for skip in skip_keywords)
        
        return has_action and has_asset and not is_header
    
    def _parse_trade_line(self, line: str, all_lines: List[str], line_index: int) -> Optional[Dict]:
        """Parse a single line that might contain trade information."""
        try:
            # Try PTR-specific parsing first
            ptr_trade = self._parse_ptr_trade_line(line, all_lines, line_index)
            if ptr_trade:
                return ptr_trade
            
            # Extract action (Buy/Sell)
            action = self._extract_action(line)
            if not action:
                return None
            
            # Determine trade type and extract asset info
            trade_info = self._extract_asset_and_type(line)
            if not trade_info:
                return None
            
            asset_name, ticker, trade_type = trade_info
            
            # Extract amount range (handle various formats)
            amount_range = self._extract_amount_range(line)
            
            # Extract transaction date
            transaction_date = self._extract_transaction_date(line, all_lines, line_index)
            
            # Extract filing date (usually in header or nearby)
            filing_date = self._extract_filing_date(all_lines)
            
            # Validate this looks like a real trade
            if asset_name and len(asset_name) > 2 and action:
                return {
                    'asset_name': asset_name,
                    'ticker': ticker,
                    'trade_type': trade_type.value,
                    'action': action,
                    'amount_range': amount_range,
                    'transaction_date': transaction_date,
                    'filing_date': filing_date,
                    'raw_line': line.strip()
                }
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Error parsing trade line: {e}")
            return None
    
    def _parse_ptr_trade_line(self, line: str, all_lines: List[str] = None, line_index: int = 0) -> Optional[Dict]:
        """Parse PTR-specific trade format: Asset (Ticker) P/S Date Date Amount"""
        try:
            # First try the original pattern (ticker on same line)
            pattern = r'([A-Z].*?)\s*\(([A-Z]{1,5})\)\s*([PS])\s+(\d{1,2}/\d{1,2}/\d{4})\s+(\d{1,2}/\d{1,2}/\d{4})\s+(\$[\d,]+(?:\s*-)?)'
            
            match = re.search(pattern, line)
            if match:
                asset_name, ticker, action_code, trans_date, notif_date, amount = match.groups()
                
                # Check if amount is incomplete (ends with dash) and look for completion on next line
                complete_amount = amount.strip()
                if amount.strip().endswith('-') and all_lines and line_index + 1 < len(all_lines):
                    next_line = all_lines[line_index + 1]
                    amount_match = re.search(r'(\$[\d,]+)', next_line)
                    if amount_match:
                        complete_amount = amount.strip() + " " + amount_match.group(1)
                
                # Convert P/S to Buy/Sell
                action = 'BUY' if action_code.upper() == 'P' else 'SELL'
                
                # Determine trade type by looking at nearby lines for options context
                trade_type = self._determine_trade_type_from_ptr_context(all_lines, line_index)
                
                # Extract description for options trades
                description = ""
                if trade_type in [TradeType.OPTION_CALL, TradeType.OPTION_PUT]:
                    description = self._extract_description_for_trade(all_lines, line_index)
                
                return {
                    'asset_name': asset_name.strip(),
                    'ticker': ticker.strip(),
                    'trade_type': trade_type.value,
                    'action': action,
                    'amount_range': complete_amount,
                    'transaction_date': trans_date.strip(),
                    'notification_date': notif_date.strip(),
                    'description': description,
                    'raw_line': line.strip()
                }
            
            # Try new pattern for multi-line format (ticker on next line)
            # Pattern: SP Asset Name P/S Date Date Amount
            # Next line: (TICKER) [TYPE] Amount
            # Also handle (partial) case: SP Asset Name P/S (partial) Date Date Amount
            pattern2 = r'SP\s+([A-Z][^P]*?)\s+([PS])(?:\s+\(partial\))?\s+(\d{1,2}/\d{1,2}/\d{4})\s+(\d{1,2}/\d{1,2}/\d{4})\s+(\$[\d,]+(?:\s*-)?)'
            
            match2 = re.search(pattern2, line)
            if match2 and all_lines and line_index + 1 < len(all_lines):
                asset_name, action_code, trans_date, notif_date, amount = match2.groups()
                
                # Look for ticker and complete amount on next line
                next_line = all_lines[line_index + 1]
                ticker_match = re.search(r'\(([A-Z]{1,5})\)', next_line)
                
                if ticker_match:
                    ticker = ticker_match.group(1)
                    
                    # Look for the second part of the amount on the next line
                    amount_match = re.search(r'(\$[\d,]+)', next_line)
                    if amount_match:
                        # Combine the amounts: "$250,001 -" + "$500,000" = "$250,001 - $500,000"
                        complete_amount = amount.strip() + " " + amount_match.group(1)
                    else:
                        complete_amount = amount.strip()
                    
                    # Convert P/S to Buy/Sell
                    action = 'BUY' if action_code.upper() == 'P' else 'SELL'
                    
                    # Determine trade type by looking at nearby lines for options context
                    trade_type = self._determine_trade_type_from_ptr_context(all_lines, line_index)
                    
                    # Extract description for options trades
                    description = ""
                    if trade_type in [TradeType.OPTION_CALL, TradeType.OPTION_PUT]:
                        description = self._extract_description_for_trade(all_lines, line_index)
                    
                    return {
                        'asset_name': asset_name.strip(),
                        'ticker': ticker.strip(),
                        'trade_type': trade_type.value,
                        'action': action,
                        'amount_range': complete_amount,
                        'transaction_date': trans_date.strip(),
                        'notification_date': notif_date.strip(),
                        'description': description,
                        'raw_line': line.strip()
                    }
            
            # Try pattern for assets with [OT] or other codes (no ticker)
            # Pattern: SP Asset Name P/S Date Date Amount
            # Next line: [OT] or other codes
            pattern3 = r'SP\s+([A-Z][^P]*?)\s+([PS])\s+(\d{1,2}/\d{1,2}/\d{4})\s+(\d{1,2}/\d{1,2}/\d{4})\s+(\$[\d,]+(?:\s*-)?)'
            
            match3 = re.search(pattern3, line)
            if match3 and all_lines and line_index + 1 < len(all_lines):
                asset_name, action_code, trans_date, notif_date, amount = match3.groups()
                
                # Check if amount is already complete (contains both min and max)
                if ' - ' in amount or ' -$' in amount:
                    # Amount is already complete on the same line
                    complete_amount = amount.strip()
                else:
                    # Look for the second part of the amount on the next line
                    next_line = all_lines[line_index + 1]
                    amount_match = re.search(r'(\$[\d,]+)', next_line)
                    if amount_match:
                        # Combine the amounts: "$15,001 -" + "$50,000" = "$15,001 - $50,000"
                        complete_amount = amount.strip() + " " + amount_match.group(1)
                    else:
                        complete_amount = amount.strip()
                
                # Convert P/S to Buy/Sell
                action = 'BUY' if action_code.upper() == 'P' else 'SELL'
                
                # For assets without tickers, determine type from context
                trade_type = self._determine_trade_type_from_ptr_context(all_lines, line_index)
                
                # Extract description for options trades
                description = ""
                if trade_type in [TradeType.OPTION_CALL, TradeType.OPTION_PUT]:
                    description = self._extract_description_for_trade(all_lines, line_index)
                
                return {
                    'asset_name': asset_name.strip(),
                    'ticker': 'N/A',  # No ticker for mutual funds, etc.
                    'trade_type': trade_type.value,
                    'action': action,
                    'amount_range': complete_amount,
                    'transaction_date': trans_date.strip(),
                    'notification_date': notif_date.strip(),
                    'description': description,
                    'raw_line': line.strip()
                }
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Error parsing PTR trade line: {e}")
            return None
    
    def _extract_description_for_trade(self, all_lines: List[str], line_index: int) -> str:
        """Extract description information for a trade, particularly for options."""
        if not all_lines:
            return ""
        
        # Look at the next few lines for description (D: lines)
        description_parts = []
        found_d_line = False
        
        for i in range(line_index + 1, min(line_index + 10, len(all_lines))):
            line = all_lines[i].strip()
            
            # Clean the line to remove null bytes and other encoding issues
            cleaned_line = line.replace('\x00', '').strip()
            
            # Look for description lines that start with 'D:'
            if cleaned_line.startswith('D:'):
                # Extract the description part (remove 'D: ')
                desc_text = cleaned_line[2:].strip()
                description_parts.append(desc_text)
                found_d_line = True
            
            # If we found a D: line, continue collecting until we hit a new section
            elif found_d_line:
                # Stop if we hit another trade line (SP) or end of trade section (L:)
                if cleaned_line.startswith('SP ') or cleaned_line.startswith('L:'):
                    break
                # Otherwise, continue the description (multi-line descriptions)
                else:
                    description_parts.append(cleaned_line)
            
            # Only stop if we hit another trade line (SP) - don't stop at F S: or C: as they might be before D:
            elif cleaned_line.startswith('SP '):
                break
        
        return ' '.join(description_parts)
    
    def _determine_trade_type_from_ptr_context(self, all_lines: List[str], line_index: int) -> TradeType:
        """Determine trade type by looking at nearby lines in PTR for options context."""
        if not all_lines:
            return TradeType.STOCK
        
        # Look at the next few lines for options details
        context_lines = []
        for i in range(line_index, min(line_index + 5, len(all_lines))):
            context_lines.append(all_lines[i])
        
        context_text = ' '.join(context_lines).upper()
        
        # Look for options keywords
        if any(keyword in context_text for keyword in ['CALL', 'PUT', 'OPTION', 'STRIKE', 'EXPIRATION']):
            if 'CALL' in context_text:
                return TradeType.OPTION_CALL
            elif 'PUT' in context_text:
                return TradeType.OPTION_PUT
            else:
                return TradeType.OPTION_CALL  # Default to call if just "option"
        
        # Default to stock
        return TradeType.STOCK
    
    def _determine_trade_type_from_context(self, asset_name: str, context: str) -> TradeType:
        """Determine trade type from context (look for options keywords)."""
        context_upper = context.upper()
        
        # Look for options keywords
        if any(keyword in context_upper for keyword in ['CALL', 'PUT', 'OPTION', 'STRIKE', 'EXPIRATION']):
            if 'CALL' in context_upper:
                return TradeType.OPTION_CALL
            elif 'PUT' in context_upper:
                return TradeType.OPTION_PUT
            else:
                return TradeType.OPTION_CALL  # Default to call if just "option"
        
        # Default to stock
        return TradeType.STOCK
    
    def _extract_action(self, line: str) -> Optional[str]:
        """Extract the trade action (Buy/Sell) from a line."""
        line_upper = line.upper()
        
        if any(keyword in line_upper for keyword in ['BUY', 'PURCHASE', 'ACQUIRED', 'ACQUISITION']):
            return 'BUY'
        elif any(keyword in line_upper for keyword in ['SELL', 'SALE', 'DISPOSED', 'DISPOSAL']):
            return 'SELL'
        
        return None
    
    def _extract_asset_and_type(self, line: str) -> Optional[tuple]:
        """
        Extract asset name, ticker, and determine if it's a stock or option.
        Returns (asset_name, ticker, trade_type) or None.
        """
        line_upper = line.upper()
        
        # Check for options first (CALL/PUT)
        if 'CALL' in line_upper or 'PUT' in line_upper:
            option_type = TradeType.OPTION_CALL if 'CALL' in line_upper else TradeType.OPTION_PUT
            
            # Extract ticker from parentheses (e.g., "AMAZON.COM INC (AMZN) - CALL")
            ticker_match = re.search(r'\(([A-Z]{1,5})\)', line)
            if ticker_match:
                ticker = ticker_match.group(1)
                # Extract company name (everything before the ticker)
                asset_name = line[:ticker_match.start()].strip()
                return asset_name, ticker, option_type
        
        # Handle regular stocks/ETFs
        # Look for patterns like "APPLE INC" or "SPY ETF"
        asset_match = re.search(r'\b([A-Z]{2,}(?:\s+[A-Z]{2,})*)\b', line)
        if asset_match:
            asset_name = asset_match.group(1).strip()
            # Try to extract ticker if present
            ticker_match = re.search(r'\(([A-Z]{1,5})\)', line)
            ticker = ticker_match.group(1) if ticker_match else None
            return asset_name, ticker, TradeType.STOCK
        
        return None
    
    def _extract_amount_range(self, line: str) -> str:
        """Extract amount range, handling various formats."""
        # Pattern 1: $1,001-$15,000
        amount_match = re.search(r'\$([0-9,]+)-?\$?([0-9,]+)?', line)
        if amount_match:
            if amount_match.group(2):
                return f"${amount_match.group(1)}-${amount_match.group(2)}"
            else:
                return f"${amount_match.group(1)}"
        
        # Pattern 2: Over $1,000,000
        over_match = re.search(r'Over\s+\$([0-9,]+)', line)
        if over_match:
            return f"Over ${over_match.group(1)}"
        
        # Pattern 3: Under $1,001
        under_match = re.search(r'Under\s+\$([0-9,]+)', line)
        if under_match:
            return f"Under ${under_match.group(1)}"
        
        # Pattern 4: $1,001 to $15,000 (with "to" instead of "-")
        to_match = re.search(r'\$([0-9,]+)\s+to\s+\$([0-9,]+)', line)
        if to_match:
            return f"${to_match.group(1)}-${to_match.group(2)}"
        
        return "Unknown"
    
    def _extract_transaction_date(self, line: str, all_lines: List[str], line_index: int) -> str:
        """Extract transaction date from the current line or nearby context."""
        # Look for MM/DD/YYYY patterns in current line
        date_match = re.search(r'\b(\d{1,2}/\d{1,2}/\d{4})\b', line)
        if date_match:
            return date_match.group(1)
        
        # Look in nearby lines for transaction date
        for i in range(max(0, line_index-2), min(len(all_lines), line_index+3)):
            nearby_line = all_lines[i]
            date_match = re.search(r'\b(\d{1,2}/\d{1,2}/\d{4})\b', nearby_line)
            if date_match:
                return date_match.group(1)
        
        return "Unknown"
    
    def _extract_filing_date(self, all_lines: List[str]) -> str:
        """Extract filing date from document header or metadata."""
        for line in all_lines[:10]:  # Check first 10 lines for header info
            if any(keyword in line.upper() for keyword in ['FILING DATE', 'DATE FILED', 'REPORT DATE']):
                date_match = re.search(r'\b(\d{1,2}/\d{1,2}/\d{4})\b', line)
                if date_match:
                    return date_match.group(1)
        
        return "Unknown"
    
    def format_trade_for_display(self, trade: Dict) -> str:
        """Format a trade for display in logs or debugging."""
        ticker_info = f" ({trade['ticker']})" if trade.get('ticker') else ""
        
        return (f"{trade['action']} {trade['trade_type'].upper()} - "
                f"{trade['asset_name']}{ticker_info} - "
                f"{trade['amount_range']} - {trade['transaction_date']}")
