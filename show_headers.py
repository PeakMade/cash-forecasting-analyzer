import pandas as pd

df = pd.read_excel('sample_files/River Oaks/155 River Oaks Cash Forecast 10.2025.xlsx', sheet_name=0, header=None)

print(f'Shape: {df.shape}')
print('\n=== First 10 rows, last 15 columns ===')
for row_idx in range(10):
    print(f'\nRow {row_idx}:')
    for col_idx in range(max(0, df.shape[1] - 15), df.shape[1]):
        val = df.iloc[row_idx, col_idx]
        print(f'  Col {col_idx}: {val} (type: {type(val).__name__})')
