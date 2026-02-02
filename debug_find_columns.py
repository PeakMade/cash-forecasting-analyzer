import pandas as pd

df = pd.read_excel('sample_files/Rittenhouse Station/550 Rittenhouse Cash Forecast - 09.2025.xlsx', sheet_name=0, header=None)

# Actually run the _find_2025_columns logic exactly as written
year_2025_cols = []

for col_idx in range(df.shape[1]):
    for row_idx in range(min(10, len(df))):
        cell = df.iloc[row_idx, col_idx]
        
        # Check if it's a datetime in 2025
        if isinstance(cell, pd.Timestamp) or hasattr(cell, 'year'):
            try:
                if cell.year == 2025:
                    print(f'Found 2025 datetime at col {col_idx}, row {row_idx}')
                    
                    # Collect all consecutive 2025 columns from this starting point
                    for c in range(col_idx, df.shape[1]):
                        cell_check = df.iloc[row_idx, c]
                        # Include if it's a 2025 datetime or contains '2025' string
                        if isinstance(cell_check, pd.Timestamp) and cell_check.year == 2025:
                            year_2025_cols.append(c)
                        elif hasattr(cell_check, 'year') and cell_check.year == 2025:
                            year_2025_cols.append(c)
                        elif str(cell_check) == '2025':  # Summary columns
                            year_2025_cols.append(c)
                        else:
                            # Stop at first non-2025 column
                            break
                    
                    if year_2025_cols:
                        print(f'Collected {len(year_2025_cols)} columns: {year_2025_cols}')
                        break
            except (AttributeError, TypeError):
                pass
        
        # Check if it contains '2025' text (like "Jan-2025")
        if cell and isinstance(cell, str) and '2025' in cell and any(month in cell for month in ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']):
            print(f'Found 2025 text format at column {col_idx}, row {row_idx}: {repr(cell)}')
            # Collect consecutive month columns
            for c in range(col_idx, df.shape[1]):
                cell_check = df.iloc[row_idx, c]
                if cell_check and '2025' in str(cell_check):
                    year_2025_cols.append(c)
                else:
                    break
            if year_2025_cols:
                print(f'Collected {len(year_2025_cols)} columns: {year_2025_cols}')
                break
    
    if year_2025_cols:
        break

print(f'\nFinal year_2025_cols: {year_2025_cols}')
