"""
Agentic AI Tax Optimizer using Amazon Bedrock Nova models
"""

import boto3
import json
from typing import Dict, List, Optional
from api.models.schemas import UserProfile, TaxAnalysis, Country

class TaxOptimizerAgent:
    def __init__(self):
        self.bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
        self.model_id = "amazon.nova-pro-v1:0"
        
        # EU tax knowledge base
        self.tax_rates = {
            "DE": {"income": 0.42, "capital_gains": 0.26375, "dividend": 0.26375},
            "FR": {"income": 0.45, "capital_gains": 0.30, "dividend": 0.30},
            "NL": {"income": 0.495, "capital_gains": 0.31, "dividend": 0.31},
            "BE": {"income": 0.50, "capital_gains": 0.33, "dividend": 0.30},
            "LU": {"income": 0.42, "capital_gains": 0.20, "dividend": 0.20}
        }
        
    async def analyze_user_profile(self, text: str, country: str, income: Optional[float]) -> UserProfile:
        """
        Use Agentic AI to extract investment profile from natural language
        """
        
        prompt = f"""
        You are a European tax-optimization expert. Analyze this investment request and extract:
        
        User Input: "{text}"
        Country: {country}
        Income: {income}
        
        Extract and return JSON with:
        1. risk_tolerance: "conservative", "moderate", or "aggressive"
        2. investment_horizon: years (integer)
        3. investment_goals: list of specific goals
        4. liquidity_needs: percentage (0.0-1.0)
        
        Consider European tax implications and cultural investment preferences.
        
        Return only valid JSON.
        """
        
        response = await self._call_bedrock(prompt)
        profile_data = json.loads(response)
        
        # Calculate tax bracket based on country and income
        tax_bracket = self._calculate_tax_bracket(country, income)
        
        return UserProfile(
            risk_tolerance=profile_data["risk_tolerance"],
            investment_horizon=profile_data["investment_horizon"],
            tax_bracket=tax_bracket,
            investment_goals=profile_data["investment_goals"],
            liquidity_needs=profile_data["liquidity_needs"]
        )
    
    async def optimize_tax_strategy(self, user_profile: UserProfile) -> TaxAnalysis:
        """
        Generate tax-optimized investment strategy using AI reasoning
        """
        
        country_code = self._get_country_from_profile(user_profile)
        tax_rates = self.tax_rates[country_code]
        
        prompt = f"""
        As a European tax optimization expert, analyze this profile:
        
        Tax Bracket: {user_profile.tax_bracket}
        Investment Horizon: {user_profile.investment_horizon} years
        Country Tax Rates: {tax_rates}
        
        Determine optimal ETF structure and provide reasoning:
        1. Should use accumulating or distributing ETFs?
        2. What's the projected annual tax savings?
        3. Optimal domicile (Ireland vs Luxembourg)?
        4. Withholding tax optimization strategies?
        
        Consider:
        - German Vorabpauschale rules
        - French PEA eligibility
        - EU tax treaties
        - Dividend withholding rates
        
        Return JSON with detailed tax analysis and reasoning.
        """
        
        response = await self._call_bedrock(prompt)
        tax_data = json.loads(response)
        
        return TaxAnalysis(
            marginal_tax_rate=user_profile.tax_bracket,
            capital_gains_rate=tax_rates["capital_gains"],
            dividend_tax_rate=tax_rates["dividend"],
            optimal_etf_structure=tax_data["optimal_structure"],
            projected_tax_savings=tax_data["projected_savings"],
            withholding_tax_optimization=tax_data["withholding_optimization"]
        )
    
    async def generate_tax_documents(self, country: str, portfolio_id: str) -> List[Dict]:
        """
        Generate country-specific tax reporting documents
        """
        
        document_templates = {
            "DE": ["steuerbescheinigung", "anlage_kap"],
            "FR": ["ifu", "declaration_revenus"],
            "NL": ["jaaropgaaf", "box3_declaration"],
            "BE": ["fiche_fiscale"],
            "LU": ["certificat_fiscal"]
        }
        
        documents = []
        for doc_type in document_templates.get(country, []):
            documents.append({
                "type": doc_type,
                "format": "pdf",
                "download_url": f"https://api.amplifolio.eu/documents/{portfolio_id}/{doc_type}.pdf",
                "generated_at": "2024-01-15T10:00:00Z"
            })
            
        return documents
    
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
                "maxTokens": 1000,
                "temperature": 0.1,
                "topP": 0.9
            }
        }
        
        response = self.bedrock.invoke_model(
            modelId=self.model_id,
            body=json.dumps(body)
        )
        
        result = json.loads(response['body'].read())
        return result['output']['message']['content'][0]['text']
    
    def _calculate_tax_bracket(self, country: str, income: Optional[float]) -> float:
        """
        Calculate marginal tax rate based on country and income
        """
        if not income:
            return self.tax_rates[country]["income"]
            
        # Simplified progressive tax calculation
        # In production, use actual tax brackets
        base_rate = self.tax_rates[country]["income"]
        
        if income > 100000:
            return min(base_rate + 0.05, 0.50)  # Higher earners
        elif income < 30000:
            return max(base_rate - 0.10, 0.20)  # Lower earners
        else:
            return base_rate
    
    def _get_country_from_profile(self, user_profile: UserProfile) -> str:
        """
        Extract country code from user profile
        In production, this would be passed explicitly
        """
        return "DE"  # Default to Germany for now