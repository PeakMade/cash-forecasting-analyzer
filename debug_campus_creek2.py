import pandas as pd

file = r'sample_files\Campus Creek Cottages\194 Campus Creek Cottages - Cash Forecast - 12.2025.xlsx'
df = pd.read_excel(file, header=None)

print(f'Shape: {df.shape}')
print(f'\n=== ALL ROWS - Columns 0-3 ===')
print(df.iloc[:, :4].to_string())

print(f'\n\n=== Looking for FCF row ===')
for i in range(len(df)):
    row_values = []
    for col_idx in range(min(4, df.shape[1])):
        val = df.iloc[i, col_idx]
        if pd.notna(val):
            val_str = str(val).strip().lower()
            if 'fcf' in val_str or 'free cash' in val_str:
                print(f'\nFOUND AT Row {i}, Column {col_idx}: {repr(df.iloc[i, col_idx])}')
                print(f'Full row values: {df.iloc[i, :].tolist()}')
