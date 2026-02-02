"""
Test PDF extraction methods for The Lyndon files
"""
import PyPDF2
import pdfplumber

income_path = r'sample_files\The Lyndon\03_The Lyndon_Comparative Income Statement_December-25.pdf'
balance_path = r'sample_files\The Lyndon\02_The Lyndon_Balance_Sheet_December-25.pdf'

print("="*80)
print("TESTING PDF TEXT EXTRACTION - THE LYNDON")
print("="*80)

# Test Income Statement
print("\n1. INCOME STATEMENT - PyPDF2:")
print("-"*80)
try:
    with open(income_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        print(f"Pages: {len(pdf_reader.pages)}")
        for i, page in enumerate(pdf_reader.pages):
            text = page.extract_text()
            print(f"\nPage {i+1} - Length: {len(text)} chars")
            if text:
                print(f"First 500 chars: {text[:500]}")
            else:
                print("  ✗ No text extracted")
except Exception as e:
    print(f"Error: {e}")

print("\n2. INCOME STATEMENT - pdfplumber:")
print("-"*80)
try:
    with pdfplumber.open(income_path) as pdf:
        print(f"Pages: {len(pdf.pages)}")
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            print(f"\nPage {i+1} - Length: {len(text) if text else 0} chars")
            if text:
                print(f"First 500 chars: {text[:500]}")
                
                # Look for key patterns
                if 'Operating Income' in text:
                    print("  ✓ Found 'Operating Income'")
                if 'Operating Expenses' in text:
                    print("  ✓ Found 'Operating Expenses'")
            else:
                print("  ✗ No text extracted")
except Exception as e:
    print(f"Error: {e}")

# Test Balance Sheet
print("\n\n3. BALANCE SHEET - PyPDF2:")
print("-"*80)
try:
    with open(balance_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        print(f"Pages: {len(pdf_reader.pages)}")
        for i, page in enumerate(pdf_reader.pages):
            text = page.extract_text()
            print(f"\nPage {i+1} - Length: {len(text)} chars")
            if text:
                print(f"First 500 chars: {text[:500]}")
            else:
                print("  ✗ No text extracted")
except Exception as e:
    print(f"Error: {e}")

print("\n4. BALANCE SHEET - pdfplumber:")
print("-"*80)
try:
    with pdfplumber.open(balance_path) as pdf:
        print(f"Pages: {len(pdf.pages)}")
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            print(f"\nPage {i+1} - Length: {len(text) if text else 0} chars")
            if text:
                print(f"First 500 chars: {text[:500]}")
                
                # Look for key patterns
                if 'Cash' in text:
                    print("  ✓ Found 'Cash'")
                if 'Liabilities' in text:
                    print("  ✓ Found 'Liabilities'")
            else:
                print("  ✗ No text extracted")
except Exception as e:
    print(f"Error: {e}")
