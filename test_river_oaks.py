import sys
sys.path.append('.')
from services.file_processor import FileProcessor

# Test River Oaks
processor = FileProcessor(openai_api_key='dummy')
result = processor.parse_cash_forecast('sample_files/River Oaks/155 River Oaks Cash Forecast - 10.2025.xlsx')

print('=== RIVER OAKS PARSE RESULT ===')
for key, value in result.items():
    print(f'{key}: {value}')
