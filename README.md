# Cash Forecast Analyzer

Student housing property cash forecast analysis tool using economic data and AI-powered insights.

## Overview

This Flask application analyzes monthly cash forecasts for off-campus student housing properties and validates accountant recommendations for cash distributions or contributions based on:

- Local economic conditions
- University enrollment trends
- Demographic data
- Occupancy projections

## Features

- **File Upload Interface**: Upload Excel cash forecasts, GL exports, and analysis files
- **External Data Integration**: Pulls data from IPEDS, Census Bureau, and BLS APIs
- **AI-Powered Analysis**: Uses OpenAI GPT-4o-mini to generate executive summaries
- **Executive Summary**: Up to 5 bullet points with drill-down capability
- **Property Management**: Handles ~100 properties with annual churn

## Technology Stack

- **Backend**: Python 3.11, Flask
- **AI**: OpenAI GPT-4o-mini
- **Data Sources**: 
  - IPEDS (University enrollment - free)
  - Census Bureau API (Demographics - free)
  - BLS API (Economic indicators - free)
- **File Processing**: pandas, openpyxl
- **Deployment**: Azure App Service

## Setup

### Prerequisites

- Python 3.11
- OpenAI API key
- (Optional) Census Bureau API key
- (Optional) BLS API key

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd cash-forecast-analyzer
```

2. Create virtual environment:
```bash
python -m venv venv
.\venv\Scripts\activate  # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file from template:
```bash
copy .env.example .env
```

5. Edit `.env` and add your API keys:
```
OPENAI_API_KEY=your-key-here
SECRET_KEY=your-secret-key-here
```

### Running Locally

```bash
python app.py
```

Access at: http://localhost:5000

## Usage

1. **Enter Property Information**:
   - Property name
   - Address
   - ZIP code (ZIP+4 format supported)
   - Associated university

2. **Upload Required Files**:
   - Cash Forecast Excel (actuals + budget)
   - GL Export
   - Additional Analysis File

3. **Review Executive Summary**:
   - Validation of accountant's recommendation
   - Up to 5 key findings
   - Drill-down details available

## File Structure

```
cash-forecast-analyzer/
├── app.py                      # Main Flask application
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
├── services/
│   ├── file_processor.py      # Excel/CSV file parsing
│   ├── analysis_engine.py     # Core analysis logic
│   ├── data_sources.py        # External API clients
│   └── summary_generator.py   # OpenAI integration
├── templates/
│   ├── base.html             # Base template
│   └── index.html            # Upload form
└── uploads/                   # Temporary file storage
```

## Development Status

### ✅ Completed
- Flask application structure
- File upload interface
- Service layer architecture
- OpenAI integration framework
- External data source clients (stubs)

### 🚧 In Progress
- Excel file parsing (waiting for sample files)
- IPEDS API integration
- Census Bureau API integration
- BLS API integration

### 📋 TODO
- Occupancy validation logic
- Economic analysis algorithms
- Drill-down detail pages
- Azure deployment configuration
- Unit tests
- Documentation

## API Integrations

### IPEDS (University Enrollment)
- **Source**: U.S. Department of Education
- **Cost**: Free
- **Data**: Enrollment trends, institutional data

### Census Bureau
- **Source**: U.S. Census Bureau
- **Cost**: Free (API key recommended)
- **Data**: Demographics, population by ZIP code

### BLS (Economic Indicators)
- **Source**: Bureau of Labor Statistics
- **Cost**: Free (API key for higher limits)
- **Data**: Unemployment, employment trends

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | OpenAI API key |
| `OPENAI_MODEL` | No | Model name (default: gpt-4o-mini) |
| `SECRET_KEY` | Yes | Flask secret key |
| `CENSUS_API_KEY` | No | Census Bureau API key |
| `BLS_API_KEY` | No | BLS API key |

## Azure Deployment

(TBD - Coming soon)

## Contributing

This is a work in progress. Current priorities:
1. Obtain sample input files from business
2. Implement file parsers
3. Connect external data sources
4. Build occupancy validation logic

## License

(TBD)

## Contact

(TBD)
