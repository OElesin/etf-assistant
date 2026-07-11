"""
ETF Scraper for European UCITS ETFs.
Fetches data from JustETF and saves to local JSON cache.
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import aiohttp
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = PROJECT_ROOT / "output.json"


class ETFScraper:
    """Scrapes ETF data from JustETF and stores it locally."""

    def __init__(self):
        self.request_delay = 2  # seconds between requests
        self.max_retries = 3
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }

    async def scrape_and_save(self) -> Dict:
        """Run a full scrape and save results to output.json."""
        start = time.time()
        etfs = await self.scrape_justetf_data()
        duration = time.time() - start

        # Save to local cache
        output = {
            "data": etfs,
            "metadata": {
                "scraped_at": datetime.utcnow().isoformat(),
                "count": len(etfs),
                "duration_seconds": round(duration, 1),
            },
        }

        OUTPUT_PATH.write_text(json.dumps(output, indent=2))
        logger.info(f"Saved {len(etfs)} ETFs to {OUTPUT_PATH}")

        return {
            "status": "completed",
            "etf_count": len(etfs),
            "duration_seconds": round(duration, 1),
            "output_path": str(OUTPUT_PATH),
        }

    async def scrape_justetf_data(self) -> List[Dict]:
        """Scrape ETF data from JustETF.com search pages."""
        etfs: List[Dict] = []

        search_urls = [
            "https://www.justetf.com/en/find-etf.html?assetClass=class-equity&groupField=index&sortField=ter&sortOrder=asc",
            "https://www.justetf.com/en/find-etf.html?assetClass=class-bonds&groupField=index&sortField=ter&sortOrder=asc",
            "https://www.justetf.com/en/find-etf.html?assetClass=class-commodities&groupField=index&sortField=ter&sortOrder=asc",
        ]

        async with aiohttp.ClientSession(headers=self.headers) as session:
            for url in search_urls:
                try:
                    page_etfs = await self._scrape_page(session, url)
                    etfs.extend(page_etfs)
                    await asyncio.sleep(self.request_delay)
                except Exception as e:
                    logger.error(f"Error scraping {url}: {e}")

        return etfs

    async def _scrape_page(self, session: aiohttp.ClientSession, url: str) -> List[Dict]:
        """Scrape a single JustETF search results page."""
        async with session.get(url) as response:
            if response.status != 200:
                logger.warning(f"Failed to fetch {url}: {response.status}")
                return []

            html = await response.text()
            soup = BeautifulSoup(html, "html.parser")

            etfs = []
            etf_rows = soup.find_all("tr", class_="etf")

            for row in etf_rows:
                try:
                    etf_data = self._parse_row(row)
                    if etf_data:
                        etfs.append(etf_data)
                except Exception as e:
                    logger.error(f"Error parsing ETF row: {e}")

            return etfs

    def _parse_row(self, row) -> Optional[Dict]:
        """Parse a single ETF row from JustETF search results."""
        name_cell = row.find("td", class_="name")
        if not name_cell:
            return None

        name = name_cell.find("a").text.strip()
        isin_cell = row.find("td", class_="isin")
        isin = isin_cell.text.strip() if isin_cell else None

        ter_cell = row.find("td", class_="ter")
        ter = None
        if ter_cell:
            try:
                ter = float(ter_cell.text.strip().replace("%", "")) / 100
            except ValueError:
                pass

        return {
            "isin": isin,
            "name": name,
            "ter": ter,
            "scraped_at": datetime.utcnow().isoformat(),
        }


if __name__ == "__main__":

    async def main():
        scraper = ETFScraper()
        result = await scraper.scrape_and_save()
        print(json.dumps(result, indent=2))

    asyncio.run(main())
