"""
Test date extraction from income statement PDFs
"""
import os
from services.file_processor import FileProcessor

# Test with University Place (December statement)
income_statement_path = r'sample_files\University Place\03_University Place_Comparative Income Statement_December-25.pdf'

if os.path.exists(income_statement_path):
    print("Testing income statement date extraction...")
    print(f"File: {income_statement_path}\n")
    
    processor = FileProcessor(openai_api_key="test")
    result = processor.parse_income_statement(income_statement_path)
    
    if result.get('status') == 'success':
        print("✓ Parse successful!\n")
        print(f"Reporting Month: {result.get('reporting_month', 'NOT FOUND')}")
        print(f"YTD Period: {result.get('ytd_period', 'NOT FOUND')}")
        print(f"\nMonth Actuals:")
        print(f"  Income: ${result.get('income_month_actual', 0):,.2f}")
        print(f"  Expenses: ${result.get('expenses_month_actual', 0):,.2f}")
        print(f"  NOI: ${result.get('noi_month_actual', 0):,.2f}")
        print(f"\nYTD Actuals:")
        print(f"  Income: ${result.get('income_ytd_actual', 0):,.2f}")
        print(f"  Expenses: ${result.get('expenses_ytd_actual', 0):,.2f}")
        print(f"  NOI: ${result.get('noi_ytd_actual', 0):,.2f}")
    else:
        print(f"✗ Parse failed: {result.get('error')}")
else:
    print(f"File not found: {income_statement_path}")

print("\n" + "="*80)

# Also test with September statement for comparison
income_statement_path2 = r'sample_files\Rittenhouse Station\04_Rittenhouse Station_Comparative_Income Statement_September 2025.pdf'
if os.path.exists(income_statement_path2):
    print("\nTesting with September statement...")
    print(f"File: {income_statement_path2}\n")
    
    result2 = processor.parse_income_statement(income_statement_path2)
    
    if result2.get('status') == 'success':
        print("✓ Parse successful!\n")
        print(f"Reporting Month: {result2.get('reporting_month', 'NOT FOUND')}")
        print(f"YTD Period: {result2.get('ytd_period', 'NOT FOUND')}")
    else:
        print(f"✗ Parse failed: {result2.get('error')}")
