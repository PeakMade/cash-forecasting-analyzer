"""
Debug script to find the FORECASTED (Distributions)/Contributions row
"""
import pandas as pd

file_path = r'sample_files\The Republic\163 The Republic Cash Forecast - 12.2025.xlsx'

try:
    # First, list all sheet names
    xls = pd.ExcelFile(file_path)
    print("="*100)
    print("AVAILABLE SHEETS")
    print("="*100)
    for sheet in xls.sheet_names:
        print(f"  - {sheet}")
    print()
    
    # Use the first sheet or find the right one
    sheet_name = xls.sheet_names[0] if xls.sheet_names else None
    if not sheet_name:
        print("No sheets found!")
        exit(1)
    
    print(f"Using sheet: {sheet_name}")
    print()
    
    df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
    
    print("="*100)
    print("SEARCHING FOR FORECASTED (Distributions)/Contributions ROW")
    print("="*100)
    print()
    
    # Search for the row
    dist_row_idx = None
    for idx, row in df.iterrows():
        if row[0] and 'FORECASTED' in str(row[0]) and 'Distribution' in str(row[0]):
            dist_row_idx = idx
            print(f"Found at row index: {idx}")
            print(f"Row label: {row[0]}")
            break
    
    if dist_row_idx is None:
        # Try alternative search
        for idx, row in df.iterrows():
            cell_val = str(row[0]).upper() if row[0] else ''
            if 'FORECAST' in cell_val and ('DISTRIBUT' in cell_val or 'CONTRIBUT' in cell_val):
                dist_row_idx = idx
                print(f"Found at row index: {idx}")
                print(f"Row label: {row[0]}")
                break
    
    if dist_row_idx:
        print()
        print("="*100)
        print("EXAMINING FILE STRUCTURE")
        print("="*100)
        
        # Check rows 0-10 to understand structure
        print("\nFirst 10 rows, first 30 columns:")
        for i in range(min(10, len(df))):
            print(f"Row {i}: {df.iloc[i, :30].tolist()[:5]}...")  # Show first 5 values
        
        print("\n" + "="*100)
        print("DISTRIBUTION ROW VALUES")
        print("="*100)
        
        # Just show the first 30 values of the distribution row
        dist_row_values = df.iloc[dist_row_idx, :30].tolist()
        print(f"\nFirst 30 values:")
        for i, val in enumerate(dist_row_values):
            if pd.notna(val) and val != 0:
                print(f"  Column {i}: {val}")
        print()
    else:
        print("\n❌ Could not find FORECASTED (Distributions)/Contributions row")
        print("\nSearching all rows for 'distribution' or 'contribution':")
        for idx, row in df.iterrows():
            if row[0]:
                cell_val = str(row[0]).upper()
                if 'DISTRIBUT' in cell_val or 'CONTRIBUT' in cell_val:
                    print(f"  Row {idx}: {row[0]}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
