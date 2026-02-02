import pandas as pd
import sys
sys.path.append('.')
from services.file_processor import FileProcessor

# Test with actual file
processor = FileProcessor(openai_api_key='dummy')
result = processor.parse_cash_forecast('sample_files/Rittenhouse Station/550 Rittenhouse Cash Forecast - 09.2025.xlsx')

print('=== PARSE RESULT ===')
for key, value in result.items():
    print(f'{key}: {value}')
