"""
Test script to check multi-month budget extraction and averaging
"""
from services.file_processor import FileProcessor

# Parse the Campus Creek file
processor = FileProcessor(openai_api_key='dummy')
data = processor.parse_cash_forecast('sample_files/Campus Creek Cottages/194 Campus Creek Cottages - Cash Forecast - 12.2025.xlsx')

projected_months = data.get('projected_months', [])
print(f"\n{'='*80}")
print(f"MULTI-MONTH BUDGET ANALYSIS")
print(f"{'='*80}\n")
print(f"Total budget months extracted: {len(projected_months)}\n")

if projected_months:
    print(f"{'Month':<20} {'Operational FCF':>20} {'After Dist/Contrib':>20}")
    print(f"{'-'*20} {'-'*20} {'-'*20}")
    
    total_operational = 0
    for i, m in enumerate(projected_months, 1):
        print(f"{m['month']:<20} ${m['operational_fcf']:>18,.2f} ${m['fcf']:>18,.2f}")
        total_operational += m['operational_fcf']
    
    average_operational = total_operational / len(projected_months)
    
    print(f"\n{'-'*62}")
    print(f"{'TOTALS':<20} ${total_operational:>18,.2f}")
    print(f"{'AVERAGE':<20} ${average_operational:>18,.2f}")
    print(f"\n{'='*80}\n")
    
    # Compare to single month
    single_month_fcf = data.get('projected_operational_fcf', 0)
    print(f"Single month (January 2026) Operational FCF: ${single_month_fcf:,.2f}")
    print(f"Average across all months: ${average_operational:,.2f}")
    print(f"\nDifference: ${abs(single_month_fcf - average_operational):,.2f}")
    if single_month_fcf != 0:
        pct_diff = ((average_operational - single_month_fcf) / abs(single_month_fcf)) * 100
        print(f"Percentage difference: {pct_diff:,.1f}%")
else:
    print("⚠️ No projected months extracted!")
