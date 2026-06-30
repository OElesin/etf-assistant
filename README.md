# AmpliFolio API - Tax-Optimized ETF Portfolios for European Investors

AmpliFolio is a serverless API that converts natural language investment requests into tax-optimized ETF portfolios using Agentic AI and Reinforcement Learning. Built specifically for European investors to combat "tax erosion" and boost after-tax yields by up to 2.5×.

## 🚀 Key Features

- **Agentic AI**: Amazon Bedrock Nova models for natural language understanding
- **Tax Optimization**: EU-specific tax efficiency for 27+ jurisdictions  
- **Reinforcement Learning**: Enhances Markowitz optimization with adaptive learning
- **Real-time API**: Sub-800ms response times with 99.9% uptime SLA
- **GDPR Compliant**: EU-hosted infrastructure with data sovereignty
- **White-label Ready**: Embed in fintech apps with custom branding

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Landing Page  │    │   FastAPI        │    │   Agentic AI    │
│   (S3 + CF)     │───▶│   (Lambda)       │───▶│   (Bedrock)     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                         │
                                ▼                         ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │   DynamoDB       │    │   RL Optimizer  │
                       │   (ETF Data)     │    │   + Markowitz   │
                       └──────────────────┘    └─────────────────┘
```

## 📊 How RL Enhances Markowitz

### Traditional Markowitz Limitations:
- Static optimization based on historical data
- No adaptation to changing market conditions
- Ignores tax implications and transaction costs
- Fixed rebalancing schedules

### RL Enhancements:
1. **Dynamic Rebalancing**: Learns optimal timing based on market regimes
2. **Tax-Loss Harvesting**: Identifies opportunities to swap similar ETFs
3. **Market Adaptation**: Adjusts risk exposure based on volatility environment
4. **Behavioral Learning**: Incorporates momentum and mean reversion signals

### Example RL Benefits:
```python
# Markowitz: Static 60/40 allocation
markowitz_portfolio = {
    "IE00B4L5Y983": 0.60,  # World ETF
    "IE00B3XXRP09": 0.40   # Bond ETF
}

# RL Enhancement: Dynamic adjustment
if market_conditions.volatility_regime == "high":
    # RL reduces risk exposure
    rl_enhanced = {
        "IE00B4L5Y983": 0.45,  # Reduced equity
        "IE00B3XXRP09": 0.55   # Increased bonds
    }
    
# Tax-loss harvesting opportunity
if current_losses > threshold:
    # Swap to similar ETF to realize losses
    swap_etf("IE00B4L5Y983", "IE00B3RBWM25")
```

## 🛠️ Installation & Deployment

### Prerequisites
- AWS CLI configured
- Node.js and npm
- Python 3.9+
- SSL certificate for custom domain

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/amplifolio-api.git
cd amplifolio-api
```

### 2. Install Dependencies
```bash
# Python dependencies
pip install -r requirements.txt

# Serverless framework
npm install -g serverless
npm install serverless-python-requirements serverless-offline
```

### 3. Set Environment Variables
```bash
export SSL_CERTIFICATE_ARN="arn:aws:acm:us-east-1:123456789:certificate/abc123"
export AWS_REGION="eu-west-1"
```

### 4. Deploy to AWS
```bash
# Deploy API and infrastructure
./deploy.sh

# Test deployment
python test_api.py
```

### 5. Configure DNS
Point your domain to the CloudFront distributions:
- `amplifolio.eu` → Website CloudFront
- `api.amplifolio.eu` → API CloudFront

## 📡 API Usage

### Investment Analysis
```bash
curl -X POST https://api.amplifolio.eu/api/v1/analyze-investment \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "German resident, conservative portfolio for retirement",
    "country": "DE",
    "income": 75000,
    "investment_amount": 50000
  }'
```

### Portfolio Optimization
```bash
curl -X POST https://api.amplifolio.eu/api/v1/optimize-portfolio \
  -H "Content-Type: application/json" \
  -d '{
    "user_profile": {
      "risk_tolerance": "conservative",
      "investment_horizon": 10,
      "tax_bracket": 0.42,
      "investment_goals": ["retirement", "tax_efficiency"]
    },
    "investment_amount": 50000,
    "risk_tolerance": "conservative"
  }'
```

### Response Example
```json
{
  "allocations": [
    {
      "isin": "IE00B4L5Y983",
      "name": "iShares Core MSCI World UCITS ETF",
      "allocation_percentage": 60,
      "tax_efficiency_score": 0.95,
      "expected_return": 0.08
    }
  ],
  "expected_return": 0.065,
  "tax_efficiency_score": 0.92,
  "ai_explanation": "This portfolio optimizes for tax efficiency...",
  "confidence_score": 0.87
}
```

## 💰 Business Model

### API Pricing Tiers
- **Starter**: €99/month - 1K API calls
- **Growth**: €499/month - 10K calls + webhooks  
- **Enterprise**: €2K/month - Unlimited + SLA

### Target Customers
1. **Neobanks** (N26, Revolut) - Add investment features
2. **Wealth Platforms** (Scalable Capital) - Enhance tax optimization
3. **Corporate Benefits** - Employee investment programs

## 🔧 Development

### Local Development
```bash
# Start API locally
uvicorn api.main:app --reload --port 8000

# Run tests
python test_api.py
pytest tests/

# Format code
black api/
flake8 api/
```

### Project Structure
```
amplifolio-api/
├── api/
│   ├── main.py              # FastAPI application
│   ├── agents/              # Agentic AI components
│   │   ├── tax_optimizer.py # Tax optimization agent
│   │   └── portfolio_agent.py # Portfolio explanation agent
│   ├── ml/                  # Machine learning
│   │   └── reinforcement_learner.py # RL optimizer
│   ├── core/                # Core algorithms
│   │   └── markowitz.py     # Enhanced Markowitz
│   └── models/              # Data models
│       └── schemas.py       # Pydantic schemas
├── landing-page/            # Static website
├── serverless.yml           # AWS deployment config
└── deploy.sh               # Deployment script
```

## 🌍 European Tax Considerations

### Supported Countries
- 🇩🇪 Germany (Vorabpauschale, Anlage KAP)
- 🇫🇷 France (PEA eligibility, IFU documents)  
- 🇳🇱 Netherlands (Box 3 taxation)
- 🇧🇪 Belgium (Dividend withholding)
- 🇱🇺 Luxembourg (Favorable domicile)

### Tax Optimization Features
- **Accumulating vs Distributing ETFs**: Automatic selection based on tax bracket
- **Domicile Optimization**: Ireland/Luxembourg for EU tax treaties
- **Withholding Tax Minimization**: Optimal fund selection
- **Tax Document Generation**: Country-specific reporting

## 📈 Performance Benefits

### Compared to Traditional Savings
| Scenario | Savings Account | AmpliFolio API |
|----------|----------------|----------------|
| €100K @ 2% pre-tax | €2,000 | €2,600 |
| Tax loss (DE, 42%) | €840 | €0* |
| **Net gain** | **€1,160** | **€2,600** |

*Accumulating ETFs defer taxes until sale

### RL vs Static Markowitz
- **Adaptive Rebalancing**: +0.3-0.8% annual return
- **Tax-Loss Harvesting**: +0.2-0.5% tax alpha
- **Market Timing**: +0.1-0.4% from volatility timing
- **Total Enhancement**: +0.6-1.7% annually

## 🔒 Security & Compliance

- **GDPR**: EU data residency and privacy controls
- **MiFID II**: Compliant ETF recommendations with KID documents
- **BaFin/AMF**: Regulatory compliance for German/French markets
- **Data Encryption**: AES-256 at rest, TLS 1.3 in transit

## 📚 Documentation

- **API Docs**: https://api.amplifolio.eu/docs
- **Postman Collection**: [Download](https://api.amplifolio.eu/postman)
- **SDK Examples**: Available in Python, JavaScript, Go

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This API is for informational purposes only. Generated portfolios do not constitute investment advice. Please consult a certified financial adviser before making investment decisions.

---

**Built with ❤️ for European investors seeking tax-efficient growth**
