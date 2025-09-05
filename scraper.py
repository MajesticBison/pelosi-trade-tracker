import requests
from bs4 import BeautifulSoup
import re
from typing import List, Dict, Optional
import logging
from urllib.parse import urljoin, urlparse

class HouseClerkScraper:
    """Scraper for the U.S. House Clerk's financial disclosure site."""
    
    def __init__(self):
        self.base_url = "https://disclosures-clerk.house.gov"
        self.search_url = f"{self.base_url}/PublicDisclosure/FinancialDisclosure"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def search_pelosi_filings(self) -> List[Dict]:
        """
        Search for Nancy Pelosi's financial disclosure filings.
        Returns list of filing information.
        """
        try:
            self.logger.info("Searching for Nancy Pelosi filings...")
            
            # Search for Pelosi filings using the actual search form
            filings = []
            
            # Search in recent years (2020-2025) for Pelosi filings
            current_year = 2025
            for year in range(current_year, 2019, -1):  # Search 2025 down to 2020
                year_filings = self._search_pelosi_by_year(year)
                filings.extend(year_filings)
                
                # Limit to avoid overwhelming the server
                if len(filings) > 20:
                    break
            
            # Sort filings by filing ID (higher ID = newer filing)
            filings.sort(key=lambda x: int(x['filing_id']), reverse=True)
            
            self.logger.info(f"Found {len(filings)} Pelosi filings across years")
            return filings
            
        except requests.RequestException as e:
            self.logger.error(f"Error scraping House Clerk site: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error during scraping: {e}")
            return []
    
    def _search_pelosi_by_year(self, year: int) -> List[Dict]:
        """
        Search for Pelosi filings in a specific year using the search form.
        """
        try:
            self.logger.info(f"Searching for Pelosi filings in {year}")
            
            # Prepare search data
            search_data = {
                'LastName': 'Pelosi',
                'FilingYear': str(year),
                'State': 'CA'  # Pelosi is from California
            }
            
            # Submit search form
            search_url = f"{self.base_url}/FinancialDisclosure/ViewMemberSearchResult"
            response = self.session.post(search_url, data=search_data)
            response.raise_for_status()
            
            # Parse search results
            soup = BeautifulSoup(response.content, 'html.parser')
            filings = self._extract_filings_from_search_results(soup, year)
            
            self.logger.info(f"Found {len(filings)} filings for {year}")
            return filings
            
        except requests.RequestException as e:
            self.logger.error(f"Error searching for year {year}: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error searching year {year}: {e}")
            return []
    
    def _extract_filings_from_search_results(self, soup: BeautifulSoup, year: int) -> List[Dict]:
        """
        Extract filing information from search results page.
        """
        filings = []
        
        # Look for the search results table
        search_table = soup.find('table', class_='library-table')
        if not search_table:
            self.logger.warning(f"No search results table found for {year}")
            return filings
        
        # Extract rows from the table
        rows = search_table.find_all('tr')[1:]  # Skip header row
        self.logger.info(f"Found {len(rows)} filing rows for {year}")
        
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 4:  # Expect: Name, Office, Filing Year, Filing
                filing_info = self._extract_filing_from_table_row(cells, year)
                if filing_info:
                    filings.append(filing_info)
        
        return filings
    
    def _extract_filing_from_table_row(self, cells, year: int) -> Optional[Dict]:
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
                'name': pdf_link.get_text(strip=True)
            }
            
            self.logger.info(f"Extracted filing: {filing_id} - {filing_type} - {pdf_url}")
            return filing_info
            
        except Exception as e:
            self.logger.debug(f"Error extracting filing from row: {e}")
            return None
    
    def _generate_filing_id_from_url(self, pdf_url: str) -> str:
        """Generate a unique filing ID from the PDF URL."""
        # Extract the filename from the URL
        filename = pdf_url.split('/')[-1]
        # Remove .pdf extension
        filing_id = filename.replace('.pdf', '')
        return filing_id
    
    def _extract_filing_info_from_link(self, link, year: int) -> Optional[Dict]:
        """Extract filing information from a link element."""
        try:
            link_text = link.get_text(strip=True)
            
            # Generate filing ID
            filing_id = f"pelosi_{year}_{hash(link_text)}"
            
            return {
                'filing_id': filing_id,
                'filing_date': str(year),
                'link_text': link_text
            }
            
        except Exception as e:
            self.logger.debug(f"Error extracting filing info from link: {e}")
            return None
    
    def _extract_filing_info(self, link_element, soup: BeautifulSoup) -> Optional[Dict]:
        """Extract filing information from a link element."""
        try:
            href = link_element.get('href')
            if not href:
                return None
            
            # Make URL absolute
            pdf_url = urljoin(self.base_url, href)
            
            # Try to find filing date and ID from link text or nearby elements
            link_text = link_element.get_text(strip=True)
            
            # Look for date patterns
            date_match = re.search(r'\b(\d{1,2}/\d{1,2}/\d{4})\b', link_text)
            filing_date = date_match.group(1) if date_match else "Unknown"
            
            # Generate a filing ID from the URL
            filing_id = self._generate_filing_id(pdf_url)
            
            return {
                'filing_id': filing_id,
                'filing_date': filing_date,
                'pdf_url': pdf_url,
                'link_text': link_text
            }
            
        except Exception as e:
            self.logger.debug(f"Error extracting filing info: {e}")
            return None
    
    def _extract_filings_from_table(self, table) -> List[Dict]:
        """Extract filings from a table element."""
        filings = []
        
        try:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 3:  # Expect at least date, name, and link columns
                    filing_info = self._extract_filing_from_row(cells)
                    if filing_info:
                        filings.append(filing_info)
        except Exception as e:
            self.logger.debug(f"Error extracting from table: {e}")
        
        return filings
    
    def _extract_filing_from_row(self, cells) -> Optional[Dict]:
        """Extract filing information from a table row."""
        try:
            # This is a simplified approach - adjust based on actual table structure
            if len(cells) < 3:
                return None
            
            # Assume: Date | Name | Document Link | Other columns...
            date_cell = cells[0].get_text(strip=True)
            name_cell = cells[1].get_text(strip=True)
            link_cell = cells[2]
            
            # Check if this is a Pelosi filing
            if not self._is_pelosi_name(name_cell):
                return None
            
            # Look for PDF link
            link = link_cell.find('a', href=re.compile(r'\.pdf$', re.I))
            if not link:
                return None
            
            href = link.get('href')
            pdf_url = urljoin(self.base_url, href)
            
            # Extract date
            date_match = re.search(r'\b(\d{1,2}/\d{1,2}/\d{4})\b', date_cell)
            filing_date = date_match.group(1) if date_match else "Unknown"
            
            filing_id = self._generate_filing_id(pdf_url)
            
            return {
                'filing_id': filing_id,
                'filing_date': filing_date,
                'pdf_url': pdf_url,
                'name': name_cell
            }
            
        except Exception as e:
            self.logger.debug(f"Error extracting from row: {e}")
            return None
    
    def _is_pelosi_filing(self, filing: Dict) -> bool:
        """Check if a filing belongs to Nancy Pelosi."""
        # Check various name variations
        pelosi_variations = [
            'pelosi', 'nancy', 'nancy pelosi', 'pelosi, nancy',
            'pelosi, nancy p', 'nancy p. pelosi'
        ]
        
        # Check in link text
        link_text = filing.get('link_text', '').lower()
        if any(variation in link_text for variation in pelosi_variations):
            return True
        
        # Check in name field
        name = filing.get('name', '').lower()
        if any(variation in name for variation in pelosi_variations):
            return True
        
        return False
    
    def _is_pelosi_name(self, name: str) -> bool:
        """Check if a name matches Nancy Pelosi."""
        name_lower = name.lower()
        pelosi_variations = [
            'pelosi', 'nancy', 'nancy pelosi', 'pelosi, nancy',
            'pelosi, nancy p', 'nancy p. pelosi'
        ]
        return any(variation in name_lower for variation in pelosi_variations)
    
    def _generate_filing_id(self, pdf_url: str) -> str:
        """Generate a unique filing ID from the PDF URL."""
        # Extract filename from URL
        parsed_url = urlparse(pdf_url)
        filename = parsed_url.path.split('/')[-1]
        
        # Remove .pdf extension and clean up
        filing_id = filename.replace('.pdf', '').replace('.PDF', '')
        
        # If no meaningful ID, use URL hash
        if not filing_id or filing_id == '':
            filing_id = str(hash(pdf_url))
        
        return filing_id
    
    def download_pdf(self, pdf_url: str, save_path: str) -> bool:
        """Download a PDF file from the given URL."""
        try:
            self.logger.info(f"Downloading PDF: {pdf_url}")
            response = self.session.get(pdf_url, stream=True)
            response.raise_for_status()
            
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            self.logger.info(f"PDF downloaded successfully: {save_path}")
            return True
            
        except requests.RequestException as e:
            self.logger.error(f"Error downloading PDF {pdf_url}: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error downloading PDF: {e}")
            return False
