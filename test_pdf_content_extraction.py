"""
Test that date extraction uses PDF content, not filename
"""
from services.file_processor import FileProcessor

processor = FileProcessor(openai_api_key="test")

# This file has "December-25" in filename
result = processor.parse_income_statement(
    r'sample_files\University Place\03_University Place_Comparative Income Statement_December-25.pdf'
)

print("="*80)
print("TESTING: PDF Content vs Filename")
print("="*80)
print()
print("Filename says: 'December-25'")
print(f"PDF content says: '{result.get('reporting_month')}'")
print(f"YTD Period: '{result.get('ytd_period')}'")
print()

if result.get('reporting_month') == 'December 2025' and result.get('ytd_period') == 'Jan-Dec':
    print("✅ SUCCESS: Extracted from PDF content (not filename)")
else:
    print("❌ FAILED: Did not extract correctly from PDF")
