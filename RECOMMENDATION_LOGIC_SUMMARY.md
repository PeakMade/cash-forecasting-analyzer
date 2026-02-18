# Cash Forecast Analyzer - Recommendation Logic Summary
## For Accounting Leadership Review

---

## **Overview**

The Cash Forecast Analyzer uses a multi-factor decision framework to generate one of three recommendations:

1. **CONTRIBUTE** - Capital contribution required
2. **DISTRIBUTE** - Cash distribution approved
3. **DO_NOTHING** - Maintain current position

All recommendations are driven by **user-selected risk tolerance** (Low/Medium/High) which controls key thresholds throughout the analysis.

---

## **Input Documents & Data Extraction**

### **1. Cash Forecast (Excel)**
**Purpose:** Understand current and projected cash flow position

**Key Extractions:**
- **Current Month Free Cash Flow (FCF)** - Actual performance
- **Projected Month FCF** - Budget forecast for next month
- **Current & Projected Occupancy** - Unit fill rates
- **Accountant's Planned Distributions/Contributions** - Forecasted cash movements
- **Multi-Month Budget Data** - Up to 12 months of forward projections (if available)

**Critical Calculation:**
```
Operational FCF = Projected FCF - Planned Distributions/Contributions
```
This isolates the property's TRUE operational cash generation before any capital decisions.

**Multi-Month Averaging:**
- System extracts all available budget months (e.g., Jan-Dec 2026)
- Calculates **average monthly operational FCF** across the period
- **Why:** Avoids distortions from single-month anomalies (e.g., 3x debt service in January)
- **Example:** January shows -$363K, but 5-month average is -$116K (68% difference)

---

### **2. Comparative Income Statement (PDF)**
**Purpose:** Assess operational performance vs. budget

**Key Extractions:**
- **Net Operating Income (NOI)** - Month Actual, Budget, Variance %
- **Total Operating Income** - YTD Actual, Budget, Variance %
- **Total Operating Expenses** - YTD Actual, Budget, Variance %
- **Reporting Period** - Month and YTD coverage

**Critical Metric:**
```
NOI YTD Variance % = (NOI Actual - NOI Budget) / NOI Budget × 100
```

**Usage in Decisions:**
- **< -5%** → Property underperforming budget (most conservative deficit projection)
- **±5%** → On budget (moderate deficit projection)
- **> +5%** → Outperforming budget (least conservative deficit projection)

---

### **3. Balance Sheet (PDF)**
**Purpose:** Evaluate financial position and liquidity

**Key Extractions:**
- **Cash Balance** (Total Cash and Cash Equivalents)
- **Current Liabilities** (Total Current Liabilities)
- **Accounts Receivable**
- **Total Debt** (Notes Payable)
- **Monthly Debt Service** (estimated from debt changes + accrued interest)

**Critical Calculations:**
```
Working Capital = Cash Balance - Current Liabilities

Current Ratio = Cash Balance / Current Liabilities
```

**Working Capital Crisis Trigger:**
- If `Working Capital < -$50,000` → **CONTRIBUTE** decision activated
- Indicates property cannot meet near-term obligations

---

## **Risk-Based Configuration**

The user selects a **Client Risk Level** at analysis time:
- **Low Risk** - More aggressive cash management, lower reserve requirements
- **Medium Risk** - Balanced approach
- **High Risk** - Most conservative, highest reserve requirements

### **Configurable Parameters by Risk Level:**

#### **Operating Reserve Months** (Environment Variables)
Number of months of operating costs to maintain as cash reserves.

- Configurable via: `RISK_LOW_MONTHS`, `RISK_MEDIUM_MONTHS`, `RISK_HIGH_MONTHS`
- **Usage:** Operating Reserve Buffer calculation
- **Formula:** `Operating Reserve = Monthly Operating Cost × Risk Months`

#### **Working Capital Target Ratio** (Environment Variables)
Target current ratio (cash/liabilities) for working capital restoration.

- Configurable via: `RISK_LOW_WC_TARGET`, `RISK_MEDIUM_WC_TARGET`, `RISK_HIGH_WC_TARGET`
- **Values range:** 0.5 (low) to 1.0 (high)
- **Usage:** Working capital restoration calculation
- **Formula:** `Target Cash = Current Liabilities × WC Target Ratio`

---

## **Contribution Calculation Logic**

When a working capital crisis is detected (working capital < -$50K), the system calculates a required contribution with **three transparent components:**

### **Component 1: Forward Deficit Coverage**

**Purpose:** Cover projected operational deficits until property stabilizes

**Formula:**
```
Forward Deficit Coverage = Average Monthly Deficit × Months Forward

Where:
    Months Forward = User's Risk Selection (reserve months directly)
```

**Philosophy:**
The accountant selects the risk level based on their complete knowledge of the property, including performance, market conditions, and investor expectations. We use their risk selection **directly** without additional multipliers, giving them full control over the recommendation.

**Examples:**
- **Low Risk (2 months):** Covers **2 months** of deficits
- **Medium Risk (4 months):** Covers **4 months** of deficits
- **High Risk (6 months):** Covers **6 months** of deficits

**Performance Context:**
While we don't multiply based on performance, the detailed analysis shows:
- NOI variance (underperforming/on budget/outperforming)
- This transparency helps accountants choose the appropriate risk level
- They can re-run with different risk selections if needed

**Monthly Deficit Value:**
- Uses **multi-month average operational FCF** if 4+ budget months available
- Otherwise uses single projected month operational FCF
- Takes absolute value if negative

---

### **Component 2: Working Capital Restoration**

**Purpose:** Restore cash position to meet near-term obligations

**Formula:**
```
WC Restoration = MAX(0, Target Cash - Current Cash)
```

Where:
    Target Cash = Current Liabilities × WC Target Ratio
    WC Target Ratio = Based on user's risk selection
```

**Current Ratio Targets by Risk:**
- **Low Risk:** 0.5 (50 cents cash per dollar of liability)
- **Medium Risk:** 0.75 (75 cents cash per dollar of liability)
- **High Risk:** 1.0 (100 cents cash per dollar of liability - fully covered)

**Example (Low Risk):**
```
Current Liabilities: $478,794
Current Cash: $29,450
WC Target Ratio: 0.5

Target Cash = $478,794 × 0.5 = $239,397
WC Restoration = $239,397 - $29,450 = $209,947
```

---

### **Component 3: Operating Reserve Buffer**

**Purpose:** Build cash reserves for unexpected expenses and seasonal variations

**Formula:**
```
Operating Reserve Buffer = Monthly Operating Cost × Reserve Months

Where:
    Monthly Operating Cost = Average Monthly Deficit (if property in deficit)
                           OR Monthly Operational FCF
    Reserve Months = User's risk selection
```

**Examples:**
- **Low Risk (2 months):** $116,255 × 2 = **$232,510**
- **Medium Risk (4 months):** $116,255 × 4 = **$465,020**
- **High Risk (6 months):** $116,255 × 6 = **$697,530**

---

### **Total Contribution Calculation**

```
TOTAL CONTRIBUTION = Forward Deficit Coverage 
                   + Working Capital Restoration 
                   + Operating Reserve Buffer
```

**Final rounding:** Rounded UP to nearest $10,000 for practicality

**Example Scenario (Campus Creek, Low Risk):**
```
1. Forward Deficit Coverage:
   - Average Monthly Deficit: $116,255
   - Months Forward: 2 months (Low Risk selection)
   - Coverage: $116,255 × 2 = $232,510

2. Working Capital Restoration:
   - Current Liabilities: $478,794
   - Current Cash: $29,450
   - Target Ratio: 0.5
   - Target Cash: $478,794 × 0.5 = $239,397
   - Restoration: $239,397 - $29,450 = $209,947

3. Operating Reserve Buffer:
   - Monthly Cost: $116,255
   - Reserve Months: 2
   - Buffer: $116,255 × 2 = $232,510

TOTAL: $232,510 + $209,947 + $232,510 = $674,967
Rounded: $680,000
```

---

## **Distribution Decision Logic**

**Trigger Conditions (ALL must be true):**
1. **Positive Projected FCF** > $50,000
2. **Working Capital Healthy** (≥ -$50,000)
3. **Adequate Reserves** (Months of Reserves ≥ Risk Requirement)
4. **No Material Performance Issues** (NOI variance not severely negative)

**Distribution Amount Calculation:**
```
Available for Distribution = MIN(
    Projected Operational FCF - (Monthly Operating Cost × Reserve Months),
    Current Cash Balance - (Current Liabilities × WC Target Ratio) - Safety Buffer
)

Final Amount = Round DOWN to nearest $10,000
```

**Safety Buffers:**
- Never distribute into working capital crisis
- Maintain minimum reserve requirements
- Conservative approach to preserve liquidity

---

## **DO_NOTHING Decision Logic**

**Trigger Conditions (ONE must be true):**
1. **Reserves Below Minimum** but no working capital crisis
2. **Projected Deficit** is minor and well within reserve capacity
3. **Market Conditions** warrant conservative cash retention
4. **Seasonal Patterns** suggest temporary variance

**Rationale Focus:**
- Building reserves to target level
- Monitoring performance trends
- Deferring distributions until reserve requirements met

---

## **Key Safeguards & Validations**

### **1. Multi-Month Averaging**
- Prevents single-month anomalies from distorting decisions
- Example: 3x debt service in January doesn't force excessive contribution

### **2. Occupancy Adjustments**
- If projected occupancy significantly differs from current, FCF is adjusted
- Prevents decisions based on unrealistic occupancy assumptions

### **3. Operational FCF Focus**
- All contribution/distribution analysis uses operational FCF (before capital movements)
- Isolates true property performance from accounting transactions

### **4. Transparent Breakdowns**
- Every contribution shows explicit components
- Users see exactly: deficit months, WC restoration, reserve buffer amounts
- Includes comparison to accountant's recommendation (if available)

### **5. Performance-Based Scaling**
- Underperforming properties get longer deficit coverage (3x multiplier)
- Outperforming properties get shorter coverage (1x multiplier)
- On-budget properties get moderate coverage (2x multiplier)

---

## **Output Format**

### **Executive Summary**
5-7 bullet points including:
- **Decision Statement** (CONTRIBUTE/DISTRIBUTE/DO_NOTHING with amount)
- **Working Capital Status** (if applicable)
- **Operational Performance** (NOI variance, occupancy trends)
- **Reserve Position** (months of coverage vs. requirement)
- **Market Context** (enrollment trends, seasonality, new supply)
- **Accountant Comparison** (if forecasted distribution/contribution exists)

### **Detailed Rationale**
Comprehensive analysis with sections:
1. **Decision Rationale** - Why this decision was made
2. **Reserve Position** - Current coverage vs. minimum requirements
3. **Operational Performance** - Budget variance analysis
4. **Cash Flow Interpretation** - Projected vs. current analysis
5. **Economic Context** - Market and seasonal factors
6. **Accountant Comparison** (if applicable) - System vs. accountant recommendations

---

## **Configuration Flexibility**

All risk-based thresholds are configured via environment variables:
- **Reserve Months:** `RISK_LOW_MONTHS`, `RISK_MEDIUM_MONTHS`, `RISK_HIGH_MONTHS`
- **WC Target Ratios:** `RISK_LOW_WC_TARGET`, `RISK_MEDIUM_WC_TARGET`, `RISK_HIGH_WC_TARGET`

**Benefits:**
- Easy to adjust without code changes
- Can be tuned based on accounting leadership preferences
- Supports A/B testing of different risk profiles
- Documented defaults with clear rationale

---

## **Example Impact of Risk Selection**

**Property:** Campus Creek Cottages (showing differences across risk levels)

| Risk Level | Reserve Months | WC Target | Deficit Months | Total Contribution |
|------------|---------------|-----------|----------------|-------------------|
| **Low**    | 2             | 0.5       | 2              | **~$680K**        |
| **Medium** | 4             | 0.75      | 4              | **~$1.1M**        |
| **High**   | 6             | 1.0       | 6              | **~$1.5M**        |

**Key Insight:** Risk selection gives accountants direct control over contribution size. They can select the risk level based on their complete knowledge of property conditions, investor expectations, and market dynamics. The system uses their selection directly without additional multipliers.

**Performance Context:** The system still shows performance metrics (NOI variance, occupancy trends) in the detailed rationale so accountants understand what drove the contribution recommendation - but these metrics don't multiply the risk selection. This allows accountants to iterate by re-running with a different risk level if needed.

---

## **Validation & Testing**

✅ **Test Suite:** 35 tests passing covering:
- Authentication & authorization
- Session management
- File upload & validation
- API endpoints
- Error handling

✅ **Multi-Month Extraction:** Verified 5-12 month budget extraction with averaging

✅ **Regression Testing:** Confirmed DO_NOTHING decisions unaffected by changes

✅ **Edge Cases Handled:**
- Missing budget data → Falls back to single month
- Zero/negative occupancy → Validation flags
- Missing financial data → Clear error messages
- Anomalous single-month values → Averaged out

---

## **Recommendations for Review**

**Questions for Leadership:**

1. **Working Capital Targets:** Are the current ratio targets (0.5/0.75/1.0) appropriate for student housing properties? Should Low Risk be even lower?

2. **Risk-Based Philosophy:** The system now uses risk selection directly without performance multipliers. Does this give accountants the right level of control? Should we add other risk configurations?

3. **Reserve Month Ranges:** Current range is 2-6 months. Should this be wider (e.g., 1-9 months)?

4. **Working Capital Crisis Threshold:** Currently triggers at -$50K. Should this be property-size dependent (e.g., % of budget)?

5. **Distribution Conservatism:** Current logic is quite conservative. Should we allow distributions with lower reserve coverage if performance is strong?

---

**Prepared by:** Cash Forecast Analyzer Development Team  
**Date:** February 2026  
**Version:** 2.1 (Risk-Based Control Update)
