"""
Test smart column detection for Cash Forecast parsing
"""
import pandas as pd
import logging
from services.file_processor import FileProcessor

# Set up logging to see debug messages
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

# Initialize processor (with dummy API key for testing)
processor = FileProcessor(openai_api_key='test-key')

# Test with Campus Creek Cottages file - this one uses a different format
test_files = [
    r'sample_files\Campus Creek Cottages\194 Campus Creek Cottages - Cash Forecast - 12.2025.xlsx',
]

for test_file in test_files:
    print("="*80)
    print("TESTING SMART COLUMN DETECTION")
    print("="*80)
    print(f"\nTest file: {test_file}\n")

    # Parse the cash forecast
    result = processor.parse_cash_forecast(test_file)

    if result['status'] == 'success':
        print("\n" + "="*80)
        print("✓ PARSING SUCCESSFUL")
        print("="*80)
        print(f"\nProperty: {result['property_name']}")
        print(f"Current Month: {result['current_month']}")
        print(f"Projected Month: {result['projected_month']}")
        print(f"\nCurrent FCF: ${result['current_fcf']:,.2f}")
        print(f"Projected FCF: ${result['projected_fcf']:,.2f}")
        print(f"Projected Operational FCF: ${result['projected_operational_fcf']:,.2f}")
        print(f"\nCurrent Occupancy: {result['current_occupancy']:.1f}%")
        print(f"Projected Occupancy: {result['projected_occupancy']:.1f}%")
        print(f"\nProjected Months Available: {len(result['projected_months'])}")
    else:
        print("\n" + "="*80)
        print("✗ PARSING FAILED")
        print("="*80)
        print(f"Error: {result.get('error', 'Unknown error')}")
    
    print("\n")
