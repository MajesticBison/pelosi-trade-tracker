#!/usr/bin/env python3
"""
Multi-politician scraper for the U.S. House Clerk's financial disclosure site.
Supports tracking multiple politicians with individual configurations.
"""

import requests
from bs4 import BeautifulSoup
import re
from typing import List, Dict, Optional
import logging
from urllib.parse import urljoin, urlparse
from politicians_config import PoliticianConfig, get_all_active_politicians

class MultiPoliticianScraper:
    """Scraper for multiple politicians' financial disclosure filings."""
    
    def __init__(self):
        self.base_url = "https://disclosures-clerk.house.gov"
        self.search_url = f"{self.base_url}/PublicDisclosure/FinancialDisclosure"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
    
    def search_politician_filings(self, politician: PoliticianConfig) -> List[Dict]:
        """
        Search for a specific politician's financial disclosure filings.
        Returns list of filing information.
        """
        try:
            self.logger.info(f"Searching for {politician.full_name} filings...")
            
            filings = []
            
            # Search in recent years (2020-2025) for politician filings
            current_year = 2025
            for year in range(current_year, 2019, -1):  # Search 2025 down to 2020
                year_filings = self._search_politician_by_year(politician, year)
                filings.extend(year_filings)
                
                # Limit to avoid overwhelming the server
                if len(filings) > 20:
                    break
            
            # Sort filings by filing ID (higher ID = newer filing)
            filings.sort(key=lambda x: int(x['filing_id']), reverse=True)
            
            self.logger.info(f"Found {len(filings)} {politician.full_name} filings across years")
            return filings
            
        except requests.RequestException as e:
            self.logger.error(f"Network error searching for {politician.full_name}: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Error searching for {politician.full_name}: {e}")
            return []
    
    def _search_politician_by_year(self, politician: PoliticianConfig, year: int) -> List[Dict]:
        """Search for politician filings in a specific year."""
        try:
            self.logger.info(f"Searching for {politician.full_name} filings in {year}")
            
            # Extract last name from search name (e.g., "Pelosi, Nancy" -> "Pelosi")
            last_name = politician.search_name.split(',')[0].strip()
            
            # Prepare search data (same format as original scraper)
            search_data = {
                'LastName': last_name,
                'FilingYear': str(year),
                'State': politician.state
            }
            
            # Submit search form
            search_url = f"{self.base_url}/FinancialDisclosure/ViewMemberSearchResult"
            response = self.session.post(search_url, data=search_data)
            response.raise_for_status()
            
            # Parse search results
            soup = BeautifulSoup(response.content, 'html.parser')
            return self._extract_filings_from_search_results(soup, politician, year)
            
        except requests.RequestException as e:
            self.logger.error(f"Network error searching {politician.full_name} in {year}: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Error searching {politician.full_name} in {year}: {e}")
            return []
    
    def _extract_filings_from_search_results(self, soup: BeautifulSoup, politician: PoliticianConfig, year: int) -> List[Dict]:
        """Extract filing information from search results page."""
        filings = []
        
        # Look for the search results table (same as original scraper)
        search_table = soup.find('table', class_='library-table')
        if not search_table:
            self.logger.warning(f"No search results table found for {politician.full_name} in {year}")
            return filings
        
        # Extract rows from the table
        rows = search_table.find_all('tr')[1:]  # Skip header row
        self.logger.info(f"Found {len(rows)} filing rows for {politician.full_name} in {year}")
        
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 4:  # Expect: Name, Office, Filing Year, Filing
                filing_info = self._extract_filing_from_table_row(cells, politician, year)
                if filing_info:
                    filings.append(filing_info)
        
        return filings
    
    def _extract_filing_from_table_row(self, cells, politician: PoliticianConfig, year: int) -> Optional[Dict]:
        """Extract filing information from a table row."""
        try:
            # Extract data from cells
            name_cell = cells[0]
            office_cell = cells[1]
            filing_year_cell = cells[2]
            filing_type_cell = cells[3]
            
            # Get the PDF link from the name cell
            pdf_link = name_cell.find('a')
            if not pdf_link:
                return None
            
            href = pdf_link.get('href')
            if not href:
                return None
            
            # Make URL absolute
            pdf_url = urljoin(self.base_url, href)
            
            # Extract filing type and determine if it's a PTR
            filing_type = filing_type_cell.get_text(strip=True)
            is_ptr = 'PTR' in filing_type.upper()
            
            # Generate unique filing ID from the PDF URL
            filing_id = self._generate_filing_id_from_url(pdf_url)
            
            filing_info = {
                'filing_id': filing_id,
                'pdf_url': pdf_url,
                'filing_date': str(year),
                'filing_type': filing_type,
                'is_ptr': is_ptr,
                'office': office_cell.get_text(strip=True),
                'politician_name': politician.name,
                'politician_full_name': politician.full_name,
                'year': year
            }
            
            self.logger.info(f"Extracted filing: {filing_id} - {filing_type} - {pdf_url}")
            return filing_info
            
        except Exception as e:
            self.logger.error(f"Error extracting filing from table row: {e}")
            return None
    
    def _generate_filing_id_from_url(self, pdf_url: str) -> str:
        """Generate a unique filing ID from the PDF URL."""
        # Extract the filename from the URL and use it as the filing ID
        # e.g., "https://...ptr-pdfs/2025/20026590.pdf" -> "20026590"
        import re
        match = re.search(r'/(\d+)\.pdf$', pdf_url)
        if match:
            return match.group(1)
        
        # Fallback: use the full URL hash
        import hashlib
        return hashlib.md5(pdf_url.encode()).hexdigest()[:8]
    
    def search_all_active_politicians(self) -> Dict[str, List[Dict]]:
        """
        Search for filings from all active politicians.
        Returns a dictionary mapping politician names to their filings.
        """
        active_politicians = get_all_active_politicians()
        all_filings = {}
        
        self.logger.info(f"Searching {len(active_politicians)} active politicians...")
        
        for politician in active_politicians:
            self.logger.info(f"Processing {politician.full_name}...")
            filings = self.search_politician_filings(politician)
            all_filings[politician.name] = filings
            
            # Add a small delay between politicians to be respectful
            import time
            time.sleep(1)
        
        total_filings = sum(len(filings) for filings in all_filings.values())
        self.logger.info(f"Found {total_filings} total filings across all politicians")
        
        return all_filings
    
    def download_pdf(self, pdf_url: str, filename: str) -> bool:
        """
        Download a PDF file from the given URL.
        Returns True if successful, False otherwise.
        """
        try:
            self.logger.info(f"Downloading PDF: {pdf_url}")
            
            response = self.session.get(pdf_url, stream=True)
            response.raise_for_status()
            
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            self.logger.info(f"PDF downloaded successfully: {filename}")
            return True
            
        except requests.RequestException as e:
            self.logger.error(f"Network error downloading PDF {pdf_url}: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error downloading PDF {pdf_url}: {e}")
            return False

# Backward compatibility - create a wrapper for the old Pelosi-specific scraper
class HouseClerkScraper:
    """Backward compatibility wrapper for the original Pelosi scraper."""
    
    def __init__(self):
        self.multi_scraper = MultiPoliticianScraper()
        self.logger = logging.getLogger(__name__)
    
    def search_pelosi_filings(self) -> List[Dict]:
        """Search for Pelosi filings (backward compatibility)."""
        from politicians_config import get_politician_config
        
        pelosi_config = get_politician_config("pelosi")
        if not pelosi_config:
            self.logger.error("Pelosi configuration not found")
            return []
        
        filings = self.multi_scraper.search_politician_filings(pelosi_config)
        
        # Convert to old format for backward compatibility
        old_format_filings = []
        for filing in filings:
            old_format_filing = {
                'filing_id': filing['filing_id'],
                'filing_type': filing['filing_type'],
                'filing_date': filing['filing_date'],
                'pdf_url': filing['pdf_url']
            }
            old_format_filings.append(old_format_filing)
        
        return old_format_filings
    
    def download_pdf(self, pdf_url: str, filename: str) -> bool:
        """Download PDF (backward compatibility)."""
        return self.multi_scraper.download_pdf(pdf_url, filename)

if __name__ == "__main__":
    # Test the multi-politician scraper
    scraper = MultiPoliticianScraper()
    
    print("Testing multi-politician scraper...")
    all_filings = scraper.search_all_active_politicians()
    
    for politician_name, filings in all_filings.items():
        print(f"\n{politician_name}: {len(filings)} filings")
        for filing in filings[:3]:  # Show first 3 filings
            print(f"  {filing['filing_id']} - {filing['filing_type']} - {filing['filing_date']}")
