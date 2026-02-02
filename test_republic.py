"""
Test the cash forecast analyzer with The Republic data
"""
from services.file_processor import FileProcessor
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize processor
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    print("Error: OPENAI_API_KEY not found in environment")
    exit(1)

processor = FileProcessor(api_key)

# The Republic property info
property_info = {
    'property': 'The Republic',
    'address': 'Reno',
    'city': 'Reno',
    'state': 'NV',
    'zip': '89501',
    'university': 'University of Nevada, Reno'
}

# File paths
base_path = r'sample_files\The Republic'
cash_forecast_path = os.path.join(base_path, '163 The Republic Cash Forecast - 12.2025.xlsx')
income_statement_path = os.path.join(base_path, '06_The Republic_Comparative Income Statement_December-25.pdf')
balance_sheet_path = os.path.join(base_path, '04_The Republic_Balance Sheet_December-25.pdf')

print("="*100)
print("TESTING THE REPUBLIC CASH FORECAST ANALYSIS")
print("="*100)
print()

# Step 1: Parse cash forecast only to see extracted data
print("Step 1: Parsing Cash Forecast Excel...")
print("-"*100)
cash_data = processor.parse_cash_forecast(cash_forecast_path)

if cash_data.get('status') == 'success':
    print(f"✓ Successfully parsed cash forecast")
    print(f"\nProperty: {cash_data['property_name']}")
    print(f"Current Month: {cash_data['current_month']}")
    print(f"Projected Month: {cash_data['projected_month']}")
    print(f"\nCurrent FCF: ${cash_data['current_fcf']:,.2f}")
    print(f"Projected FCF: ${cash_data['projected_fcf']:,.2f}")
    print(f"\nCurrent Occupancy: {cash_data['current_occupancy']:.1f}%")
    print(f"Projected Occupancy: {cash_data['projected_occupancy']:.1f}%")
    print(f"\nCurrent Distributions (Actual): ${cash_data['current_distributions']:,.2f}")
    print(f"Projected Distributions (Forecasted): ${cash_data.get('projected_distributions', 0):,.2f}")
    
    projected_distributions = cash_data.get('projected_distributions', 0)
    if projected_distributions < 0:
        print(f"  → Accountant recommends DISTRIBUTION of ${abs(projected_distributions):,.2f}")
    elif projected_distributions > 0:
        print(f"  → Accountant recommends CONTRIBUTION of ${projected_distributions:,.2f}")
    else:
        print(f"  → No distribution or contribution recommended")
    
    print(f"\n{'='*60}")
    print(f"PROJECTED MONTHS (Count: {len(cash_data.get('projected_months', []))})")
    print(f"{'='*60}")
    
    projected_months = cash_data.get('projected_months', [])
    if projected_months:
        for i, month in enumerate(projected_months, 1):
            print(f"{i}. {month['month']:<15} FCF: ${month['fcf']:>12,.2f}  Occ: {month['occupancy']:>5.1f}%")
    else:
        print("No projected months data available")
    
    print()
    print("="*100)
    print("VALIDATION CHECK")
    print("="*100)
    print()
    
    # Check the issue mentioned by user
    if len(projected_months) == 1:
        print("✓ CORRECT: Only 1 month of budget data extracted (as expected)")
        print(f"  Month: {projected_months[0]['month']}")
    elif len(projected_months) == 2:
        print("✗ ISSUE: 2 months extracted when only 1 should exist")
        print("  This suggests February 2026 is being included incorrectly")
        for month in projected_months:
            print(f"  - {month['month']}: FCF=${month['fcf']:,.2f}, Occ={month['occupancy']:.1f}%")
    elif len(projected_months) > 2:
        print(f"✗ ISSUE: {len(projected_months)} months extracted when only 1 should exist")
    else:
        print("✗ ISSUE: No projected months found")
    
else:
    print(f"✗ Failed to parse cash forecast: {cash_data.get('error', 'Unknown error')}")

print()
print("="*100)
print("Step 2: Full Analysis (if cash forecast parsing succeeded)")
print("-"*100)

if cash_data.get('status') == 'success':
    # Run full analysis
    result = processor.process_and_analyze(
        cash_forecast_path=cash_forecast_path,
        income_statement_path=income_statement_path,
        balance_sheet_path=balance_sheet_path,
        property_info=property_info
    )
    
    if result.get('success'):
        print("✓ Full analysis completed successfully")
        print()
        
        # Show the recommendation details
        recommendation = result.get('recommendation', {})
        details = result.get('details', {})
        
        print("="*100)
        print("CASH FORECAST ANALYSIS OUTPUT")
        print("="*100)
        if 'cash_forecast_data' in details:
            cash_analysis = details['cash_forecast_data']
            print(f"\nProperty: {cash_analysis.get('property_name')}")
            print(f"Current Month: {cash_analysis.get('current_month')} (Actual)")
            print(f"Projected Month: {cash_analysis.get('projected_month')} (Budget)")
            print(f"\nCurrent FCF: ${cash_analysis.get('current_fcf', 0):,.2f}")
            print(f"Projected FCF: ${cash_analysis.get('projected_fcf', 0):,.2f}")
            
            projected_months = cash_analysis.get('projected_months', [])
            print(f"\nProjected Months Available: {len(projected_months)}")
            for i, month in enumerate(projected_months, 1):
                print(f"  {i}. {month['month']}: FCF=${month['fcf']:,.2f}, Occ={month['occupancy']:.1f}%")
        
        print("\n" + "="*100)
        print("RECOMMENDATION SUMMARY")
        print("="*100)
        print(f"\nDecision: {recommendation.get('decision')}")
        if recommendation.get('amount'):
            print(f"Amount: ${recommendation.get('amount'):,.2f}")
        print(f"Confidence: {recommendation.get('confidence')}")
    else:
        print(f"✗ Analysis failed: {result.get('error', 'Unknown error')}")
