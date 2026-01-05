"""
Test script to process recent files locally with detailed logging
"""
import os
import logging
from pathlib import Path
from services.file_processor import FileProcessor

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# River Oaks files from sample_files folder
UPLOAD_FOLDER = "sample_files"

# File paths
cash_forecast_path = os.path.join(UPLOAD_FOLDER, "155 River Oaks Cash Forecast - 10.2025.xlsx")
income_statement_path = os.path.join(UPLOAD_FOLDER, "04_River Oaks_Comparative_Income Statement_October 2025.pdf")
balance_sheet_path = os.path.join(UPLOAD_FOLDER, "03_River Oaks_Balance Sheet_October 2025.pdf")

# Property info
property_info = {
    'entity_number': '155',
    'name': 'River Oaks',
    'address': 'Unknown',
    'city': 'Unknown',
    'state': 'Unknown',
    'zip': 'Unknown',
    'university': 'Unknown'
}

def main():
    logger.info("="*80)
    logger.info("STARTING LOCAL TEST RUN")
    logger.info("="*80)
    
    # Verify files exist
    for filepath in [cash_forecast_path, income_statement_path, balance_sheet_path]:
        if not os.path.exists(filepath):
            logger.error(f"FILE NOT FOUND: {filepath}")
            return
        logger.info(f"✓ File found: {filepath}")
    
    # Get OpenAI API key
    from dotenv import load_dotenv
    load_dotenv()
    openai_api_key = os.getenv('OPENAI_API_KEY')
    
    if not openai_api_key:
        logger.warning("No OpenAI API key found - economic analysis will be skipped")
    
    # Initialize processor
    logger.info("\nInitializing FileProcessor...")
    processor = FileProcessor(openai_api_key=openai_api_key)
    
    # Process and analyze
    logger.info("\n" + "="*80)
    logger.info("PROCESSING FILES")
    logger.info("="*80)
    
    result = processor.process_and_analyze(
        cash_forecast_path=cash_forecast_path,
        income_statement_path=income_statement_path,
        balance_sheet_path=balance_sheet_path,
        property_info=property_info
    )
    
    logger.info("\n" + "="*80)
    logger.info("RESULTS")
    logger.info("="*80)
    
    if result.get('success'):
        logger.info("✓ Processing SUCCEEDED")
        
        # Display raw data
        if 'raw_data' in result:
            logger.info("\n--- CASH FORECAST DATA ---")
            cash_data = result['raw_data'].get('cash_forecast', {})
            for key, value in cash_data.items():
                logger.info(f"  {key}: {value}")
            
            logger.info("\n--- INCOME STATEMENT DATA ---")
            income_data = result['raw_data'].get('income_statement', {})
            for key, value in income_data.items():
                if key != 'status' and key != 'file_path':
                    logger.info(f"  {key}: {value}")
            
            logger.info("\n--- BALANCE SHEET DATA ---")
            balance_data = result['raw_data'].get('balance_sheet', {})
            for key, value in balance_data.items():
                if key != 'status' and key != 'file_path':
                    logger.info(f"  {key}: {value}")
        
        # Display recommendation
        if 'recommendation' in result:
            rec = result['recommendation']
            logger.info("\n--- RECOMMENDATION ---")
            logger.info(f"  Decision: {rec.get('decision', 'N/A')}")
            logger.info(f"  Executive Summary: {rec.get('executive_summary', 'N/A')[:200]}...")
    else:
        logger.error("✗ Processing FAILED")
        logger.error(f"Error: {result.get('error', 'Unknown error')}")
    
    logger.info("\n" + "="*80)
    logger.info("TEST COMPLETE")
    logger.info("="*80)

if __name__ == '__main__':
    main()
