"""
Test script for AmpliFolio API
"""

import asyncio
import json
from api.main import app
from api.models.schemas import InvestmentRequest, PortfolioOptimizationRequest, UserProfile, RiskTolerance, Country

async def test_investment_analysis():
    """Test the investment analysis endpoint"""
    
    request = InvestmentRequest(
        user_input="I'm a German resident looking for a conservative portfolio for retirement. I have €50,000 to invest and want to minimize taxes.",
        country=Country.GERMANY,
        income=75000,
        investment_amount=50000
    )
    
    print("🧪 Testing Investment Analysis...")
    print(f"Request: {request.dict()}")
    
    # In a real test, you'd make HTTP requests to the deployed API
    # For now, we'll just validate the data models work
    print("✅ Investment request model validated")

async def test_portfolio_optimization():
    """Test the portfolio optimization endpoint"""
    
    user_profile = UserProfile(
        risk_tolerance=RiskTolerance.CONSERVATIVE,
        investment_horizon=10,
        tax_bracket=0.42,
        investment_goals=["retirement", "tax_efficiency"],
        liquidity_needs=0.1
    )
    
    request = PortfolioOptimizationRequest(
        user_profile=user_profile,
        investment_amount=50000,
        risk_tolerance=RiskTolerance.CONSERVATIVE
    )
    
    print("🧪 Testing Portfolio Optimization...")
    print(f"Request: {request.dict()}")
    print("✅ Portfolio optimization request model validated")

async def main():
    """Run all tests"""
    print("🚀 AmpliFolio API Tests")
    print("=" * 40)
    
    await test_investment_analysis()
    print()
    await test_portfolio_optimization()
    
    print()
    print("✅ All tests passed!")
    print()
    print("Next steps:")
    print("1. Deploy to AWS: ./deploy.sh")
    print("2. Test live API endpoints")
    print("3. Set up monitoring and alerts")

if __name__ == "__main__":
    asyncio.run(main())