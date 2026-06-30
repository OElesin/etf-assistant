"""
ETF Data Scraper for European UCITS ETFs
Based on JustETF and other European data sources
"""

import asyncio
import aiohttp
import json
import boto3
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import pandas as pd
from bs4 import BeautifulSoup
import time
import logging

logger = logging.getLogger(__name__)

class ETFDataScraper:
    """
    Scrapes ETF data from multiple European sources:
    1. JustETF (primary source for European ETFs)
    2. Morningstar Europe
    3. ETF.com Europe
    4. Fund provider websites (iShares, Vanguard, etc.)
    """
    
    def __init__(self):
        self.s3 = boto3.client('s3')
        self.dynamodb = boto3.resource('dynamodb')
        self.etf_table = self.dynamodb.Table('etf-data-prod')
        
        # Rate limiting
        self.request_delay = 2  # seconds between requests
        self.max_retries = 3
        
        # Headers to avoid blocking
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }

    async def scrape_justetf_data(self) -> List[Dict]:
        """
        Scrape ETF data from JustETF.com
        Focus on European UCITS ETFs with tax efficiency data
        """
        
        etfs = []
        
        # JustETF search URLs for different categories
        search_urls = [
            "https://www.justetf.com/en/find-etf.html?assetClass=class-equity&groupField=index&sortField=ter&sortOrder=asc",
            "https://www.justetf.com/en/find-etf.html?assetClass=class-bonds&groupField=index&sortField=ter&sortOrder=asc",
            "https://www.justetf.com/en/find-etf.html?assetClass=class-commodities&groupField=index&sortField=ter&sortOrder=asc"
        ]
        
        async with aiohttp.ClientSession(headers=self.headers) as session:
            for url in search_urls:
                try:
                    etfs.extend(await self._scrape_justetf_page(session, url))
                    await asyncio.sleep(self.request_delay)
                except Exception as e:
                    logger.error(f"Error scraping {url}: {e}")
        
        return etfs

    async def _scrape_justetf_page(self, session: aiohttp.ClientSession, url: str) -> List[Dict]:
        """
        Scrape a single JustETF search results page
        """
        
        async with session.get(url) as response:
            if response.status != 200:
                logger.warning(f"Failed to fetch {url}: {response.status}")
                return []
            
            html = await response.text()
            soup = BeautifulSoup(html, 'html.parser')
            
            etfs = []
            
            # Find ETF table rows
            etf_rows = soup.find_all('tr', class_='etf')
            
            for row in etf_rows:
                try:
                    etf_data = await self._parse_justetf_row(session, row)
                    if etf_data:
                        etfs.append(etf_data)
                except Exception as e:
                    logger.error(f"Error parsing ETF row: {e}")
            
            return etfs

    async def _parse_justetf_row(self, session: aiohttp.ClientSession, row) -> Optional[Dict]:
        """
        Parse individual ETF row from JustETF table
        """
        
        try:
            # Extract basic info
            name_cell = row.find('td', class_='name')
            if not name_cell:
                return None
                
            name = name_cell.find('a').text.strip()
            etf_url = "https://www.justetf.com" + name_cell.find('a')['href']
            
            # Extract ISIN
            isin_cell = row.find('td', class_='isin')
            isin = isin_cell.text.strip() if isin_cell else None
            
            # Extract TER (Total Expense Ratio)
            ter_cell = row.find('td', class_='ter')
            ter = float(ter_cell.text.strip().replace('%', '')) / 100 if ter_cell else None
            
            # Get detailed data from ETF page
            detailed_data = await self._scrape_etf_details(session, etf_url, isin)
            
            etf_data = {
                'isin': isin,
                'name': name,
                'ter': ter,
                'source_url': etf_url,
                'scraped_at': datetime.utcnow().isoformat(),
                **detailed_data
            }
            
            return etf_data
            
        except Exception as e:
            logger.error(f"Error parsing ETF row: {e}")
            return None

    async def _scrape_etf_details(self, session: aiohttp.ClientSession, etf_url: str, isin: str) -> Dict:
        """
        Scrape detailed ETF information from individual ETF page
        """
        
        await asyncio.sleep(self.request_delay)  # Rate limiting
        
        try:
            async with session.get(etf_url) as response:
                if response.status != 200:
                    return {}
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                details = {}
                
                # Extract domicile
                domicile_elem = soup.find('span', string='Domicile')
                if domicile_elem:
                    details['domicile'] = domicile_elem.find_next('span').text.strip()
                
                # Extract replication method (important for tax efficiency)
                replication_elem = soup.find('span', string='Replication')
                if replication_elem:
                    details['replication'] = replication_elem.find_next('span').text.strip()
                
                # Extract distribution policy (Accumulating vs Distributing)
                distribution_elem = soup.find('span', string='Distribution policy')
                if distribution_elem:
                    policy = distribution_elem.find_next('span').text.strip()
                    details['distribution_policy'] = policy
                    details['is_accumulating'] = 'accumulating' in policy.lower()
                
                # Extract fund size (AUM)
                aum_elem = soup.find('span', string='Fund size')
                if aum_elem:
                    aum_text = aum_elem.find_next('span').text.strip()
                    details['aum'] = self._parse_aum(aum_text)
                
                # Extract performance data
                performance_data = await self._extract_performance_data(soup)
                details.update(performance_data)
                
                # Calculate tax efficiency score
                details['tax_efficiency_score'] = self._calculate_tax_efficiency(details)
                
                return details
                
        except Exception as e:
            logger.error(f"Error scraping ETF details for {isin}: {e}")
            return {}

    def _parse_aum(self, aum_text: str) -> Optional[float]:
        """
        Parse AUM text like "€1,234 m" to float in millions
        """
        try:
            # Remove currency symbols and spaces
            clean_text = aum_text.replace('€', '').replace('$', '').replace(',', '').strip()
            
            if 'm' in clean_text.lower():
                return float(clean_text.lower().replace('m', '').strip())
            elif 'bn' in clean_text.lower():
                return float(clean_text.lower().replace('bn', '').strip()) * 1000
            else:
                return float(clean_text)
        except:
            return None

    async def _extract_performance_data(self, soup: BeautifulSoup) -> Dict:
        """
        Extract historical performance data
        """
        
        performance = {}
        
        # Look for performance table
        perf_table = soup.find('table', class_='performance')
        if perf_table:
            rows = perf_table.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 2:
                    period = cells[0].text.strip()
                    return_pct = cells[1].text.strip()
                    
                    try:
                        return_val = float(return_pct.replace('%', '')) / 100
                        if '1 year' in period.lower():
                            performance['return_1y'] = return_val
                        elif '3 year' in period.lower():
                            performance['return_3y'] = return_val
                        elif '5 year' in period.lower():
                            performance['return_5y'] = return_val
                    except:
                        continue
        
        # Estimate volatility (in production, calculate from daily returns)
        if 'return_1y' in performance:
            # Rough estimate: equity ETFs ~15%, bond ETFs ~5%
            if performance['return_1y'] > 0.05:
                performance['volatility'] = 0.15  # Equity-like
            else:
                performance['volatility'] = 0.05  # Bond-like
        
        return performance

    def _calculate_tax_efficiency(self, etf_details: Dict) -> float:
        """
        Calculate tax efficiency score based on ETF characteristics
        """
        
        score = 0.5  # Base score
        
        # Accumulating ETFs are more tax efficient
        if etf_details.get('is_accumulating', False):
            score += 0.3
        
        # Irish domicile is optimal for EU investors
        if etf_details.get('domicile') == 'Ireland':
            score += 0.2
        
        # Physical replication is generally more tax efficient
        replication = etf_details.get('replication', '').lower()
        if 'physical' in replication or 'full' in replication:
            score += 0.1
        
        # Large funds have better liquidity and lower tracking error
        aum = etf_details.get('aum', 0)
        if aum > 1000:  # > €1bn
            score += 0.1
        elif aum > 100:  # > €100m
            score += 0.05
        
        return min(score, 1.0)  # Cap at 1.0

    async def scrape_alternative_sources(self) -> List[Dict]:
        """
        Scrape from alternative sources to complement JustETF data
        """
        
        etfs = []
        
        # Morningstar Europe ETF screener
        morningstar_data = await self._scrape_morningstar()
        etfs.extend(morningstar_data)
        
        # Direct from major providers
        ishares_data = await self._scrape_ishares_europe()
        etfs.extend(ishares_data)
        
        vanguard_data = await self._scrape_vanguard_europe()
        etfs.extend(vanguard_data)
        
        return etfs

    async def _scrape_morningstar(self) -> List[Dict]:
        """
        Scrape Morningstar Europe ETF data
        """
        # Implementation for Morningstar scraping
        # Similar pattern to JustETF but different selectors
        return []

    async def _scrape_ishares_europe(self) -> List[Dict]:
        """
        Scrape iShares Europe ETF data directly from BlackRock
        """
        # Implementation for iShares scraping
        return []

    async def _scrape_vanguard_europe(self) -> List[Dict]:
        """
        Scrape Vanguard Europe ETF data
        """
        # Implementation for Vanguard scraping
        return []

    async def store_etf_data(self, etfs: List[Dict]):
        """
        Store scraped ETF data in S3 and DynamoDB
        """
        
        timestamp = datetime.utcnow().isoformat()
        
        # Store raw data in S3
        s3_key = f"daily/{timestamp}.json"
        await self._store_to_s3(etfs, s3_key)
        
        # Store processed data in DynamoDB
        await self._store_to_dynamodb(etfs, timestamp)

    async def _store_to_s3(self, etfs: List[Dict], s3_key: str):
        """
        Store raw ETF data to S3
        """
        
        try:
            self.s3.put_object(
                Bucket='etf-data-prod',
                Key=s3_key,
                Body=json.dumps(etfs, indent=2),
                ContentType='application/json'
            )
            logger.info(f"Stored {len(etfs)} ETFs to S3: {s3_key}")
        except Exception as e:
            logger.error(f"Error storing to S3: {e}")

    async def _store_to_dynamodb(self, etfs: List[Dict], timestamp: str):
        """
        Store processed ETF data to DynamoDB
        """
        
        try:
            with self.etf_table.batch_writer() as batch:
                for etf in etfs:
                    if etf.get('isin'):
                        item = {
                            'isin': etf['isin'],
                            'updated_at': timestamp,
                            **etf
                        }
                        batch.put_item(Item=item)
            
            logger.info(f"Stored {len(etfs)} ETFs to DynamoDB")
        except Exception as e:
            logger.error(f"Error storing to DynamoDB: {e}")

    async def get_etf_universe(self, filters: Optional[Dict] = None) -> List[Dict]:
        """
        Get current ETF universe from DynamoDB with optional filters
        """
        
        try:
            # Scan table for latest ETF data
            response = self.etf_table.scan()
            etfs = response['Items']
            
            # Apply filters
            if filters:
                etfs = self._apply_filters(etfs, filters)
            
            return etfs
            
        except Exception as e:
            logger.error(f"Error fetching ETF universe: {e}")
            return []

    def _apply_filters(self, etfs: List[Dict], filters: Dict) -> List[Dict]:
        """
        Apply filters to ETF universe
        """
        
        filtered_etfs = etfs
        
        # Filter by domicile
        if 'domicile' in filters:
            filtered_etfs = [etf for etf in filtered_etfs 
                           if etf.get('domicile') == filters['domicile']]
        
        # Filter by minimum AUM
        if 'min_aum' in filters:
            filtered_etfs = [etf for etf in filtered_etfs 
                           if etf.get('aum', 0) >= filters['min_aum']]
        
        # Filter by accumulating only
        if filters.get('accumulating_only', False):
            filtered_etfs = [etf for etf in filtered_etfs 
                           if etf.get('is_accumulating', False)]
        
        # Filter by maximum TER
        if 'max_ter' in filters:
            filtered_etfs = [etf for etf in filtered_etfs 
                           if etf.get('ter', 1.0) <= filters['max_ter']]
        
        return filtered_etfs


# Lambda handler for scheduled scraping
async def handler(event, context):
    """
    AWS Lambda handler for daily ETF data scraping
    """
    
    scraper = ETFDataScraper()
    
    try:
        # Scrape from all sources
        logger.info("Starting ETF data scraping...")
        
        justetf_data = await scraper.scrape_justetf_data()
        logger.info(f"Scraped {len(justetf_data)} ETFs from JustETF")
        
        alternative_data = await scraper.scrape_alternative_sources()
        logger.info(f"Scraped {len(alternative_data)} ETFs from alternative sources")
        
        # Combine and deduplicate
        all_etfs = justetf_data + alternative_data
        unique_etfs = {etf['isin']: etf for etf in all_etfs if etf.get('isin')}.values()
        
        # Store data
        await scraper.store_etf_data(list(unique_etfs))
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'Successfully scraped and stored {len(unique_etfs)} ETFs',
                'timestamp': datetime.utcnow().isoformat()
            })
        }
        
    except Exception as e:
        logger.error(f"ETF scraping failed: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            })
        }


if __name__ == "__main__":
    # For local testing
    async def main():
        scraper = ETFDataScraper()
        etfs = await scraper.scrape_justetf_data()
        print(f"Scraped {len(etfs)} ETFs")
        for etf in etfs[:3]:  # Show first 3
            print(json.dumps(etf, indent=2))
    
    asyncio.run(main())