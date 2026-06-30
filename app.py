import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import json
import os
import boto3
# Using scikit-learn instead of pypfopt for portfolio optimization
from sklearn.covariance import LedoitWolf

# Page configuration
st.set_page_config(
    page_title="AmpliFolio - ETF Portfolio Assistant",
    page_icon="📊",
    layout="wide"
)

# Create data directory if it doesn't exist
os.makedirs("data", exist_ok=True)

# Function to create Bedrock client
def create_bedrock_client():
    return boto3.client(
        service_name='bedrock-runtime',
        region_name='us-east-1'
    )

# Function to analyze risk profile using Amazon Bedrock
def analyze_risk_profile(user_input):
    """Use Amazon Bedrock to analyze user input and determine risk profile"""
    # For demo purposes, we'll use a simple keyword matching approach
    # In production, this would call Amazon Bedrock
    
    user_input = user_input.lower()
    
    conservative_keywords = ["conservative", "safe", "low risk", "stable", "bonds", "income"]
    aggressive_keywords = ["aggressive", "high risk", "growth", "stocks", "equity", "emerging"]
    
    conservative_score = sum(1 for word in conservative_keywords if word in user_input)
    aggressive_score = sum(1 for word in aggressive_keywords if word in user_input)
    
    # Extract geography preferences
    geography = []
    if "us" in user_input or "united states" in user_input or "america" in user_input:
        geography.append("US")
    if "europe" in user_input or "european" in user_input:
        geography.append("Europe")
    if "asia" in user_input or "asian" in user_input:
        geography.append("Asia")
    if "emerging" in user_input or "developing" in user_input:
        geography.append("Emerging Markets")
    
    # Extract sector preferences
    sectors = []
    if "tech" in user_input or "technology" in user_input:
        sectors.append("Technology")
    if "health" in user_input or "healthcare" in user_input:
        sectors.append("Healthcare")
    if "finance" in user_input or "financial" in user_input:
        sectors.append("Financial")
    if "energy" in user_input:
        sectors.append("Energy")
    
    # Determine ESG focus
    esg_focus = "esg" in user_input or "sustainable" in user_input or "green" in user_input
    
    # Determine risk profile
    if conservative_score > aggressive_score:
        risk_profile = "conservative"
    elif aggressive_score > conservative_score:
        risk_profile = "aggressive"
    else:
        risk_profile = "moderate"
    
    return {
        "risk_profile": risk_profile,
        "preferences": {
            "geography": geography,
            "sectors": sectors,
            "esg_focus": esg_focus
        }
    }

# Function to generate portfolio insights
def generate_portfolio_insights(portfolio_data):
    """Generate human-readable insights about the portfolio"""
    # In production, this would call Amazon Bedrock
    
    risk_level = "low"
    if float(portfolio_data["metrics"]["volatility"].strip('%')) > 15:
        risk_level = "high"
    elif float(portfolio_data["metrics"]["volatility"].strip('%')) > 10:
        risk_level = "moderate"
    
    # Generate insights based on portfolio data
    insights = f"""
    ## Portfolio Analysis

    This portfolio has a **{risk_level} risk profile** with an expected annual return of {portfolio_data["metrics"]["expected_return"]} and volatility of {portfolio_data["metrics"]["volatility"]}.
    
    ### Key Observations:
    
    - The portfolio has a Sharpe ratio of {portfolio_data["metrics"]["sharpe_ratio"]}, indicating a reasonable risk-adjusted return.
    - The allocation is diversified across {len(portfolio_data["allocation"])} ETFs, providing good exposure to different market segments.
    - Based on our projections, the portfolio could grow by {portfolio_data["scenarios"]["expected_5y"]} over 5 years in our expected scenario.
    
    ### Recommendations:
    
    - Consider rebalancing this portfolio annually to maintain the target allocation.
    - Monitor market conditions and be prepared to adjust if economic indicators change significantly.
    - For tax efficiency, consider holding this portfolio in a tax-advantaged account if possible.
    """
    
    return insights

# Function to filter ETFs by preferences
def filter_etfs_by_preferences(etf_data, preferences):
    """Filter ETFs based on user preferences"""
    filtered_etfs = etf_data.copy()
    
    if not preferences:
        return filtered_etfs
    
    # Check if we have metadata columns or just returns data
    has_metadata = "Geography" in filtered_etfs.columns
    
    # If we only have returns data, we can't filter by preferences
    if not has_metadata:
        return filtered_etfs
    
    # Filter by geography
    if preferences["geography"]:
        geography_mask = filtered_etfs["Geography"].apply(
            lambda x: any(geo in str(x) for geo in preferences["geography"])
        )
        filtered_etfs = filtered_etfs[geography_mask]
    
    # Filter by sectors
    if preferences["sectors"] and "Sector" in filtered_etfs.columns:
        sector_mask = filtered_etfs["Sector"].apply(
            lambda x: any(sector in str(x) for sector in preferences["sectors"])
        )
        filtered_etfs = filtered_etfs[sector_mask]
    
    # Filter by ESG
    if preferences["esg_focus"] and "ESG" in filtered_etfs.columns:
        filtered_etfs = filtered_etfs[filtered_etfs["ESG"] == True]
    
    # If filtering removed too many ETFs, add some back
    if len(filtered_etfs) < 5:
        return etf_data
    
    return filtered_etfs

# Function to generate Markowitz portfolio
def generate_markowitz_portfolio(etf_data, risk_profile, preferences=None):
    """Generate optimized portfolio using Markowitz approach"""
    # Filter ETFs based on preferences if provided
    filtered_etfs = filter_etfs_by_preferences(etf_data, preferences)
    
    # Use returns data for optimization
    returns_data = filtered_etfs[filtered_etfs.columns[7:]]  # Assuming returns data starts at column 7
    
    # Calculate expected returns
    mean_returns = returns_data.mean() * 252  # Annualized returns
    
    # Calculate covariance matrix using Ledoit-Wolf shrinkage
    lw = LedoitWolf().fit(returns_data)
    cov_matrix = lw.covariance_ * 252  # Annualized covariance
    
    # Number of assets
    n_assets = len(returns_data.columns)
    
    # Set weights based on risk profile
    if risk_profile == "conservative":
        # Conservative: More weight to less volatile assets
        volatility = returns_data.std() * np.sqrt(252)  # Annualized volatility
        inv_volatility = 1 / volatility
        weights = inv_volatility / inv_volatility.sum()
    elif risk_profile == "aggressive":
        # Aggressive: More weight to higher return assets
        weights = mean_returns / mean_returns.sum()
        weights = weights.clip(lower=0)  # Ensure non-negative weights
        weights = weights / weights.sum()  # Normalize
    else:  # moderate
        # Moderate: Equal weight
        weights = pd.Series(1/n_assets, index=returns_data.columns)
    
    # Calculate portfolio performance
    portfolio_return = (weights * mean_returns).sum()
    portfolio_volatility = np.sqrt(weights.dot(cov_matrix).dot(weights))
    sharpe_ratio = portfolio_return / portfolio_volatility
    
    # Convert weights to dictionary
    weights_dict = weights.to_dict()
    
    return {
        "weights": weights_dict,
        "expected_return": portfolio_return,
        "volatility": portfolio_volatility,
        "sharpe_ratio": sharpe_ratio
    }

# Function to enhance portfolio with RL (simplified version for demo)
def enhance_with_rl(markowitz_portfolio, etf_data, risk_profile):
    """Enhance portfolio allocation using reinforcement learning (simplified)"""
    # For demo purposes, we'll just slightly adjust the Markowitz weights
    # In production, this would use a trained RL model
    
    weights = markowitz_portfolio["weights"]
    tickers = list(weights.keys())
    
    # Apply small random adjustments based on risk profile
    if risk_profile == "conservative":
        adjustment_factor = 0.05  # Small adjustments
    elif risk_profile == "aggressive":
        adjustment_factor = 0.15  # Larger adjustments
    else:  # moderate
        adjustment_factor = 0.1  # Medium adjustments
    
    # Apply adjustments
    adjusted_weights = {}
    for ticker in tickers:
        # Random adjustment between -adjustment_factor and +adjustment_factor
        adjustment = np.random.uniform(-adjustment_factor, adjustment_factor)
        adjusted_weights[ticker] = max(0, weights[ticker] * (1 + adjustment))
    
    # Normalize weights to sum to 1
    total = sum(adjusted_weights.values())
    adjusted_weights = {k: v/total for k, v in adjusted_weights.items()}
    
    return adjusted_weights

# Function to generate scenarios
def generate_scenarios(portfolio, etf_data):
    """Generate conservative, expected, and optimistic return scenarios"""
    weights = list(portfolio["weights"].values())
    tickers = list(portfolio["weights"].keys())
    
    # Get historical returns for portfolio assets
    returns_data = etf_data[tickers]
    
    # Calculate portfolio mean and std
    portfolio_mean = np.sum(weights * returns_data.mean().values) * 252  # Annualized
    portfolio_std = np.sqrt(np.dot(weights, np.dot(returns_data.cov() * 252, weights)))
    
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

# Function to create allocation chart
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

# Function to create scenario chart
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

# Function to create risk-return chart
def create_risk_return_chart(etf_data, portfolio):
    """Create scatter plot showing risk vs return for ETFs and portfolio"""
    # Calculate risk and return for individual ETFs
    etf_returns = etf_data.mean() * 252  # Annualized returns
    etf_risk = etf_data.std() * np.sqrt(252)  # Annualized volatility
    
    # Create dataframe for plotting
    plot_data = pd.DataFrame({
        'ETF': etf_data.columns.tolist() + ['Portfolio'],
        'Risk': etf_risk.tolist() + [portfolio["volatility"]],
        'Return': etf_returns.tolist() + [portfolio["expected_return"]]
    })
    
    fig = px.scatter(
        plot_data,
        x='Risk',
        y='Return',
        text='ETF',
        title='Risk vs Return',
        labels={'Risk': 'Volatility (Risk)', 'Return': 'Expected Annual Return'}
    )
    
    # Highlight the portfolio point
    fig.add_trace(
        go.Scatter(
            x=[portfolio["volatility"]],
            y=[portfolio["expected_return"]],
            mode='markers',
            marker=dict(size=15, color='red'),
            name='Your Portfolio'
        )
    )
    
    return fig

# Load or generate sample ETF data
@st.cache_data
def load_etf_data():
    """Load ETF data or generate sample data if file doesn't exist"""
    try:
        return pd.read_csv("data/etf_data.csv")
    except FileNotFoundError:
        # Generate sample ETF data
        np.random.seed(42)
        
        # Define ETF metadata
        etfs = [
            {"Ticker": "VTI", "Name": "Vanguard Total Stock Market ETF", "Asset_Class": "Equity", "Geography": "US", "Sector": "Broad Market", "Expense_Ratio": 0.03, "ESG": False},
            {"Ticker": "VOO", "Name": "Vanguard S&P 500 ETF", "Asset_Class": "Equity", "Geography": "US", "Sector": "Large Cap", "Expense_Ratio": 0.03, "ESG": False},
            {"Ticker": "QQQ", "Name": "Invesco QQQ Trust", "Asset_Class": "Equity", "Geography": "US", "Sector": "Technology", "Expense_Ratio": 0.20, "ESG": False},
            {"Ticker": "VGT", "Name": "Vanguard Information Technology ETF", "Asset_Class": "Equity", "Geography": "US", "Sector": "Technology", "Expense_Ratio": 0.10, "ESG": False},
            {"Ticker": "VHT", "Name": "Vanguard Health Care ETF", "Asset_Class": "Equity", "Geography": "US", "Sector": "Healthcare", "Expense_Ratio": 0.10, "ESG": False},
            {"Ticker": "VFH", "Name": "Vanguard Financials ETF", "Asset_Class": "Equity", "Geography": "US", "Sector": "Financial", "Expense_Ratio": 0.10, "ESG": False},
            {"Ticker": "VPU", "Name": "Vanguard Utilities ETF", "Asset_Class": "Equity", "Geography": "US", "Sector": "Utilities", "Expense_Ratio": 0.10, "ESG": False},
            {"Ticker": "VDC", "Name": "Vanguard Consumer Staples ETF", "Asset_Class": "Equity", "Geography": "US", "Sector": "Consumer Staples", "Expense_Ratio": 0.10, "ESG": False},
            {"Ticker": "VCR", "Name": "Vanguard Consumer Discretionary ETF", "Asset_Class": "Equity", "Geography": "US", "Sector": "Consumer Discretionary", "Expense_Ratio": 0.10, "ESG": False},
            {"Ticker": "VWO", "Name": "Vanguard FTSE Emerging Markets ETF", "Asset_Class": "Equity", "Geography": "Emerging Markets", "Sector": "Broad Market", "Expense_Ratio": 0.10, "ESG": False},
            {"Ticker": "VEA", "Name": "Vanguard FTSE Developed Markets ETF", "Asset_Class": "Equity", "Geography": "Europe,Asia", "Sector": "Broad Market", "Expense_Ratio": 0.05, "ESG": False},
            {"Ticker": "ESGV", "Name": "Vanguard ESG U.S. Stock ETF", "Asset_Class": "Equity", "Geography": "US", "Sector": "Broad Market", "Expense_Ratio": 0.09, "ESG": True},
            {"Ticker": "VSGX", "Name": "Vanguard ESG International Stock ETF", "Asset_Class": "Equity", "Geography": "International", "Sector": "Broad Market", "Expense_Ratio": 0.12, "ESG": True},
            {"Ticker": "BND", "Name": "Vanguard Total Bond Market ETF", "Asset_Class": "Bond", "Geography": "US", "Sector": "Broad Market", "Expense_Ratio": 0.03, "ESG": False},
            {"Ticker": "BNDX", "Name": "Vanguard Total International Bond ETF", "Asset_Class": "Bond", "Geography": "International", "Sector": "Broad Market", "Expense_Ratio": 0.08, "ESG": False},
            {"Ticker": "BSV", "Name": "Vanguard Short-Term Bond ETF", "Asset_Class": "Bond", "Geography": "US", "Sector": "Short-Term", "Expense_Ratio": 0.04, "ESG": False},
            {"Ticker": "BLV", "Name": "Vanguard Long-Term Bond ETF", "Asset_Class": "Bond", "Geography": "US", "Sector": "Long-Term", "Expense_Ratio": 0.04, "ESG": False},
            {"Ticker": "VCSH", "Name": "Vanguard Short-Term Corporate Bond ETF", "Asset_Class": "Bond", "Geography": "US", "Sector": "Corporate", "Expense_Ratio": 0.04, "ESG": False},
            {"Ticker": "VCLT", "Name": "Vanguard Long-Term Corporate Bond ETF", "Asset_Class": "Bond", "Geography": "US", "Sector": "Corporate", "Expense_Ratio": 0.04, "ESG": False},
            {"Ticker": "VTIP", "Name": "Vanguard Short-Term Inflation-Protected Securities ETF", "Asset_Class": "Bond", "Geography": "US", "Sector": "Inflation-Protected", "Expense_Ratio": 0.04, "ESG": False}
        ]
        
        # Create DataFrame with ETF metadata
        df = pd.DataFrame(etfs)
        
        # Generate 252 days of returns data (1 year of trading days)
        days = 252
        returns_data = {}
        
        for etf in etfs:
            ticker = etf["Ticker"]
            
            # Generate returns based on asset class
            if etf["Asset_Class"] == "Equity":
                if "Technology" in etf["Sector"]:
                    mean_return = 0.00045  # Higher mean for tech
                    std_dev = 0.015  # Higher volatility for tech
                elif "Emerging" in etf["Geography"]:
                    mean_return = 0.0004
                    std_dev = 0.016  # Higher volatility for emerging markets
                else:
                    mean_return = 0.00035
                    std_dev = 0.01
            else:  # Bond
                if "Short" in etf["Sector"]:
                    mean_return = 0.00015
                    std_dev = 0.003
                else:
                    mean_return = 0.0002
                    std_dev = 0.005
            
            # Generate daily returns
            returns = np.random.normal(mean_return, std_dev, days)
            returns_data[ticker] = returns
        
        # Create returns DataFrame
        returns_df = pd.DataFrame(returns_data)
        
        # Combine metadata and returns
        result = pd.concat([df, returns_df], axis=1)
        
        # Save to CSV
        result.to_csv("data/etf_data.csv", index=False)
        return result

# Load ETF data
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
        # Extract returns data for optimization (columns after the 7th column are assumed to be returns)
        returns_columns = etf_data.columns[7:]  # Assuming returns data starts at column 7
        returns_data = etf_data[returns_columns]
        
        # Step 2: Generate portfolio using Markowitz optimization
        markowitz_portfolio = generate_markowitz_portfolio(etf_data, risk_profile, preferences)
        
        # Step 3: Enhance with reinforcement learning
        enhanced_weights = enhance_with_rl(markowitz_portfolio, returns_data, risk_profile)
        enhanced_weights = enhance_with_rl(markowitz_portfolio, returns_data, risk_profile)
        
        # Create final portfolio object
        portfolio = {
            "weights": enhanced_weights,
            "expected_return": markowitz_portfolio["expected_return"],
            "volatility": markowitz_portfolio["volatility"],
            "sharpe_ratio": markowitz_portfolio["sharpe_ratio"]
        }
        
        # Step 4: Generate scenarios
        scenarios = generate_scenarios(portfolio, returns_data)
    
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
    
    # Disclaimer
    st.markdown("---")
    st.caption("Disclaimer: This tool is for educational purposes only. It does not constitute investment advice.")
