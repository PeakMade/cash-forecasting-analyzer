import pandas as pd

df = pd.read_excel('sample_files/Rittenhouse Station/550 Rittenhouse Cash Forecast - 09.2025.xlsx', sheet_name=0, header=None)

# Simulate _find_2025_columns
year_2025_cols = list(range(79, 92))  # Based on what we found
print(f'year_2025_cols: {year_2025_cols} (length: {len(year_2025_cols)})')

# Extract status row (row 6)
status_row = df.iloc[6, year_2025_cols].tolist()
print(f'\nstatus_row (length {len(status_row)}): {status_row}')

# Find current_month_idx
current_month_idx = None
next_month_idx = None

for i, status in enumerate(status_row):
    if isinstance(status, str):
        if 'actual' in status.lower():
            current_month_idx = i  # Keep updating to get the LAST actual month
        elif 'budget' in status.lower() and current_month_idx is not None and next_month_idx is None:
            next_month_idx = i
            break

print(f'\ncurrent_month_idx: {current_month_idx}, next_month_idx: {next_month_idx}')

# Get FCF row (row 48)
fcf_row = df.iloc[48, year_2025_cols].tolist()
print(f'\nfcf_row (length {len(fcf_row)}): {fcf_row}')

# Try to access
print(f'\nTrying to access fcf_row[{current_month_idx}]...')
if current_month_idx < len(fcf_row):
    print(f'SUCCESS: fcf_row[{current_month_idx}] = {fcf_row[current_month_idx]}')
else:
    print(f'ERROR: Index {current_month_idx} out of range for list of length {len(fcf_row)}')
