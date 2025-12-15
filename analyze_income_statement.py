"""
Analyze the Comparative Income Statement PDF
Extract key totals: Operating Income, Operating Expenses, Net Operating Income, etc.
"""
import pdfplumber
import re

pdf_path = r'sample_files\04_Rittenhouse_Station_Comparative Income Statement_September_2025.pdf'

print("=" * 100)
print("COMPARATIVE INCOME STATEMENT ANALYSIS")
print("=" * 100)
print()

with pdfplumber.open(pdf_path) as pdf:
    print(f"Total pages: {len(pdf.pages)}")
    print()
    
    for page_num, page in enumerate(pdf.pages, 1):
        print(f"\n{'='*100}")
        print(f"PAGE {page_num}")
        print(f"{'='*100}\n")
        
        # Extract text
        text = page.extract_text()
        if text:
            print(text)
        
        # Try to extract tables
        tables = page.extract_tables()
        if tables:
            print(f"\n--- Found {len(tables)} table(s) on page {page_num} ---\n")
            for i, table in enumerate(tables, 1):
                print(f"Table {i}:")
                for row in table[:10]:  # Show first 10 rows
                    print(row)
                if len(table) > 10:
                    print(f"... ({len(table) - 10} more rows)")
                print()
