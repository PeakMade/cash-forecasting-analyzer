"""
Debug script to examine The Republic cash forecast file structure
"""
import pandas as pd
import sys

file_path = r'sample_files\The Republic\163 The Republic Cash Forecast - 12.2025.xlsx'

try:
    df = pd.read_excel(file_path, sheet_name='Cash Forecast', header=None)
    
    print("="*100)
    print("EXAMINING THE REPUBLIC CASH FORECAST FILE")
    print("="*100)
    print()
    
    # Find year 2025 columns (row 5 has year)
    year_row = df.iloc[5, :].tolist()
    year_2025_cols = [i for i, val in enumerate(year_row) if pd.notna(val) and (val == 2025 or str(val) == '2025')]
    print(f"Year 2025 columns: {year_2025_cols}")
    print()
    
    # Extract status and month rows for 2025 columns only
    status_row = df.iloc[6, year_2025_cols].tolist()
    month_row = df.iloc[7, year_2025_cols].tolist()
    
    print("Status row (row 6) for 2025 columns:")
    for i, (status, month) in enumerate(zip(status_row, month_row)):
        print(f"  Col {year_2025_cols[i]:2d}: Status='{status}', Month={month}")
    print()
    
    # Count actual vs budget columns
    actual_count = sum(1 for s in status_row if isinstance(s, str) and 'actual' in s.lower())
    budget_count = sum(1 for s in status_row if isinstance(s, str) and 'budget' in s.lower())
    
    print(f"Actual months: {actual_count}")
    print(f"Budget months: {budget_count}")
    print()
    
    # Find the current month index and budget month indices
    current_month_idx = None
    budget_month_indices = []
    
    for i, status in enumerate(status_row):
        if isinstance(status, str):
            if 'actual' in status.lower():
                current_month_idx = i
            elif 'budget' in status.lower() and current_month_idx is not None:
                budget_month_indices.append(i)
    
    print(f"Current month index (last actual): {current_month_idx}")
    print(f"Budget month indices found: {budget_month_indices}")
    print()
    
    if current_month_idx is not None:
        print(f"Current month: {month_row[current_month_idx]}")
    
    print(f"\nBudget months found ({len(budget_month_indices)}):")
    for idx in budget_month_indices:
        print(f"  - {month_row[idx]}")
    print()
    
    # Check FCF row for these months
    fcf_label = 'Free Cash Flow'
    fcf_row_idx = None
    for idx, row in df.iterrows():
        if row[0] == fcf_label:
            fcf_row_idx = idx
            break
    
    if fcf_row_idx:
        print(f"FCF row found at index {fcf_row_idx}")
        fcf_row = df.iloc[fcf_row_idx, year_2025_cols].tolist()
        
        print("\nFCF values for budget months:")
        for idx in budget_month_indices:
            val = fcf_row[idx]
            print(f"  {month_row[idx]}: {val} (is NaN: {pd.isna(val)})")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
