"""
Extract and analyze key financial totals from Comparative Income Statement
"""
import PyPDF2
import re

pdf_path = r'sample_files\04_Rittenhouse Station_Comparative Income Statement_September 2025.pdf'

def clean_number(s):
    """Convert string like '425,818.20' or '(1,234.56)' to float"""
    s = s.replace(',', '').replace('$', '').strip()
    if s.startswith('(') and s.endswith(')'):
        return -float(s[1:-1])
    return float(s)

def extract_line_item(text, label):
    """Extract a financial line item with month and YTD data"""
    # Pattern: Label Actual Budget $Var %Var Actual Budget $Var %Var
    pattern = rf'{re.escape(label)}\s+([\d,.-]+(?:\(\))?)\s+([\d,.-]+(?:\(\))?)\s+\(?([\d,.-]+)\)?\s+([-\d.]+%)\s+([\d,.-]+(?:\(\))?)\s+([\d,.-]+(?:\(\))?)\s+\(?([\d,.-]+)\)?\s+([-\d.]+%)'
    
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return {
            'month_actual': match.group(1),
            'month_budget': match.group(2),
            'month_variance_$': match.group(3),
            'month_variance_%': match.group(4),
            'ytd_actual': match.group(5),
            'ytd_budget': match.group(6),
            'ytd_variance_$': match.group(7),
            'ytd_variance_%': match.group(8),
        }
    return None

print("=" * 120)
print("RITTENHOUSE STATION - COMPARATIVE INCOME STATEMENT")
print("September 2025")
print("=" * 120)
print()

with open(pdf_path, 'rb') as file:
    pdf_reader = PyPDF2.PdfReader(file)
    
    # Combine all pages
    all_text = ""
    for page in pdf_reader.pages:
        all_text += page.extract_text() + "\n"
    
    # Key line items to extract
    line_items = [
        'Total Operating Income',
        'Total Operating Expenses',
        'NET OPERATING INCOME',
        'NET INCOME'
    ]
    
    results = {}
    for item in line_items:
        data = extract_line_item(all_text, item)
        if data:
            results[item] = data
    
    if results:
        print("SEPTEMBER 2025 (CURRENT MONTH)")
        print("-" * 120)
        print(f"{'Line Item':<35} {'Actual':>18} {'Budget':>18} {'$ Variance':>18} {'% Variance':>15}")
        print("-" * 120)
        
        for label, data in results.items():
            actual_val = clean_number(data['month_actual'])
            budget_val = clean_number(data['month_budget'])
            var_val = clean_number(data['month_variance_$'])
            var_pct = data['month_variance_%']
            
            print(f"{label:<35} ${actual_val:>17,.2f} ${budget_val:>17,.2f} ${var_val:>17,.2f} {var_pct:>14}")
        
        print()
        print()
        print("YEAR-TO-DATE 2025 (JAN - SEP)")
        print("-" * 120)
        print(f"{'Line Item':<35} {'Actual':>18} {'Budget':>18} {'$ Variance':>18} {'% Variance':>15}")
        print("-" * 120)
        
        for label, data in results.items():
            actual_val = clean_number(data['ytd_actual'])
            budget_val = clean_number(data['ytd_budget'])
            var_val = clean_number(data['ytd_variance_$'])
            var_pct = data['ytd_variance_%']
            
            print(f"{label:<35} ${actual_val:>17,.2f} ${budget_val:>17,.2f} ${var_val:>17,.2f} {var_pct:>14}")
        
        print()
        print()
        print("=" * 120)
        print("KEY INSIGHTS FOR CASH FORECAST VALIDATION")
        print("=" * 120)
        print()
        
        if 'NET OPERATING INCOME' in results:
            noi_data = results['NET OPERATING INCOME']
            ytd_var_pct = float(noi_data['ytd_variance_%'].replace('%', ''))
            month_var_pct = float(noi_data['month_variance_%'].replace('%', ''))
            ytd_actual = clean_number(noi_data['ytd_actual'])
            ytd_budget = clean_number(noi_data['ytd_budget'])
            
            print(f"1. NET OPERATING INCOME Analysis:")
            print(f"   YTD Actual:  ${ytd_actual:,.2f}")
            print(f"   YTD Budget:  ${ytd_budget:,.2f}")
            print(f"   YTD Variance: {ytd_var_pct:+.2f}%")
            print(f"   Sep Variance: {month_var_pct:+.2f}%")
            print()
            
            if abs(ytd_var_pct) > 10:
                print(f"   ⚠️  CRITICAL: NOI variance exceeds 10% - budget assumptions significantly off!")
            elif abs(ytd_var_pct) > 5:
                print(f"   ⚠️  WARNING: NOI variance exceeds 5% - review budget assumptions")
            else:
                print(f"   ✓  NOI tracking within acceptable range")
            print()
        
        if 'Total Operating Income' in results:
            income_data = results['Total Operating Income']
            ytd_var_pct = float(income_data['ytd_variance_%'].replace('%', ''))
            
            print(f"2. OPERATING INCOME Analysis:")
            print(f"   YTD Variance: {ytd_var_pct:+.2f}%")
            
            if ytd_var_pct < -5:
                print(f"   ⚠️  Revenue tracking below budget - occupancy or rates may be issue")
            elif ytd_var_pct > 5:
                print(f"   ✓  Revenue exceeding budget")
            else:
                print(f"   ✓  Revenue tracking to budget")
            print()
        
        if 'Total Operating Expenses' in results:
            expense_data = results['Total Operating Expenses']
            ytd_var_pct = float(expense_data['ytd_variance_%'].replace('%', ''))
            ytd_var_amt = clean_number(expense_data['ytd_variance_$'])
            
            print(f"3. OPERATING EXPENSES Analysis:")
            print(f"   YTD Variance: {ytd_var_pct:+.2f}% (${ytd_var_amt:,.2f})")
            
            if ytd_var_pct > 5:
                print(f"   ⚠️  Expenses exceeding budget - investigate major cost overruns")
            elif ytd_var_pct < 0:
                print(f"   ✓  Expenses under budget")
            else:
                print(f"   ✓  Expenses tracking to budget")
            print()
        
        print("\n" + "=" * 120)
        print("RECOMMENDATION FOR CASH FORECAST:")
        print("=" * 120)
        print()
        print("Based on actual vs. budget performance through September:")
        print("- Use income statement variances to adjust remaining 2025 budget assumptions")
        print("- If NOI variance is significant, recalculate projected cash flow for Oct-Dec")
        print("- Review specific expense categories with large variances before finalizing recommendation")
        
    else:
        print("⚠️  Could not extract financial totals")
        print("\nShowing sample text for debugging:")
        print(all_text[:1500])

print()
