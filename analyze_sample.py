"""
Quick script to analyze the sample Excel file structure
"""
import pandas as pd
import openpyxl

file_path = r'sample_files\550 Rittenhouse Cash Forecast - 09.2025.xlsx'

# Load workbook to see sheet names
wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
print('Sheet Names:', wb.sheetnames)
print()

# Load first sheet to examine structure
df = pd.read_excel(file_path, sheet_name=0, header=None)
print(f'File Shape: {df.shape[0]} rows x {df.shape[1]} columns')
print()
print('First 30 rows, first 15 columns:')
print(df.iloc[:30, :15].to_string())
print()

# Search for 'Free Cash Flow' row
for idx, row in df.iterrows():
    row_str = str(row.iloc[0]).lower() if pd.notna(row.iloc[0]) else ''
    if 'free cash flow' in row_str and 'distribution' in row_str:
        print(f'\nFound "Free Cash Flow - Available for Distribution" at row {idx}')
        print(f'Row content (first 15 values): {row.tolist()[:15]}')
        break
