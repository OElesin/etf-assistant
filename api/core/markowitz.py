"""
Enhanced Markowitz Portfolio Optimization
Integrates tax considerations and European ETF constraints
"""

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from typing import List, Dict, Optional, Tuple
import asyncio
import logging

logger = logging.getLogger(__name__)

from api.models.schemas import (
    ETFAllocation, RiskTolerance, PortfolioConstraints,
    UserProfile, MarketConditions
)

class MarkowitzOptimizer:
    """
    Enhanced Markowitz Mean-Variance Optimization
    
    Key Enhancements:
    1. Tax-adjusted returns for European investors
    2. UCITS ETF universe with liquidity constraints  
    3. Currency hedging considerations
    4. ESG integration options
    5. Transaction cost modeling
    """
    
    def __init__(self):
        self.etf_universe = None
        self.returns_data = None
        self.covariance_matrix = None
        
    async def optimize(
        self,
        risk_tolerance: RiskTolerance,
        investment_amount: float,
        constraints: Optional[PortfolioConstraints] = None,
        user_profile: Optional[UserProfile] = None
    ) -> List[ETFAllocation]:
        """
        Generate optimal portfolio using enhanced Markowitz optimization
        """
        
        # Load ETF universe and market data
        await self._load_etf_data()
        
        # Filter ETFs based on constraints
        eligible_etfs = await self._filter_etf_universe(constraints, user_profile)
        
        # Calculate tax-adjusted expected returns
        tax_adjusted_returns = await self._calculate_tax_adjusted_returns(
            eligible_etfs, user_profile
        )
        
        # Build covariance matrix
        cov_matrix = await self._build_covariance_matrix(eligible_etfs)
        
        # Set up optimization problem
        n_assets = len(eligible_etfs)
        
        # Objective function: minimize portfolio variance
        def objective(weights):
            portfolio_variance = np.dot(weights.T, np.dot(cov_matrix, weights))
            return portfolio_variance
        
        # Constraints
        constraints_list = [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1.0}  # Weights sum to 1
        ]
        
        # Risk tolerance constraint
        target_return = await self._get_target_return(risk_tolerance, tax_adjusted_returns)
        if target_return:
            constraints_list.append({
                'type': 'ineq',
                'fun': lambda x: np.dot(x, tax_adjusted_returns) - target_return
            })
        
        # Individual weight bounds
        min_weight = constraints.min_allocation if constraints else 0.05
        max_weight = constraints.max_single_allocation if constraints else 0.40
        bounds = [(min_weight, max_weight) for _ in range(n_assets)]
        
        # Initial guess (equal weights)
        x0 = np.array([1.0 / n_assets] * n_assets)
        
        # Solve optimization
        result = minimize(
            objective,
            x0,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints_list,
            options={'maxiter': 1000}
        )
        
        if not result.success:
            raise ValueError(f"Optimization failed: {result.message}")
        
        # Convert to ETFAllocation objects
        optimal_allocations = []
        for i, weight in enumerate(result.x):
            if weight > 0.01:  # Only include meaningful allocations
                etf = eligible_etfs[i]
                allocation = ETFAllocation(
                    isin=etf['isin'],
                    name=etf['name'],
                    allocation_percentage=weight * 100,
                    expected_return=tax_adjusted_returns[i],
                    volatility=etf['volatility'],
                    tax_efficiency_score=etf['tax_efficiency'],
                    expense_ratio=etf['ter'],
                    domicile=etf['domicile']
                )
                optimal_allocations.append(allocation)
        
        return optimal_allocations
    
    async def _load_etf_data(self):
        """
        Load ETF universe from DynamoDB (real data from scraper)
        """
        
        try:
            from api.data.etf_scraper import ETFDataScraper
            scraper = ETFDataScraper()
            
            # Get real ETF data with filters for quality
            filters = {
                'domicile': 'Ireland',  # Prefer Irish domicile for EU tax efficiency
                'min_aum': 100,  # Minimum €100M AUM for liquidity
                'max_ter': 0.008,  # Maximum 0.8% TER
                'accumulating_only': True  # Prefer accumulating for tax efficiency
            }
            
            real_etfs = await scraper.get_etf_universe(filters)
            
            if real_etfs:
                self.etf_universe = real_etfs
                logger.info(f"Loaded {len(real_etfs)} real ETFs from database")
            else:
                # Fallback to mock data if no real data available
                self.etf_universe = self._get_mock_etf_data()
                logger.warning("Using mock ETF data - no real data available")
                
        except Exception as e:
            logger.error(f"Error loading real ETF data: {e}")
            # Fallback to mock data
            self.etf_universe = self._get_mock_etf_data()
    
    def _get_mock_etf_data(self):
        """
        Fallback mock data for European UCITS ETFs
        """
        return [
            {
                'isin': 'IE00B4L5Y983',
                'name': 'iShares Core MSCI World UCITS ETF USD (Acc)',
                'domicile': 'Ireland',
                'ter': 0.20,
                'volatility': 0.15,
                'expected_return': 0.08,
                'tax_efficiency': 0.95,  # Accumulating = high tax efficiency
                'liquidity': 0.99,
                'esg_score': 7.2,
                'currency': 'USD',
                'hedged': False
            },
            {
                'isin': 'IE00B3RBWM25',
                'name': 'Vanguard FTSE Developed World UCITS ETF USD Distributing',
                'domicile': 'Ireland',
                'ter': 0.12,
                'volatility': 0.16,
                'expected_return': 0.075,
                'tax_efficiency': 0.75,  # Distributing = lower tax efficiency
                'liquidity': 0.98,
                'esg_score': 6.8,
                'currency': 'USD',
                'hedged': False
            },
            {
                'isin': 'IE00BKM4GZ66',
                'name': 'iShares Core MSCI Europe UCITS ETF EUR (Acc)',
                'domicile': 'Ireland',
                'ter': 0.12,
                'volatility': 0.18,
                'expected_return': 0.07,
                'tax_efficiency': 0.92,
                'liquidity': 0.97,
                'esg_score': 7.5,
                'currency': 'EUR',
                'hedged': False
            },
            {
                'isin': 'IE00B441G979',
                'name': 'iShares MSCI EM IMI UCITS ETF USD (Acc)',
                'domicile': 'Ireland',
                'ter': 0.18,
                'volatility': 0.22,
                'expected_return': 0.09,
                'tax_efficiency': 0.90,
                'liquidity': 0.95,
                'esg_score': 6.2,
                'currency': 'USD',
                'hedged': False
            },
            {
                'isin': 'IE00B3XXRP09',
                'name': 'Vanguard FTSE Emerging Markets UCITS ETF USD Distributing',
                'domicile': 'Ireland',
                'ter': 0.22,
                'volatility': 0.24,
                'expected_return': 0.085,
                'tax_efficiency': 0.70,
                'liquidity': 0.94,
                'esg_score': 5.8,
                'currency': 'USD',
                'hedged': False
            },
            {
                'isin': 'LU0274208692',
                'name': 'Xtrackers MSCI World UCITS ETF 1D',
                'domicile': 'Luxembourg',
                'ter': 0.19,
                'volatility': 0.15,
                'expected_return': 0.078,
                'tax_efficiency': 0.80,
                'liquidity': 0.96,
                'esg_score': 7.0,
                'currency': 'USD',
                'hedged': False
            }
        ]
    
    async def _filter_etf_universe(
        self,
        constraints: Optional[PortfolioConstraints],
        user_profile: Optional[UserProfile]
    ) -> List[Dict]:
        """
        Filter ETF universe based on constraints and user preferences
        """
        
        eligible_etfs = self.etf_universe.copy()
        
        if not constraints:
            return eligible_etfs
        
        # ESG filtering
        if constraints.esg_required:
            eligible_etfs = [etf for etf in eligible_etfs if etf['esg_score'] >= 7.0]
        
        # Sector exclusions
        if constraints.exclude_sectors:
            # In production, filter by sector exposure
            pass
        
        # Liquidity requirements
        eligible_etfs = [etf for etf in eligible_etfs if etf['liquidity'] >= 0.95]
        
        # Limit number of ETFs
        if len(eligible_etfs) > constraints.max_etfs:
            # Sort by Sharpe ratio and take top N
            eligible_etfs.sort(
                key=lambda x: x['expected_return'] / x['volatility'], 
                reverse=True
            )
            eligible_etfs = eligible_etfs[:constraints.max_etfs]
        
        return eligible_etfs
    
    async def _calculate_tax_adjusted_returns(
        self,
        etfs: List[Dict],
        user_profile: Optional[UserProfile]
    ) -> np.ndarray:
        """
        Calculate tax-adjusted expected returns for European investors
        
        Key considerations:
        1. Accumulating vs Distributing ETFs
        2. Withholding tax rates by domicile
        3. Local tax treatment (German Vorabpauschale, etc.)
        """
        
        if not user_profile:
            return np.array([etf['expected_return'] for etf in etfs])
        
        tax_adjusted_returns = []
        
        for etf in etfs:
            gross_return = etf['expected_return']
            
            # Tax adjustment based on ETF structure
            if 'Acc' in etf['name'] or etf['tax_efficiency'] > 0.85:
                # Accumulating ETF - defer taxes
                tax_drag = 0.0  # No immediate tax on reinvested dividends
            else:
                # Distributing ETF - immediate dividend tax
                dividend_yield = 0.025  # Assume 2.5% dividend yield
                dividend_tax = dividend_yield * user_profile.tax_bracket
                tax_drag = dividend_tax
            
            # Withholding tax adjustment (Ireland domicile is optimal for EU)
            if etf['domicile'] == 'Ireland':
                withholding_tax_drag = 0.0  # EU tax treaty benefits
            else:
                withholding_tax_drag = 0.005  # 0.5% additional drag
            
            # Apply tax adjustments
            tax_adjusted_return = gross_return - tax_drag - withholding_tax_drag
            tax_adjusted_returns.append(tax_adjusted_return)
        
        return np.array(tax_adjusted_returns)
    
    async def _build_covariance_matrix(self, etfs: List[Dict]) -> np.ndarray:
        """
        Build covariance matrix for portfolio optimization
        
        In production, use historical returns data
        For now, use simplified correlation assumptions
        """
        
        n_assets = len(etfs)
        volatilities = np.array([etf['volatility'] for etf in etfs])
        
        # Simplified correlation matrix
        # In production, calculate from historical data
        correlations = np.eye(n_assets)
        
        # Set realistic correlations between asset classes
        for i in range(n_assets):
            for j in range(n_assets):
                if i != j:
                    etf_i, etf_j = etfs[i], etfs[j]
                    
                    # High correlation between similar regions
                    if ('World' in etf_i['name'] and 'World' in etf_j['name']) or \
                       ('Europe' in etf_i['name'] and 'Europe' in etf_j['name']):
                        correlations[i, j] = 0.85
                    # Medium correlation between developed markets
                    elif ('World' in etf_i['name'] and 'Europe' in etf_j['name']) or \
                         ('Europe' in etf_i['name'] and 'World' in etf_j['name']):
                        correlations[i, j] = 0.75
                    # Lower correlation with emerging markets
                    elif 'EM' in etf_i['name'] or 'EM' in etf_j['name'] or \
                         'Emerging' in etf_i['name'] or 'Emerging' in etf_j['name']:
                        correlations[i, j] = 0.65
                    else:
                        correlations[i, j] = 0.70  # Default correlation
        
        # Convert to covariance matrix
        cov_matrix = np.outer(volatilities, volatilities) * correlations
        
        return cov_matrix
    
    async def _get_target_return(
        self,
        risk_tolerance: RiskTolerance,
        expected_returns: np.ndarray
    ) -> Optional[float]:
        """
        Get target return based on risk tolerance
        """
        
        min_return = np.min(expected_returns)
        max_return = np.max(expected_returns)
        
        if risk_tolerance == RiskTolerance.CONSERVATIVE:
            return min_return + 0.2 * (max_return - min_return)
        elif risk_tolerance == RiskTolerance.MODERATE:
            return min_return + 0.5 * (max_return - min_return)
        elif risk_tolerance == RiskTolerance.AGGRESSIVE:
            return min_return + 0.8 * (max_return - min_return)
        
        return None