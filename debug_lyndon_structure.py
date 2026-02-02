"""
Deep dive into The Lyndon Excel structure
"""
import pandas as pd

cash_forecast_path = r'sample_files\The Lyndon\139 Lyndon Cash Forecast_12.2025.xlsx'

df = pd.read_excel(cash_forecast_path, sheet_name=0, header=None)

print("="*80)
print("SEARCHING FOR KEY ROWS IN THE LYNDON EXCEL")
print("="*80)

# Look for key terms in column 1 (row labels)
search_terms = [
    'Free Cash Flow',
    'FCF',
    'free cash',
    'Ending Cash',
    'Distribution',
    'Contribution',
    'ACTUAL',
    'Occupancy',
    'Cash Balance'
]

print("\nSearching column 1 for key terms:")
for term in search_terms:
    for i in range(len(df)):
        val = str(df.iloc[i, 1]).lower()
        if term.lower() in val:
            print(f"  Row {i}: Found '{term}' in '{df.iloc[i, 1]}'")

print("\n" + "="*80)
print("ALL ROWS IN COLUMN 1 (first 40 rows):")
print("="*80)
for i in range(min(40, len(df))):
    val = df.iloc[i, 1]
    if pd.notna(val):
        print(f"Row {i:2d}: {val}")

print("\n" + "="*80)
print("OCCUPANCY ROWS:")
print("="*80)
print(f"Row 3 (Budgeted Occupancy): {df.iloc[3, 3:15].tolist()}")
print(f"Row 4 (Actual Occupancy): {df.iloc[4, 3:15].tolist()}")

print("\n" + "="*80)
print("STATUS AND MONTH ROWS:")
print("="*80)
print(f"Row 5 (Status): {df.iloc[5, 3:15].tolist()}")
print(f"Row 6 (Dates): {df.iloc[6, 3:15].tolist()}")

print("\n" + "="*80)
print("ROW 29 (Ending Cash Balance Available):")
print("="*80)
print(f"Row 29: {df.iloc[29, 3:15].tolist()}")

print("\n" + "="*80)
print("ROW 28 (ACTUAL Distributions/Contributions):")
print("="*80)
print(f"Row 28: {df.iloc[28, 3:15].tolist()}")
