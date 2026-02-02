import pandas as pd

df = pd.read_excel('sample_files/River Oaks/155 River Oaks Cash Forecast 10.2025.xlsx', sheet_name=0, header=None)

# Find 2025 columns
print('=== Finding 2025 data ===')
for col_idx in range(df.shape[1]):
    for row_idx in range(min(10, len(df))):
        cell = df.iloc[row_idx, col_idx]
        if cell and isinstance(cell, str) and '2025' in cell and any(month in cell for month in ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']):
            print(f'Found 2025 months starting at column {col_idx}, row {row_idx}')
            # Show months
            month_row = df.iloc[row_idx, col_idx:col_idx+15].tolist()
            print(f'Months: {month_row}')
            
            # Find Free Cash Flow row
            for r in range(len(df)):
                if pd.notna(df.iloc[r, 0]) and 'free cash' in str(df.iloc[r, 0]).lower():
                    print(f'\nFree Cash Flow at row {r}')
                    fcf_values = df.iloc[r, col_idx:col_idx+15].tolist()
                    print(f'FCF values: {fcf_values}')
                    
                    # Find status row
                    status_row_idx = row_idx - 1
                    status_values = df.iloc[status_row_idx, col_idx:col_idx+15].tolist()
                    print(f'\nStatus row {status_row_idx}: {status_values}')
                    
                    # Find October and November
                    for i, month in enumerate(month_row):
                        if 'Oct' in str(month) and '2025' in str(month):
                            print(f'\nOctober 2025 at index {i}:')
                            print(f'  Status: {status_values[i]}')
                            print(f'  FCF: {fcf_values[i]}')
                        if 'Nov' in str(month) and '2025' in str(month):
                            print(f'\nNovember 2025 at index {i}:')
                            print(f'  Status: {status_values[i]}')
                            print(f'  FCF: {fcf_values[i]}')
                    break
            break
    if 'Found 2025' in str(locals()):
        break
