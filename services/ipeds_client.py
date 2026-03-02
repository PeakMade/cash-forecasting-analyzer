"""
IPEDS Client - College Scorecard API Integration
Retrieves official university enrollment data from US Department of Education
"""

import os
import logging
import requests
from typing import Dict, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class IPEDSClient:
    """Client for College Scorecard API (includes IPEDS data)"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize IPEDS client
        
        Args:
            api_key: College Scorecard API key from api.data.gov
        """
        self.api_key = api_key or os.environ.get('COLLEGE_SCORECARD_API_KEY')
        self.base_url = "https://api.data.gov/ed/collegescorecard/v1/schools"
        
        if not self.api_key:
            logger.warning("College Scorecard API key not configured - enrollment data unavailable")
            self.enabled = False
        else:
            logger.info("IPEDS/College Scorecard API enabled for enrollment data")
            self.enabled = True
    
    def search_university(self, university_name: str) -> Optional[Dict]:
        """
        Search for a university by name and return enrollment data
        
        Args:
            university_name: Name of university (e.g., "University of Cincinnati")
            
        Returns:
            Dict with enrollment data or None if not found
        """
        if not self.enabled:
            return None
        
        try:
            # Search for university
            params = {
                'api_key': self.api_key,
                'school.name': university_name,
                'fields': ','.join([
                    'id',
                    'school.name',
                    'school.city',
                    'school.state',
                    'school.zip',
                    'school.institutional_characteristics.level',
                    'latest.student.size',
                    'latest.student.enrollment.all',
                    'latest.student.enrollment.undergrad',
                    'latest.student.enrollment.grad',
                    # Historical enrollment data (multiple years)
                    '2022.student.size',
                    '2021.student.size',
                    '2020.student.size',
                    '2019.student.size',
                    '2018.student.size'
                ]),
                'per_page': 5  # Get top 5 matches
            }
            
            logger.info(f"Searching College Scorecard API for: {university_name}")
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if not data.get('results'):
                logger.warning(f"No results found for: {university_name}")
                return None
            
            # Get best match (first result is usually most relevant)
            best_match = data['results'][0]
            
            # Parse the data
            enrollment_data = self._parse_enrollment_data(best_match)
            
            logger.info(f"Found enrollment data for {enrollment_data['name']} (UNITID: {enrollment_data['unitid']})")
            
            return enrollment_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching enrollment data: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error parsing enrollment data: {str(e)}")
            return None
    
    def _parse_enrollment_data(self, raw_data: Dict) -> Dict:
        """
        Parse raw College Scorecard data into structured enrollment info
        
        Args:
            raw_data: Raw JSON from API
            
        Returns:
            Structured enrollment dictionary
        """
        # Current enrollment
        current_enrollment = raw_data.get('latest.student.size') or raw_data.get('latest.student.enrollment.all')
        undergrad = raw_data.get('latest.student.enrollment.undergrad')
        grad = raw_data.get('latest.student.enrollment.grad')
        
        # Historical enrollment (last 5 years)
        historical = []
        for year in [2022, 2021, 2020, 2019, 2018]:
            size = raw_data.get(f'{year}.student.size')
            if size:
                historical.append({
                    'year': year,
                    'enrollment': size
                })
        
        # Calculate trend
        trend = self._calculate_trend(historical)
        
        # School info
        level = raw_data.get('school.institutional_characteristics.level')
        level_name = {
            1: '4-year',
            2: '2-year',
            3: 'Less than 2-year'
        }.get(level, 'Unknown')
        
        return {
            'unitid': raw_data.get('id'),
            'name': raw_data.get('school.name'),
            'city': raw_data.get('school.city'),
            'state': raw_data.get('school.state'),
            'zip': raw_data.get('school.zip'),
            'level': level_name,
            'current_enrollment': current_enrollment,
            'undergraduate': undergrad,
            'graduate': grad,
            'historical_enrollment': historical,
            'trend': trend,
            'data_source': 'College Scorecard API (IPEDS)',
            'retrieved_date': datetime.now().strftime('%Y-%m-%d')
        }
    
    def _calculate_trend(self, historical: List[Dict]) -> Dict:
        """
        Calculate enrollment trend from historical data
        
        Args:
            historical: List of year/enrollment dicts
            
        Returns:
            Trend analysis dict
        """
        if len(historical) < 2:
            return {
                'direction': 'Unknown',
                'description': 'Insufficient historical data',
                'change_1yr': None,
                'change_5yr': None
            }
        
        # Sort by year descending
        sorted_data = sorted(historical, key=lambda x: x['year'], reverse=True)
        
        # Calculate 1-year change
        if len(sorted_data) >= 2:
            recent = sorted_data[0]['enrollment']
            previous = sorted_data[1]['enrollment']
            change_1yr = ((recent - previous) / previous * 100) if previous else 0
        else:
            change_1yr = None
        
        # Calculate 5-year change
        if len(sorted_data) >= 5:
            recent = sorted_data[0]['enrollment']
            oldest = sorted_data[4]['enrollment']
            change_5yr = ((recent - oldest) / oldest * 100) if oldest else 0
        else:
            change_5yr = None
        
        # Determine direction
        if change_1yr is not None:
            if change_1yr > 2:
                direction = 'Growing'
            elif change_1yr < -2:
                direction = 'Declining'
            else:
                direction = 'Stable'
        else:
            direction = 'Unknown'
        
        # Create description
        if change_1yr is not None and change_5yr is not None:
            description = f"{direction} ({change_1yr:+.1f}% 1-year, {change_5yr:+.1f}% 5-year)"
        elif change_1yr is not None:
            description = f"{direction} ({change_1yr:+.1f}% year-over-year)"
        else:
            description = "Trend data unavailable"
        
        return {
            'direction': direction,
            'description': description,
            'change_1yr': round(change_1yr, 2) if change_1yr is not None else None,
            'change_5yr': round(change_5yr, 2) if change_5yr is not None else None
        }
    
    def format_for_analysis(self, enrollment_data: Dict) -> str:
        """
        Format enrollment data for inclusion in economic analysis prompt
        
        Args:
            enrollment_data: Parsed enrollment data dict
            
        Returns:
            Formatted string for LLM consumption
        """
        if not enrollment_data:
            return "University enrollment data unavailable."
        
        output = f"""
=== OFFICIAL UNIVERSITY ENROLLMENT DATA ===
Source: U.S. Department of Education College Scorecard / IPEDS
Retrieved: {enrollment_data['retrieved_date']}

Institution: {enrollment_data['name']}
UNITID: {enrollment_data['unitid']}
Location: {enrollment_data['city']}, {enrollment_data['state']} {enrollment_data['zip']}
Type: {enrollment_data['level']} institution

CURRENT ENROLLMENT:
- Total Students: {enrollment_data['current_enrollment']:,} (most recent data)
"""
        
        if enrollment_data['undergraduate']:
            output += f"- Undergraduate: {enrollment_data['undergraduate']:,}\n"
        if enrollment_data['graduate']:
            output += f"- Graduate: {enrollment_data['graduate']:,}\n"
        
        output += f"\nENROLLMENT TREND: {enrollment_data['trend']['description']}\n"
        
        if enrollment_data['historical_enrollment']:
            output += "\nHISTORICAL ENROLLMENT:\n"
            for record in enrollment_data['historical_enrollment'][:5]:
                output += f"- {record['year']}: {record['enrollment']:,} students\n"
        
        trend_analysis = enrollment_data['trend']
        if trend_analysis['change_1yr'] is not None:
            output += f"\nYEAR-OVER-YEAR CHANGE: {trend_analysis['change_1yr']:+.1f}%\n"
        if trend_analysis['change_5yr'] is not None:
            output += f"5-YEAR CHANGE: {trend_analysis['change_5yr']:+.1f}%\n"
        
        output += "\nNOTE: This is official IPEDS data from the U.S. Department of Education.\n"
        output += "Use these specific figures when discussing enrollment trends.\n"
        
        return output
    
    def get_multiple_universities(self, university_names: List[str]) -> Dict[str, Dict]:
        """
        Get enrollment data for multiple universities
        
        Args:
            university_names: List of university names
            
        Returns:
            Dict mapping university name to enrollment data
        """
        results = {}
        
        for name in university_names:
            data = self.search_university(name)
            if data:
                results[name] = data
        
        return results
