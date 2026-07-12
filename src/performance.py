"""
ETF Performance Data — 6-week and 12-month return calculations.
Fetches price history from Yahoo Finance and computes weekly/monthly returns,
cumulative growth, and year-over-year comparisons.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import yfinance as yf

logger = logging.getLogger(__name__)

# Eurozone inflation rate (annualized) — update periodically
DEFAULT_INFLATION_RATE = 0.022  # 2.2% as of mid-2026


def fetch_performance_data(
    tickers: List[str],
    inflation_rate: float = DEFAULT_INFLATION_RATE,
) -> Dict:
    """
    Fetch 6-week and 12-month performance data for a list of tickers.
    Returns structured JSON matching the generate_612_chart schema.
    """
    today = datetime.now().date()
    ticker_results = []

    for ticker_symbol in tickers:
        try:
            result = _compute_ticker_performance(ticker_symbol, today, inflation_rate)
            if result:
                ticker_results.append(result)
        except Exception as e:
            logger.error(f"Error computing performance for {ticker_symbol}: {e}")
            ticker_results.append({
                "ticker": ticker_symbol,
                "error": str(e),
            })

    return {
        "reference_date": today.isoformat(),
        "inflation_rate": inflation_rate,
        "tickers": ticker_results,
    }


def _compute_ticker_performance(
    ticker_symbol: str, reference_date, inflation_rate: float
) -> Optional[Dict]:
    """Compute full performance metrics for a single ticker."""
    ticker = yf.Ticker(ticker_symbol)

    # Fetch ~14 months of daily data (need prior year for YoY)
    hist = ticker.history(period="14mo")
    if hist.empty or len(hist) < 60:
        return {"ticker": ticker_symbol, "error": "Insufficient price history"}

    # Get ticker name
    info = ticker.info
    name = info.get("shortName") or info.get("longName") or ticker_symbol

    # Weekly returns (Friday-to-Friday)
    weekly = hist["Close"].resample("W-FRI").last().dropna()
    weekly_returns = weekly.pct_change().dropna() * 100  # percentage

    # Monthly returns (month-end)
    monthly = hist["Close"].resample("ME").last().dropna()
    monthly_returns = monthly.pct_change().dropna() * 100  # percentage

    # --- 6-week data ---
    six_week_returns = _get_six_week_data(weekly, weekly_returns)

    # --- 12-month data ---
    twelve_month_returns = _get_twelve_month_data(monthly, monthly_returns)

    # --- Summary metrics ---
    summary = _compute_summary(
        weekly_returns, monthly_returns, weekly, monthly, inflation_rate
    )

    # --- Cumulative growth ---
    cumulative = _compute_cumulative(weekly, monthly, inflation_rate)

    return {
        "ticker": ticker_symbol,
        "name": name,
        "summary": summary,
        "returns": {
            "six_weeks": six_week_returns,
            "twelve_months": twelve_month_returns,
        },
        "cumulative": cumulative,
    }


def _get_six_week_data(weekly, weekly_returns) -> Dict:
    """Get the last 6 weeks of returns + prior year equivalent."""
    # Current 6 weeks
    current_6w = weekly_returns.tail(6)
    x_labels = [f"W{d.isocalendar()[1]}" for d in current_6w.index]
    current_values = [round(v, 2) for v in current_6w.values]

    # Prior year same weeks (offset by ~52 weeks)
    prior_year_values = []
    for date in current_6w.index:
        target = date - timedelta(weeks=52)
        # Find closest available week
        closest_idx = weekly_returns.index.get_indexer([target], method="nearest")
        if closest_idx[0] >= 0 and closest_idx[0] < len(weekly_returns):
            prior_year_values.append(round(weekly_returns.iloc[closest_idx[0]], 2))
        else:
            prior_year_values.append(0.0)

    return {
        "x_labels": x_labels,
        "current": current_values,
        "prior_year": prior_year_values,
    }


def _get_twelve_month_data(monthly, monthly_returns) -> Dict:
    """Get the last 12 months of returns + prior year equivalent."""
    current_12m = monthly_returns.tail(12)
    x_labels = [d.strftime("%b'%y") for d in current_12m.index]
    current_values = [round(v, 2) for v in current_12m.values]

    # Prior year same months
    prior_year_values = []
    for date in current_12m.index:
        target = date - timedelta(days=365)
        closest_idx = monthly_returns.index.get_indexer([target], method="nearest")
        if closest_idx[0] >= 0 and closest_idx[0] < len(monthly_returns):
            prior_year_values.append(round(monthly_returns.iloc[closest_idx[0]], 2))
        else:
            prior_year_values.append(0.0)

    return {
        "x_labels": x_labels,
        "current": current_values,
        "prior_year": prior_year_values,
    }


def _compute_summary(weekly_returns, monthly_returns, weekly, monthly, inflation_rate) -> Dict:
    """Compute summary statistics."""
    # Last week return
    last_week_return = round(float(weekly_returns.iloc[-1]), 2) if len(weekly_returns) > 0 else 0.0

    # 6-week average return
    six_week_avg = round(float(weekly_returns.tail(6).mean()), 2) if len(weekly_returns) >= 6 else 0.0

    # 6-week avg YoY delta (current 6-week avg minus prior year 6-week avg)
    if len(weekly_returns) >= 58:  # 6 + 52
        prior_6w_avg = float(weekly_returns.iloc[-58:-52].mean())
        six_week_yoy_delta = round(six_week_avg - prior_6w_avg, 2)
    else:
        six_week_yoy_delta = 0.0

    # Trailing 12-month (TTM) return
    if len(monthly) >= 13:
        ttm_return = round(
            (float(monthly.iloc[-1]) / float(monthly.iloc[-13]) - 1) * 100, 2
        )
    else:
        ttm_return = 0.0

    # TTM YoY delta
    if len(monthly) >= 25:
        prior_ttm = (float(monthly.iloc[-13]) / float(monthly.iloc[-25]) - 1) * 100
        ttm_yoy_delta = round(ttm_return - prior_ttm, 2)
    else:
        ttm_yoy_delta = 0.0

    # Cumulative 6-week growth
    if len(weekly) >= 7:
        cumulative_6w = round(float(weekly.iloc[-1]) / float(weekly.iloc[-7]) * 100, 2)
    else:
        cumulative_6w = 100.0

    # Cumulative 12-month growth
    if len(monthly) >= 13:
        cumulative_12m = round(float(monthly.iloc[-1]) / float(monthly.iloc[-13]) * 100, 2)
    else:
        cumulative_12m = 100.0

    # Inflation comparison (weekly = annualized / 52, monthly over 12m)
    weekly_inflation = inflation_rate / 52 * 100
    beats_inflation_6w = six_week_avg > weekly_inflation
    beats_inflation_12m = ttm_return > (inflation_rate * 100)

    return {
        "last_week_return": last_week_return,
        "six_week_avg_return": six_week_avg,
        "six_week_yoy_delta_pp": six_week_yoy_delta,
        "ttm_return": ttm_return,
        "ttm_yoy_delta_pp": ttm_yoy_delta,
        "cumulative_6w": cumulative_6w,
        "cumulative_12m": cumulative_12m,
        "beats_inflation_6w": beats_inflation_6w,
        "beats_inflation_12m": beats_inflation_12m,
    }


def _compute_cumulative(weekly, monthly, inflation_rate) -> Dict:
    """Compute cumulative growth curves normalized to 100."""
    result = {}

    # 6-week cumulative (7 data points: start + 6 weeks)
    if len(weekly) >= 7:
        recent_7w = weekly.tail(7)
        base = float(recent_7w.iloc[0])
        current_cumulative = [round(float(v) / base * 100, 2) for v in recent_7w.values]
        x_labels_6w = [f"W{d.isocalendar()[1]}" for d in recent_7w.index]

        # Prior year equivalent
        prior_start_idx = max(0, len(weekly) - 7 - 52)
        prior_end_idx = prior_start_idx + 7
        if prior_end_idx <= len(weekly):
            prior_7w = weekly.iloc[prior_start_idx:prior_end_idx]
            prior_base = float(prior_7w.iloc[0])
            prior_cumulative = [round(float(v) / prior_base * 100, 2) for v in prior_7w.values]
        else:
            prior_cumulative = [100.0] * 7

        # Purchasing power erosion (weekly inflation)
        weekly_inflation_factor = (1 + inflation_rate) ** (1 / 52)
        purchasing_power = [round(100.0 / (weekly_inflation_factor ** i), 2) for i in range(7)]

        result["six_weeks"] = {
            "x_labels": x_labels_6w,
            "current": current_cumulative,
            "prior_year": prior_cumulative,
            "purchasing_power": purchasing_power,
        }

    # 12-month cumulative (13 data points: start + 12 months)
    if len(monthly) >= 13:
        recent_13m = monthly.tail(13)
        base = float(recent_13m.iloc[0])
        current_cumulative = [round(float(v) / base * 100, 2) for v in recent_13m.values]
        x_labels_12m = [d.strftime("%b'%y") for d in recent_13m.index]

        # Prior year equivalent
        prior_start_idx = max(0, len(monthly) - 25)
        prior_end_idx = prior_start_idx + 13
        if prior_end_idx <= len(monthly):
            prior_13m = monthly.iloc[prior_start_idx:prior_end_idx]
            prior_base = float(prior_13m.iloc[0])
            prior_cumulative = [round(float(v) / prior_base * 100, 2) for v in prior_13m.values]
        else:
            prior_cumulative = [100.0] * 13

        # Purchasing power erosion (monthly inflation)
        monthly_inflation_factor = (1 + inflation_rate) ** (1 / 12)
        purchasing_power = [round(100.0 / (monthly_inflation_factor ** i), 2) for i in range(13)]

        result["twelve_months"] = {
            "x_labels": x_labels_12m,
            "current": current_cumulative,
            "prior_year": prior_cumulative,
            "purchasing_power": purchasing_power,
        }

    return result


def generate_plotly_spec(data: Dict) -> Dict:
    """
    Generate a Plotly JSON spec ({data, layout}) for the 612 chart.
    This is the raw spec that Plotly.js can consume directly with Plotly.newPlot().
    """
    figures = []

    for ticker_data in data.get("tickers", []):
        if "error" in ticker_data:
            continue

        ticker = ticker_data["ticker"]
        name = ticker_data.get("name", ticker)
        cumulative = ticker_data.get("cumulative", {})

        # 6-week cumulative chart
        if "six_weeks" in cumulative:
            six_w = cumulative["six_weeks"]
            figures.append({
                "title": f"{name} — 6-Week Cumulative Growth",
                "data": [
                    {"x": six_w["x_labels"], "y": six_w["current"], "name": "Current", "type": "scatter", "mode": "lines+markers"},
                    {"x": six_w["x_labels"], "y": six_w["prior_year"], "name": "Prior Year", "type": "scatter", "mode": "lines+markers", "line": {"dash": "dash"}},
                    {"x": six_w["x_labels"], "y": six_w["purchasing_power"], "name": "Purchasing Power", "type": "scatter", "mode": "lines", "line": {"dash": "dot", "color": "red"}},
                ],
                "layout": {"yaxis": {"title": "Growth (base=100)"}, "template": "plotly_white"},
            })

        # 12-month cumulative chart
        if "twelve_months" in cumulative:
            twelve_m = cumulative["twelve_months"]
            figures.append({
                "title": f"{name} — 12-Month Cumulative Growth",
                "data": [
                    {"x": twelve_m["x_labels"], "y": twelve_m["current"], "name": "Current", "type": "scatter", "mode": "lines+markers"},
                    {"x": twelve_m["x_labels"], "y": twelve_m["prior_year"], "name": "Prior Year", "type": "scatter", "mode": "lines+markers", "line": {"dash": "dash"}},
                    {"x": twelve_m["x_labels"], "y": twelve_m["purchasing_power"], "name": "Purchasing Power", "type": "scatter", "mode": "lines", "line": {"dash": "dot", "color": "red"}},
                ],
                "layout": {"yaxis": {"title": "Growth (base=100)"}, "template": "plotly_white"},
            })

    return {"figures": figures}
