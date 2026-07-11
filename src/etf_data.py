"""
ETF data loading and normalization.
Loads the ETF universe from local JSON cache files.
"""

import json
import logging
import os
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)

# Resolve data paths relative to the project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOCAL_PATHS = [
    PROJECT_ROOT / "output.json",
    PROJECT_ROOT / "demo.json",
]


def normalize_etf(etf: dict) -> dict:
    """Standardize raw JustETF data to a common model format."""
    # Already normalized
    if "is_accumulating" in etf:
        return etf

    # TER: "0.15%" -> 0.0015
    ter_raw = etf.get("ter", "0%")
    try:
        ter = float(str(ter_raw).replace("%", "").strip()) / 100.0
    except Exception:
        ter = 0.0

    # AUM in millions
    aum_raw = etf.get("fundSize", "0")
    try:
        aum = float(str(aum_raw).replace(",", "").strip())
    except Exception:
        aum = 0.0

    # Distribution policy
    policy = etf.get("distributionPolicy", "Accumulating")
    is_accumulating = "accumulating" in policy.lower()

    domicile = etf.get("domicileCountry", "Ireland")
    replication = etf.get("replicationMethod", "Full replication")

    # Tax efficiency score (heuristic)
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
        "quality_score": round(tax_efficiency_score * 0.9, 2),
    }


def load_etf_universe() -> List[dict]:
    """Load the ETF universe from local JSON cache files."""
    for path in LOCAL_PATHS:
        if path.exists():
            try:
                logger.info(f"Loading ETF data from {path}...")
                with open(path, "r") as f:
                    content = json.load(f)
                    data = content.get("data", []) if isinstance(content, dict) else content
                    return [normalize_etf(item) for item in data]
            except Exception as e:
                logger.error(f"Error loading {path}: {e}")

    logger.warning("No ETF data files found.")
    return []
