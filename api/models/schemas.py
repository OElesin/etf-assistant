"""
Pydantic models for API request/response schemas
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Union
from datetime import datetime
from enum import Enum

class Country(str, Enum):
    GERMANY = "DE"
    FRANCE = "FR"
    NETHERLANDS = "NL"
    BELGIUM = "BE"
    LUXEMBOURG = "LU"

class RiskTolerance(str, Enum):
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"

class InvestmentRequest(BaseModel):
    user_input: str = Field(..., description="Natural language investment goals")
    country: Country
    income: Optional[float] = Field(None, description="Annual income in EUR")
    investment_amount: float = Field(..., description="Amount to invest in EUR")
    
class UserProfile(BaseModel):
    risk_tolerance: RiskTolerance
    investment_horizon: int = Field(..., description="Investment horizon in years")
    tax_bracket: float = Field(..., description="Marginal tax rate")
    investment_goals: List[str]
    liquidity_needs: float = Field(default=0.1, description="Required liquidity %")

class TaxAnalysis(BaseModel):
    marginal_tax_rate: float
    capital_gains_rate: float
    dividend_tax_rate: float
    optimal_etf_structure: str  # "accumulating" or "distributing"
    projected_tax_savings: float
    withholding_tax_optimization: Dict[str, float]

class AIInsight(BaseModel):
    category: str  # "risk", "tax", "allocation", "timing"
    insight: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    impact_score: float = Field(..., ge=0.0, le=10.0)

class InvestmentAnalysis(BaseModel):
    user_profile: UserProfile
    tax_analysis: TaxAnalysis
    ai_insights: List[AIInsight]
    timestamp: datetime

class ETFAllocation(BaseModel):
    isin: str
    name: str
    allocation_percentage: float = Field(..., ge=0.0, le=100.0)
    expected_return: float
    volatility: float
    tax_efficiency_score: float = Field(..., ge=0.0, le=1.0)
    expense_ratio: float
    domicile: str
    
class RiskMetrics(BaseModel):
    portfolio_volatility: float
    sharpe_ratio: float
    max_drawdown: float
    var_95: float  # Value at Risk 95%
    beta: float

class PortfolioConstraints(BaseModel):
    max_etfs: int = Field(default=8, description="Maximum number of ETFs")
    min_allocation: float = Field(default=0.05, description="Minimum allocation per ETF")
    max_single_allocation: float = Field(default=0.4, description="Maximum single ETF allocation")
    exclude_sectors: Optional[List[str]] = None
    esg_required: bool = Field(default=False)

class PortfolioOptimizationRequest(BaseModel):
    user_profile: UserProfile
    investment_amount: float
    risk_tolerance: RiskTolerance
    constraints: Optional[PortfolioConstraints] = None

class OptimizedPortfolio(BaseModel):
    allocations: List[ETFAllocation]
    expected_return: float = Field(..., description="Annual expected return")
    risk_metrics: RiskMetrics
    tax_efficiency_score: float = Field(..., ge=0.0, le=1.0)
    ai_explanation: str = Field(..., description="AI-generated portfolio explanation")
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    rebalancing_frequency: str = Field(default="quarterly")
    
class MarketConditions(BaseModel):
    volatility_regime: str  # "low", "medium", "high"
    interest_rate_environment: str  # "rising", "falling", "stable"
    economic_cycle: str  # "expansion", "contraction", "recovery"
    geopolitical_risk: float = Field(..., ge=0.0, le=1.0)

class RLState(BaseModel):
    """State representation for RL agent"""
    market_conditions: MarketConditions
    user_profile: UserProfile
    current_allocations: List[ETFAllocation]
    performance_history: Dict[str, float]
    
class RLAction(BaseModel):
    """Action space for RL agent"""
    rebalance_weights: Dict[str, float]  # ISIN -> new weight
    add_etfs: Optional[List[str]] = None  # New ISINs to add
    remove_etfs: Optional[List[str]] = None  # ISINs to remove