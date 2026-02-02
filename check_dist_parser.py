"""
Check what distribution row the parser is finding
"""
import pandas as pd
import os

file_path = r'sample_files\The Republic\163 The Republic Cash Forecast - 12.2025.xlsx'

df = pd.read_excel(file_path, sheet_name=0, header=None)

print("="*100)
print("SEARCHING FOR DISTRIBUTION ROWS")
print("="*100)
print()

# Find all rows mentioning distribution or contribution
for idx, row in df.iterrows():
    cell_val = str(row[0]).upper() if row[0] else ''
    if 'DISTRIBUT' in cell_val or 'CONTRIBUT' in cell_val:
        print(f"Row {idx}: {row[0]}")
        # Show a few values from this row
        sample_vals = [v for v in row[1:10].tolist() if pd.notna(v) and v != 0]
        if sample_vals:
            print(f"  Sample values: {sample_vals[:3]}")
        print()

print("="*100)
print("WHAT THE PARSER WOULD FIND")
print("="*100)
print()

# Simulate what the parser does
search_terms = ['Distributions', 'Contribution', 'ACTUAL (Distributions)']
for term in search_terms:
    for idx, row in df.iterrows():
        if pd.notna(row[0]) and term in str(row[0]):
            print(f"Term '{term}' matches row {idx}: {row[0]}")
            break
    else:
        print(f"Term '{term}' - NO MATCH")

print()
print("="*100)
print("RECOMMENDATION")
print("="*100)
print()
print("We should be looking for:")
print("  - 'FORECASTED' or 'Forecasted' for budget month distributions")
print("  - 'ACTUAL' for actual month distributions (what already happened)")
