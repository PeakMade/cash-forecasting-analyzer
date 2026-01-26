"""
File Processor Service
Parses Excel cash forecast, PDF Income Statement, PDF Balance Sheet
Integrates with Economic Analysis and Recommendation Engine
"""

import pandas as pd
import PyPDF2
import re
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
import logging
import os

from services.economic_analysis import EconomicAnalyzer
from services.recommendation_engine import RecommendationEngine

logger = logging.getLogger(__name__)


class FileProcessor:
    """Processes uploaded files and generates cash forecast recommendations"""
    
    def __init__(self, openai_api_key: str):
        """Initialize with OpenAI API key for economic analysis"""
        self.economic_analyzer = EconomicAnalyzer(api_key=openai_api_key)
        self.recommendation_engine = RecommendationEngine()
    
    def process_and_analyze(self,
                           cash_forecast_path: str,
                           income_statement_path: str,
                           balance_sheet_path: str,
                           property_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process all three required files and generate comprehensive recommendation
        
        Args:
            cash_forecast_path: Path to Excel cash forecast file
            income_statement_path: Path to PDF income statement
            balance_sheet_path: Path to PDF balance sheet
            property_info: Dictionary with property information (name, university, address, etc.)
            
        Returns:
            Complete analysis with decision, executive summary, and detailed rationale
        """
        logger.info(f"Processing files for property: {property_info.get('name', 'Unknown')}")
        
        try:
            # Step 1: Parse cash forecast
            cash_data = self.parse_cash_forecast(cash_forecast_path)
            
            # Override property_name with database value (more reliable than filename parsing)
            cash_data['property_name'] = property_info.get('name', cash_data.get('property_name', 'Unknown'))
            
            # Step 2: Parse income statement
            income_data = self.parse_income_statement(income_statement_path)
            
            # Step 3: Parse balance sheet
            balance_data = self.parse_balance_sheet(balance_sheet_path)
            
            # Step 4: Get economic analysis
            economic_data = self.get_economic_context(
                property_name=property_info.get('name', 'Unknown'),
                university=property_info.get('university', 'Unknown'),
                city=property_info.get('city', 'Unknown'),
                state=property_info.get('state', 'Unknown'),
                zip_code=property_info.get('zip', ''),
                current_month=cash_data.get('current_month', 'Unknown')
            )
            
            # Step 5: Generate recommendation
            recommendation = self.recommendation_engine.analyze_and_recommend(
                cash_forecast_data=cash_data,
                income_statement_data=income_data,
                balance_sheet_data=balance_data,
                economic_analysis=economic_data
            )
            
            return {
                'success': True,
                'property_info': property_info,
                'recommendation': recommendation,
                'raw_data': {
                    'cash_forecast': cash_data,
                    'income_statement': income_data,
                    'balance_sheet': balance_data,
                    'economic_analysis': economic_data
                },
                'processed_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing files: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'property_info': property_info
            }
    
    def parse_cash_forecast(self, file_path: str) -> Dict[str, Any]:
        """
        Parse Excel cash forecast file
        Extracts: Free Cash Flow, Distributions/Contributions, Occupancy data, Month info
        Supports multiple formats by auto-detecting structure
        """
        logger.info(f"Parsing cash forecast: {file_path}")
        
        try:
            # Parse filename for property info
            filename = os.path.basename(file_path)
            entity_number, property_name, current_month = self._parse_cash_forecast_filename(filename)
            logger.debug(f"Parsed filename - Entity: {entity_number}, Property: {property_name}, Month: {current_month}")
            
            # Read Excel file
            df = pd.read_excel(file_path, sheet_name=0, header=None)
            logger.debug(f"Excel file loaded - Shape: {df.shape}")
            
            # Auto-detect format by looking for 2025 data
            year_2025_cols = self._find_2025_columns(df)
            logger.debug(f"Using columns {year_2025_cols[0]} to {year_2025_cols[-1]} for 2025 data ({len(year_2025_cols)} columns)")
            
            # Find key rows dynamically by searching for labels
            status_row_idx = self._find_row_by_label(df, ['Actual', 'Budget'], column=year_2025_cols[0])
            if status_row_idx is None:
                # Try looking in column 1 for status row
                for row_idx in range(min(10, len(df))):
                    row_vals = df.iloc[row_idx, year_2025_cols].tolist()
                    if any('actual' in str(v).lower() for v in row_vals if pd.notna(v)):
                        status_row_idx = row_idx
                        break
            
            # Month row is typically one row after status row
            month_row_idx = status_row_idx + 1 if status_row_idx is not None else None
            
            # Find occupancy rows (search column 0 = column A)
            budgeted_occ_idx = self._find_row_by_label(df, ['Budgeted Occupancy', 'Budget Occupancy'], column=0)
            actual_occ_idx = self._find_row_by_label(df, ['Actual Occupancy'], column=0)
            
            # Find FCF and distribution rows (search column 0 = column A)
            fcf_row_idx = self._find_row_by_label(df, ['Free Cash Flow', 'Free Cash'], column=0)
            dist_row_idx = self._find_row_by_label(df, ['Distributions', 'Contribution', 'ACTUAL (Distributions)'], column=0)
            
            logger.debug(f"Row indices - Status:{status_row_idx}, Month:{month_row_idx}, BudgetedOcc:{budgeted_occ_idx}, ActualOcc:{actual_occ_idx}, FCF:{fcf_row_idx}, Dist:{dist_row_idx}")
            
            # Extract rows
            status_row = df.iloc[status_row_idx, year_2025_cols].tolist() if status_row_idx is not None else []
            month_row = df.iloc[month_row_idx, year_2025_cols].tolist() if month_row_idx is not None else []
            budgeted_occ_row = df.iloc[budgeted_occ_idx, year_2025_cols].tolist() if budgeted_occ_idx is not None else []
            actual_occ_row = df.iloc[actual_occ_idx, year_2025_cols].tolist() if actual_occ_idx is not None else []
            distributions_row = df.iloc[dist_row_idx, year_2025_cols].tolist() if dist_row_idx is not None else []
            fcf_row = df.iloc[fcf_row_idx, year_2025_cols].tolist() if fcf_row_idx is not None else []
            
            logger.debug(f"Status row: {status_row}")
            logger.debug(f"Month row: {month_row}")
            logger.debug(f"FCF row: {fcf_row}")
            logger.debug(f"Distributions row: {distributions_row}")
            
            # Find current month (most recent "Actual" = LAST actual column) and next 6 months (Budget months)
            current_month_idx = None
            budget_month_indices = []  # Collect multiple budget months
            
            for i, status in enumerate(status_row):
                if isinstance(status, str):
                    if 'actual' in status.lower():
                        current_month_idx = i  # Keep updating to get the LAST actual month
                    elif 'budget' in status.lower() and current_month_idx is not None:
                        budget_month_indices.append(i)
                        if len(budget_month_indices) >= 6:  # Collect up to 6 budget months
                            break
            
            next_month_idx = budget_month_indices[0] if budget_month_indices else None
            logger.debug(f"Current month index: {current_month_idx}, Next month index: {next_month_idx}")
            logger.debug(f"Budget month indices (next 6 months): {budget_month_indices}")
            
            # Extract data for current and projected months
            # Convert datetime objects to strings in "Month YYYY" format
            raw_current_month = month_row[current_month_idx] if current_month_idx is not None else 'Unknown'
            raw_projected_month = month_row[next_month_idx] if next_month_idx is not None else 'Unknown'
            
            # Format datetime objects as "Month YYYY" strings
            if isinstance(raw_current_month, pd.Timestamp) or isinstance(raw_current_month, datetime):
                current_month_name = raw_current_month.strftime('%B %Y')
            else:
                current_month_name = str(raw_current_month)
                
            if isinstance(raw_projected_month, pd.Timestamp) or isinstance(raw_projected_month, datetime):
                projected_month_name = raw_projected_month.strftime('%B %Y')
            else:
                projected_month_name = str(raw_projected_month)
            
            logger.info(f"Current month: {current_month_name}, Projected month: {projected_month_name}")
            
            current_fcf = fcf_row[current_month_idx] if current_month_idx is not None else 0
            projected_fcf = fcf_row[next_month_idx] if next_month_idx is not None else 0
            
            current_occupancy = actual_occ_row[current_month_idx] if current_month_idx is not None else 0
            projected_occupancy = budgeted_occ_row[next_month_idx] if next_month_idx is not None else 0
            
            current_distributions = distributions_row[current_month_idx] if current_month_idx is not None else 0
            
            logger.debug(f"Raw values - FCF: {current_fcf}/{projected_fcf}, Occ: {current_occupancy}/{projected_occupancy}, Dist: {current_distributions}")
            
            # Convert to float, handle potential non-numeric values
            current_fcf = float(current_fcf) if pd.notna(current_fcf) else 0.0
            projected_fcf = float(projected_fcf) if pd.notna(projected_fcf) else 0.0
            current_occupancy = float(current_occupancy) * 100 if pd.notna(current_occupancy) else 0.0
            projected_occupancy = float(projected_occupancy) * 100 if pd.notna(projected_occupancy) else 0.0
            current_distributions = float(current_distributions) if pd.notna(current_distributions) else 0.0
            
            logger.info(f"Parsed values - Current FCF: ${current_fcf:,.2f}, Projected FCF: ${projected_fcf:,.2f}")
            logger.info(f"Occupancy - Current: {current_occupancy:.1f}%, Projected: {projected_occupancy:.1f}%")
            logger.info(f"Current distributions: ${current_distributions:,.2f}")
            
            # Extract 6-month projection data
            projected_months = []
            for idx in budget_month_indices:
                month_date = month_row[idx]
                month_name = month_date.strftime('%B %Y') if isinstance(month_date, (pd.Timestamp, datetime)) else str(month_date)
                
                month_fcf = float(fcf_row[idx]) if pd.notna(fcf_row[idx]) else 0.0
                month_occupancy = float(budgeted_occ_row[idx]) * 100 if pd.notna(budgeted_occ_row[idx]) else 0.0
                
                projected_months.append({
                    'month': month_name,
                    'fcf': month_fcf,
                    'occupancy': month_occupancy
                })
            
            logger.info(f"Extracted {len(projected_months)} months of projections")
            for i, proj in enumerate(projected_months[:3], 1):  # Log first 3 months
                logger.debug(f"  Month {i}: {proj['month']} - FCF: ${proj['fcf']:,.2f}, Occ: {proj['occupancy']:.1f}%")
            
            result = {
                'status': 'success',
                'property_name': property_name,
                'entity_number': entity_number,
                'current_month': current_month_name,
                'projected_month': projected_month_name,
                'current_fcf': current_fcf,
                'projected_fcf': projected_fcf,
                'current_occupancy': current_occupancy,
                'projected_occupancy': projected_occupancy,
                'current_distributions': current_distributions,
                'projected_months': projected_months,  # NEW: 6-month projection data
                'file_path': file_path
            }
            
            logger.info(f"✓ Successfully parsed cash forecast")
            return result
            
        except Exception as e:
            logger.error(f"Error parsing cash forecast: {str(e)}", exc_info=True)
            return {
                'status': 'error',
                'error': str(e),
                'file_path': file_path
            }
    
    def parse_income_statement(self, file_path: str) -> Dict[str, Any]:
        """
        Parse PDF income statement
        Extracts: Total Operating Income, Total Operating Expenses, NOI (month and YTD)
        """
        logger.info(f"Parsing income statement: {file_path}")
        
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                all_text = ''.join([page.extract_text() for page in pdf_reader.pages])
            
            # Extract key line items
            line_items = {
                'Total Operating Income': self._extract_financial_line(all_text, 'Total Operating Income'),
                'Total Operating Expenses': self._extract_financial_line(all_text, 'Total Operating Expenses'),
                'NET OPERATING INCOME': self._extract_financial_line(all_text, 'NET OPERATING INCOME'),
            }
            
            # Parse into structured data
            result = {'status': 'success', 'file_path': file_path}
            
            if line_items['Total Operating Income']:
                data = line_items['Total Operating Income']
                result['income_month_actual'] = self._clean_number(data['month_actual'])
                result['income_month_budget'] = self._clean_number(data['month_budget'])
                result['income_month_variance_pct'] = self._clean_number(data['month_variance_%'].replace('%', ''))
                result['income_ytd_actual'] = self._clean_number(data['ytd_actual'])
                result['income_ytd_budget'] = self._clean_number(data['ytd_budget'])
                result['income_ytd_variance_pct'] = self._clean_number(data['ytd_variance_%'].replace('%', ''))
            
            if line_items['Total Operating Expenses']:
                data = line_items['Total Operating Expenses']
                result['expenses_month_actual'] = self._clean_number(data['month_actual'])
                result['expenses_month_budget'] = self._clean_number(data['month_budget'])
                # CRITICAL: Invert expense variance sign for correct interpretation
                # PDF shows positive % when spending more (bad), but our logic expects:
                # negative % = under budget = GOOD, positive % = over budget = BAD
                # The PDF may show this inverted, so we flip it here
                result['expenses_month_variance_pct'] = -self._clean_number(data['month_variance_%'].replace('%', ''))
                result['expenses_ytd_actual'] = self._clean_number(data['ytd_actual'])
                result['expenses_ytd_budget'] = self._clean_number(data['ytd_budget'])
                result['expenses_ytd_variance_pct'] = -self._clean_number(data['ytd_variance_%'].replace('%', ''))

            
            if line_items['NET OPERATING INCOME']:
                data = line_items['NET OPERATING INCOME']
                result['noi_month_actual'] = self._clean_number(data['month_actual'])
                result['noi_month_budget'] = self._clean_number(data['month_budget'])
                result['noi_month_variance_pct'] = self._clean_number(data['month_variance_%'].replace('%', ''))
                result['noi_ytd_actual'] = self._clean_number(data['ytd_actual'])
                result['noi_ytd_budget'] = self._clean_number(data['ytd_budget'])
                result['noi_ytd_variance_pct'] = self._clean_number(data['ytd_variance_%'].replace('%', ''))
            
            return result
            
        except Exception as e:
            logger.error(f"Error parsing income statement: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'file_path': file_path
            }
    
    def parse_balance_sheet(self, file_path: str) -> Dict[str, Any]:
        """
        Parse PDF balance sheet
        Extracts: Cash, Current Assets/Liabilities, Debt, Working Capital
        """
        logger.info(f"Parsing balance sheet: {file_path}")
        
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                all_text = ''.join([page.extract_text() for page in pdf_reader.pages])
            
            # Extract key items using regex
            patterns = {
                'Total Cash and Cash Equivalents': r'Total Cash and Cash Equivalents\s+([\d,.-]+)\s+([\d,.-]+)',
                'Total Accounts Receivable': r'Total Accounts Receivable\s+([\d,.-]+)\s+([\d,.-]+)',
                'Total Current Liabilities': r'Total Current Liabilities\s+([\d,.-]+)\s+([\d,.-]+)',
                'Total Notes Payable': r'Total Notes Payable\s+([\d,.-]+)\s+([\d,.-]+)',
                'Accrued Interest': r'Accrued Interest\s+([\d,.-]+)\s+([\d,.-]+)',
            }
            
            result = {'status': 'success', 'file_path': file_path}
            
            for label, pattern in patterns.items():
                match = re.search(pattern, all_text)
                if match:
                    current_val = self._clean_number(match.group(1))
                    prior_val = self._clean_number(match.group(2))
                    
                    if label == 'Total Cash and Cash Equivalents':
                        result['cash_balance'] = current_val
                        result['cash_prior_month'] = prior_val
                    elif label == 'Total Accounts Receivable':
                        result['accounts_receivable'] = current_val
                    elif label == 'Total Current Liabilities':
                        result['current_liabilities'] = current_val
                    elif label == 'Total Notes Payable':
                        result['total_debt'] = current_val
                        result['monthly_principal'] = abs(current_val - prior_val)
                    elif label == 'Accrued Interest':
                        result['accrued_interest'] = current_val
            
            # Calculate monthly debt service (principal + interest estimate)
            if 'monthly_principal' in result and 'accrued_interest' in result:
                # Rough estimate: interest change month-over-month
                result['monthly_debt_service'] = result['monthly_principal'] + (result['monthly_principal'] * 0.1)
            
            # Calculate months of reserves
            if 'cash_balance' in result and 'monthly_debt_service' in result and 'current_liabilities' in result:
                monthly_needs = result['monthly_debt_service'] + (result['current_liabilities'] * 0.1)
                result['months_of_reserves'] = result['cash_balance'] / monthly_needs if monthly_needs > 0 else 999
            
            return result
            
        except Exception as e:
            logger.error(f"Error parsing balance sheet: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'file_path': file_path
            }
    
    def get_economic_context(self, property_name: str, university: str, city: str, 
                            state: str, zip_code: str, current_month: str) -> Dict[str, Any]:
        """
        Get economic and market context using OpenAI API
        """
        logger.info(f"Getting economic context for {property_name}")
        
        try:
            # Get full economic analysis
            analysis_result = self.economic_analyzer.analyze_property_context(
                property_name=property_name,
                university=university,
                city=city,
                state=state,
                zip_code=zip_code,
                current_month=current_month
            )
            
            # Get seasonal factor
            # Handle different month formats: "September 2025", "Jan-2025", "September"
            if '-' in current_month:
                # Format like "Jan-2025" or "Sept-2025" - extract month abbreviation
                month_abbr = current_month.split('-')[0].strip()
                # Convert abbreviation to full name
                month_map = {
                    'jan': 'January', 'feb': 'February', 'mar': 'March', 'apr': 'April',
                    'may': 'May', 'jun': 'June', 'jul': 'July', 'aug': 'August',
                    'sep': 'September', 'sept': 'September',  # Handle both Sep and Sept
                    'oct': 'October', 'nov': 'November', 'dec': 'December'
                }
                month_name = month_map.get(month_abbr.lower(), month_abbr)
            elif ' ' in current_month:
                # Format like "September 2025" - extract first word
                month_name = current_month.split()[0]
            else:
                month_name = current_month
                
            print(f"DEBUG: Extracting month for seasonal factor: '{month_name}' from '{current_month}'")
            seasonal_factor = self.economic_analyzer.get_seasonal_factor(month_name)
            print(f"DEBUG: Seasonal factor result: {seasonal_factor}")
            
            # Determine enrollment trend from analysis text
            enrollment_trend = 'stable'
            if analysis_result.get('success'):
                analysis_text = analysis_result.get('analysis', '').lower()
                if 'growing' in analysis_text or 'growth' in analysis_text or 'increasing' in analysis_text:
                    enrollment_trend = 'growing'
                elif 'declining' in analysis_text or 'decrease' in analysis_text or 'falling' in analysis_text:
                    enrollment_trend = 'declining'
            
            # Check for new supply mentions
            new_supply = False
            if analysis_result.get('success'):
                analysis_text = analysis_result.get('analysis', '').lower()
                if 'new' in analysis_text and ('construction' in analysis_text or 'development' in analysis_text or 'supply' in analysis_text):
                    new_supply = True
            
            return {
                'success': analysis_result.get('success', False),
                'seasonal_factor': seasonal_factor,
                'enrollment_trend': enrollment_trend,
                'new_supply': new_supply,
                'full_analysis': analysis_result.get('analysis', ''),
                'tokens_used': analysis_result.get('tokens_used', 0)
            }
            
        except Exception as e:
            logger.error(f"Error getting economic context: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'seasonal_factor': {'season': 'Unknown', 'expected_occupancy': 'Unknown', 'cash_flow_pattern': 'Unknown'},
                'enrollment_trend': 'unknown',
                'new_supply': False,
                'full_analysis': ''
            }
    
    # Helper methods
    
    def _find_2025_columns(self, df: pd.DataFrame) -> list:
        """
        Auto-detect which columns contain month data (current and future years)
        Returns list of column indices
        NOTE: Method name kept as _find_2025_columns for compatibility, but now finds all month columns
        """
        # Search for columns containing dates in first 10 rows
        month_cols = []
        first_date_col = None
        
        for col_idx in range(df.shape[1]):
            for row_idx in range(min(10, len(df))):
                cell = df.iloc[row_idx, col_idx]
                
                # Check if it's a datetime (any year)
                if isinstance(cell, pd.Timestamp) or hasattr(cell, 'year'):
                    try:
                        # Found first date column, now collect ALL date columns from here
                        if first_date_col is None:
                            first_date_col = col_idx
                            logger.debug(f"Found first date column at {col_idx}, row {row_idx}: {cell}")
                        
                        # Collect ALL columns from first date onwards, skipping non-dates but continuing to look
                        # This handles: [Aug-2025, Sep-2025, ..., Dec-2025, YTD 2025, Budget 2025, blank, Jan-2026, ...]
                        consecutive_non_date = 0
                        for c in range(first_date_col, df.shape[1]):
                            cell_check = df.iloc[row_idx, c]
                            
                            # Include if it's a datetime (any year)
                            if isinstance(cell_check, pd.Timestamp) or hasattr(cell_check, 'year'):
                                try:
                                    _ = cell_check.year  # Verify it has a year attribute
                                    if c not in month_cols:
                                        month_cols.append(c)
                                    consecutive_non_date = 0  # Reset counter
                                except (AttributeError, TypeError):
                                    consecutive_non_date += 1
                            else:
                                consecutive_non_date += 1
                            
                            # Stop if we've hit 5 consecutive non-date columns (end of data)
                            if consecutive_non_date >= 5:
                                break
                        
                        if month_cols:
                            logger.debug(f"Collected {len(month_cols)} month columns: {month_cols}")
                            return month_cols
                    except (AttributeError, TypeError):
                        pass
                
                # Check if it contains year text (like "Jan-2025", "Jan-2026")
                if cell and isinstance(cell, str) and any(month in cell for month in ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']):
                    # Extract year from the cell
                    import re
                    year_match = re.search(r'20\d{2}', str(cell))
                    if year_match:
                        logger.debug(f"Found text format date at column {col_idx}: {cell}")
                        # Collect consecutive month columns (any year)
                        text_format_cols = []
                        consecutive_non_date = 0
                        for c in range(col_idx, df.shape[1]):
                            cell_check = df.iloc[row_idx, c]
                            # Check if it looks like a month column
                            if cell_check and isinstance(cell_check, str) and any(month in str(cell_check) for month in ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']):
                                text_format_cols.append(c)
                                consecutive_non_date = 0
                            else:
                                consecutive_non_date += 1
                            
                            # Stop after 5 consecutive non-date columns
                            if consecutive_non_date >= 5:
                                break
                        
                        if text_format_cols:
                            logger.debug(f"Collected {len(text_format_cols)} text format month columns: {text_format_cols}")
                            return text_format_cols
        
        # Fallback: if we found nothing, assume old format (columns 79-93)
        if not month_cols:
            logger.warning("Could not auto-detect month columns, using default columns 79-93")
            return list(range(79, 94))
        
        return month_cols
    
    def _find_row_by_label(self, df: pd.DataFrame, search_terms: list, column: int = 1) -> Optional[int]:
        """
        Find a row by searching for keywords in a specific column (default column B = index 1)
        Returns row index or None
        """
        for row_idx in range(len(df)):
            cell = df.iloc[row_idx, column]
            if pd.notna(cell):
                cell_str = str(cell).lower()
                if any(term.lower() in cell_str for term in search_terms):
                    return row_idx
        return None
    
    def _parse_cash_forecast_filename(self, filename: str) -> Tuple[str, str, str]:
        """
        Parse filename - flexible to handle various formats
        Examples:
          - "550 Rittenhouse Station Cash Forecast - 09.2025.xlsx"
          - "550 Rittenhouse Cash Forecast - 09.2025.xlsx"
          - "Cash Forecast - 09.2025.xlsx"
        Returns: (entity_number, property_name, current_month)
        """
        print(f"DEBUG: Parsing filename: '{filename}'")
        
        # Normalize underscores to spaces (Windows may convert spaces to underscores)
        filename = filename.replace('_', ' ')
        
        # Try standard format: "### PropertyName Cash Forecast - MM.YYYY"
        match = re.match(r'(\d+)\s+(.+?)\s+Cash\s+Forecast\s+-\s+(\d{2})\.(\d{4})', filename, re.IGNORECASE)
        if match:
            entity_number = match.group(1)
            property_name = match.group(2).strip()
            month = match.group(3)
            year = match.group(4)
            
            month_names = ['', 'January', 'February', 'March', 'April', 'May', 'June',
                          'July', 'August', 'September', 'October', 'November', 'December']
            month_name = month_names[int(month)] if int(month) <= 12 else 'Unknown'
            
            current_month = f"{month_name} {year}"
            
            print(f"DEBUG: PRIMARY match succeeded -> Entity: {entity_number}, Property: {property_name}, Month: {current_month}")
            return entity_number, property_name, current_month
        
        print(f"DEBUG: Primary regex failed, trying fallback...")
        
        # Try alternate format: just extract entity number and month if present
        entity_match = re.search(r'^(\d+)', filename)
        date_match = re.search(r'(\d{2})\.(\d{4})', filename)
        
        entity_number = entity_match.group(1) if entity_match else 'Unknown'
        
        if date_match:
            month = date_match.group(1)
            year = date_match.group(2)
            month_names = ['', 'January', 'February', 'March', 'April', 'May', 'June',
                          'July', 'August', 'September', 'October', 'November', 'December']
            month_name = month_names[int(month)] if int(month) <= 12 else 'Unknown'
            current_month = f"{month_name} {year}"
            print(f"DEBUG: Fallback parsing -> Entity: {entity_number}, Month: {current_month}")
        else:
            current_month = 'Unknown'
            print(f"DEBUG: Could not parse month from filename: {filename}")
        
        # Property name will be overridden by database lookup in process_and_analyze
        return entity_number, 'From Database', current_month
    
    def _extract_financial_line(self, text: str, label: str) -> Optional[Dict[str, str]]:
        """Extract a financial line item with month and YTD data"""
        pattern = rf'{re.escape(label)}\s+([\d,.-]+(?:\(\))?)\s+([\d,.-]+(?:\(\))?)\s+\(?([\d,.-]+)\)?\s+([-\d.]+%)\s+([\d,.-]+(?:\(\))?)\s+([\d,.-]+(?:\(\))?)\s+\(?([\d,.-]+)\)?\s+([-\d.]+%)'
        
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return {
                'month_actual': match.group(1),
                'month_budget': match.group(2),
                'month_variance_$': match.group(3),
                'month_variance_%': match.group(4),
                'ytd_actual': match.group(5),
                'ytd_budget': match.group(6),
                'ytd_variance_$': match.group(7),
                'ytd_variance_%': match.group(8),
            }
        return None
    
    def _clean_number(self, s) -> float:
        """Convert string like '425,818.20' or '(1,234.56)' to float"""
        if not isinstance(s, str):
            return float(s) if pd.notna(s) else 0.0
        
        s = s.replace(',', '').replace('$', '').strip()
        if s.startswith('(') and s.endswith(')'):
            return -float(s[1:-1])
        try:
            return float(s)
        except:
            return 0.0
