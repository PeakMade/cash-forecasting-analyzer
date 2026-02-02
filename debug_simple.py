import pandas as pd
import sys

try:
    df = pd.read_excel('sample_files/River Oaks/155 River Oaks Cash Forecast 10.2025.xlsx', sheet_name=0, header=None)
    
    print(f'DataFrame shape: {df.shape}')
    
    # Find 2025 columns
    found_2025 = False
    for col_idx in range(df.shape[1]):
        for row_idx in range(min(10, len(df))):
            cell = str(df.iloc[row_idx, col_idx])
            if '2025' in cell and any(month in cell for month in ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']):
                print(f'\nFound 2025 at column {col_idx}, row {row_idx}')
                
                # Show next 15 columns from this row (months)
                month_row = []
                for i in range(15):
                    if col_idx + i < df.shape[1]:
                        month_row.append(str(df.iloc[row_idx, col_idx + i]))
                print(f'Month headers: {month_row}')
                
                # Status row (one above)
                status_row = []
                if row_idx > 0:
                    for i in range(15):
                        if col_idx + i < df.shape[1]:
                            status_row.append(str(df.iloc[row_idx - 1, col_idx + i]))
                    print(f'Status row: {status_row}')
                
                # Find FCF row
                for r in range(len(df)):
                    label = str(df.iloc[r, 0]).lower()
                    if 'free cash' in label:
                        print(f'\nFCF row at {r}')
                        fcf_row = []
                        for i in range(15):
                            if col_idx + i < df.shape[1]:
                                val = df.iloc[r, col_idx + i]
                                fcf_row.append(val)
                        print(f'FCF values: {fcf_row}')
                        
                        # Find Oct and Nov specifically
                        for i, month in enumerate(month_row):
                            if 'Oct' in month and '2025' in month:
                                print(f'\n>>> OCTOBER 2025 (index {i}):')
                                print(f'    Status: {status_row[i] if i < len(status_row) else "N/A"}')
                                print(f'    FCF: {fcf_row[i] if i < len(fcf_row) else "N/A"}')
                            if 'Nov' in month and '2025' in month:
                                print(f'\n>>> NOVEMBER 2025 (index {i}):')
                                print(f'    Status: {status_row[i] if i < len(status_row) else "N/A"}')
                                print(f'    FCF: {fcf_row[i] if i < len(fcf_row) else "N/A"}')
                        break
                
                found_2025 = True
                break
        if found_2025:
            break
    
    if not found_2025:
        print('Could not find 2025 data')
        
except Exception as e:
    print(f'ERROR: {e}')
    import traceback
    traceback.print_exc()
