"""
Detailed analysis of the cash forecast file
"""
import pandas as pd
import re

file_path = r'sample_files\550 Rittenhouse Cash Forecast - 09.2025.xlsx'

# Parse filename
filename = '550 Rittenhouse Cash Forecast - 09.2025.xlsx'
match = re.match(r'(\d+)\s+(.+?)\s+Cash Forecast\s+-\s+(\d+)\.(\d+)', filename)
if match:
    entity_num, prop_name, month_num, year = match.groups()
    print(f'Entity Number: {entity_num}')
    print(f'Property Name: {prop_name}')
    print(f'Current Month: {month_num}/{year}')
    print()

# Load the file
df = pd.read_excel(file_path, sheet_name='Cash Forecast', header=None)

# Find the month row (row 7 has month names)
print('Month headers (row 7):')
month_row = df.iloc[7, :20]
print(month_row.tolist())
print()

# Find the status row (row 6 has "Actual" or other status)
print('Status row (row 6 - Actual vs Budget):')
status_row = df.iloc[6, :20]
print(status_row.tolist())
print()

# Find "Free Cash Flow - Available for Distribution" row
fcf_row_idx = None
for idx, row in df.iterrows():
    row_str = str(row.iloc[0]).lower() if pd.notna(row.iloc[0]) else ''
    if 'free cash flow' in row_str and 'distribution' in row_str:
        fcf_row_idx = idx
        break

if fcf_row_idx:
    print(f'Free Cash Flow row is at index: {fcf_row_idx}')
    print(f'First 20 values:')
    fcf_values = df.iloc[fcf_row_idx, :20]
    for i, val in enumerate(fcf_values):
        status = status_row.iloc[i] if i < len(status_row) else 'N/A'
        month = month_row.iloc[i] if i < len(month_row) else 'N/A'
        print(f'  Col {i}: Month={month}, Status={status}, Value={val}')
