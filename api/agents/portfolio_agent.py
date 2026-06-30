"""
Portfolio Agent for generating AI insights and explanations
"""

import boto3
import json
from typing import List, Dict
from api.models.schemas import UserProfile, TaxAnalysis, AIInsight, ETFAllocation

class PortfolioAgent:
    def __init__(self):
        self.bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
        self.model_id = "amazon.nova-pro-v1:0"
    
    async def generate_insights(
        self, 
        user_profile: UserProfile, 
        tax_analysis: TaxAnalysis
    ) -> List[AIInsight]:
        """
        Generate AI insights about the user's investment profile and tax situation
        """
        
        prompt = f"""
        As a European investment advisor, analyze this profile and provide 4 key insights:
        
        Profile:
        - Risk Tolerance: {user_profile.risk_tolerance}
        - Investment Horizon: {user_profile.investment_horizon} years
        - Tax Bracket: {user_profile.tax_bracket}
        - Goals: {user_profile.investment_goals}
        
        Tax Analysis:
        - Optimal Structure: {tax_analysis.optimal_etf_structure}
        - Projected Savings: €{tax_analysis.projected_tax_savings}
        
        Provide insights on:
        1. Risk management strategy
        2. Tax optimization opportunities  
        3. Asset allocation recommendations
        4. Timing considerations
        
        Return JSON array with insights, each having:
        - category: "risk", "tax", "allocation", or "timing"
        - insight: detailed explanation (2-3 sentences)
        - confidence: 0.0-1.0
        - impact_score: 0.0-10.0 (potential impact on returns)
        """
        
        response = await self._call_bedrock(prompt)
        insights_data = json.loads(response)
        
        return [
            AIInsight(
                category=insight["category"],
                insight=insight["insight"],
                confidence=insight["confidence"],
                impact_score=insight["impact_score"]
            )
            for insight in insights_data
        ]
    
    async def explain_portfolio(
        self,
        portfolio: List[ETFAllocation],
        user_context: UserProfile
    ) -> str:
        """
        Generate human-readable explanation of the optimized portfolio
        """
        
        # Prepare portfolio summary
        portfolio_summary = []
        for allocation in portfolio:
            portfolio_summary.append({
                "name": allocation.name,
                "allocation": allocation.allocation_percentage,
                "tax_efficiency": allocation.tax_efficiency_score,
                "expense_ratio": allocation.expense_ratio
            })
        
        prompt = f"""
        As a European investment advisor, explain this optimized portfolio to the client:
        
        Client Profile:
        - Risk Tolerance: {user_context.risk_tolerance}
        - Investment Horizon: {user_context.investment_horizon} years
        - Tax Bracket: {user_context.tax_bracket}
        
        Portfolio Allocations:
        {json.dumps(portfolio_summary, indent=2)}
        
        Provide a clear, engaging explanation covering:
        1. Why these specific ETFs were chosen
        2. How the allocation matches their risk profile
        3. Tax efficiency benefits
        4. Expected performance and risks
        5. Rebalancing recommendations
        
        Write in a conversational tone, avoiding jargon. Focus on the benefits and rationale.
        Maximum 300 words.
        """
        
        explanation = await self._call_bedrock(prompt)
        return explanation
    
    async def _call_bedrock(self, prompt: str) -> str:
        """
        Call Amazon Bedrock Nova model
        """
        
        body = {
            "messages": [
                {
                    "role": "user",
                    "content": [{"text": prompt}]
                }
            ],
            "inferenceConfig": {
                "maxTokens": 1500,
                "temperature": 0.3,
                "topP": 0.9
            }
        }
        
        response = self.bedrock.invoke_model(
            modelId=self.model_id,
            body=json.dumps(body)
        )
        
        result = json.loads(response['body'].read())
        return result['output']['message']['content'][0]['text']