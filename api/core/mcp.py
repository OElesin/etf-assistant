"""
Model Context Protocol (MCP) Server for JustETF Data Access
Allows agentic AI models to search, filter, and score European UCITS ETFs.
"""

from mcp.server.fastmcp import FastMCP
import json
import os
import boto3
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

# Initialize FastMCP Server
mcp = FastMCP("JustETF-Assistant")

# Environment & Table Configuration
STAGE = os.getenv("STAGE", "dev")
TABLE_NAME = f"etf-data-{STAGE}"
LOCAL_PATHS = ["output.json", "demo.json"]

def get_dynamodb_table():
    """Returns the DynamoDB Table resource if available."""
    try:
        # Check if AWS credentials exist/are configured
        session = boto3.Session()
        if session.get_credentials():
            dynamodb = boto3.resource("dynamodb", region_name=os.getenv("AWS_REGION", "eu-west-1"))
            # Test if table exists
            table = dynamodb.Table(TABLE_NAME)
            table.table_status
            return table
    except Exception as e:
        logger.warning(f"DynamoDB is not available: {e}")
    return None

def normalize_etf(etf: dict) -> dict:
    """Standardizes raw JustETF search output keys to a common model format."""
    # If it is already normalized by the scraping pipeline, return as is
    if "is_accumulating" in etf:
        return etf

    # Normalize TER (e.g. "0.15%" -> 0.0015)
    ter_raw = etf.get("ter", "0%")
    try:
        ter = float(str(ter_raw).replace("%", "").strip()) / 100.0
    except Exception:
        ter = 0.0

    # Normalize AUM (fundSize in millions, e.g. "1500" -> 1500.0)
    aum_raw = etf.get("fundSize", "0")
    try:
        aum = float(str(aum_raw).replace(",", "").strip())
    except Exception:
        aum = 0.0

    # Normalize distribution policy & accumulating status
    policy = etf.get("distributionPolicy", "Accumulating")
    is_accumulating = "accumulating" in policy.lower()

    # Domicile country
    domicile = etf.get("domicileCountry", "Ireland")

    # Replication method
    replication = etf.get("replicationMethod", "Full replication")

    # Calculate Tax Efficiency Score
    score = 0.5
    if is_accumulating:
        score += 0.3
    if domicile == "Ireland":
        score += 0.2
    elif domicile == "Luxembourg":
        score += 0.15
    if "physical" in replication.lower() or "full" in replication.lower():
        score += 0.1
    if aum > 1000:
        score += 0.1
    elif aum > 100:
        score += 0.05
    tax_efficiency_score = min(score, 1.0)

    return {
        "isin": etf.get("isin", ""),
        "name": etf.get("name", ""),
        "ter": ter,
        "domicile": domicile,
        "aum": aum,
        "is_accumulating": is_accumulating,
        "replication": replication,
        "distribution_policy": policy,
        "currency": etf.get("fundCurrency", ""),
        "ticker": etf.get("ticker", ""),
        "tax_efficiency_score": tax_efficiency_score,
        "quality_score": round(tax_efficiency_score * 0.9, 2)
    }

def load_etf_universe() -> List[dict]:
    """Loads ETF universe from DynamoDB or falls back to local JSON cache."""
    # 1. Try DynamoDB
    table = get_dynamodb_table()
    if table:
        try:
            logger.info(f"Scanning DynamoDB Table {TABLE_NAME}...")
            response = table.scan()
            items = response.get("Items", [])
            # Handle pagination in DynamoDB scans
            while "LastEvaluatedKey" in response:
                response = table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
                items.extend(response.get("Items", []))
            if items:
                return [normalize_etf(item) for item in items]
        except Exception as e:
            logger.error(f"Error scanning DynamoDB Table: {e}")

    # 2. Fallback to local files
    for path in LOCAL_PATHS:
        if os.path.exists(path):
            try:
                logger.info(f"Loading local ETF cache from {path}...")
                with open(path, "r") as f:
                    content = json.load(f)
                    data = content.get("data", []) if isinstance(content, dict) else content
                    return [normalize_etf(item) for item in data]
            except Exception as e:
                logger.error(f"Error loading {path}: {e}")
                
    return []

@mcp.tool()
def search_etfs(
    query: str = "",
    domicile: Optional[str] = None,
    accumulating_only: bool = False,
    max_ter: Optional[float] = None,
    min_aum: Optional[float] = None,
    limit: int = 15
) -> str:
    """
    Search and filter the European UCITS ETF universe.

    Args:
        query: Search term matched against ETF Name, ISIN, or Ticker.
        domicile: Filter by domicile country (e.g., 'Ireland', 'Luxembourg').
        accumulating_only: If True, only returns accumulating ETFs (tax-efficient).
        max_ter: Maximum Total Expense Ratio (TER), e.g. 0.002 (0.20%).
        min_aum: Minimum fund size (Assets Under Management) in EUR Millions.
        limit: Limit the number of search results returned (defaults to 15).
    """
    etfs = load_etf_universe()
    results = []
    
    query_lower = query.lower()
    for etf in etfs:
        # Match text query
        if query and not (
            query_lower in etf.get("name", "").lower() or 
            query_lower in etf.get("isin", "").lower() or 
            query_lower in etf.get("ticker", "").lower()
        ):
            continue
            
        # Filter by domicile
        if domicile and etf.get("domicile", "").lower() != domicile.lower():
            continue
            
        # Filter by distribution policy
        if accumulating_only and not etf.get("is_accumulating", False):
            continue
            
        # Filter by TER
        if max_ter is not None and etf.get("ter", 1.0) > max_ter:
            continue
            
        # Filter by AUM
        if min_aum is not None and etf.get("aum", 0.0) < min_aum:
            continue
            
        results.append(etf)
        
    return json.dumps(results[:limit], indent=2)

@mcp.tool()
def get_etf_details(isin: str) -> str:
    """
    Retrieve comprehensive details for a specific ETF by its ISIN.

    Args:
        isin: The International Securities Identification Number (ISIN) of the ETF.
    """
    etfs = load_etf_universe()
    for etf in etfs:
        if etf.get("isin", "").upper() == isin.upper():
            return json.dumps(etf, indent=2)
    return json.dumps({"error": f"ETF with ISIN '{isin}' not found."}, indent=2)

@mcp.tool()
def calculate_tax_efficiency(isin: str) -> str:
    """
    Calculate and analyze the tax efficiency score for a given ETF.

    Args:
        isin: The ISIN of the ETF.
    """
    etfs = load_etf_universe()
    target_etf = None
    for etf in etfs:
        if etf.get("isin", "").upper() == isin.upper():
            target_etf = etf
            break
            
    if not target_etf:
        return json.dumps({"error": f"ETF with ISIN '{isin}' not found."}, indent=2)

    # Re-verify points breakdown
    is_accumulating = target_etf.get("is_accumulating", False)
    domicile = target_etf.get("domicile", "")
    replication = target_etf.get("replication", "")
    ter = target_etf.get("ter", 0.0)
    aum = target_etf.get("aum", 0.0)
    
    breakdown = {
        "base_score": 0.5,
        "is_accumulating_bonus": 0.3 if is_accumulating else 0.0,
        "domicile_bonus": 0.2 if domicile == "Ireland" else (0.15 if domicile == "Luxembourg" else 0.0),
        "physical_replication_bonus": 0.1 if ("physical" in replication.lower() or "full" in replication.lower()) else 0.0,
        "low_ter_bonus": 0.05 if ter < 0.002 else 0.0,
        "liquidity_size_bonus": 0.1 if aum > 1000 else (0.05 if aum > 100 else 0.0)
    }
    
    total_score = min(sum(breakdown.values()), 1.0)
    
    analysis = {
        "isin": isin,
        "name": target_etf.get("name"),
        "total_tax_efficiency_score": round(total_score, 2),
        "score_breakdown": breakdown,
        "details": {
            "domicile": domicile,
            "distribution_policy": target_etf.get("distribution_policy"),
            "replication_method": replication,
            "total_expense_ratio": f"{ter * 100:.2f}%",
            "fund_size_m": aum
        },
        "tax_implications_summary": (
            "Highly optimal for EU investors. Accumulating policy defers dividend taxation. "
            "Irish domicile optimizes withholding tax treaties." if total_score >= 0.85 else
            "Moderately optimal. Check domicile tax treaties or physical replication details." if total_score >= 0.65 else
            "Low tax efficiency. Distributing dividends may trigger immediate tax liability depending on local jurisdiction."
        )
    }
    
    return json.dumps(analysis, indent=2)

@mcp.tool()
async def trigger_scraper() -> str:
    """
    Trigger a manual background run of the ETF scraper to fetch fresh data from JustETF.
    Note: This process runs asynchronously and takes some time to complete.
    """
    try:
        from api.data.etf_scraper import ETFDataScraper
        scraper = ETFDataScraper()
        
        # Run scraping asynchronously
        import asyncio
        asyncio.create_task(scraper.scrape_justetf_data())
        return json.dumps({"status": "initiated", "message": "Scraper job started in the background."}, indent=2)
    except Exception as e:
        return json.dumps({"status": "failed", "error": str(e)}, indent=2)

if __name__ == "__main__":
    mcp.run()
