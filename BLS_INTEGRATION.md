# Unemployment Data Integration

## Overview

The system now integrates official unemployment data from the **Bureau of Labor Statistics (BLS)** to complement the web search approach. This provides credible government data for capital committee presentations.

## Architecture

### Hybrid Data Approach

Similar to the IPEDS integration for enrollment data, we now have a dual approach for unemployment:

1. **BLS API** (if enabled): Official government unemployment rates
   - Source: U.S. Bureau of Labor Statistics
   - Data: Monthly unemployment rates by metro area
   - Credibility: Official government statistics
   - Currency: Updated monthly (typically 2-3 weeks lag)

2. **Web Search** (fallback): Additional employment context
   - Job growth trends
   - Major employers
   - Recent layoffs or economic changes
   - Student employment opportunities

### Data Flow

```
Property Analysis Request
         ↓
    ┌────────────────────────────┐
    │ Economic Analyzer          │
    └────────────────────────────┘
         ↓
    ┌────────────────────────────┐
    │ Fetch Official Data:       │
    │  - IPEDS: Enrollment       │
    │  - BLS: Unemployment       │
    └────────────────────────────┘
         ↓
    ┌────────────────────────────┐
    │ Build Prompt with          │
    │ Official Data Context      │
    └────────────────────────────┘
         ↓
    ┌────────────────────────────┐
    │ OpenAI Responses API       │
    │ with web_search tool       │
    │ - Current enrollment       │
    │ - Employment trends        │
    │ - Economic outlook         │
    └────────────────────────────┘
         ↓
    ┌────────────────────────────┐
    │ Combined Analysis          │
    │ - Official BLS unemployment │
    │ - Historical IPEDS data    │
    │ - Current web search data  │
    └────────────────────────────┘
```

## Getting a BLS API Key (Free)

### Step 1: Register
1. Go to: https://www.bls.gov/developers/home.htm
2. Click **"Registration"** or visit: https://data.bls.gov/registrationEngine/
3. Fill out the registration form
   - Name and email required
   - No credit card needed
   - Free forever

### Step 2: Receive Key
- API key sent to your email immediately
- Key looks like: `abcd1234efgh5678ijkl9012mnop3456`

### Step 3: Add to .env
```bash
# BLS API (optional, free tier available)
BLS_API_KEY=your_actual_key_here
```

### Step 4: Test
```bash
python test_bls_integration.py
```

## Free Tier Limits

BLS API free tier provides:
- **500 queries per day** (enough for 500 property analyses/day)
- **25 queries per 10 seconds** (rate limiting)
- **10 years of data** per query
- **No cost** ever

For our use case (1 unemployment query per property analysis), this is more than sufficient.

## Metro Area Coverage

The BLS client includes ~200 metro areas covering all major university cities:

### Examples
- Cincinnati, OH → Cincinnati metro area
- Austin, TX → Austin-Round Rock metro
- Boston, MA → Boston-Cambridge-Newton metro
- Columbus, OH → Columbus metro
- Ann Arbor, MI → Ann Arbor metro

### What Happens If Metro Not Found?
- System logs a warning
- Falls back to web search for unemployment data
- Analysis continues without BLS data
- No errors or failures

## Data Quality

### BLS Data (when available)
```
Unemployment Rate: 3.8% (January 2026, Bureau of Labor Statistics)
```

**Advantages:**
- ✓ Official government source
- ✓ Specific percentage (3.8%)
- ✓ Recent date (January 2026)
- ✓ Credible for executive presentations
- ✓ Consistent methodology across cities

### Web Search Data (always used for context)
```
Job Growth Trends: -8,300 jobs lost June-Nov 2025 (wlwt.com)
Major Employers: Fifth Third, Kroger, P&G, Cincinnati Children's
```

**Advantages:**
- ✓ Current news and trends
- ✓ Qualitative context (layoffs, new employers)
- ✓ Student-specific employment info
- ✓ Complements BLS quantitative data

## Integration Points

### services/bls_client.py
- BLS API client
- Metro area FIPS code mapping
- Unemployment rate fetching
- Error handling for unavailable metros

### services/economic_analysis.py
- Imports `BLSClient`
- Fetches unemployment data for property location
- Includes BLS data in prompt context
- Instructs AI to use official BLS figures when provided
- Falls back to web search if BLS unavailable

### .env
```bash
BLS_API_KEY=your_key_here  # Optional, enables BLS data
```

## Testing

### Test BLS Integration Only
```bash
python test_bls_integration.py
```

Shows:
- Whether BLS API key is configured
- Instructions to get free API key
- Test unemployment data for multiple cities
- Metro area coverage confirmation

### Test Full Employment Data
```bash
python test_employment_data.py
```

Shows:
- Complete employment section analysis
- BLS unemployment rate (if enabled)
- Web search employment trends
- Major employers
- Economic outlook
- Risk factors

## Example Output

### With BLS Enabled
```
3. LOCAL EMPLOYMENT & ECONOMIC CONDITIONS

=== OFFICIAL UNEMPLOYMENT DATA (Bureau of Labor Statistics) ===
Unemployment Rate: 3.8% (January 2026, Bureau of Labor Statistics)

Employment Metrics (2025-2026):
- Unemployment Rate: 3.8% (January 2026, Bureau of Labor Statistics)
- Job Growth Trends: -8,300 jobs lost June-Nov 2025 (wlwt.com)
- Major Employers: Fifth Third Bank, Kroger, P&G, Cincinnati Children's
- Industries: Finance, healthcare, education, manufacturing
```

### Without BLS (Web Search Only)
```
3. LOCAL EMPLOYMENT & ECONOMIC CONDITIONS

Employment Metrics (2025-2026):
- Unemployment Rate: Specific current data not available
- Job Growth Trends: -8,300 jobs lost June-Nov 2025 (wlwt.com)
- Major Employers: Fifth Third Bank, Kroger, P&G, Cincinnati Children's
```

## Recommendation

**Get a BLS API key** - it takes 2 minutes and provides:
1. Official government data for credibility
2. Specific unemployment rates for every property
3. No cost, no usage concerns
4. Better presentations to capital committee

The web search still provides valuable qualitative context (layoffs, new employers, trends), so you get both:
- **BLS**: Authoritative unemployment rate
- **Web Search**: Current economic context and trends

This is the same successful pattern we used for enrollment (IPEDS + web search).

## Production Deployment

Add to production environment variables:
```bash
BLS_API_KEY=your_production_key_here
```

That's it - no code changes needed. The system automatically uses BLS data when available.
