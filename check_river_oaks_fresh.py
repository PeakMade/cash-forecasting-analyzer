import pandas as pd
import os

file_path = 'sample_files/River Oaks/155 River Oaks Cash Forecast - 10.2025.xlsx'

# Get file modification time
mod_time = os.path.getmtime(file_path)
import datetime
print(f'File last modified: {datetime.datetime.fromtimestamp(mod_time)}')

# Read fresh
df = pd.read_excel(file_path, sheet_name=0, header=None)

print('\n=== First 5 rows, columns 0-2 ===')
for i in range(5):
    print(f'Row {i}: Col0={repr(df.iloc[i, 0])}, Col1={repr(df.iloc[i, 1])}')

print('\n=== Looking for Occupancy in column 0 ===')
for i in range(len(df)):
    col0 = str(df.iloc[i, 0]) if pd.notna(df.iloc[i, 0]) else ''
    if 'occupancy' in col0.lower():
        print(f'Row {i}, Col 0: {repr(df.iloc[i, 0])}')
