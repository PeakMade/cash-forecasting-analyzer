"""
Analyze Balance Sheet for cash forecasting insights
Key focus: Liquidity, debt service capability, working capital trends
"""
import PyPDF2
import re

pdf_path = r'sample_files\03_Rittenhouse Station_Balance Sheet_September 2025.pdf'

def clean_number(s):
    """Convert string like '647,795.50' or '(6,300,604.77)' to float"""
    s = s.replace(',', '').replace('$', '').strip()
    if s.startswith('(') and s.endswith(')'):
        return -float(s[1:-1])
    try:
        return float(s)
    except:
        return 0.0

print("=" * 120)
print("RITTENHOUSE STATION - BALANCE SHEET ANALYSIS")
print("September 2025 vs August 2025")
print("=" * 120)
print()

with open(pdf_path, 'rb') as file:
    pdf_reader = PyPDF2.PdfReader(file)
    all_text = ''.join([page.extract_text() for page in pdf_reader.pages])
    
    # Extract key balance sheet items
    patterns = {
        'Total Cash and Cash Equivalents': r'Total Cash and Cash Equivalents\s+([\d,.-]+)\s+([\d,.-]+)\s+\(?([\d,.-]+)\)?',
        'Total Accounts Receivable': r'Total Accounts Receivable\s+([\d,.-]+)\s+([\d,.-]+)\s+\(?([\d,.-]+)\)?',
        'Total Fixed Assets': r'Total Fixed Assets\s+([\d,.-]+)\s+([\d,.-]+)\s+\(?([\d,.-]+)\)?',
        'Total Assets': r'Total Assets\s+([\d,.-]+)\s+([\d,.-]+)\s+\(?([\d,.-]+)\)?',
        'Total Current Liabilities': r'Total Current Liabilities\s+([\d,.-]+)\s+([\d,.-]+)\s+\(?([\d,.-]+)\)?',
        'Total Notes Payable': r'Total Notes Payable\s+([\d,.-]+)\s+([\d,.-]+)\s+\(?([\d,.-]+)\)?',
        'Total Liabilities': r'Total Liabilities\s+([\d,.-]+)\s+([\d,.-]+)\s+\(?([\d,.-]+)\)?',
        'Total Capital/Equity': r'Total Capital/Equity\s+([\d,.-]+)\s+([\d,.-]+)\s+\(?([\d,.-]+)\)?',
        'Retained Earnings': r'3300-00 Retained Earnings\s+\(?([\d,.-]+)\)?\s+\(?([\d,.-]+)\)?\s+\(?([\d,.-]+)\)?',
        'Security Deposits Payable': r'2020-00 Security Deposits Payable\s+([\d,.-]+)\s+([\d,.-]+)\s+\(?([\d,.-]+)\)?',
        'Accrued Interest': r'2070-00 Accrued Interest\s+([\d,.-]+)\s+([\d,.-]+)\s+\(?([\d,.-]+)\)?',
    }
    
    data = {}
    for label, pattern in patterns.items():
        match = re.search(pattern, all_text)
        if match:
            data[label] = {
                'sep_2025': clean_number(match.group(1)),
                'aug_2025': clean_number(match.group(2)),
                'variance': clean_number(match.group(3))
            }
    
    if data:
        # Display key sections
        print("ASSETS")
        print("-" * 120)
        print(f"{'Line Item':<40} {'Sep 2025':>18} {'Aug 2025':>18} {'Variance':>18} {'% Change':>15}")
        print("-" * 120)
        
        asset_items = ['Total Cash and Cash Equivalents', 'Total Accounts Receivable', 'Total Fixed Assets', 'Total Assets']
        for item in asset_items:
            if item in data:
                sep_val = data[item]['sep_2025']
                aug_val = data[item]['aug_2025']
                var_val = data[item]['variance']
                pct_change = (var_val / aug_val * 100) if aug_val != 0 else 0
                print(f"{item:<40} ${sep_val:>17,.2f} ${aug_val:>17,.2f} ${var_val:>17,.2f} {pct_change:>14.2f}%")
        
        print()
        print("LIABILITIES")
        print("-" * 120)
        print(f"{'Line Item':<40} {'Sep 2025':>18} {'Aug 2025':>18} {'Variance':>18} {'% Change':>15}")
        print("-" * 120)
        
        liability_items = ['Total Current Liabilities', 'Total Notes Payable', 'Total Liabilities']
        for item in liability_items:
            if item in data:
                sep_val = data[item]['sep_2025']
                aug_val = data[item]['aug_2025']
                var_val = data[item]['variance']
                pct_change = (var_val / aug_val * 100) if aug_val != 0 else 0
                print(f"{item:<40} ${sep_val:>17,.2f} ${aug_val:>17,.2f} ${var_val:>17,.2f} {pct_change:>14.2f}%")
        
        print()
        print("EQUITY")
        print("-" * 120)
        print(f"{'Line Item':<40} {'Sep 2025':>18} {'Aug 2025':>18} {'Variance':>18} {'% Change':>15}")
        print("-" * 120)
        
        if 'Total Capital/Equity' in data:
            sep_val = data['Total Capital/Equity']['sep_2025']
            aug_val = data['Total Capital/Equity']['aug_2025']
            var_val = data['Total Capital/Equity']['variance']
            pct_change = (var_val / aug_val * 100) if aug_val != 0 else 0
            print(f"{'Total Capital/Equity':<40} ${sep_val:>17,.2f} ${aug_val:>17,.2f} ${var_val:>17,.2f} {pct_change:>14.2f}%")
        
        if 'Retained Earnings' in data:
            sep_val = data['Retained Earnings']['sep_2025']
            aug_val = data['Retained Earnings']['aug_2025']
            var_val = data['Retained Earnings']['variance']
            print(f"{'  - Retained Earnings':<40} ${sep_val:>17,.2f} ${aug_val:>17,.2f} ${var_val:>17,.2f}")
        
        print()
        print()
        print("=" * 120)
        print("LIQUIDITY & CASH FORECASTING INSIGHTS")
        print("=" * 120)
        print()
        
        # Calculate key metrics
        if 'Total Cash and Cash Equivalents' in data and 'Total Current Liabilities' in data:
            cash_sep = data['Total Cash and Cash Equivalents']['sep_2025']
            cash_aug = data['Total Cash and Cash Equivalents']['aug_2025']
            cash_variance = data['Total Cash and Cash Equivalents']['variance']
            current_liab = data['Total Current Liabilities']['sep_2025']
            
            print(f"1. CASH POSITION:")
            print(f"   September Cash: ${cash_sep:,.2f}")
            print(f"   August Cash:    ${cash_aug:,.2f}")
            print(f"   Change:         ${cash_variance:,.2f} ({(cash_variance/cash_aug*100):.2f}%)")
            print()
            
            # Cash decreased by ~$140k - this aligns with positive cash flow in the forecast
            if cash_variance < -100000:
                print(f"   ⚠️  CRITICAL: Cash declined by ${abs(cash_variance):,.2f} month-over-month")
                print(f"      • This is a significant cash outflow - investigate causes")
                print(f"      • Could indicate: debt payments, distributions, capex, or operating losses")
            elif cash_variance < 0:
                print(f"   ⚠️  Cash decreased by ${abs(cash_variance):,.2f}")
            else:
                print(f"   ✓  Cash increased - positive operating performance")
            print()
            
            # Working Capital Analysis
            print(f"2. WORKING CAPITAL (Current Liquidity):")
            if 'Total Accounts Receivable' in data:
                ar = data['Total Accounts Receivable']['sep_2025']
                working_capital = cash_sep + ar - current_liab
                current_ratio = (cash_sep + ar) / current_liab if current_liab > 0 else 0
                
                print(f"   Current Assets (Cash + AR): ${cash_sep + ar:,.2f}")
                print(f"   Current Liabilities:        ${current_liab:,.2f}")
                print(f"   Working Capital:            ${working_capital:,.2f}")
                print(f"   Current Ratio:              {current_ratio:.2f}:1")
                print()
                
                if current_ratio < 1.0:
                    print(f"   ⚠️  CRITICAL: Current ratio below 1.0 - liquidity concerns!")
                elif current_ratio < 1.5:
                    print(f"   ⚠️  Current ratio below 1.5 - monitor liquidity closely")
                else:
                    print(f"   ✓  Healthy current ratio - adequate liquidity")
            print()
        
        if 'Total Notes Payable' in data:
            debt_sep = data['Total Notes Payable']['sep_2025']
            debt_aug = data['Total Notes Payable']['aug_2025']
            debt_paydown = abs(data['Total Notes Payable']['variance'])
            
            print(f"3. DEBT SERVICE:")
            print(f"   Outstanding Debt:     ${debt_sep:,.2f}")
            print(f"   Principal Paid (Sep): ${debt_paydown:,.2f}")
            print()
            
            if 'Accrued Interest' in data:
                accrued_interest = data['Accrued Interest']['sep_2025']
                print(f"   Accrued Interest:     ${accrued_interest:,.2f}")
                print()
            
            # Monthly debt service (principal + interest estimate)
            monthly_debt_service = debt_paydown + (debt_paydown * 0.5)  # Rough estimate
            print(f"   Est. Monthly Debt Service: ~${monthly_debt_service:,.2f}")
            print()
            
            if cash_sep < monthly_debt_service * 3:
                print(f"   ⚠️  WARNING: Cash covers less than 3 months of debt service")
            else:
                print(f"   ✓  Adequate cash reserves for debt service")
            print()
        
        # NOI calculation from Income Statement for debt service coverage
        print(f"4. DEBT SERVICE COVERAGE (Using Income Statement NOI):")
        print(f"   September NOI: $245,061 (from Income Statement)")
        if 'Total Notes Payable' in data:
            debt_paydown = abs(data['Total Notes Payable']['variance'])
            if 'Accrued Interest' in data:
                # Interest variance shows interest paid/accrued change
                accrued_int_variance = data['Accrued Interest']['variance']
                monthly_debt = debt_paydown + abs(accrued_int_variance)
                dscr = 245061 / monthly_debt if monthly_debt > 0 else 0
                print(f"   Est. Debt Service: ${monthly_debt:,.2f}")
                print(f"   DSCR: {dscr:.2f}x")
                print()
                
                if dscr < 1.0:
                    print(f"   🚨 CRITICAL: DSCR below 1.0 - property cannot cover debt from operations!")
                elif dscr < 1.25:
                    print(f"   ⚠️  WARNING: DSCR below 1.25 - tight debt coverage")
                else:
                    print(f"   ✓  Healthy DSCR - strong debt service capacity")
        print()
        
        print()
        print("=" * 120)
        print("KEY BALANCE SHEET INSIGHTS FOR CASH FORECASTING")
        print("=" * 120)
        print()
        
        print("SUMMARY:")
        print()
        print("• Cash Position: Cash decreased $140k month-over-month despite positive NOI")
        print("  → Likely due to: debt service ($57k principal + interest), and other outflows")
        print()
        print("• Liquidity Ratio: Strong current ratio indicates ability to meet short-term obligations")
        print()
        print("• Debt Service: Property making regular principal payments (~$57k/month)")
        print("  → This is a significant fixed cash outflow that reduces available free cash")
        print()
        print("• October Forecast Deficit: The projected -$18k FCF may be accurate considering:")
        print("  → Seasonal factors, debt service obligations, and recent cash burn rate")
        print()
        print("RECOMMENDATION FACTORS:")
        print("✓ YTD NOI is 3.24% ahead of budget → Property performing well operationally")
        print("✓ Strong liquidity position → Can absorb temporary deficit without issue")
        print("⚠️  Sept NOI was 8.61% below budget → Recent performance weakening")
        print("⚠️  Cash burned $140k in September → Investigate if this trend continues")
        print()
        print("DECISION: With $1.47M cash and October showing -$18k deficit:")
        print("→ NO IMMEDIATE ACTION NEEDED - property has ample reserves")
        print("→ MONITOR: If cash burn continues at $140k/month, reserves deplete in ~10 months")
        print("→ CONSIDER: Review Q4 budget assumptions if September trend persists")

print()
