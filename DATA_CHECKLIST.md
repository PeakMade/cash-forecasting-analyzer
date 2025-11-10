# Data Collection Checklist

## Files Needed from Business

To complete the implementation, we need sample files (anonymized if necessary) for each of these inputs:

### ✅ Checklist

#### 1. Cash Forecast Excel File
- [ ] Obtain sample Excel file
- [ ] Document sheet structure:
  - [ ] Which sheet contains the cash forecast?
  - [ ] Row headers (line items: revenue, expenses, etc.)
  - [ ] Column headers (months)
  - [ ] Where is the current month indicator?
  - [ ] Where are actuals vs. budget differentiated?
  - [ ] Where is the distribution/contribution line item?
  - [ ] Where is occupancy data stored?

**Key Questions:**
- How are months formatted? (e.g., "Jan 2025", "2025-01", "January 2025")
- How is the recommendation shown? (e.g., positive number = distribution, negative = contribution)
- Are there multiple properties per file, or one file per property?
- Is there a summary page or just detailed data?

#### 2. GL Export File
- [ ] Obtain sample GL export
- [ ] Document format:
  - [ ] File type (Excel, CSV, fixed-width text?)
  - [ ] Column structure
  - [ ] Account number format
  - [ ] Date format
  - [ ] Any header rows?
  - [ ] Any footer/summary rows?

**Key Questions:**
- What accounting system generates this? (e.g., Yardi, MRI, etc.)
- Is this a standard export or custom report?
- What date range does it cover?
- Does it include all accounts or filtered subset?

#### 3. Mystery Analysis File
- [ ] Obtain sample file
- [ ] Understand its purpose
- [ ] Document structure:
  - [ ] File type
  - [ ] Contents
  - [ ] How it relates to the other files

**Key Questions:**
- What does the accountant use this file for?
- Does it contain calculations? Raw data? Both?
- Is this something they create manually or system-generated?

### Data Points We Need to Extract

From the files, we need to identify and extract:

#### From Cash Forecast Excel:
1. **Current Analysis Month**: Which month was just converted from budget to actuals?
2. **Historical Occupancy**: Actual occupancy rates for past months
3. **Projected Occupancy**: Budgeted/forecasted occupancy for future months
4. **Historical Revenue**: Actual revenue (to validate occupancy impact)
5. **Projected Revenue**: Budgeted revenue (to validate against occupancy assumptions)
6. **Recommendation Details**:
   - Type (distribution, contribution, or neither)
   - Amount ($)
   - Target month
7. **Property Identifier**: How is the property identified in the file?

#### From GL Export:
- (TBD based on file format and purpose)
- Possibly: Actual account balances for validation?

#### From Analysis File:
- (TBD once we understand what it contains)

### Property Master Data

Beyond the files, we need to know:

- [ ] How to map property name to university?
- [ ] How to get exact property location (ZIP+4)?
- [ ] Is there a master property list we should reference?
- [ ] Do property codes/IDs change when properties turn over?

### API Access

For external data sources:

- [ ] OpenAI API Key (you have this ✅)
- [ ] Census Bureau API Key (optional but recommended) - Register at: https://api.census.gov/data/key_signup.html
- [ ] BLS API Key (optional) - Register at: https://data.bls.gov/registrationEngine/

### Testing Properties

To build and test the system, ideal sample data would include:

1. **At least 3 properties**:
   - One recommending distribution
   - One recommending contribution
   - One recommending no action

2. **Different scenarios**:
   - Growing university enrollment
   - Declining enrollment
   - Stable enrollment

3. **Time coverage**:
   - At least 6 months of historical data
   - At least 6 months of forecasted data

### Anonymization Guidelines

If anonymizing files for sharing:
- ✅ OK to share: Structure, formulas, formats
- ✅ OK to change: Property names, addresses, dollar amounts (but keep relative proportions)
- ✅ OK to change: Specific university names
- ⚠️ Keep realistic: ZIP codes (use similar metro area), occupancy percentages, revenue patterns

### When Sharing Files

Please provide:
1. The actual files (Excel, CSV, etc.)
2. A brief description of what each file contains
3. Any special notes about how accountants use them
4. Example of a "good" vs "concerning" forecast (if available)

### Timeline

Once we receive the sample files:
- **Day 1**: Review file structures, update parsers
- **Day 2-3**: Test extraction logic, handle edge cases
- **Day 4-5**: Connect external APIs, implement analysis algorithms
- **Day 6-7**: End-to-end testing, refinement

Let me know when you have any of these files ready! 🎯
