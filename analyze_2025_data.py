"""
Find and extract current year (2025) data from the cash forecast
"""
import pandas as pd
import re

file_path = r'sample_files\550 Rittenhouse Cash Forecast - 09.2025.xlsx'

# Load the file
df = pd.read_excel(file_path, sheet_name='Cash Forecast', header=None)

# Row indices
occupancy_idx = 5
status_idx = 6
month_idx = 7
distributions_idx = 47
fcf_idx = 48

# Get month row
month_row = df.iloc[month_idx, :]

# Find columns for 2025
print("Finding 2025 data...")
print()

current_year_cols = []
for col_idx in range(len(month_row)):
    month_val = str(month_row.iloc[col_idx])
    if '2025' in month_val and 'Totals' not in month_val:
        current_year_cols.append(col_idx)

print(f"Found {len(current_year_cols)} columns with 2025 data")
print(f"Column range: {min(current_year_cols)} to {max(current_year_cols)}")
print()

# Extract 2025 data
print("2025 Monthly Data:")
print("-" * 80)

status_row = df.iloc[status_idx, :]
occupancy_row = df.iloc[occupancy_idx, :]
fcf_row = df.iloc[fcf_idx, :]
dist_row = df.iloc[distributions_idx, :]

for col_idx in current_year_cols:
    month = month_row.iloc[col_idx]
    status = status_row.iloc[col_idx]
    occupancy = occupancy_row.iloc[col_idx]
    fcf = fcf_row.iloc[col_idx]
    dist = dist_row.iloc[col_idx]
    
    print(f"{month:12} | Status: {status:8} | Occupancy: {occupancy:6} | FCF: ${fcf:12,.2f} | Dist: {dist}")

print()
print("Summary:")
print(f"  Current year: 2025")
print(f"  File date: 09.2025 (September is most recent actual)")
print(f"  Actual months: Jan-Sep 2025")
print(f"  Forecast months: Oct-Dec 2025")
