"""
Test BLS (Bureau of Labor Statistics) API Integration
Shows how to get official unemployment data
"""
import os
from dotenv import load_dotenv
from services.bls_client import BLSClient

# Load environment variables
load_dotenv()

def test_bls_client():
    """Test BLS client for unemployment data"""
    
    print("=" * 80)
    print("BLS API Client Test")
    print("=" * 80)
    
    # Initialize client
    client = BLSClient()
    
    print(f"\nBLS API Key Found: {client.enabled}")
    
    if not client.enabled:
        print("\n" + "=" * 80)
        print("HOW TO GET A FREE BLS API KEY")
        print("=" * 80)
        print("\n1. Go to: https://www.bls.gov/developers/home.htm")
        print("2. Click 'Registration' or go to: https://data.bls.gov/registrationEngine/")
        print("3. Fill out the registration form (free, no credit card)")
        print("4. You'll receive an API key via email immediately")
        print("5. Add to .env file: BLS_API_KEY=your_key_here")
        print("\nFree tier limits:")
        print("  - 500 queries per day")
        print("  - 25 queries per 10 seconds")
        print("  - Sufficient for our needs (1 query per property analysis)")
        print("\n" + "=" * 80)
        return
    
    # Test cities
    test_cases = [
        ("Cincinnati", "OH"),
        ("Columbus", "OH"),
        ("Austin", "TX"),
        ("Boston", "MA"),
        ("Unknown City", "ZZ"),  # Should fail gracefully
    ]
    
    print("\n" + "=" * 80)
    print("Testing Unemployment Data Retrieval")
    print("=" * 80)
    
    for city, state in test_cases:
        print(f"\n{city}, {state}:")
        print("-" * 40)
        
        data = client.get_unemployment_rate(city, state)
        
        if data:
            print(f"  ✓ Success!")
            print(f"    Unemployment Rate: {data['unemployment_rate']}%")
            print(f"    Period: {data['period']}")
            print(f"    Source: {data['source']}")
            print(f"    Formatted: {client.format_for_analysis(data)}")
        else:
            print(f"  ✗ No data available")
    
    print("\n" + "=" * 80)
    print("Test Complete")
    print("=" * 80)
    
    # Test with economic analysis
    print("\n" + "=" * 80)
    print("Testing Integration with Economic Analysis")
    print("=" * 80)
    
    from services.economic_analysis import EconomicAnalyzer
    
    analyzer = EconomicAnalyzer()
    print(f"\nBLS Enabled in Analyzer: {analyzer.bls.enabled}")
    print(f"IPEDS Enabled in Analyzer: {analyzer.ipeds.enabled}")
    
    if analyzer.bls.enabled:
        print("\n✓ BLS client successfully integrated into economic analysis")
        print("  Unemployment data will be automatically included in property analyses")
    else:
        print("\n⚠ BLS client not enabled - add BLS_API_KEY to .env file")

if __name__ == "__main__":
    test_bls_client()
