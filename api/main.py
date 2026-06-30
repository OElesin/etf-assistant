"""
AmpliFolio API - Tax-Optimized Portfolio Generation
FastAPI backend with Agentic AI and Reinforcement Learning
"""

from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import uvicorn
from datetime import datetime

from api.agents.tax_optimizer import TaxOptimizerAgent
from api.agents.portfolio_agent import PortfolioAgent
from api.ml.reinforcement_learner import RLPortfolioOptimizer
from api.core.markowitz import MarkowitzOptimizer
from api.models.schemas import *

app = FastAPI(
    title="AmpliFolio API",
    description="Tax-Optimized ETF Portfolio Generation for European Investors",
    version="1.0.0"
)

# Mount MCP Server (Server-Sent Events endpoints under /mcp)
from api.core.mcp import mcp
app.mount("/mcp", mcp.get_fastapi_app())


# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://amplifolio.eu", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize AI agents
tax_agent = TaxOptimizerAgent()
portfolio_agent = PortfolioAgent()
rl_optimizer = RLPortfolioOptimizer()
markowitz = MarkowitzOptimizer()

@app.post("/api/v1/analyze-investment", response_model=InvestmentAnalysis)
async def analyze_investment(request: InvestmentRequest):
    """
    Analyze user's investment goals with Agentic AI
    Combines natural language processing with tax optimization
    """
    try:
        # Agentic AI layer - understand user intent
        user_profile = await tax_agent.analyze_user_profile(
            text=request.user_input,
            country=request.country,
            income=request.income
        )
        
        # Tax optimization analysis
        tax_analysis = await tax_agent.optimize_tax_strategy(user_profile)
        
        # Generate AI insights
        ai_insights = await portfolio_agent.generate_insights(
            user_profile, tax_analysis
        )
        
        return InvestmentAnalysis(
            user_profile=user_profile,
            tax_analysis=tax_analysis,
            ai_insights=ai_insights,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/optimize-portfolio", response_model=OptimizedPortfolio)
async def optimize_portfolio(request: PortfolioOptimizationRequest):
    """
    Generate tax-optimized portfolio using RL + Markowitz
    """
    try:
        # Step 1: Markowitz baseline optimization
        markowitz_portfolio = await markowitz.optimize(
            risk_tolerance=request.risk_tolerance,
            investment_amount=request.investment_amount,
            constraints=request.constraints
        )
        
        # Step 2: RL enhancement for tax efficiency
        market_conditions = await get_market_conditions()
        rl_enhanced_portfolio = await rl_optimizer.enhance_portfolio(
            base_portfolio=markowitz_portfolio,
            user_profile=request.user_profile,
            market_conditions=market_conditions
        )
        
        # Step 3: Agentic AI explanation
        ai_explanation = await portfolio_agent.explain_portfolio(
            portfolio=rl_enhanced_portfolio,
            user_context=request.user_profile
        )
        
        return OptimizedPortfolio(
            allocations=rl_enhanced_portfolio.allocations,
            expected_return=rl_enhanced_portfolio.expected_return,
            risk_metrics=rl_enhanced_portfolio.risk_metrics,
            tax_efficiency_score=rl_enhanced_portfolio.tax_efficiency,
            ai_explanation=ai_explanation,
            confidence_score=rl_enhanced_portfolio.confidence
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/tax-documents/{country}/{portfolio_id}")
async def generate_tax_documents(country: str, portfolio_id: str):
    """
    Generate country-specific tax reporting documents
    """
    try:
        documents = await tax_agent.generate_tax_documents(
            country=country,
            portfolio_id=portfolio_id
        )
        return {"documents": documents}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/etf-data/status")
async def get_etf_data_status():
    """
    Get status of ETF data pipeline and available ETFs
    """
    try:
        from api.data.etf_scraper import ETFDataScraper
        scraper = ETFDataScraper()
        
        # Get ETF universe stats
        etfs = await scraper.get_etf_universe()
        
        # Calculate stats
        total_etfs = len(etfs)
        accumulating_count = sum(1 for etf in etfs if etf.get('is_accumulating', False))
        irish_domicile_count = sum(1 for etf in etfs if etf.get('domicile') == 'Ireland')
        
        # Get latest update time
        latest_update = None
        if etfs:
            latest_update = max(etf.get('updated_at', '') for etf in etfs)
        
        return {
            "status": "healthy" if total_etfs > 50 else "degraded",
            "total_etfs": total_etfs,
            "accumulating_etfs": accumulating_count,
            "irish_domicile_etfs": irish_domicile_count,
            "latest_update": latest_update,
            "data_sources": ["JustETF", "Morningstar", "iShares", "Vanguard"],
            "update_frequency": "daily"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/etf-data/search")
async def search_etfs(
    query: Optional[str] = None,
    domicile: Optional[str] = None,
    min_aum: Optional[float] = None,
    accumulating_only: Optional[bool] = None,
    limit: int = 20
):
    """
    Search ETF database with filters
    """
    try:
        from api.data.etf_scraper import ETFDataScraper
        scraper = ETFDataScraper()
        
        # Build filters
        filters = {}
        if domicile:
            filters['domicile'] = domicile
        if min_aum:
            filters['min_aum'] = min_aum
        if accumulating_only:
            filters['accumulating_only'] = accumulating_only
        
        # Get filtered ETFs
        etfs = await scraper.get_etf_universe(filters)
        
        # Text search if query provided
        if query:
            query_lower = query.lower()
            etfs = [etf for etf in etfs 
                   if query_lower in etf.get('name', '').lower() or 
                      query_lower in etf.get('isin', '').lower()]
        
        # Limit results
        etfs = etfs[:limit]
        
        # Return simplified data
        simplified_etfs = []
        for etf in etfs:
            simplified_etfs.append({
                'isin': etf.get('isin'),
                'name': etf.get('name'),
                'ter': etf.get('ter'),
                'domicile': etf.get('domicile'),
                'aum': etf.get('aum'),
                'is_accumulating': etf.get('is_accumulating'),
                'tax_efficiency_score': etf.get('tax_efficiency_score'),
                'quality_score': etf.get('quality_score')
            })
        
        return {
            "etfs": simplified_etfs,
            "total_found": len(simplified_etfs),
            "filters_applied": filters
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def get_market_conditions() -> MarketConditions:
    """
    Get current market conditions for RL optimization
    In production, this would fetch real market data
    """
    return MarketConditions(
        volatility_regime="medium",
        interest_rate_environment="rising",
        economic_cycle="expansion",
        geopolitical_risk=0.3
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)