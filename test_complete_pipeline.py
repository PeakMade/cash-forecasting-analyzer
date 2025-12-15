"""
Test the complete file processing pipeline with sample files
"""
import os
import sys

from services.file_processor import FileProcessor
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize file processor
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    print("Error: OPENAI_API_KEY not found in environment variables")
    sys.exit(1)

processor = FileProcessor(openai_api_key=api_key)

# Sample file paths
cash_forecast_path = r'sample_files\550 Rittenhouse Cash Forecast - 09.2025.xlsx'
income_statement_path = r'sample_files\04_Rittenhouse Station_Comparative Income Statement_September 2025.pdf'
balance_sheet_path = r'sample_files\03_Rittenhouse Station_Balance Sheet_September 2025.pdf'

# Property info
property_info = {
    'entity_number': '550',
    'name': 'Rittenhouse Station',
    'address': '2625 Eden Ave, Cincinnati, OH',
    'city': 'Cincinnati',
    'state': 'OH',
    'zip': '45219',
    'university': 'University of Cincinnati'
}

print("="*100)
print("TESTING COMPLETE FILE PROCESSING PIPELINE")
print("="*100)
print()

# Process all files
print("Processing files...")
result = processor.process_and_analyze(
    cash_forecast_path=cash_forecast_path,
    income_statement_path=income_statement_path,
    balance_sheet_path=balance_sheet_path,
    property_info=property_info
)

if result.get('success'):
    print("[SUCCESS] Processing successful!\n")
    
    recommendation = result['recommendation']
    
    print("="*100)
    print(f"CASH FORECAST RECOMMENDATION - {recommendation['property_name']}")
    print(f"{recommendation['analysis_month']} → {recommendation['projected_month']}")
    print("="*100)
    print()
    
    print(f"DECISION: {recommendation['decision']}")
    if recommendation.get('amount'):
        print(f"AMOUNT: ${recommendation['amount']:,.2f}")
    print(f"CONFIDENCE: {recommendation['confidence']}")
    print()
    
    print("EXECUTIVE SUMMARY")
    print("-"*100)
    for i, bullet in enumerate(recommendation['executive_summary'], 1):
        print(f"{i}. {bullet}")
    print()
    
    print("\n" + "="*100)
    print("DECISION RATIONALE")
    print("="*100)
    print(recommendation['detailed_rationale']['decision_rationale'])
    
    print("\n[SUCCESS] Test completed successfully!")
    
else:
    print(f"[ERROR] Processing failed: {result.get('error', 'Unknown error')}")
    sys.exit(1)
