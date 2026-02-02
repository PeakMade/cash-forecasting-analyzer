"""
Detailed test to see the full cash forecast analysis output
"""
from services.file_processor import FileProcessor
import os
from dotenv import load_dotenv

load_dotenv()

processor = FileProcessor(os.getenv('OPENAI_API_KEY'))

property_info = {
    'property': 'The Republic',
    'address': 'Reno',
    'city': 'Reno',
    'state': 'NV',
    'zip': '89501',
    'university': 'University of Nevada, Reno'
}

base_path = r'sample_files\The Republic'
cash_forecast_path = os.path.join(base_path, '163 The Republic Cash Forecast - 12.2025.xlsx')
income_statement_path = os.path.join(base_path, '06_The Republic_Comparative Income Statement_December-25.pdf')
balance_sheet_path = os.path.join(base_path, '04_The Republic_Balance Sheet_December-25.pdf')

result = processor.process_and_analyze(
    cash_forecast_path=cash_forecast_path,
    income_statement_path=income_statement_path,
    balance_sheet_path=balance_sheet_path,
    property_info=property_info
)

if result.get('success'):
    # Get the recommendation object
    recommendation = result.get('recommendation', {})
    
    # Print the formatted sections
    print("="*100)
    print("DETAILED RATIONALE (includes cash forecast analysis)")
    print("="*100)
    print(recommendation.get('detailed_rationale', 'Not available'))
    
    print("\n" + "="*100)
    print("EXECUTIVE SUMMARY")
    print("="*100)
    for bullet in recommendation.get('executive_summary', []):
        print(f"• {bullet}")
    
    print("\n" + "="*100)
    print("SUMMARY")
    print("="*100)
    print(f"Decision: {recommendation.get('decision')}")
    if recommendation.get('amount'):
        print(f"Amount: ${recommendation.get('amount'):,.2f}")
    print(f"Confidence: {recommendation.get('confidence')}")
else:
    print(f"Error: {result.get('error')}")
