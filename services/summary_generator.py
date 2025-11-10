"""
Executive Summary Generator Service
Uses OpenAI GPT-4o-mini to generate executive summary with bullet points
"""

import os
import logging
from typing import Dict, Any, List
from openai import OpenAI

logger = logging.getLogger(__name__)

class SummaryGenerator:
    """Generates executive summaries using OpenAI API"""
    
    def __init__(self):
        self.client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
        self.model = os.environ.get('OPENAI_MODEL', 'gpt-4o-mini')
    
    def generate_summary(self, 
                        analysis_results: Dict[str, Any],
                        property_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate executive summary with up to 5 bullet points
        
        Args:
            analysis_results: Results from AnalysisEngine
            property_info: Property details
            
        Returns:
            Executive summary with bullets and drill-down details
        """
        logger.info(f"Generating executive summary for {property_info['name']}")
        
        try:
            # Prepare context for OpenAI
            context = self._prepare_context(analysis_results, property_info)
            
            # Generate summary using OpenAI
            summary = self._call_openai(context)
            
            # Parse and structure the response
            structured_summary = self._structure_summary(summary, analysis_results)
            
            return structured_summary
            
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            # Return fallback summary
            return self._generate_fallback_summary(analysis_results, property_info)
    
    def _prepare_context(self, analysis_results: Dict[str, Any], property_info: Dict[str, Any]) -> str:
        """
        Prepare context for OpenAI prompt
        """
        recommendation = analysis_results.get('recommendation', {})
        occupancy = analysis_results.get('occupancy_analysis', {})
        economic = analysis_results.get('economic_analysis', {})
        validation = analysis_results.get('validation', {})
        
        context = f"""
You are analyzing a cash forecast for a student housing property. Provide an executive summary
that validates whether the accountant's recommendation is appropriate based on economic conditions.

PROPERTY INFORMATION:
- Name: {property_info['name']}
- Location: {property_info['address']}, {property_info['zip_code']}
- University: {property_info['university']}

ACCOUNTANT'S RECOMMENDATION:
- Type: {recommendation.get('type', 'Unknown')}
- Amount: ${recommendation.get('amount', 0):,.2f}
- Month: {recommendation.get('month', 'Unknown')}

OCCUPANCY ANALYSIS:
- Historical Trend: {occupancy.get('historical_trend', 'Unknown')}
- University Enrollment Trend: {occupancy.get('university_enrollment_trend', 'Unknown')}
- Risk Factors: {', '.join(occupancy.get('risk_factors', ['None identified']))}

ECONOMIC CONDITIONS:
- Unemployment Rate: {economic.get('unemployment_rate', 'Unknown')}
- Employment Trend: {economic.get('employment_trend', 'Unknown')}
- Economic Outlook: {economic.get('economic_outlook', 'Unknown')}

VALIDATION RESULTS:
- Result: {validation.get('validation_result', 'Pending')}
- Supporting Factors: {', '.join(validation.get('supporting_factors', ['Analysis in progress']))}
- Risk Factors: {', '.join(validation.get('risk_factors', ['None identified']))}

Generate an executive summary with 3-5 bullet points that:
1. Validates or questions the accountant's recommendation
2. Cites specific economic/demographic factors
3. Provides clear, actionable insights
4. Uses professional, concise language

Each bullet should be a complete thought that a CFO or property owner can act on.
"""
        return context
    
    def _call_openai(self, context: str) -> str:
        """
        Call OpenAI API to generate summary
        """
        logger.info(f"Calling OpenAI API with model: {self.model}")
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a financial analyst specializing in student housing and real estate cash flow analysis. Provide clear, concise, actionable insights."
                    },
                    {
                        "role": "user",
                        "content": context
                    }
                ],
                temperature=0.7,
                max_tokens=800
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise
    
    def _structure_summary(self, summary_text: str, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Structure the OpenAI response into bullets with drill-down capability
        """
        # Parse bullet points from summary
        lines = summary_text.strip().split('\n')
        bullets = []
        
        for line in lines:
            line = line.strip()
            if line and (line.startswith('•') or line.startswith('-') or line.startswith('*') or line[0].isdigit()):
                # Clean up bullet markers
                cleaned = line.lstrip('•-*0123456789. ')
                if cleaned:
                    bullets.append({
                        'id': len(bullets) + 1,
                        'text': cleaned,
                        'has_details': True
                    })
        
        # Ensure we have at least 3 bullets, max 5
        if len(bullets) < 3:
            bullets.append({
                'id': len(bullets) + 1,
                'text': 'Additional analysis pending - awaiting complete data inputs',
                'has_details': False
            })
        
        bullets = bullets[:5]  # Cap at 5 bullets
        
        return {
            'property_name': analysis_results['property']['name'],
            'analysis_date': analysis_results['analyzed_at'],
            'recommendation_validation': analysis_results['validation'].get('validation_result', 'pending'),
            'executive_summary': summary_text,
            'bullets': bullets,
            'confidence_score': analysis_results['validation'].get('confidence_score'),
            'full_analysis': analysis_results
        }
    
    def _generate_fallback_summary(self, analysis_results: Dict[str, Any], property_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a fallback summary if OpenAI fails
        """
        logger.warning("Using fallback summary generation")
        
        return {
            'property_name': property_info['name'],
            'analysis_date': analysis_results.get('analyzed_at', 'Unknown'),
            'recommendation_validation': 'pending',
            'executive_summary': 'Analysis in progress. Full data integration pending.',
            'bullets': [
                {
                    'id': 1,
                    'text': 'File processing completed successfully',
                    'has_details': True
                },
                {
                    'id': 2,
                    'text': 'External data sources being integrated',
                    'has_details': True
                },
                {
                    'id': 3,
                    'text': 'Full analysis will be available once data sources are connected',
                    'has_details': False
                }
            ],
            'confidence_score': None,
            'full_analysis': analysis_results
        }
