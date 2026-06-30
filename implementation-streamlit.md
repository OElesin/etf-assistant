# AmpliFolio Streamlit Implementation Plan

## Overview

We'll build a Streamlit application that:
1. Loads ETF data from a dataframe
2. Uses Amazon Bedrock Converse API to analyze user input and determine risk profile
3. Generates optimized portfolios using Markowitz portfolio theory and reinforcement learning
4. Visualizes portfolio insights using Plotly
5. Shows 3 return scenarios (conservative, expected, optimistic)
6. Provides human-readable financial analysis using Amazon Bedrock Converse API

## Implementation Phases

### Phase 1: Project Setup and Data Preparation

1. **Create project structure**
   ```
   amplify-etf-assistant/
   ├── app.py                # Main Streamlit application
   ├── requirements.txt      # Dependencies
   ├── data/
   │   └── etf_data.csv      # ETF dataset
   ├── modules/
   │   ├── bedrock_client.py # Amazon Bedrock integration
   │   ├── portfolio.py      # Portfolio optimization logic
   │   ├── visualization.py  # Plotly visualization functions
   │   └── scenarios.py      # Return scenario generation
   └── README.md             # Documentation
   ```

2. **Set up environment and dependencies**
   ```
   pip install streamlit pandas numpy plotly boto3 pypfopt gym stable-baselines3
   ```

3. **Prepare ETF dataset**
   - Create a comprehensive ETF dataset with the following columns:
     - Ticker
     - Name
     - Asset Class
     - Geography
     - Expense Ratio
     - Historical Returns (1Y, 3Y, 5Y)
     - Volatility
     - Daily price data (for covariance calculation)

### Phase 2: Amazon Bedrock Integration

1. **Set up Amazon Bedrock client**
   ```python
   import boto3
   import json
   
   def create_bedrock_client():
       return boto3.client(
           service_name='bedrock-runtime',
           region_name='us-east-1'
       )
   
   def analyze_risk_profile(user_input):
       """Use Amazon Bedrock to analyze user input and determine risk profile"""
       client = create_bedrock_client()
       
       prompt = f"""
       Analyze the following investment request and determine the investor's risk profile.
       Classify as: conservative, moderate, or aggressive.
       Also extract any specific preferences like geography, sectors, or ESG considerations.
       
       Investment request: {user_input}
       
       Respond in JSON format with the following structure:
       {{
           "risk_profile": "conservative|moderate|aggressive",
           "preferences": {{
               "geography": ["US", "Europe", etc.],
               "sectors": ["Technology", "Healthcare", etc.],
               "esg_focus": true|false
           }}
       }}
       """
       
       response = client.invoke_model(
           modelId='anthropic.claude-3-sonnet-20240229-v1:0',
           contentType='application/json',
           accept='application/json',
           body=json.dumps({
               "prompt": prompt,
               "max_tokens": 500
           })
       )
       
       result = json.loads(response['body'].read())
       return json.loads(result['completion'])
   ```

### Phase 3: Portfolio Optimization Engine

1. **Implement Markowitz portfolio optimization**
   ```python
   from pypfopt import EfficientFrontier, risk_models, expected_returns
   import pandas as pd
   import numpy as np
   
   def generate_markowitz_portfolio(etf_data, risk_profile, preferences=None):
       """Generate optimized portfolio using Markowitz approach"""
       # Filter ETFs based on preferences if provided
       filtered_etfs = filter_etfs_by_preferences(etf_data, preferences)
       
       # Calculate expected returns and sample covariance
       mu = expected_returns.mean_historical_return(filtered_etfs)
       S = risk_models.sample_cov(filtered_etfs)
       
       # Set optimization parameters based on risk profile
       if risk_profile == "conservative":
           ef = EfficientFrontier(mu, S)
           weights = ef.min_volatility()
       elif risk_profile == "aggressive":
           ef = EfficientFrontier(mu, S)
           weights = ef.max_sharpe()
       else:  # moderate
           ef = EfficientFrontier(mu, S)
           weights = ef.efficient_risk(target_risk=0.1)  # Adjust target risk as needed
       
       cleaned_weights = ef.clean_weights()
       performance = ef.portfolio_performance()
       
       return {
           "weights": cleaned_weights,
           "expected_return": performance[0],
           "volatility": performance[1],
           "sharpe_ratio": performance[2]
       }
   ```

2. **Implement reinforcement learning enhancement**
   ```python
   import gym
   from gym import spaces
   import numpy as np
   from stable_baselines3 import PPO

   class PortfolioEnv(gym.Env):
       """Custom Environment for portfolio optimization"""
       def __init__(self, returns_data, risk_aversion=1.0):
           super(PortfolioEnv, self).__init__()
           
           self.returns_data = returns_data
           self.n_assets = returns_data.shape[1]
           self.risk_aversion = risk_aversion
           self.current_step = 0
           self.max_steps = len(returns_data) - 1
           
           # Action space: portfolio weights (sum to 1)
           self.action_space = spaces.Box(
               low=0, high=1, shape=(self.n_assets,), dtype=np.float32
           )
           
           # Observation space: historical returns
           self.observation_space = spaces.Box(
               low=-np.inf, high=np.inf, 
               shape=(10, self.n_assets), dtype=np.float32
           )
           
           self.reset()
       
       def reset(self):
           self.current_step = 0
           return self._get_observation()
       
       def _get_observation(self):
           # Get last 10 days of returns as observation
           start = max(0, self.current_step - 9)
           end = self.current_step + 1
           return self.returns_data.iloc[start:end].values
       
       def step(self, action):
           # Normalize weights to sum to 1
           weights = action / np.sum(action)
           
           # Calculate portfolio return
           next_return = self.returns_data.iloc[self.current_step+1].values
           portfolio_return = np.sum(weights * next_return)
           
           # Calculate portfolio variance (risk)
           if self.current_step >= 30:  # Need enough history for covariance
               lookback = self.returns_data.iloc[self.current_step-30:self.current_step]
               cov_matrix = lookback.cov().values
               portfolio_variance = np.dot(weights.T, np.dot(cov_matrix, weights))
           else:
               portfolio_variance = 0
           
           # Reward: return - risk_aversion * variance
           reward = portfolio_return - self.risk_aversion * portfolio_variance
           
           # Move to next step
           self.current_step += 1
           done = self.current_step >= self.max_steps
           
           return self._get_observation(), reward, done, {}

   def train_rl_model(returns_data, risk_profile):
       """Train RL model for portfolio optimization"""
       # Set risk aversion based on risk profile
       if risk_profile == "conservative":
           risk_aversion = 2.0
       elif risk_profile == "aggressive":
           risk_aversion = 0.5
       else:  # moderate
           risk_aversion = 1.0
       
       # Create environment
       env = PortfolioEnv(returns_data, risk_aversion)
       
       # Train model
       model = PPO("MlpPolicy", env, verbose=0)
       model.learn(total_timesteps=10000)
       
       return model
   
   def enhance_with_rl(markowitz_portfolio, returns_data, risk_profile):
       """Enhance portfolio allocation using reinforcement learning"""
       # Get base weights from Markowitz
       base_weights = np.array(list(markowitz_portfolio["weights"].values()))
       tickers = list(markowitz_portfolio["weights"].keys())
       
       # Train RL model
       model = train_rl_model(returns_data[tickers], risk_profile)
       
       # Get RL weights
       obs = returns_data[tickers].iloc[-10:].values
       rl_weights = model.predict(obs)[0]
       
       # Normalize RL weights
       rl_weights = rl_weights / np.sum(rl_weights)
       
       # Blend Markowitz and RL weights
       if risk_profile == "conservative":
           blend_ratio = 0.8  # 80% Markowitz, 20% RL
       elif risk_profile == "aggressive":
           blend_ratio = 0.5  # 50% Markowitz, 50% RL
       else:  # moderate
           blend_ratio = 0.7  # 70% Markowitz, 30% RL
       
       final_weights = blend_ratio * base_weights + (1 - blend_ratio) * rl_weights
       
       # Normalize final weights
       final_weights = final_weights / np.sum(final_weights)
       
       # Convert back to dictionary
       return {ticker: weight for ticker, weight in zip(tickers, final_weights)}
   ```

### Phase 4: Scenario Generation and Visualization

1. **Implement scenario generation**
   ```python
   def generate_scenarios(portfolio, historical_data):
       """Generate conservative, expected, and optimistic return scenarios"""
       weights = np.array(list(portfolio["weights"].values()))
       tickers = list(portfolio["weights"].keys())
       
       # Get historical returns for portfolio assets
       returns = historical_data[tickers]
       
       # Calculate portfolio mean and std
       portfolio_mean = np.sum(weights * returns.mean().values) * 252  # Annualized
       portfolio_std = np.sqrt(np.dot(weights.T, np.dot(returns.cov() * 252, weights)))
       
       # Monte Carlo simulation for different scenarios
       num_simulations = 1000
       time_horizon = 5  # 5 years
       
       # Initialize array for simulation results
       simulation_results = np.zeros((num_simulations, time_horizon))
       
       # Run simulations
       for i in range(num_simulations):
           # Start with $1
           curr_value = 1
           for j in range(time_horizon):
               # Generate random return from normal distribution
               annual_return = np.random.normal(portfolio_mean, portfolio_std)
               curr_value *= (1 + annual_return)
               simulation_results[i, j] = curr_value
       
       # Extract percentiles for scenarios
       conservative = np.percentile(simulation_results, 25, axis=0)
       expected = np.percentile(simulation_results, 50, axis=0)
       optimistic = np.percentile(simulation_results, 75, axis=0)
       
       return {
           "conservative": conservative,
           "expected": expected,
           "optimistic": optimistic,
           "time_horizon": time_horizon
       }
   ```

2. **Implement Plotly visualizations**
   ```python
   import plotly.graph_objects as go
   import plotly.express as px
   
   def create_allocation_chart(portfolio):
       """Create pie chart showing portfolio allocation"""
       labels = list(portfolio["weights"].keys())
       values = list(portfolio["weights"].values())
       
       fig = px.pie(
           names=labels, 
           values=values, 
           title="Portfolio Allocation",
           hole=0.4
       )
       
       return fig
   
   def create_scenario_chart(scenarios):
       """Create line chart showing different return scenarios"""
       years = list(range(scenarios["time_horizon"] + 1))
       
       fig = go.Figure()
       
       # Add traces for each scenario
       fig.add_trace(go.Scatter(
           x=years,
           y=[1] + list(scenarios["conservative"]),
           mode='lines',
           name='Conservative',
           line=dict(color='blue')
       ))
       
       fig.add_trace(go.Scatter(
           x=years,
           y=[1] + list(scenarios["expected"]),
           mode='lines',
           name='Expected',
           line=dict(color='green')
       ))
       
       fig.add_trace(go.Scatter(
           x=years,
           y=[1] + list(scenarios["optimistic"]),
           mode='lines',
           name='Optimistic',
           line=dict(color='red')
       ))
       
       fig.update_layout(
           title="Portfolio Value Projection (Starting with $10,000)",
           xaxis_title="Years",
           yaxis_title="Portfolio Value ($)",
           yaxis_tickformat="$,.0f"
       )
       
       return fig
   ```

### Phase 5: Main Streamlit Application

```python
import streamlit as st
import pandas as pd
import json
from modules.bedrock_client import analyze_risk_profile, generate_portfolio_insights
from modules.portfolio import generate_markowitz_portfolio, enhance_with_rl
from modules.visualization import create_allocation_chart, create_scenario_chart
from modules.scenarios import generate_scenarios

# Page configuration
st.set_page_config(
    page_title="AmpliFolio - ETF Portfolio Assistant",
    page_icon="📊",
    layout="wide"
)

# Load ETF data
@st.cache_data
def load_etf_data():
    return pd.read_csv("data/etf_data.csv")

etf_data = load_etf_data()

# App title and description
st.title("AmpliFolio - ETF Portfolio Assistant")
st.markdown("Convert natural language investment requests into optimized ETF portfolios")

# User input section
st.header("What kind of portfolio are you looking for?")
query = st.text_area(
    "Describe your investment goals, risk tolerance, and preferences:",
    "I want a balanced portfolio with some exposure to tech and international markets. I'm planning to invest for 10 years."
)

# Generate portfolio button
if st.button("Generate Portfolio"):
    with st.spinner("Analyzing your investment preferences..."):
        # Step 1: Analyze risk profile using Amazon Bedrock
        risk_analysis = analyze_risk_profile(query)
        risk_profile = risk_analysis["risk_profile"]
        preferences = risk_analysis["preferences"]
        
        # Display risk profile
        st.subheader("Your Investment Profile")
        st.write(f"Risk Profile: **{risk_profile.capitalize()}**")
        
        if preferences["geography"]:
            st.write(f"Geographic Focus: {', '.join(preferences['geography'])}")
        if preferences["sectors"]:
            st.write(f"Sector Preferences: {', '.join(preferences['sectors'])}")
        if preferences["esg_focus"]:
            st.write("ESG Focus: Yes")
    
    with st.spinner("Generating optimized portfolio..."):
        # Step 2: Generate portfolio using Markowitz optimization
        markowitz_portfolio = generate_markowitz_portfolio(etf_data, risk_profile, preferences)
        
        # Step 3: Enhance with reinforcement learning
        enhanced_weights = enhance_with_rl(markowitz_portfolio, etf_data, risk_profile)
        
        # Create final portfolio object
        portfolio = {
            "weights": enhanced_weights,
            "expected_return": markowitz_portfolio["expected_return"],
            "volatility": markowitz_portfolio["volatility"],
            "sharpe_ratio": markowitz_portfolio["sharpe_ratio"]
        }
        
        # Step 4: Generate scenarios
        scenarios = generate_scenarios(portfolio, etf_data)
    
    # Display portfolio allocation
    st.header("Your Optimized Portfolio")
    
    # Create two columns for layout
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # Display allocation chart
        allocation_chart = create_allocation_chart(portfolio)
        st.plotly_chart(allocation_chart, use_container_width=True)
        
        # Display portfolio metrics
        st.subheader("Portfolio Metrics")
        st.write(f"Expected Annual Return: **{portfolio['expected_return']:.2%}**")
        st.write(f"Annual Volatility: **{portfolio['volatility']:.2%}**")
        st.write(f"Sharpe Ratio: **{portfolio['sharpe_ratio']:.2f}**")
    
    with col2:
        # Display scenario chart
        scenario_chart = create_scenario_chart(scenarios)
        st.plotly_chart(scenario_chart, use_container_width=True)
    
    # Get AI insights
    with st.spinner("Generating expert insights..."):
        portfolio_data = {
            "allocation": {k: f"{v:.2%}" for k, v in portfolio["weights"].items()},
            "metrics": {
                "expected_return": f"{portfolio['expected_return']:.2%}",
                "volatility": f"{portfolio['volatility']:.2%}",
                "sharpe_ratio": f"{portfolio['sharpe_ratio']:.2f}"
            },
            "scenarios": {
                "conservative_5y": f"{scenarios['conservative'][-1]:.2%}",
                "expected_5y": f"{scenarios['expected'][-1]:.2%}",
                "optimistic_5y": f"{scenarios['optimistic'][-1]:.2%}"
            }
        }
        
        insights = generate_portfolio_insights(portfolio_data)
    
    # Display AI insights
    st.header("Expert Portfolio Analysis")
    st.write(insights)
    
    # Disclaimer
    st.warning("""
    **Disclaimer**: This tool is for educational and informational purposes only. 
    The generated portfolio does not constitute investment advice. 
    Please consult a certified financial adviser before making investment decisions.
    """)

# Add sidebar with additional information
with st.sidebar:
    st.header("About AmpliFolio")
    st.write("AmpliFolio is a tool that helps you create optimized ETF portfolios based on your investment preferences.")
    
    st.header("How it works")
    st.write("1. Describe your investment goals")
    st.write("2. Our AI analyzes your risk profile")
    st.write("3. We generate an optimized portfolio using modern portfolio theory and reinforcement learning")
    st.write("4. View interactive visualizations and expert insights")
```

## Implementation Timeline

| Week | Tasks |
|------|-------|
| Week 1 | - Project setup<br>- ETF data collection and preparation<br>- Basic Streamlit UI implementation |
| Week 2 | - Amazon Bedrock integration<br>- Risk profile analysis implementation<br>- Basic portfolio generation |
| Week 3 | - Markowitz portfolio optimization<br>- Reinforcement learning enhancement<br>- Scenario generation |
| Week 4 | - Plotly visualization implementation<br>- AI insights integration<br>- Testing and refinement |

## Required AWS Setup

1. **Amazon Bedrock Access**
   - Ensure you have access to Amazon Bedrock service
   - Set up appropriate IAM permissions
   - Configure AWS credentials locally

2. **AWS CLI Configuration**
   ```bash
   aws configure
   # Enter your AWS Access Key ID, Secret Access Key, and preferred region
   ```

## Testing Plan

1. **Unit Testing**
   - Test Bedrock API integration
   - Test portfolio optimization functions
   - Test scenario generation

2. **Integration Testing**
   - End-to-end flow from user input to portfolio generation
   - Verify visualization rendering
   - Test different user inputs and risk profiles

## Next Steps and Future Enhancements

1. **Enhanced Data Pipeline**
   - Automated ETF data updates
   - More comprehensive ETF database
   - Historical performance tracking

2. **Advanced Portfolio Features**
   - Tax-efficient portfolio suggestions
   - Rebalancing recommendations
   - Custom constraints (e.g., ESG filters)

3. **User Experience**
   - Portfolio comparison tool
   - Save and track multiple portfolios
   - Export to PDF report
