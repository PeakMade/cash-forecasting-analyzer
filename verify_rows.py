"""
Verify the correct row indices based on Excel row numbers
"""
import pandas as pd

file_path = r'sample_files\550 Rittenhouse Cash Forecast - 09.2025.xlsx'

# Load the file
df = pd.read_excel(file_path, sheet_name='Cash Forecast', header=None)

print("Checking key rows (Excel row number → Python index):")
print()

# Excel Row 6 → Index 5 (Occupancy percentages)
print("Excel Row 6 (Index 5) - Actual Occupancy:")
print(df.iloc[5, 0:15].tolist())
print()

# Excel Row 7 → Index 6 (Actual vs Budget status)
print("Excel Row 7 (Index 6) - Status (Actual/Budget):")
print(df.iloc[6, 0:15].tolist())
print()

# Excel Row 8 → Index 7 (Month names)
print("Excel Row 8 (Index 7) - Month names:")
print(df.iloc[7, 0:15].tolist())
print()

# Excel Row 48 → Index 47 (Distributions/Collections)
print("Excel Row 48 (Index 47) - Distributions/Collections:")
row_47_label = df.iloc[47, 0]
print(f"Label: {row_47_label}")
print(f"First 10 values: {df.iloc[47, 2:12].tolist()}")
print()

# Excel Row 49 → Index 48 (Free Cash Flow)
print("Excel Row 49 (Index 48) - Free Cash Flow:")
row_48_label = df.iloc[48, 0]
print(f"Label: {row_48_label}")
print(f"First 10 values: {df.iloc[48, 2:12].tolist()}")
