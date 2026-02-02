"""
Debug The Lyndon data extraction issues
"""
import pandas as pd
import PyPDF2
import logging
import os
from services.file_processor import FileProcessor

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# File paths
base_path = r'sample_files\The Lyndon'
cash_forecast_path = os.path.join(base_path, '139 Lyndon Cash Forecast_12.2025.xlsx')
income_statement_path = os.path.join(base_path, '03_The Lyndon_Comparative Income Statement_December-25.pdf')
balance_sheet_path = os.path.join(base_path, '02_The Lyndon_Balance_Sheet_December-25.pdf')

print("="*80)
print("EXAMINING THE LYNDON FILES")
print("="*80)

# Test 1: Cash Forecast Excel
print("\n1. CASH FORECAST ANALYSIS")
print("-"*80)
try:
    df = pd.read_excel(cash_forecast_path, sheet_name=0, header=None)
    print(f"✓ File loaded successfully - Shape: {df.shape}")
    
    print("\nFirst 10 rows, first 15 columns:")
    print(df.iloc[:10, :15])
    
    print("\nRow 6 (Status row?):")
    print(df.iloc[6, :15].tolist())
    
    print("\nRow 7 (Month row?):")
    print(df.iloc[7, :15].tolist())
    
    print("\nColumn 1 (Row labels):")
    for i in range(30):
        val = df.iloc[i, 1]
        if pd.notna(val):
            print(f"  Row {i}: {val}")
    
except Exception as e:
    print(f"✗ Error loading cash forecast: {str(e)}")

# Test 2: Income Statement
print("\n\n2. INCOME STATEMENT ANALYSIS")
print("-"*80)
try:
    with open(income_statement_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        print(f"✓ File loaded - {len(pdf_reader.pages)} page(s)")
        
        text = pdf_reader.pages[0].extract_text()
        print("\nFirst 1000 characters of extracted text:")
        print(text[:1000])
        
        # Look for key patterns
        if 'Total Operating Income' in text:
            print("\n✓ Found 'Total Operating Income'")
        else:
            print("\n✗ 'Total Operating Income' not found")
            
        if 'Total Operating Expenses' in text:
            print("✓ Found 'Total Operating Expenses'")
        else:
            print("✗ 'Total Operating Expenses' not found")
            
except Exception as e:
    print(f"✗ Error loading income statement: {str(e)}")

# Test 3: Balance Sheet
print("\n\n3. BALANCE SHEET ANALYSIS")
print("-"*80)
try:
    with open(balance_sheet_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        print(f"✓ File loaded - {len(pdf_reader.pages)} page(s)")
        
        text = pdf_reader.pages[0].extract_text()
        print("\nFirst 1000 characters of extracted text:")
        print(text[:1000])
        
        # Look for key patterns
        if 'Cash and Cash Equivalents' in text:
            print("\n✓ Found 'Cash and Cash Equivalents'")
        else:
            print("\n✗ 'Cash and Cash Equivalents' not found")
            
        if 'Current Liabilities' in text:
            print("✓ Found 'Current Liabilities'")
        else:
            print("✗ 'Current Liabilities' not found")
            
except Exception as e:
    print(f"✗ Error loading balance sheet: {str(e)}")

# Test 4: Full FileProcessor parse
print("\n\n4. FILEPROCESSOR PARSE TEST")
print("-"*80)
try:
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("⚠ Warning: OPENAI_API_KEY not found")
        api_key = "dummy"
    
    processor = FileProcessor(api_key)
    
    print("\nParsing cash forecast...")
    cash_result = processor.parse_cash_forecast(cash_forecast_path)
    print(f"Status: {cash_result.get('status')}")
    if cash_result.get('status') == 'success':
        print(f"  Property: {cash_result.get('property_name')}")
        print(f"  Current Month: {cash_result.get('current_month')}")
        print(f"  Current FCF: ${cash_result.get('current_fcf', 0):,.2f}")
        print(f"  Projected FCF: ${cash_result.get('projected_fcf', 0):,.2f}")
        print(f"  Current Occupancy: {cash_result.get('current_occupancy', 0):.1f}%")
    else:
        print(f"  Error: {cash_result.get('error')}")
    
    print("\nParsing income statement...")
    income_result = processor.parse_income_statement(income_statement_path)
    print(f"Status: {income_result.get('status')}")
    if income_result.get('status') == 'success':
        print(f"  Reporting Month: {income_result.get('reporting_month')}")
        print(f"  Income (Month): ${income_result.get('income_month_actual', 0):,.2f}")
        print(f"  NOI (Month): ${income_result.get('noi_month_actual', 0):,.2f}")
    else:
        print(f"  Error: {income_result.get('error')}")
    
    print("\nParsing balance sheet...")
    balance_result = processor.parse_balance_sheet(balance_sheet_path)
    print(f"Status: {balance_result.get('status')}")
    if balance_result.get('status') == 'success':
        print(f"  Cash Balance: ${balance_result.get('cash_balance', 0):,.2f}")
        print(f"  Current Liabilities: ${balance_result.get('current_liabilities', 0):,.2f}")
        print(f"  Months of Reserves: {balance_result.get('months_of_reserves', 0):.1f}")
    else:
        print(f"  Error: {balance_result.get('error')}")
    
except Exception as e:
    print(f"✗ Error in FileProcessor test: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
print("DEBUG COMPLETE")
print("="*80)
