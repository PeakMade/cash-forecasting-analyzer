import pandas as pd

df = pd.read_excel('sample_files/Rittenhouse Station/550 Rittenhouse Cash Forecast - 09.2025.xlsx', sheet_name=0, header=None)

cols = [79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93]
status_row = df.iloc[6, cols].tolist()
print(f'Status row (len {len(status_row)}): {status_row}')

fcf_row = df.iloc[48, cols].tolist()
print(f'\nFCF row (len {len(fcf_row)}): {fcf_row}')

print(f'\nFinding current month...')
idx = None
for i, s in enumerate(status_row):
    if isinstance(s, str) and 'actual' in s.lower():
        idx = i
        
print(f'Last Actual index: {idx}')
if idx is not None and idx < len(fcf_row):
    print(f'fcf_row[{idx}] = {fcf_row[idx]}')
else:
    print(f'ERROR: Index {idx} out of range for list length {len(fcf_row)}')
