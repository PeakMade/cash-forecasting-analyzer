import pandas as pd

df = pd.read_excel('sample_files/155 River Oaks Cash Forecast - 10.2025.xlsx', sheet_name=0, header=None)

print('Row 5 (Status - Actual/Budget):')
print(df.iloc[5, 18:31].tolist())

print('\nRow 6 (Month dates):')
print(df.iloc[6, 18:31].tolist())

print('\nRow 3 (Budgeted Occupancy):')
print(df.iloc[3, 18:31].tolist())

print('\nRow 4 (Actual Occupancy):')
print(df.iloc[4, 18:31].tolist())

print('\nSearching for FCF and Distributions rows:')
for i in range(len(df)):
    row_label = df.iloc[i, 1]
    if pd.notna(row_label):
        label_lower = str(row_label).lower()
        if 'free cash' in label_lower or 'distribution' in label_lower or 'contribution' in label_lower:
            print(f'Row {i}: {row_label}')
            print(f'  2025 values: {df.iloc[i, 18:31].tolist()}')

print('\nAll row labels (column B):')
for i in range(len(df)):
    label = df.iloc[i, 1]
    if pd.notna(label):
        print(f'Row {i}: {label}')
