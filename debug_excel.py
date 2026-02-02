import pandas as pd

df = pd.read_excel('sample_files/Rittenhouse Station/550 Rittenhouse Cash Forecast - 09.2025.xlsx', sheet_name=0, header=None)

print('=== Row 7, columns 76-91 (2025 months) ===')
for i in range(76, 92):
    cell = df.iloc[7, i]
    print(f'Col {i}: {repr(cell)}, Type: {type(cell)}, Contains 2025: {"2025" in str(cell) if pd.notna(cell) else False}')

print('\n=== Row 6 (Status row), columns 76-91 ===')
for i in range(76, 92):
    cell = df.iloc[6, i]
    print(f'Col {i}: {repr(cell)}')

print('\n=== Looking for Free Cash Flow row ===')
for row_idx in range(len(df)):
    first_cell = str(df.iloc[row_idx, 0])
    if 'Free Cash Flow' in first_cell or 'Free Cash' in first_cell:
        print(f'Found at row {row_idx}: {first_cell}')
        print(f'Values in that row (cols 76-91):')
        print([df.iloc[row_idx, i] for i in range(76, 92)])
        break
