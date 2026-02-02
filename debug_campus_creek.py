import pandas as pd
import sys

file = r'sample_files\Campus Creek Cottages\194 Campus Creek Cottages - Cash Forecast - 12.2025.xlsx'
df = pd.read_excel(file, header=None)

print(f'Shape: {df.shape}')
print(f'\n=== First 15 rows, first 3 columns ===')
print(df.iloc[:15, :3].to_string())

print(f'\n=== Column 0 values (first 20 rows) ===')
for i in range(min(20, len(df))):
    val = df.iloc[i, 0]
    print(f'Row {i}: [{repr(val)}]')

print(f'\n=== Column 1 values (first 20 rows) ===')
for i in range(min(20, len(df))):
    val = df.iloc[i, 1]
    print(f'Row {i}: [{repr(val)}]')

print(f'\n=== Searching for FCF patterns ===')
for col_idx in [0, 1]:
    print(f'\nColumn {col_idx}:')
    for i in range(len(df)):
        val = str(df.iloc[i, col_idx]).strip().lower() if pd.notna(df.iloc[i, col_idx]) else ''
        if 'fcf' in val or 'free cash flow' in val or 'cash flow' in val:
            print(f'  Row {i}: [{repr(df.iloc[i, col_idx])}] - POTENTIAL MATCH')
