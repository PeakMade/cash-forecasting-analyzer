import pandas as pd

df = pd.read_excel('sample_files/River Oaks/155 River Oaks Cash Forecast - 10.2025.xlsx', sheet_name=0, header=None)

print('=== First 10 rows, first 5 columns ===')
print(df.iloc[:10, :5])

print('\n=== Searching for labels in columns 0 and 1 ===')
for i in range(10):
    print(f'Row {i} - Col 0: {repr(df.iloc[i, 0])}, Col 1: {repr(df.iloc[i, 1])}')

print('\n=== Looking for Occupancy and FCF rows ===')
for i in range(len(df)):
    col0 = str(df.iloc[i, 0]) if pd.notna(df.iloc[i, 0]) else ''
    col1 = str(df.iloc[i, 1]) if pd.notna(df.iloc[i, 1]) else ''
    if 'occupancy' in col0.lower() or 'occupancy' in col1.lower():
        print(f'Row {i}: Col0={repr(df.iloc[i, 0])}, Col1={repr(df.iloc[i, 1])}')
    if 'free cash' in col0.lower() or 'free cash' in col1.lower():
        print(f'Row {i}: Col0={repr(df.iloc[i, 0])}, Col1={repr(df.iloc[i, 1])}')
