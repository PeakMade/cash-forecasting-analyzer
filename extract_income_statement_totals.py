"""
Extract key totals from Comparative Income Statement PDF
Focus on: Total Operating Income, Total Operating Expenses, Net Operating Income
"""
import PyPDF2
import re

pdf_path = r'sample_files\04_Rittenhouse Station_Comparative Income Statement_September 2025.pdf'

def extract_financial_data(text):
    """Extract key financial line items from the income statement"""
    
    # Patterns to find key totals
    patterns = {
        'Total Operating Income': r'Total Operating Income\s+([\d,.-]+)\s+([\d,.-]+)\s+([\d,.-]+)\s+([\d,.-]+%)\s+([\d,.-]+)\s+([\d,.-]+)\s+([\d,.-]+)\s+([\d,.-]+%)',
        'Total Administrative Expenses': r'Total Administrative Expenses\s+([\d,.-]+)\s+([\d,.-]+)\s+([\d,.-]+)\s+([\d,.-]+%)\s+([\d,.-]+)\s+([\d,.-]+)\s+([\d,.-]+)\s+([\d,.-]+%)',
        'Total Operating Expenses': r'Total Operating Expenses\s+([\d,.-]+)\s+([\d,.-]+)\s+([\d,.-]+)\s+([\d,.-]+%)\s+([\d,.-]+)\s+([\d,.-]+)\s+([\d,.-]+)\s+([\d,.-]+%)',
        'Net Operating Income': r'Net Operating Income\s+([\d,.-]+)\s+([\d,.-]+)\s+([\d,.-]+)\s+([\d,.-]+%)\s+([\d,.-]+)\s+([\d,.-]+)\s+([\d,.-]+)\s+([\d,.-]+%)',
        'Cash Flow': r'Cash Flow.*?\s+([\d,.-]+)\s+([\d,.-]+)\s+([\d,.-]+)\s+([\d,.-]+%)\s+([\d,.-]+)\s+([\d,.-]+)\s+([\d,.-]+)\s+([\d,.-]+%)',
    }
    
    results = {}
    for label, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            results[label] = {
                'month_actual': match.group(1),
                'month_budget': match.group(2),
                'month_variance_$': match.group(3),
                'month_variance_%': match.group(4),
                'ytd_actual': match.group(5),
                'ytd_budget': match.group(6),
                'ytd_variance_$': match.group(7),
                'ytd_variance_%': match.group(8),
            }
    
    return results

print("=" * 120)
print("COMPARATIVE INCOME STATEMENT - KEY TOTALS ANALYSIS")
print("=" * 120)
print()

with open(pdf_path, 'rb') as file:
    pdf_reader = PyPDF2.PdfReader(file)
    
    all_text = ""
    for page in pdf_reader.pages:
        all_text += page.extract_text() + "\n"
    
    # Extract financial data
    financial_data = extract_financial_data(all_text)
    
    if financial_data:
        print("SEPTEMBER 2025 (MONTH)")
        print("-" * 120)
        print(f"{'Line Item':<40} {'Actual':>15} {'Budget':>15} {'Variance $':>15} {'Variance %':>12}")
        print("-" * 120)
        
        for label, data in financial_data.items():
            print(f"{label:<40} ${data['month_actual']:>14} ${data['month_budget']:>14} ${data['month_variance_$']:>14} {data['month_variance_%']:>11}")
        
        print()
        print()
        print("YEAR-TO-DATE 2025 (JAN - SEP)")
        print("-" * 120)
        print(f"{'Line Item':<40} {'Actual':>15} {'Budget':>15} {'Variance $':>15} {'Variance %':>12}")
        print("-" * 120)
        
        for label, data in financial_data.items():
            print(f"{label:<40} ${data['ytd_actual']:>14} ${data['ytd_budget']:>14} ${data['ytd_variance_$']:>14} {data['ytd_variance_%']:>11}")
        
        print()
        print("=" * 120)
        print("ANALYSIS")
        print("=" * 120)
        
        # Parse numeric values for analysis
        if 'Net Operating Income' in financial_data:
            noi_data = financial_data['Net Operating Income']
            ytd_variance_pct = float(noi_data['ytd_variance_%'].replace('%', '').replace(',', ''))
            
            print(f"\nNet Operating Income YTD Variance: {ytd_variance_pct:+.2f}%")
            
            if abs(ytd_variance_pct) > 5:
                print(f"⚠️  WARNING: NOI variance exceeds 5% threshold")
                print(f"   This suggests budget assumptions may be significantly off")
            else:
                print(f"✓  NOI tracking within 5% of budget")
        
    else:
        print("Could not extract financial totals from PDF")
        print("\nShowing raw text for debugging:")
        print("-" * 120)
        print(all_text[:2000])

print()
