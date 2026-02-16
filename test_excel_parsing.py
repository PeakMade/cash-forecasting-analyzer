"""
Quick test script to verify Excel parsing without running the full app
No API calls, no Flask, no authentication overhead
"""
import sys
from pathlib import Path
from services.file_processor import FileProcessor
import glob

def test_campus_creek_parsing():
    """Test parsing Campus Creek Excel file to verify distribution extraction"""
    
    # Use the file from sample_files folder
    excel_file = Path("sample_files") / "Campus Creek Cottages" / "194 Campus Creek Cottages - Cash Forecast - 12.2025.xlsx"
    
    if not excel_file.exists():
        print(f"❌ File not found: {excel_file}")
        print("Expected location: sample_files/Campus Creek Cottages/194 Campus Creek Cottages - Cash Forecast - 12.2025.xlsx")
        return
    
    print(f"Found file: {excel_file}")
    
    print(f"Testing Excel parsing for: {excel_file}")
    print("=" * 80)
    
    # Initialize FileProcessor (no API key needed for just parsing)
    processor = FileProcessor(openai_api_key="dummy")
    
    # Parse just the cash forecast
    try:
        cash_data = processor.parse_cash_forecast(str(excel_file))
        
        print("\n✅ PARSING SUCCESSFUL")
        print("\nExtracted Data:")
        print("-" * 80)
        print(f"Property Name: {cash_data.get('property_name')}")
        print(f"Entity Number: {cash_data.get('entity_number')}")
        print(f"Current Month: {cash_data.get('current_month')}")
        print(f"Projected Month: {cash_data.get('projected_month')}")
        print(f"Reporting Month: {cash_data.get('reporting_month')}")
        print()
        print(f"Current FCF: ${cash_data.get('current_fcf', 0):,.2f}")
        print(f"Projected FCF: ${cash_data.get('projected_fcf', 0):,.2f}")
        print()
        print(f"Current Occupancy: {cash_data.get('current_occupancy', 0):.1f}%")
        print(f"Projected Occupancy: {cash_data.get('projected_occupancy', 0):.1f}%")
        print()
        print(f"Current Distributions (Actual): ${cash_data.get('current_distributions', 0):,.2f}")
        print(f"Projected Distributions (Forecasted): ${cash_data.get('projected_distributions', 0):,.2f}")
        print()
        print(f"Projected Operational FCF: ${cash_data.get('projected_operational_fcf', 0):,.2f}")
        print()
        
        # Check if projected_distributions is being extracted
        projected_dist = cash_data.get('projected_distributions', 0)
        if projected_dist == 0:
            print("⚠️  WARNING: projected_distributions is 0 - extraction may have failed")
            print("Expected value for Campus Creek: approximately -$388,000")
        elif projected_dist < 0:
            print(f"✅ Successfully extracted negative distribution: ${projected_dist:,.2f}")
            print("This indicates a planned distribution (outflow)")
        else:
            print(f"ℹ️  Positive value extracted: ${projected_dist:,.2f}")
            print("This indicates a planned contribution (inflow)")
        
        print("\n" + "=" * 80)
        print("Test complete - no API calls made")
        
    except Exception as e:
        print(f"\n❌ ERROR during parsing:")
        print(f"   {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_campus_creek_parsing()
