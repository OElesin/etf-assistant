"""
JustETF MCP Server
Provides European UCITS ETF data access for AI agents via Model Context Protocol.

Transport modes:
  - stdio (default): For local MCP clients (Claude Desktop, Cursor, etc.)
  - streamable-http: For remote deployment on AWS Lambda with Web Adapter
    Set env var MCP_TRANSPORT=streamable-http to enable.
"""

import json
import logging
import os
from typing import Optional

from mcp.server.fastmcp import FastMCP

from src.etf_data import load_etf_universe

logger = logging.getLogger(__name__)

# Determine transport mode from environment
TRANSPORT = os.getenv("MCP_TRANSPORT", "stdio")

# Initialize FastMCP Server with settings appropriate for the transport
mcp = FastMCP(
    "JustETF-Assistant",
    host="0.0.0.0",
    port=8000,
    stateless_http=TRANSPORT == "streamable-http",
)


@mcp.tool()
def search_etfs(
    query: str = "",
    domicile: Optional[str] = None,
    accumulating_only: bool = False,
    max_ter: Optional[float] = None,
    min_aum: Optional[float] = None,
    limit: int = 15,
) -> str:
    """
    Search and filter the European UCITS ETF universe.

    Args:
        query: Search term matched against ETF Name, ISIN, or Ticker.
        domicile: Filter by domicile country (e.g., 'Ireland', 'Luxembourg').
        accumulating_only: If True, only returns accumulating ETFs (tax-efficient).
        max_ter: Maximum Total Expense Ratio (TER), e.g. 0.002 (0.20%).
        min_aum: Minimum fund size (Assets Under Management) in EUR millions.
        limit: Limit the number of search results returned (defaults to 15).
    """
    etfs = load_etf_universe()
    results = []

    query_lower = query.lower()
    for etf in etfs:
        if query and not (
            query_lower in etf.get("name", "").lower()
            or query_lower in etf.get("isin", "").lower()
            or query_lower in etf.get("ticker", "").lower()
        ):
            continue

        if domicile and etf.get("domicile", "").lower() != domicile.lower():
            continue

        if accumulating_only and not etf.get("is_accumulating", False):
            continue

        if max_ter is not None and etf.get("ter", 1.0) > max_ter:
            continue

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
    Returns a detailed breakdown of scoring factors relevant for EU investors.

    Args:
        isin: The ISIN of the ETF to analyze.
    """
    etfs = load_etf_universe()
    target_etf = None
    for etf in etfs:
        if etf.get("isin", "").upper() == isin.upper():
            target_etf = etf
            break

    if not target_etf:
        return json.dumps({"error": f"ETF with ISIN '{isin}' not found."}, indent=2)

    is_accumulating = target_etf.get("is_accumulating", False)
    domicile = target_etf.get("domicile", "")
    replication = target_etf.get("replication", "")
    ter = target_etf.get("ter", 0.0)
    aum = target_etf.get("aum", 0.0)

    breakdown = {
        "base_score": 0.5,
        "is_accumulating_bonus": 0.3 if is_accumulating else 0.0,
        "domicile_bonus": (
            0.2 if domicile == "Ireland" else (0.15 if domicile == "Luxembourg" else 0.0)
        ),
        "physical_replication_bonus": (
            0.1
            if ("physical" in replication.lower() or "full" in replication.lower())
            else 0.0
        ),
        "low_ter_bonus": 0.05 if ter < 0.002 else 0.0,
        "liquidity_size_bonus": 0.1 if aum > 1000 else (0.05 if aum > 100 else 0.0),
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
            "fund_size_m": aum,
        },
        "tax_implications_summary": (
            "Highly optimal for EU investors. Accumulating policy defers dividend taxation. "
            "Irish domicile optimizes withholding tax treaties."
            if total_score >= 0.85
            else (
                "Moderately optimal. Check domicile tax treaties or physical replication details."
                if total_score >= 0.65
                else "Low tax efficiency. Distributing dividends may trigger immediate tax liability depending on local jurisdiction."
            )
        ),
    }

    return json.dumps(analysis, indent=2)


@mcp.tool()
async def refresh_etf_data() -> str:
    """
    Trigger a scrape of JustETF to fetch fresh ETF data and update the local cache.
    This runs in the background and may take a few minutes to complete.
    """
    try:
        from src.scraper import ETFScraper

        scraper = ETFScraper()
        result = await scraper.scrape_and_save()
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"status": "failed", "error": str(e)}, indent=2)


@mcp.tool()
def generate_612_chart(
    tickers: list[str],
    inflation_rate: Optional[float] = None,
    render: bool = False,
) -> str:
    """
    Generate 6-week and 12-month ETF performance data with year-over-year comparison.

    Returns structured JSON with weekly/monthly returns, cumulative growth curves,
    and summary metrics including inflation-adjusted purchasing power.

    Use Yahoo Finance ticker symbols (e.g., VWCE.DE for Xetra-listed ETFs).

    Args:
        tickers: List of Yahoo Finance ticker symbols (e.g., ["VWCE.DE", "CSPX.L"]).
        inflation_rate: Annual inflation rate as decimal (e.g., 0.022 for 2.2%). Defaults to current Eurozone rate.
        render: If True, also includes a Plotly JSON spec ({data, layout}) for direct rendering.
    """
    try:
        from src.performance import fetch_performance_data, generate_plotly_spec

        kwargs = {}
        if inflation_rate is not None:
            kwargs["inflation_rate"] = inflation_rate

        data = fetch_performance_data(tickers, **kwargs)

        if render:
            data["plotly_spec"] = generate_plotly_spec(data)

        return json.dumps(data, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


if __name__ == "__main__":
    mcp.run(transport=TRANSPORT)
