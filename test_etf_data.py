"""
Test ETF Data Pipeline
"""

import asyncio
import json
from api.data.etf_scraper import ETFDataScraper
from api.data.data_pipeline import ETFDataPipeline

async def test_etf_scraper():
    """Test the ETF scraper functionality"""
    
    print("🧪 Testing ETF Data Scraper...")
    
    scraper = ETFDataScraper()
    
    # Test mock data loading (since we can't scrape in test environment)
    print("📊 Testing ETF universe loading...")
    
    try:
        # This will use mock data since we don't have real DynamoDB
        etfs = await scraper.get_etf_universe()
        print(f"✅ Loaded {len(etfs)} ETFs from universe")
        
        if etfs:
            sample_etf = etfs[0]
            print(f"📋 Sample ETF: {sample_etf.get('name', 'Unknown')}")
            print(f"   ISIN: {sample_etf.get('isin', 'N/A')}")
            print(f"   TER: {sample_etf.get('ter', 'N/A')}")
            print(f"   Domicile: {sample_etf.get('domicile', 'N/A')}")
            print(f"   Tax Efficiency: {sample_etf.get('tax_efficiency_score', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Error testing scraper: {e}")

async def test_data_pipeline():
    """Test the data pipeline functionality"""
    
    print("\n🧪 Testing ETF Data Pipeline...")
    
    pipeline = ETFDataPipeline()
    
    # Test data quality validation
    mock_etfs = [
        {
            'isin': 'IE00B4L5Y983',
            'name': 'iShares Core MSCI World UCITS ETF USD (Acc)',
            'ter': 0.002,
            'domicile': 'Ireland',
            'aum': 1500,
            'is_accumulating': True,
            'scraped_at': '2024-01-15T10:00:00'
        },
        {
            'isin': 'IE00B3RBWM25',
            'name': 'Vanguard FTSE Developed World UCITS ETF',
            'ter': 0.0012,
            'domicile': 'Ireland',
            'aum': 800,
            'is_accumulating': False,
            'scraped_at': '2024-01-15T10:00:00'
        }
    ]
    
    try:
        # Test data quality validation
        quality_result = await pipeline._validate_data_quality(mock_etfs)
        print(f"✅ Data quality validation: {'PASSED' if quality_result['passed'] else 'FAILED'}")
        
        if quality_result['issues']:
            print(f"⚠️  Quality issues: {quality_result['issues']}")
        
        # Test data enrichment
        enrichment_result = await pipeline._enrich_data(mock_etfs)
        enriched_etfs = enrichment_result['enriched_etfs']
        
        print(f"✅ Data enrichment completed: {len(enriched_etfs)} ETFs enriched")
        
        if enriched_etfs:
            sample = enriched_etfs[0]
            print(f"📊 Sample enriched ETF:")
            print(f"   Tax Efficiency Score: {sample.get('tax_efficiency_score', 'N/A')}")
            print(f"   Liquidity Score: {sample.get('liquidity_score', 'N/A')}")
            print(f"   Quality Score: {sample.get('quality_score', 'N/A')}")
            print(f"   Risk Category: {sample.get('risk_category', 'N/A')}")
            print(f"   Geographic Exposure: {sample.get('geographic_exposure', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Error testing pipeline: {e}")

async def test_etf_filtering():
    """Test ETF filtering functionality"""
    
    print("\n🧪 Testing ETF Filtering...")
    
    scraper = ETFDataScraper()
    
    try:
        # Test different filter combinations
        filters_to_test = [
            {'domicile': 'Ireland'},
            {'min_aum': 100},
            {'accumulating_only': True},
            {'max_ter': 0.005},
            {'domicile': 'Ireland', 'accumulating_only': True, 'min_aum': 100}
        ]
        
        for filters in filters_to_test:
            etfs = await scraper.get_etf_universe(filters)
            print(f"✅ Filter {filters}: {len(etfs)} ETFs found")
        
    except Exception as e:
        print(f"❌ Error testing filters: {e}")

def test_tax_efficiency_calculation():
    """Test tax efficiency score calculation"""
    
    print("\n🧪 Testing Tax Efficiency Calculation...")
    
    pipeline = ETFDataPipeline()
    
    test_etfs = [
        {
            'name': 'iShares Core MSCI World UCITS ETF USD (Acc)',
            'domicile': 'Ireland',
            'is_accumulating': True,
            'replication': 'Physical',
            'ter': 0.002
        },
        {
            'name': 'Vanguard FTSE Developed World UCITS ETF USD Distributing',
            'domicile': 'Ireland',
            'is_accumulating': False,
            'replication': 'Physical',
            'ter': 0.0012
        },
        {
            'name': 'SPDR MSCI World UCITS ETF',
            'domicile': 'Luxembourg',
            'is_accumulating': False,
            'replication': 'Synthetic',
            'ter': 0.008
        }
    ]
    
    for etf in test_etfs:
        score = pipeline._calculate_tax_efficiency(etf)
        print(f"📊 {etf['name'][:30]}...")
        print(f"   Tax Efficiency Score: {score:.2f}")
        print(f"   Factors: Accumulating={etf.get('is_accumulating')}, "
              f"Domicile={etf.get('domicile')}, TER={etf.get('ter')}")
        print()

async def main():
    """Run all ETF data tests"""
    
    print("🚀 AmpliFolio ETF Data Pipeline Tests")
    print("=" * 50)
    
    await test_etf_scraper()
    await test_data_pipeline()
    await test_etf_filtering()
    test_tax_efficiency_calculation()
    
    print("\n✅ All ETF data tests completed!")
    print("\nETF Data Sources:")
    print("1. 🇪🇺 JustETF.com - Primary European ETF database")
    print("2. 📊 Morningstar Europe - Alternative data source")
    print("3. 🏦 iShares/Vanguard - Direct provider data")
    print("4. 🔄 Daily automated scraping with quality checks")
    print("\nData Quality Features:")
    print("• Validation of ISIN, TER, AUM, domicile")
    print("• Tax efficiency scoring for EU investors")
    print("• Liquidity and quality scoring")
    print("• Geographic and sector classification")
    print("• Automated alerts for data issues")

if __name__ == "__main__":
    asyncio.run(main())