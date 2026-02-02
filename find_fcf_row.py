import pandas as pd

df = pd.read_excel('sample_files/River Oaks/155 River Oaks Cash Forecast 10.2025.xlsx', sheet_name=0, header=None)

print('Looking for FCF row...\n')
for r in range(len(df)):
    label = str(df.iloc[r, 0])
    if 'free cash' in label.lower() or 'fcf' in label.lower():
        print(f'Row {r}: {label}')
        # Show Oct, Nov, Dec values (cols 26, 27, 28)
        print(f'  Col 26 (Oct): {df.iloc[r, 26]}')
        print(f'  Col 27 (Nov): {df.iloc[r, 27]}')
        print(f'  Col 28 (Dec): {df.iloc[r, 28]}')
