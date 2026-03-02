"""
Economic and Geographic Analysis Service for Student Housing
Uses OpenAI Responses API with web search for current enrollment data
Integrates IPEDS for official historical enrollment baseline (2018-2022)
Combines official government data with real-time web search for comprehensive analysis
"""
import os
from openai import OpenAI
from datetime import datetime
import json
import logging
from services.ipeds_client import IPEDSClient
from services.bls_client import BLSClient

logger = logging.getLogger(__name__)


class EconomicAnalyzer:
    def __init__(self, api_key=None, model=None):
        """Initialize the OpenAI client and IPEDS client"""
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable or pass api_key parameter.")
        
        self.model = model or os.getenv('OPENAI_MODEL', 'gpt-4o')
        self.client = OpenAI(api_key=self.api_key)
        self.current_date = datetime.now().strftime("%B %Y")
        
        # Initialize IPEDS client for official enrollment data
        self.ipeds = IPEDSClient()
        if self.ipeds.enabled:
            logger.info("IPEDS client enabled for official university enrollment data")
        else:
            logger.warning("IPEDS client disabled - analysis will rely on model training data")
        
        # Initialize BLS client for unemployment data
        self.bls = BLSClient()
        if self.bls.enabled:
            logger.info("BLS client enabled for official unemployment data")
        else:
            logger.warning("BLS client disabled - unemployment data from web search only")
    
    def analyze_property_context(self, property_name, university, city, state, zip_code, current_month):
        """
        Generate comprehensive economic and geographic analysis for a student housing property
        
        Args:
            property_name: Name of the property (e.g., "Rittenhouse Station")
            university: Associated university (e.g., "University of Cincinnati")
            city: City location
            state: State location
            zip_code: Property ZIP code
            current_month: Current month for context (e.g., "September 2025")
            
        Returns:
            dict: Analysis results with enrollment trends, economic outlook, seasonal factors, and recommendations
        """
        
        # Get official enrollment data from IPEDS
        enrollment_context = ""
        enrollment_data = None
        
        if self.ipeds.enabled:
            logger.info(f"Fetching IPEDS enrollment data for {university}")
            enrollment_data = self.ipeds.search_university(university)
            
            if enrollment_data:
                enrollment_context = self.ipeds.format_for_analysis(enrollment_data)
                logger.info(f"Retrieved enrollment data: {enrollment_data['current_enrollment']:,} students, {enrollment_data['trend']['description']}")
            else:
                logger.warning(f"Could not find enrollment data for {university}")
                enrollment_context = "\n=== UNIVERSITY ENROLLMENT DATA ===\nOfficial enrollment data not available for this institution.\n"
        else:
            logger.warning("IPEDS client not enabled - using model knowledge only")
        
        # Get official unemployment data from BLS
        unemployment_context = ""
        unemployment_data = None
        
        if self.bls.enabled:
            logger.info(f"Fetching BLS unemployment data for {city}, {state}")
            unemployment_data = self.bls.get_unemployment_rate(city, state)
            
            if unemployment_data:
                unemployment_context = f"\n=== OFFICIAL UNEMPLOYMENT DATA (Bureau of Labor Statistics) ===\nUnemployment Rate: {self.bls.format_for_analysis(unemployment_data)}\n"
                logger.info(f"Retrieved unemployment rate: {unemployment_data['unemployment_rate']}% for {unemployment_data['period']}")
            else:
                logger.warning(f"Could not find unemployment data for {city}, {state}")
        else:
            logger.info("BLS client not enabled - unemployment data from web search only")
        
        prompt = f"""You are a real estate financial analyst specializing in student housing properties. 
Analyze the following student housing property and provide a comprehensive economic and market context assessment.

Property Information:
- Property Name: {property_name}
- University: {university}
- Location: {city}, {state} {zip_code}
- Current Analysis Month: {current_month}
- Today's Date: {self.current_date}

{enrollment_context}
{unemployment_context}

IMPORTANT ENROLLMENT DATA INSTRUCTIONS:
1. The enrollment data above is from the official U.S. Department of Education IPEDS database (historical data 2018-2022)
2. Use these EXACT IPEDS figures when discussing historical enrollment trends
3. ADDITIONALLY: Search the web for CURRENT {university} enrollment for 2025-2026 academic year
4. Present both: historical IPEDS baseline + current web-sourced enrollment estimate
5. Clearly distinguish between official historical data and current estimates

Please provide a structured analysis covering:

1. UNIVERSITY ENROLLMENT TRENDS
   - Historical: Use the IPEDS data provided above for 2018-2022 enrollment baseline
   - Current: Search for and report current 2025-2026 enrollment (cite web sources)
   - Compare historical trend vs. current enrollment
   - Enrollment projections for next academic year
   - Any notable enrollment initiatives or challenges

2. ACADEMIC CALENDAR & SEASONAL FACTORS
   - Current point in academic year (fall/spring/summer)
   - Key lease-up periods for student housing
   - Expected occupancy patterns for next 3-6 months
   - Summer occupancy considerations

3. LOCAL EMPLOYMENT & ECONOMIC CONDITIONS
   CRITICAL: If official BLS unemployment data is provided above, USE THOSE EXACT FIGURES.
   Otherwise, search the web for CURRENT {city}, {state} economic data:
   
   A. Employment Metrics (search for latest 2025-2026 data):
      - Current unemployment rate for {city} metro area (USE BLS DATA IF PROVIDED ABOVE)
      - Job growth trends (year-over-year change)
      - Labor force participation rate
      - Major employers in {city} (top 5-10)
      - Industries driving local economy
      
   B. Student Employment Market:
      - On-campus employment opportunities at {university}
      - Part-time job availability for students
      - Average student wages in {city}
      - Co-op/internship programs and placement rates
      - Gig economy presence (food delivery, rideshare, etc.)
      
   C. Economic Outlook:
      - GDP growth or economic expansion indicators for {city} region
      - Recent major business openings/closings
      - Infrastructure projects or development plans
      - Cost of living trends (rent, groceries, utilities)
      - Housing affordability index for {city}
      
   D. Risk Factors:
      - Economic headwinds or challenges facing {city}
      - Industry layoffs or contractions
      - Population migration trends (growing/declining)

4. STUDENT HOUSING MARKET
   - Supply/demand dynamics in {city}
   - New student housing construction or competition
   - Average rental rates and trends
   - Market occupancy rates

5. SHORT-TERM OUTLOOK (Next 6 Months)
   - Expected cash flow patterns based on academic calendar
   - Risk factors to monitor
   - Opportunities for the property
   - Market position assessment

6. CASH FORECASTING IMPLICATIONS
   - How seasonal factors should impact cash flow projections
   - Reliability of budget assumptions given market conditions
   - Recommended adjustments or considerations for forecasting

IMPORTANT INSTRUCTIONS:
- Use web search to find CURRENT data (2025-2026) for enrollment, employment, and economic conditions
- Cite specific data sources and dates when presenting statistics
- For enrollment: Present both official IPEDS historical baseline AND current web-sourced estimates
- For employment/economy: Focus on most recent available data (prioritize 2025-2026, accept 2024 data if newer not available)
- Be specific with numbers (unemployment rates, enrollment figures, job growth percentages)
- Focus on actionable insights for cash flow forecasting and decision-making
- Format your response as a structured analysis with clear sections and bullet points"""

        try:
            # Use Responses API with web search to get current enrollment and economic data
            response = self.client.responses.create(
                model=self.model,
                instructions="""You are an expert real estate financial analyst specializing in student housing markets. 

Your expertise includes:
- University enrollment trends and projections
- Local labor markets and employment conditions
- Student housing supply/demand dynamics
- Economic factors affecting student housing cash flows

Data Sources:
1. IPEDS data (when provided): Official historical enrollment baseline - cite these exact figures
2. Web search: Use to find current 2025-2026 enrollment, employment rates, economic conditions, and market data
3. Always cite specific sources and dates for statistics you present

Deliverable: Provide data-driven, specific insights with concrete numbers and actionable recommendations for cash flow forecasting.""",
                input=prompt,
                tools=[{"type": "web_search"}],
                temperature=0.7,
                max_output_tokens=2500
            )
            
            # Extract content from Response object
            # The response.output is a list of ResponseOutput objects (web search calls + messages)
            # We want the text from the final message
            analysis_text = ""
            logger.info(f"Response type: {type(response)}, has output: {hasattr(response, 'output')}")
            
            if hasattr(response, 'output') and isinstance(response.output, list):
                logger.info(f"Response.output is list with {len(response.output)} items")
                for idx, item in enumerate(response.output):
                    logger.info(f"  Item {idx}: type={getattr(item, 'type', 'no-type')}")
                    # Look for ResponseOutputMessage with content
                    if hasattr(item, 'type') and item.type == 'message':
                        if hasattr(item, 'content') and isinstance(item.content, list):
                            logger.info(f"    Found message with {len(item.content)} content items")
                            for content_item in item.content:
                                if hasattr(content_item, 'text'):
                                    text_len = len(content_item.text)
                                    logger.info(f"      Extracted text: {text_len} characters")
                                    analysis_text += content_item.text
            
            if not analysis_text:
                # Fallback to string representation
                analysis_text = str(response)
                logger.warning(f"Could not extract text from response, using string representation ({len(analysis_text)} chars)")
            else:
                logger.info(f"Successfully extracted analysis text: {len(analysis_text)} characters")
            
            # Structure the response
            tokens_used = 0
            if hasattr(response, 'usage') and response.usage:
                tokens_used = getattr(response.usage, 'total_tokens', 0)
            
            result = {
                'success': True,
                'property_name': property_name,
                'university': university,
                'location': f"{city}, {state}",
                'analysis_date': self.current_date,
                'current_month': current_month,
                'analysis': analysis_text,
                'tokens_used': tokens_used,
                'ipeds_enabled': self.ipeds.enabled,
                'enrollment_data': enrollment_data
            }
            
            if enrollment_data:
                logger.info(f"Analysis completed for {property_name} using official IPEDS enrollment data")
            else:
                logger.info(f"Analysis completed for {property_name} without enrollment data")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in analyze_property_context: {str(e)}", exc_info=True)
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e) if str(e) else repr(e),
                'property_name': property_name
            }
    
    def get_seasonal_factor(self, month_name):
        """
        Determine seasonal factor for student housing based on month
        
        Args:
            month_name: Month name (e.g., "October", "June")
            
        Returns:
            dict: Seasonal classification and occupancy expectation
        """
        month_lower = month_name.lower()
        
        # Academic year seasonal patterns
        fall_semester = ['august', 'september', 'october', 'november', 'december']
        spring_semester = ['january', 'february', 'march', 'april', 'may']
        summer = ['june', 'july']
        
        if month_lower in fall_semester:
            return {
                'season': 'Fall Semester',
                'expected_occupancy': 'High (90-95%)',
                'cash_flow_pattern': 'Strong - peak leasing season',
                'notes': 'Prime academic period, expect stable/strong cash flow'
            }
        elif month_lower in spring_semester:
            return {
                'season': 'Spring Semester',
                'expected_occupancy': 'High (88-93%)',
                'cash_flow_pattern': 'Strong - mid academic year',
                'notes': 'Stable period, some move-outs in May for graduation'
            }
        elif month_lower in summer:
            return {
                'season': 'Summer Session',
                'expected_occupancy': 'Low-Medium (40-60%)',
                'cash_flow_pattern': 'Weak - summer dip expected',
                'notes': 'Significant occupancy decline, budget should reflect lower revenue'
            }
        else:
            return {
                'season': 'Unknown',
                'expected_occupancy': 'Unable to determine',
                'cash_flow_pattern': 'Unknown',
                'notes': 'Unable to classify month'
            }
    
    def generate_recommendation_context(self, analysis_result, seasonal_factor, current_fcf, projected_fcf):
        """
        Generate specific recommendations based on economic analysis and cash flow projections
        
        Args:
            analysis_result: Result from analyze_property_context()
            seasonal_factor: Result from get_seasonal_factor()
            current_fcf: Current month free cash flow
            projected_fcf: Next month projected free cash flow
            
        Returns:
            dict: Recommendation factors and decision guidance
        """
        
        if not analysis_result.get('success'):
            return {
                'warning': 'Economic analysis failed - proceeding with financial data only',
                'factors': []
            }
        
        factors = []
        
        # Seasonal considerations
        if seasonal_factor['season'] == 'Fall Semester' and projected_fcf < 0:
            factors.append({
                'category': 'Seasonal',
                'severity': 'Medium',
                'insight': f"Deficit during {seasonal_factor['season']} is unusual - typically strong cash flow period",
                'recommendation': 'Investigate specific causes - may indicate budget assumption errors or one-time expenses'
            })
        elif seasonal_factor['season'] == 'Summer Session' and projected_fcf < 0:
            factors.append({
                'category': 'Seasonal',
                'severity': 'Low',
                'insight': f"Deficit during {seasonal_factor['season']} is expected due to lower occupancy",
                'recommendation': 'This is normal seasonal pattern - reserves should cover summer dip'
            })
        
        # Cash flow magnitude
        if abs(projected_fcf) < 50000:
            factors.append({
                'category': 'Magnitude',
                'severity': 'Low',
                'insight': f"Projected deficit of ${abs(projected_fcf):,.2f} is relatively small",
                'recommendation': 'Minor variance - likely timing or budget rounding issue'
            })
        
        return {
            'success': True,
            'factors': factors,
            'analysis_summary': analysis_result.get('analysis', '')[:500] + '...'  # First 500 chars
        }


def format_analysis_for_report(analysis_result):
    """
    Format the economic analysis into a clean report structure
    
    Args:
        analysis_result: Result from EconomicAnalyzer.analyze_property_context()
        
    Returns:
        str: Formatted text report
    """
    if not analysis_result.get('success'):
        return f"⚠️  Economic Analysis Failed: {analysis_result.get('error', 'Unknown error')}"
    
    report = f"""
{'='*120}
ECONOMIC & GEOGRAPHIC CONTEXT ANALYSIS
{'='*120}

Property: {analysis_result['property_name']}
University: {analysis_result['university']}
Location: {analysis_result['location']}
Analysis Date: {analysis_result['analysis_date']}
Current Period: {analysis_result['current_month']}

{'-'*120}

{analysis_result['analysis']}

{'-'*120}
Analysis generated using {analysis_result['tokens_used']} tokens
{'='*120}
"""
    return report


if __name__ == "__main__":
    # Test the service
    print("Testing Economic Analysis Service...\n")
    
    # Initialize analyzer (reads from OPENAI_API_KEY environment variable)
    analyzer = EconomicAnalyzer()
    
    # Test with Rittenhouse Station
    print("Analyzing Rittenhouse Station (University of Cincinnati)...\n")
    
    result = analyzer.analyze_property_context(
        property_name="Rittenhouse Station",
        university="University of Cincinnati",
        city="Cincinnati",
        state="OH",
        zip_code="45219",
        current_month="October 2025"
    )
    
    if result['success']:
        print(format_analysis_for_report(result))
        
        # Test seasonal factor
        print("\n\nSEASONAL FACTOR ANALYSIS")
        print("="*120)
        seasonal = analyzer.get_seasonal_factor("October")
        print(f"Season: {seasonal['season']}")
        print(f"Expected Occupancy: {seasonal['expected_occupancy']}")
        print(f"Cash Flow Pattern: {seasonal['cash_flow_pattern']}")
        print(f"Notes: {seasonal['notes']}")
        
    else:
        print(f"❌ Analysis failed: {result['error']}")
