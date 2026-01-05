import pandas as pd

df = pd.read_excel('sample_files/155 River Oaks Cash Forecast - 10.2025.xlsx', sheet_name=0, header=None)

print('Checking row 6 for datetime objects:')
for col in range(min(df.shape[1], 32)):
    cell = df.iloc[6, col]
    print(f'Col {col:2d}: type={type(cell).__name__:20s}, value={cell}')
