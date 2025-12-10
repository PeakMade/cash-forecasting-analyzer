"""
Economic and Geographic Analysis Service for Student Housing
Uses OpenAI API to gather contextual information about university, local economy, and market conditions
"""
import os
from openai import OpenAI
from datetime import datetime
import json

class EconomicAnalyzer:
    def __init__(self, api_key=None, model=None):
        """Initialize the OpenAI client"""
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable or pass api_key parameter.")
        
        self.model = model or os.getenv('OPENAI_MODEL', 'gpt-4o')
        self.client = OpenAI(api_key=self.api_key)
        self.current_date = datetime.now().strftime("%B %Y")
    
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
        
        prompt = f"""You are a real estate financial analyst specializing in student housing properties. 
Analyze the following student housing property and provide a comprehensive economic and market context assessment.

Property Information:
- Property Name: {property_name}
- University: {university}
- Location: {city}, {state} {zip_code}
- Current Analysis Month: {current_month}
- Today's Date: {self.current_date}

Please provide a structured analysis covering:

1. UNIVERSITY ENROLLMENT TRENDS
   - Current enrollment figures for {university}
   - Year-over-year enrollment trends (last 3 years)
   - Enrollment projections for next academic year
   - Any notable enrollment initiatives or challenges

2. ACADEMIC CALENDAR & SEASONAL FACTORS
   - Current point in academic year (fall/spring/summer)
   - Key lease-up periods for student housing
   - Expected occupancy patterns for next 3-6 months
   - Summer occupancy considerations

3. LOCAL ECONOMIC INDICATORS
   - {city} economic outlook and job market
   - Student employment opportunities
   - Cost of living trends
   - Major economic developments or concerns

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

Please be specific, cite recent data where possible, and focus on actionable insights for cash flow forecasting and decision-making.
Format your response as a structured analysis with clear sections and bullet points."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert real estate financial analyst with deep knowledge of student housing markets, university trends, and local economic conditions. Provide data-driven, actionable insights."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2500
            )
            
            analysis_text = response.choices[0].message.content
            
            # Structure the response
            return {
                'success': True,
                'property_name': property_name,
                'university': university,
                'location': f"{city}, {state}",
                'analysis_date': self.current_date,
                'current_month': current_month,
                'analysis': analysis_text,
                'tokens_used': response.usage.total_tokens
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
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
