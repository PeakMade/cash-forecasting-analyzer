# System Architecture & Data Flow

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User (Accountant)                        │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Web Browser (UI)                              │
│  • Property Info Form                                            │
│  • File Upload (3 files)                                         │
│  • Results Display                                               │
└─────────────────────────┬───────────────────────────────────────┘
                          │ HTTP/HTTPS
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Flask Application (app.py)                    │
│  • Route Handlers                                                │
│  • Session Management                                            │
│  • File Handling                                                 │
└─────────────┬───────────────────────┬───────────────────────────┘
              │                       │
              ▼                       ▼
┌─────────────────────────┐  ┌─────────────────────────────────┐
│  FileProcessor Service  │  │    AnalysisEngine Service       │
│  • Parse Excel          │  │  • Validate Occupancy           │
│  • Parse GL Export      │  │  • Analyze Economics            │
│  • Parse Analysis File  │  │  • Generate Validation          │
└─────────────────────────┘  └──────┬──────────────────────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              │                     │                     │
              ▼                     ▼                     ▼
    ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
    │  IPEDSClient     │  │  CensusClient    │  │    BLSClient     │
    │  (University     │  │  (Demographics)  │  │  (Economics)     │
    │   Enrollment)    │  │                  │  │                  │
    └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘
             │                     │                     │
             │                     │                     │
             ▼                     ▼                     ▼
    ┌──────────────────────────────────────────────────────────────┐
    │              External Data Sources (Free APIs)               │
    │  • IPEDS API (education.gov)                                 │
    │  • Census Bureau API (census.gov)                            │
    │  • BLS API (bls.gov)                                         │
    └──────────────────────────────────────────────────────────────┘

                          ┌───────────────────┐
                          │ SummaryGenerator  │
                          │ Service           │
                          └─────────┬─────────┘
                                    │
                                    ▼
                          ┌───────────────────┐
                          │   OpenAI API      │
                          │   (GPT-4o-mini)   │
                          └───────────────────┘
```

## Detailed Data Flow

### Step 1: File Upload & Property Info
```
User
  │
  ├─ Fills Property Form
  │   • Name
  │   • Address
  │   • ZIP+4
  │   • University
  │
  ├─ Uploads 3 Files
  │   • Cash Forecast Excel
  │   • GL Export
  │   • Analysis File
  │
  └─► POST /upload
         │
         ├─ Validates files
         ├─ Creates session folder
         ├─ Saves files to uploads/
         └─ Creates analysis_id (UUID)
```

### Step 2: File Processing
```
FileProcessor.process_files()
  │
  ├─ Parse Cash Forecast Excel
  │   ├─ Identify current month
  │   ├─ Extract actuals (past months)
  │   ├─ Extract budget (future months)
  │   ├─ Parse distribution/contribution line
  │   ├─ Extract occupancy data
  │   │   ├─ Historical occupancy %
  │   │   └─ Projected occupancy %
  │   └─ Extract revenue data
  │
  ├─ Parse GL Export
  │   ├─ Extract account balances
  │   └─ Map to forecast line items
  │
  └─ Parse Analysis File
      └─ Extract supplemental data
```

### Step 3: External Data Gathering
```
AnalysisEngine.analyze()
  │
  ├─ Property Info (ZIP+4, University)
  │
  ├─► IPEDSClient.get_enrollment_data(university)
  │      │
  │      ├─ Search university by name → UNITID
  │      ├─ Fetch enrollment history (5 years)
  │      ├─ Calculate trend (growing/stable/declining)
  │      └─ Return enrollment_data
  │
  ├─► CensusClient.get_demographics(zip_code)
  │      │
  │      ├─ Fetch population data
  │      ├─ Extract age 18-24 population
  │      ├─ Get population trends
  │      ├─ Get median income
  │      └─ Return demographic_data
  │
  └─► BLSClient.get_economic_indicators(zip_code)
         │
         ├─ Map ZIP → Metro Area
         ├─ Fetch unemployment rate
         ├─ Get employment trends
         ├─ Calculate job growth
         └─ Return economic_data
```

### Step 4: Occupancy Analysis
```
AnalysisEngine._analyze_occupancy()
  │
  ├─ Input:
  │   ├─ Accountant's projected occupancy
  │   ├─ Historical occupancy
  │   ├─ University enrollment trend
  │   └─ Demographic trends
  │
  ├─ Analysis:
  │   ├─ Compare projected vs historical
  │   ├─ Factor in enrollment trend
  │   │   ├─ Growing enrollment = supports higher occupancy
  │   │   └─ Declining enrollment = questions higher occupancy
  │   ├─ Consider demographic factors
  │   │   ├─ Population 18-24 growing? = positive
  │   │   └─ Population 18-24 declining? = concern
  │   └─ Calculate confidence score (0-100)
  │
  └─ Output:
      ├─ Validation result (supports/caution/contradicts)
      ├─ Supporting factors []
      ├─ Risk factors []
      └─ Confidence score
```

### Step 5: Economic Analysis
```
AnalysisEngine._analyze_economic_conditions()
  │
  ├─ Input:
  │   ├─ Unemployment rate
  │   ├─ Employment trend
  │   └─ Job growth indicators
  │
  ├─ Analysis:
  │   ├─ Assess economic health
  │   ├─ Correlate with student housing demand
  │   └─ Identify risk factors
  │
  └─ Output:
      ├─ Economic outlook (positive/neutral/negative)
      ├─ Impact on housing demand
      └─ Risk factors []
```

### Step 6: Recommendation Validation
```
AnalysisEngine._validate_recommendation()
  │
  ├─ Input:
  │   ├─ Accountant's recommendation
  │   │   ├─ Type (distribution/contribution/none)
  │   │   └─ Amount ($)
  │   ├─ Occupancy analysis results
  │   └─ Economic analysis results
  │
  ├─ Synthesis:
  │   ├─ If recommendation = distribution:
  │   │   ├─ Check: Is occupancy projection supported?
  │   │   ├─ Check: Is economic outlook favorable?
  │   │   └─ Check: Is amount reasonable?
  │   │
  │   ├─ If recommendation = contribution:
  │   │   ├─ Check: Are there legitimate concerns?
  │   │   ├─ Check: Is amount sufficient?
  │   │   └─ Check: Are there alternatives?
  │   │
  │   └─ If recommendation = none:
  │       └─ Check: Is this appropriately conservative?
  │
  └─ Output:
      ├─ Validation result (approved/caution/concern)
      ├─ Confidence score (0-100)
      ├─ Supporting factors []
      ├─ Risk factors []
      └─ Alternative recommendation (if applicable)
```

### Step 7: Executive Summary Generation
```
SummaryGenerator.generate_summary()
  │
  ├─ Prepare Context for OpenAI:
  │   ├─ Property details
  │   ├─ Accountant's recommendation
  │   ├─ Occupancy analysis
  │   ├─ Economic analysis
  │   └─ Validation results
  │
  ├─► OpenAI API (gpt-4o-mini)
  │      │
  │      ├─ System Prompt:
  │      │   "You are a financial analyst specializing in
  │      │    student housing. Generate executive summary..."
  │      │
  │      ├─ User Prompt:
  │      │   [Full context with data]
  │      │
  │      ├─ Parameters:
  │      │   ├─ Model: gpt-4o-mini
  │      │   ├─ Temperature: 0.7
  │      │   └─ Max Tokens: 800
  │      │
  │      └─► Returns: Executive summary text
  │
  ├─ Parse Response:
  │   ├─ Extract bullet points (3-5)
  │   ├─ Create drill-down details
  │   └─ Structure data
  │
  └─ Output:
      ├─ Executive summary text
      ├─ Bullet points [] (each with drill-down link)
      ├─ Confidence score
      └─ Full analysis data
```

### Step 8: Return to User
```
Response
  │
  ├─ HTTP 200 OK
  │
  └─ JSON Response:
      ├─ success: true
      ├─ analysis_id: "uuid"
      ├─ property: { name, address, etc. }
      └─ summary: {
          ├─ property_name
          ├─ analysis_date
          ├─ recommendation_validation
          ├─ executive_summary (text)
          ├─ bullets: [
          │   { id: 1, text: "...", has_details: true },
          │   { id: 2, text: "...", has_details: true },
          │   ...
          │ ]
          ├─ confidence_score
          └─ full_analysis: { ... }
      }
```

## Production Architecture (Azure)

```
┌─────────────────────────────────────────────────────────────────┐
│                       Internet (HTTPS)                           │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │  Azure App Service    │
              │  (Flask App)          │
              │  • Python 3.11        │
              │  • Managed Identity   │
              └────┬──────────┬───────┘
                   │          │
       ┌───────────┘          └─────────────┐
       │                                    │
       ▼                                    ▼
┌──────────────────┐              ┌──────────────────┐
│ Azure Key Vault  │              │  Azure Storage   │
│ • OPENAI_API_KEY │              │  • Blob Storage  │
│ • Other Secrets  │              │  • File Uploads  │
└──────────────────┘              └──────────────────┘
       │                                    │
       └────────────┬───────────────────────┘
                    │
                    ▼
         ┌────────────────────┐
         │ Application        │
         │ Insights           │
         │ • Monitoring       │
         │ • Logging          │
         │ • Metrics          │
         └────────────────────┘

Optional (Future):
         ┌────────────────────┐
         │ Azure Redis Cache  │
         │ • API Results      │
         │ • Session Data     │
         └────────────────────┘
```

## Caching Strategy (Future Optimization)

```
Request
  │
  ├─ Check Cache (Redis)
  │   │
  │   ├─ Cache Key: "ipeds:{university_name}"
  │   │   └─ TTL: 365 days (enrollment updated annually)
  │   │
  │   ├─ Cache Key: "census:{zip_code}"
  │   │   └─ TTL: 90 days (quarterly updates)
  │   │
  │   └─ Cache Key: "bls:{metro_area}:{month}"
  │       └─ TTL: 30 days (monthly updates)
  │
  ├─ If Cache Hit:
  │   └─► Return cached data (fast!)
  │
  └─ If Cache Miss:
      ├─► Fetch from External API
      ├─► Store in Cache
      └─► Return data
```

## Error Handling Flow

```
Error Occurs
  │
  ├─ File Upload Error?
  │   ├─► Validate file type
  │   ├─► Check file size
  │   └─► Return 400 with clear message
  │
  ├─ File Parsing Error?
  │   ├─► Log error details
  │   ├─► Continue with partial data
  │   └─► Flag in analysis results
  │
  ├─ External API Error?
  │   ├─► Log error
  │   ├─► Try alternate data source
  │   ├─► Use cached data if available
  │   └─► Continue with degraded analysis
  │
  ├─ OpenAI API Error?
  │   ├─► Log error
  │   ├─► Retry once (rate limit)
  │   └─► Use fallback summary generator
  │
  └─ Unexpected Error?
      ├─► Log full stack trace
      ├─► Return 500 with generic message
      └─► Alert monitoring system
```

## Data Security & Privacy

```
Input Files
  │
  ├─► Uploaded via HTTPS (encrypted in transit)
  │
  ├─► Saved temporarily with UUID filename
  │   └─► Location: uploads/{analysis_id}/
  │
  ├─► Processed in memory (not logged)
  │
  └─► Deleted after analysis (configurable retention)

API Keys
  │
  ├─► Stored in Azure Key Vault (encrypted at rest)
  │
  ├─► Retrieved via Managed Identity
  │
  └─► Never logged or exposed in responses

Personal Data
  │
  └─► None collected (property data only)
```

---

This architecture supports:
- ✅ Scalability (stateless design)
- ✅ Cost optimization (caching, efficient APIs)
- ✅ Security (encryption, Key Vault, Managed Identity)
- ✅ Reliability (error handling, fallbacks)
- ✅ Maintainability (clear separation of concerns)
