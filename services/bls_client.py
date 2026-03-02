"""
Bureau of Labor Statistics (BLS) API Client
Retrieves official unemployment and employment data from BLS
"""
import os
import requests
from typing import Dict, Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class BLSClient:
    """Client for BLS API to fetch unemployment and employment data"""
    
    # State FIPS codes (2-digit)
    STATE_FIPS = {
        "AL": "01", "AK": "02", "AZ": "04", "AR": "05", "CA": "06",
        "CO": "08", "CT": "09", "DE": "10", "FL": "12", "GA": "13",
        "HI": "15", "ID": "16", "IL": "17", "IN": "18", "IA": "19",
        "KS": "20", "KY": "21", "LA": "22", "ME": "23", "MD": "24",
        "MA": "25", "MI": "26", "MN": "27", "MS": "28", "MO": "29",
        "MT": "30", "NE": "31", "NV": "32", "NH": "33", "NJ": "34",
        "NM": "35", "NY": "36", "NC": "37", "ND": "38", "OH": "39",
        "OK": "40", "OR": "41", "PA": "42", "RI": "44", "SC": "45",
        "SD": "46", "TN": "47", "TX": "48", "UT": "49", "VT": "50",
        "VA": "51", "WA": "53", "WV": "54", "WI": "55", "WY": "56",
    }
    
    # Metro area CBSA codes (5-digit) for unemployment series
    METRO_AREAS = {
        # Alabama
        "birmingham, al": "13820",
        "huntsville, al": "26620",
        "mobile, al": "33660",
        
        # Arizona
        "phoenix, az": "38060",
        "tucson, az": "46060",
        
        # Arkansas
        "fayetteville, ar": "22220",
        "little rock, ar": "30780",
        
        # California
        "los angeles, ca": "31080",
        "san diego, ca": "41740",
        "san francisco, ca": "41860",
        "san jose, ca": "41940",
        "sacramento, ca": "40900",
        "fresno, ca": "23420",
        
        # Colorado
        "denver, co": "19740",
        "colorado springs, co": "17820",
        "boulder, co": "14500",
        "fort collins, co": "22660",
        
        # Connecticut
        "hartford, ct": "25540",
        "new haven, ct": "35300",
        
        # Delaware
        "dover, de": "20100",
        
        # Florida
        "miami, fl": "33100",
        "tampa, fl": "45300",
        "orlando, fl": "36740",
        "jacksonville, fl": "27260",
        "tallahassee, fl": "45220",
        "gainesville, fl": "23540",
        
        # Georgia
        "atlanta, ga": "12060",
        "athens, ga": "12020",
        "savannah, ga": "42340",
        
        # Idaho
        "boise, id": "14260",
        
        # Illinois
        "chicago, il": "16980",
        "champaign, il": "16580",
        
        # Indiana
        "indianapolis, in": "26900",
        "bloomington, in": "14020",
        "fort wayne, in": "23060",
        
        # Iowa
        "des moines, ia": "19780",
        "iowa city, ia": "26980",
        
        # Kansas
        "wichita, ks": "48620",
        "lawrence, ks": "29940",
        
        # Kentucky
        "louisville, ky": "31140",
        "lexington, ky": "30460",
        
        # Louisiana
        "new orleans, la": "35380",
        "baton rouge, la": "12940",
        
        # Maryland
        "baltimore, md": "12580",
        "college park, md": "47900",  # Washington-Arlington-Alexandria
        
        # Massachusetts
        "boston, ma": "14460",
        "worcester, ma": "49340",
        "amherst, ma": "43620",  # Springfield
        
        # Michigan
        "detroit, mi": "19820",
        "ann arbor, mi": "11460",
        "lansing, mi": "29620",
        "kalamazoo, mi": "28020",
        
        # Minnesota
        "minneapolis, mn": "33460",
        "duluth, mn": "20260",
        
        # Mississippi
        "jackson, ms": "27140",
        "oxford, ms": "37780",
        
        # Missouri
        "st. louis, mo": "41180",
        "kansas city, mo": "28140",
        "columbia, mo": "17860",
        
        # Nebraska
        "omaha, ne": "36540",
        "lincoln, ne": "30700",
        
        # Nevada
        "las vegas, nv": "29820",
        "reno, nv": "39900",
        
        # New Hampshire
        "manchester, nh": "31700",
        "durham, nh": "14460",  # Boston metro
        
        # New Jersey
        "newark, nj": "35620",
        "trenton, nj": "45940",
        
        # New Mexico
        "albuquerque, nm": "10740",
        
        # New York
        "new york, ny": "35620",
        "buffalo, ny": "15380",
        "rochester, ny": "40380",
        "syracuse, ny": "45060",
        "ithaca, ny": "27060",
        "albany, ny": "10580",
        
        # North Carolina
        "charlotte, nc": "16740",
        "raleigh, nc": "39580",
        "greensboro, nc": "24660",
        "chapel hill, nc": "20500",  # Durham-Chapel Hill
        
        # Ohio
        "columbus, oh": "18140",
        "cleveland, oh": "17460",
        "cincinnati, oh": "17140",
        "toledo, oh": "45780",
        "akron, oh": "10420",
        "oxford, oh": "17140",  # Cincinnati metro
        "athens, oh": "10740",
        
        # Oklahoma
        "oklahoma city, ok": "36420",
        "tulsa, ok": "46140",
        "norman, ok": "36420",  # OKC metro
        
        # Oregon
        "portland, or": "38900",
        "eugene, or": "21660",
        "corvallis, or": "18700",
        
        # Pennsylvania
        "philadelphia, pa": "37980",
        "pittsburgh, pa": "38300",
        "state college, pa": "44300",
        
        # Rhode Island
        "providence, ri": "39300",
        
        # South Carolina
        "charleston, sc": "16700",
        "columbia, sc": "17900",
        "greenville, sc": "24860",
        "clemson, sc": "24860",  # Greenville metro
        
        # Tennessee
        "nashville, tn": "34980",
        "memphis, tn": "32820",
        "knoxville, tn": "28940",
        "chattanooga, tn": "16860",
        
        # Texas
        "houston, tx": "26420",
        "dallas, tx": "19100",
        "austin, tx": "12420",
        "san antonio, tx": "41700",
        "college station, tx": "17780",
        "lubbock, tx": "31180",
        
        # Utah
        "salt lake city, ut": "41620",
        "provo, ut": "39340",
        
        # Vermont
        "burlington, vt": "15540",
        
        # Virginia
        "richmond, va": "40060",
        "virginia beach, va": "47260",
        "charlottesville, va": "16820",
        "blacksburg, va": "13980",
        
        # Washington
        "seattle, wa": "42660",
        "spokane, wa": "44060",
        "pullman, wa": "44060",  # Spokane metro
        
        # West Virginia
        "morgantown, wv": "34060",
        
        # Wisconsin
        "milwaukee, wi": "33340",
        "madison, wi": "31540",
        
        # Wyoming
        "cheyenne, wy": "16940",
        "laramie, wy": "16940",  # Cheyenne metro
    }
    
    def __init__(self):
        """Initialize BLS client"""
        self.api_key = os.getenv('BLS_API_KEY', '')
        self.base_url = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
        self.enabled = bool(self.api_key)
        
        if not self.enabled:
            logger.info("BLS API key not found - unemployment data will not be available")
        else:
            logger.info("BLS client initialized successfully")
    
    def _get_metro_fips(self, city: str, state: str) -> Optional[str]:
        """Get metro area FIPS code from city and state"""
        # Normalize the location
        location_key = f"{city.lower()}, {state.lower()}"
        
        # Direct match
        if location_key in self.METRO_AREAS:
            return self.METRO_AREAS[location_key]
        
        # Try just city name
        city_lower = city.lower()
        for key, fips in self.METRO_AREAS.items():
            if city_lower in key and state.lower() in key:
                return fips
        
        logger.warning(f"Metro area FIPS code not found for {city}, {state}")
        return None
    
    def get_unemployment_rate(self, city: str, state: str) -> Optional[Dict]:
        """
        Get current unemployment rate for a metro area
        
        Args:
            city: City name
            state: State abbreviation
            
        Returns:
            Dictionary with unemployment data or None if not available
        """
        if not self.enabled:
            return None
        
        # Get metro area FIPS code
        fips = self._get_metro_fips(city, state)
        if not fips:
            return None
        
        # Get state FIPS code
        state_fips = self.STATE_FIPS.get(state.upper())
        if not state_fips:
            logger.warning(f"State FIPS code not found for {state}")
            return None
        
        # Build series ID for unemployment rate
        # Format: LAUMT{STATE_FIPS}{METRO_CBSA}00000003
        # Example: LAUMT391714000000003 (Cincinnati, OH)
        #   LAUMT = prefix
        #   39 = Ohio state FIPS
        #   17140 = Cincinnati metro CBSA
        #   00000003 = unemployment rate series code
        series_id = f"LAUMT{state_fips}{fips}00000003"
        logger.info(f"BLS series ID for {city}, {state}: {series_id}")
        
        try:
            # Get current year and last year
            current_year = datetime.now().year
            start_year = current_year - 1
            
            # Build request
            headers = {'Content-type': 'application/json'}
            data = {
                'seriesid': [series_id],
                'startyear': str(start_year),
                'endyear': str(current_year),
                'registrationkey': self.api_key
            }
            
            # Make request
            response = requests.post(
                self.base_url,
                json=data,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            
            # Parse response
            json_data = response.json()
            
            if json_data.get('status') != 'REQUEST_SUCCEEDED':
                logger.error(f"BLS API request failed: {json_data.get('message')}")
                return None
            
            # Extract most recent data point
            series = json_data.get('Results', {}).get('series', [])
            if not series or not series[0].get('data'):
                logger.warning(f"No unemployment data returned for {city}, {state}")
                return None
            
            # Get most recent month
            latest = series[0]['data'][0]
            
            return {
                'unemployment_rate': float(latest['value']),
                'period': f"{latest['periodName']} {latest['year']}",
                'year': latest['year'],
                'month': latest['periodName'],
                'metro_area': series[0].get('seriesID'),
                'source': 'Bureau of Labor Statistics'
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"BLS API request failed: {e}")
            return None
        except (KeyError, ValueError, IndexError) as e:
            logger.error(f"Error parsing BLS response: {e}")
            return None
    
    def format_for_analysis(self, unemployment_data: Optional[Dict]) -> str:
        """
        Format unemployment data for inclusion in economic analysis
        
        Args:
            unemployment_data: Data from get_unemployment_rate()
            
        Returns:
            Formatted string for analysis
        """
        if not unemployment_data:
            return "Unemployment rate data not available"
        
        rate = unemployment_data['unemployment_rate']
        period = unemployment_data['period']
        
        return f"{rate}% ({period}, Bureau of Labor Statistics)"
