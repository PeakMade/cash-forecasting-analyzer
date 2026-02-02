import pandas as pd
import sys
import os
sys.path.append('.')
from services.file_processor import FileProcessor

# Create processor and parse
processor = FileProcessor(openai_api_key=os.environ.get('OPENAI_API_KEY', 'dummy'))
result = processor.parse_cash_forecast('sample_files/River Oaks/155 River Oaks Cash Forecast 10.2025.xlsx')

print('\n=== RESULT ===')
print(f"Current Month: {result.get('current_month')}")
print(f"Current FCF: ${result.get('current_fcf', 0):,.2f}")
print(f"Projected Month: {result.get('projected_month')}")
print(f"Projected FCF: ${result.get('projected_fcf', 0):,.2f}")
