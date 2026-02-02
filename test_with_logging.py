import pandas as pd
import sys
sys.path.append('.')

# Enable detailed logging
import logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

from services.file_processor import FileProcessor

processor = FileProcessor(openai_api_key='dummy')
result = processor.parse_cash_forecast('sample_files/Rittenhouse Station/550 Rittenhouse Cash Forecast - 09.2025.xlsx')

print('\n=== FINAL RESULT ===')
for key, value in result.items():
    print(f'{key}: {value}')
