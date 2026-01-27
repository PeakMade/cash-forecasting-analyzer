"""
Comprehensive Recommendation Engine
Synthesizes Cash Forecast, Income Statement, Balance Sheet, and Economic Analysis
Produces tiered recommendations: Executive Decision → Summary Bullets → Detailed Analysis
"""
from datetime import datetime
from typing import Dict, List, Tuple


class RecommendationEngine:
    def __init__(self):
        self.decision_thresholds = {
            'minor_deficit': 50000,      # Less than $50k deficit = minor
            'moderate_deficit': 150000,  # $50k-$150k = moderate
            'major_deficit': 150000,     # More than $150k = major
            'distribution_min': 100000,  # Minimum surplus to recommend distribution
            'cash_reserve_months': 6,    # Minimum months of reserves to maintain
        }
    
    def analyze_and_recommend(self, cash_forecast_data: Dict, income_statement_data: Dict, 
                             balance_sheet_data: Dict, economic_analysis: Dict) -> Dict:
        """
        Generate comprehensive recommendation based on all input data
        
        Returns:
            dict: {
                'decision': 'CONTRIBUTE' | 'DISTRIBUTE' | 'DO_NOTHING',
                'amount': float or None,
                'executive_summary': [list of 5-7 bullet points],
                'detailed_rationale': {detailed analysis sections},
                'confidence': 'HIGH' | 'MEDIUM' | 'LOW'
            }
        """
        
        # Extract key metrics
        projected_fcf = cash_forecast_data.get('projected_fcf', 0)
        current_fcf = cash_forecast_data.get('current_fcf', 0)
        cash_balance = balance_sheet_data.get('cash_balance', 0)
        current_liabilities = balance_sheet_data.get('current_liabilities', 0)
        monthly_debt_service = balance_sheet_data.get('monthly_debt_service', 0)
        
        current_occupancy = cash_forecast_data.get('current_occupancy', 0)
        projected_occupancy = cash_forecast_data.get('projected_occupancy', 0)
        
        # NEW: Extract and analyze multi-month projection
        projected_months = cash_forecast_data.get('projected_months', [])
        multi_month_analysis = self._analyze_multi_month_projection(projected_months) if projected_months else None
        
        noi_ytd_variance_pct = income_statement_data.get('noi_ytd_variance_pct', 0)
        noi_month_variance_pct = income_statement_data.get('noi_month_variance_pct', 0)
        expenses_ytd_variance_pct = income_statement_data.get('expenses_ytd_variance_pct', 0)
        
        seasonal_factor = economic_analysis.get('seasonal_factor', {})
        enrollment_trend = economic_analysis.get('enrollment_trend', 'stable')
        
        # CRITICAL: Adjust projected FCF if occupancy gap exists
        occupancy_adjusted_fcf, occupancy_adjustment_note = self._adjust_fcf_for_occupancy(
            projected_fcf, current_occupancy, projected_occupancy
        )
        
        # Calculate key ratios
        months_of_reserves = self._calculate_months_of_reserves(
            cash_balance, monthly_debt_service, current_liabilities
        )
        
        working_capital = cash_balance - current_liabilities
        
        # Determine decision using ADJUSTED cash flow and multi-month analysis
        decision, amount, confidence, contribution_breakdown = self._make_decision(
            projected_fcf=occupancy_adjusted_fcf,  # Use adjusted value
            current_fcf=current_fcf,
            cash_balance=cash_balance,
            months_of_reserves=months_of_reserves,
            working_capital=working_capital,
            noi_ytd_variance_pct=noi_ytd_variance_pct,
            monthly_debt_service=monthly_debt_service,
            current_liabilities=current_liabilities,
            seasonal_factor=seasonal_factor,
            enrollment_trend=enrollment_trend,
            multi_month_analysis=multi_month_analysis  # NEW: Pass multi-month data
        )
        
        # Generate executive summary bullets
        executive_summary = self._generate_executive_summary(
            decision=decision,
            amount=amount,
            projected_fcf=occupancy_adjusted_fcf,  # Use adjusted value
            cash_balance=cash_balance,
            months_of_reserves=months_of_reserves,
            noi_ytd_variance_pct=noi_ytd_variance_pct,
            noi_month_variance_pct=noi_month_variance_pct,
            expenses_ytd_variance_pct=expenses_ytd_variance_pct,
            seasonal_factor=seasonal_factor,
            enrollment_trend=enrollment_trend,
            working_capital=working_capital,
            current_liabilities=current_liabilities,
            contribution_breakdown=contribution_breakdown
        )
        
        # Add occupancy adjustment note to summary if significant
        if occupancy_adjustment_note:
            executive_summary.insert(2, occupancy_adjustment_note)  # Insert after decision and FCF bullets
        
        # Generate detailed rationale
        detailed_rationale = self._generate_detailed_rationale(
            cash_forecast_data=cash_forecast_data,
            income_statement_data=income_statement_data,
            balance_sheet_data=balance_sheet_data,
            economic_analysis=economic_analysis,
            decision=decision,
            amount=amount,
            months_of_reserves=months_of_reserves,
            occupancy_adjustment_note=occupancy_adjustment_note
        )
        
        return {
            'decision': decision,
            'amount': amount,
            'executive_summary': executive_summary,
            'detailed_rationale': detailed_rationale,
            'confidence': confidence,
            'property_name': cash_forecast_data.get('property_name', 'Unknown'),
            'analysis_month': cash_forecast_data.get('current_month', 'Unknown'),
            'projected_month': cash_forecast_data.get('projected_month', 'Unknown'),
            'occupancy_adjusted': occupancy_adjusted_fcf != projected_fcf,
            'multi_month_analysis': multi_month_analysis  # NEW: Include 6-month analysis in output
        }
    
    def _adjust_fcf_for_occupancy(self, projected_fcf: float, current_occupancy: float, 
                                  projected_occupancy: float) -> tuple:
        """
        Adjust projected FCF if occupancy assumptions are unrealistic
        
        If there's a significant gap between current actual occupancy and the occupancy
        assumed in the budget/projection, adjust the projected FCF proportionally.
        
        Example: If current is 90.2% but projection assumes 96%, that's a 6% gap.
        Revenue projections may be overstated by approximately 6%.
        
        Args:
            projected_fcf: The forecasted cash flow from the Excel projection
            current_occupancy: Actual occupancy percentage (e.g., 90.2 = 90.2%)
            projected_occupancy: Occupancy percentage assumed in budget (e.g., 96 = 96%)
        
        Returns:
            tuple: (adjusted_fcf, warning_note)
                - adjusted_fcf: Original FCF adjusted for occupancy gap
                - warning_note: String explaining adjustment, or None if no adjustment needed
        """
        # Only adjust if we have valid occupancy data
        if not current_occupancy or not projected_occupancy:
            return projected_fcf, None
        
        # Calculate occupancy gap
        occupancy_gap_pct = projected_occupancy - current_occupancy
        
        # Only flag if gap is significant (>3 percentage points)
        if abs(occupancy_gap_pct) < 3.0:
            return projected_fcf, None
        
        # Adjust projected FCF by occupancy ratio
        # If projected assumes 96% but actual is 90.2%, multiply by (90.2/96) = 0.94
        if projected_occupancy > 0:
            occupancy_ratio = current_occupancy / projected_occupancy
            adjusted_fcf = projected_fcf * occupancy_ratio
            adjustment_amount = adjusted_fcf - projected_fcf
            
            warning_note = (
                f"⚠️ OCCUPANCY GAP DETECTED: Current occupancy is {current_occupancy:.1f}% "
                f"but projection assumes {projected_occupancy:.1f}%. Adjusted projected FCF "
                f"from ${projected_fcf:,.0f} to ${adjusted_fcf:,.0f} "
                f"({adjustment_amount:+,.0f}) to reflect realistic revenue expectations."
            )
            
            return adjusted_fcf, warning_note
        else:
            # Can't adjust if projected occupancy is 0
            return projected_fcf, None
    
    def _analyze_multi_month_projection(self, projected_months: List[Dict]) -> Dict:
        """
        Analyze 6-month cash flow projection
        
        Returns:
            dict: {
                'total_fcf': Total cumulative FCF over period,
                'average_fcf': Average monthly FCF,
                'lowest_month': {'month': str, 'fcf': float},
                'highest_month': {'month': str, 'fcf': float},
                'positive_months': int,
                'negative_months': int,
                'trend': 'INCREASING' | 'DECREASING' | 'STABLE',
                'all_positive': bool
            }
        """
        if not projected_months:
            return None
        
        total_fcf = sum(m['fcf'] for m in projected_months)
        average_fcf = total_fcf / len(projected_months) if projected_months else 0
        
        # Find lowest and highest months
        lowest_month = min(projected_months, key=lambda x: x['fcf'])
        highest_month = max(projected_months, key=lambda x: x['fcf'])
        
        # Count positive/negative months
        positive_months = sum(1 for m in projected_months if m['fcf'] > 0)
        negative_months = sum(1 for m in projected_months if m['fcf'] < 0)
        
        # Determine trend (compare first half to second half)
        if len(projected_months) >= 4:
            half_point = len(projected_months) // 2
            if half_point == 0:
                trend = 'STABLE'
            else:
                first_half = projected_months[:half_point]
                second_half = projected_months[half_point:]
                
                first_half_sum = sum(m['fcf'] for m in first_half)
                second_half_sum = sum(m['fcf'] for m in second_half)
                
                first_half_avg = first_half_sum / len(first_half) if len(first_half) > 0 else 0
                second_half_avg = second_half_sum / len(second_half) if len(second_half) > 0 else 0
                
                # Calculate percentage difference, handling zero values
                if first_half_avg != 0:
                    diff_pct = ((second_half_avg - first_half_avg) / abs(first_half_avg)) * 100
                else:
                    diff_pct = 0
                
                if diff_pct > 10:
                    trend = 'INCREASING'
                elif diff_pct < -10:
                    trend = 'DECREASING'
                else:
                    trend = 'STABLE'
        else:
            trend = 'STABLE'
        
        return {
            'total_fcf': total_fcf,
            'average_fcf': average_fcf,
            'lowest_month': {'month': lowest_month['month'], 'fcf': lowest_month['fcf']},
            'highest_month': {'month': highest_month['month'], 'fcf': highest_month['fcf']},
            'positive_months': positive_months,
            'negative_months': negative_months,
            'trend': trend,
            'all_positive': negative_months == 0,
            'months_analyzed': len(projected_months)
        }
    
    def _calculate_reserves_after_distribution(self, balance_data: Dict, distribution_amount: float) -> float:
        """
        Calculate months of reserves remaining after distribution
        Handles case where monthly_debt_service is 0
        """
        current_reserves = balance_data.get('months_of_reserves', 0)
        cash_balance = balance_data.get('cash_balance', 0)
        monthly_debt_service = balance_data.get('monthly_debt_service', 0)
        current_liabilities = balance_data.get('current_liabilities', 0)
        
        # Calculate new cash balance after distribution
        new_cash_balance = cash_balance - distribution_amount
        
        # Recalculate reserves with new cash balance
        if monthly_debt_service > 0:
            monthly_needs = monthly_debt_service + (current_liabilities * 0.1)
        else:
            # If no debt service, use simplified calculation based on current liabilities
            monthly_needs = current_liabilities * 0.1 if current_liabilities > 0 else 42000  # fallback estimate
        
        if monthly_needs > 0:
            return new_cash_balance / monthly_needs
        else:
            return 999  # Very safe position
    
    def _calculate_months_of_reserves(self, cash_balance: float, monthly_debt_service: float, 
                                     current_liabilities: float) -> float:
        """Calculate how many months of operating expenses + debt service the cash covers"""
        if monthly_debt_service <= 0:
            return 999  # No debt service, very safe
        
        # Estimate monthly operating cash needs (debt service + portion of current liabilities)
        monthly_needs = monthly_debt_service + (current_liabilities * 0.1)  # Assume 10% of current liab per month
        
        if monthly_needs <= 0:
            return 999
        
        return cash_balance / monthly_needs
    
    def _make_decision(self, projected_fcf: float, current_fcf: float, cash_balance: float,
                      months_of_reserves: float, working_capital: float, noi_ytd_variance_pct: float,
                      seasonal_factor: Dict, enrollment_trend: str, multi_month_analysis: Dict = None,
                      monthly_debt_service: float = 0, current_liabilities: float = 0) -> Tuple[str, float, str]:
        """
        Make the primary decision: CONTRIBUTE, DISTRIBUTE, or DO_NOTHING
        Uses multi-month projection data when available for more robust analysis
        
        Returns:
            Tuple[decision, amount, confidence, contribution_breakdown]
        """
        
        # CRITICAL CHECK: Working capital crisis (current liabilities > current assets)
        # This indicates past-due obligations or structural cash flow problems
        if working_capital < -50000:
            # Severe working capital deficit - property is behind on payments
            # Calculate contribution with transparent breakdown:
            # 1. Multi-month projected deficits (not just one month)
            # 2. Working capital restoration (to get current ratio to 1.0)
            # 3. Operating reserve buffer (3-6 months)
            
            wc_deficit = abs(working_capital)
            monthly_deficit = abs(projected_fcf) if projected_fcf < 0 else 0
            
            # CRITICAL: If NOI is underperforming or there's persistent deficit, project forward
            # Don't just cover one month - cover until property stabilizes
            if projected_fcf < 0:
                # If property showing deficit, assume it continues for multiple months
                # Use 3 months as minimum forward projection period
                if noi_ytd_variance_pct < -5:
                    # Underperforming - use 6 months forward projection
                    months_forward = 6
                    forward_reason = "Property underperforming budget by >5%, projecting 6 months of deficits"
                elif abs(noi_ytd_variance_pct) < 5:
                    # On budget but still showing deficit - structural issue, use 4 months
                    months_forward = 4
                    forward_reason = "Property on budget but showing structural deficit, projecting 4 months"
                else:
                    # Outperforming but still deficit - likely seasonal, use 3 months
                    months_forward = 3
                    forward_reason = "Property outperforming but showing deficit, projecting 3 months minimum"
                
                projected_multi_month_deficit = monthly_deficit * months_forward
            else:
                # No deficit projected, but working capital crisis exists from past issues
                projected_multi_month_deficit = 0
                months_forward = 0
                forward_reason = "No projected deficit, but past working capital crisis requires restoration"
            
            # Operating reserve buffer: 3 months of debt service + monthly deficit
            monthly_operating_cost = abs(projected_fcf) if projected_fcf < 0 else (current_fcf if current_fcf > 0 else 50000)
            operating_reserve_buffer = monthly_operating_cost * 3
            
            # Need to cover: forward deficits + restore working capital + operating reserves
            contribution_breakdown = {
                'projected_deficit': monthly_deficit,
                'months_forward': months_forward,
                'forward_projected_deficit': projected_multi_month_deficit,
                'working_capital_restoration': wc_deficit,
                'operating_reserve_buffer': operating_reserve_buffer,
                'forward_reason': forward_reason,
                'total': projected_multi_month_deficit + wc_deficit + operating_reserve_buffer
            }
            
            return ('CONTRIBUTE', contribution_breakdown['total'], 'LOW', contribution_breakdown)
        
        # Decision Logic Tree
        
        # Case 1: Projected deficit
        if projected_fcf < 0:
            deficit_amount = abs(projected_fcf)
            
            # Minor deficit with strong reserves
            if deficit_amount < self.decision_thresholds['minor_deficit'] and \
               months_of_reserves > self.decision_thresholds['cash_reserve_months']:
                return ('DO_NOTHING', None, 'HIGH', None)
            
            # Moderate deficit with adequate reserves
            elif deficit_amount < self.decision_thresholds['moderate_deficit'] and \
                 months_of_reserves > 4:
                return ('DO_NOTHING', None, 'MEDIUM', None)
            
            # Major deficit or low reserves
            elif deficit_amount >= self.decision_thresholds['moderate_deficit'] or \
                 months_of_reserves < 3:
                # Check if seasonal - if summer deficit, may not need contribution
                if seasonal_factor.get('season') == 'Summer Session':
                    return ('DO_NOTHING', None, 'MEDIUM', None)
                else:
                    # Calculate contribution with transparent breakdown
                    contribution_breakdown = {
                        'projected_deficit': deficit_amount,
                        'safety_buffer': deficit_amount * 0.10,  # 10% buffer
                        'working_capital_restoration': 0,  # No WC crisis in this path
                        'total': deficit_amount * 1.1
                    }
                    return ('CONTRIBUTE', contribution_breakdown['total'], 'MEDIUM', contribution_breakdown)
            
            else:
                return ('DO_NOTHING', None, 'MEDIUM', None)
        
        # Case 2: Projected surplus
        else:
            surplus_amount = projected_fcf
            
            # NEW: Use multi-month analysis for better distribution decisions
            if multi_month_analysis:
                # Multi-month data available - use it for robust analysis
                avg_fcf = multi_month_analysis['average_fcf']
                all_positive = multi_month_analysis['all_positive']
                total_fcf = multi_month_analysis['total_fcf']
                lowest_month_fcf = multi_month_analysis['lowest_month']['fcf']
                months_analyzed = multi_month_analysis['months_analyzed']
                
                # Recommend distribution if:
                # 1. ALL projected months are positive
                # 2. Average FCF > $100k
                # 3. Even lowest month is positive
                # 4. Reserves are strong (>10 months currently)
                
                if all_positive and avg_fcf > self.decision_thresholds['distribution_min'] and \
                   lowest_month_fcf > 0 and months_of_reserves > 10:
                    
                    # Calculate safe distribution:
                    # Keep enough cash to maintain minimum 6 months of reserves AFTER distribution
                    
                    # Calculate monthly operating needs
                    if monthly_debt_service > 0:
                        monthly_operating_needs = monthly_debt_service + (current_liabilities * 0.1)
                    elif current_liabilities > 0:
                        monthly_operating_needs = current_liabilities * 0.1
                    else:
                        monthly_operating_needs = 50000  # Default estimate
                    
                    # Required reserve: keep 6 months minimum
                    required_reserve = monthly_operating_needs * 6
                    
                    # Maximum safe distribution: current cash - required reserves
                    max_safe_distribution = cash_balance - required_reserve
                    
                    # Conservative recommendation: lesser of
                    # - 50% of projected 6-month FCF (more conservative than 70%)
                    # - Available cash after maintaining 6-month reserve
                    safe_distribution = min(total_fcf * 0.5, max_safe_distribution)
                    
                    # Verify reserves will be adequate after distribution
                    balance_data_dict = {
                        'months_of_reserves': months_of_reserves,
                        'cash_balance': cash_balance,
                        'monthly_debt_service': monthly_debt_service,
                        'current_liabilities': current_liabilities
                    }
                    reserves_after = self._calculate_reserves_after_distribution(balance_data_dict, safe_distribution)
                    
                    if safe_distribution > 50000 and reserves_after >= 6:
                        return ('DISTRIBUTE', safe_distribution, 'HIGH', None)
                    else:
                        return ('DO_NOTHING', None, 'MEDIUM', None)
                
                # If NOT all positive months, or lowest month concerning, hold cash
                elif not all_positive or lowest_month_fcf < 0:
                    return ('DO_NOTHING', None, 'MEDIUM', None)
                
                # If avg FCF positive but low, wait longer
                elif avg_fcf < self.decision_thresholds['distribution_min']:
                    return ('DO_NOTHING', None, 'MEDIUM', None)
                
                else:
                    return ('DO_NOTHING', None, 'MEDIUM', None)
            
            else:
                # FALLBACK: Single-month analysis (backward compatible)
                # Only recommend distribution if surplus is substantial and reserves are strong
                if surplus_amount > self.decision_thresholds['distribution_min'] and \
                   months_of_reserves > self.decision_thresholds['cash_reserve_months'] * 1.5 and \
                   noi_ytd_variance_pct > 0:  # Performing above budget
                    
                    # Calculate safe distribution amount (leave 6 months reserves)
                    safe_distribution = min(
                        surplus_amount,
                        working_capital - (self.decision_thresholds['cash_reserve_months'] * 
                                          (cash_balance / months_of_reserves))
                    )
                    
                    if safe_distribution > 50000:
                        return ('DISTRIBUTE', safe_distribution, 'HIGH', None)
                
                # Default: do nothing
                return ('DO_NOTHING', None, 'MEDIUM', None)
    
    def _generate_executive_summary(self, decision: str, amount: float, projected_fcf: float,
                                   cash_balance: float, months_of_reserves: float,
                                   noi_ytd_variance_pct: float, noi_month_variance_pct: float,
                                   expenses_ytd_variance_pct: float, seasonal_factor: Dict,
                                   enrollment_trend: str, working_capital: float = 0,
                                   current_liabilities: float = 0, 
                                   contribution_breakdown: Dict = None) -> List[str]:
        """Generate 5-7 executive summary bullet points supporting the decision"""
        
        bullets = []
        
        # PRIORITY BULLET: Working capital crisis warning
        if working_capital < -50000:
            current_ratio = (cash_balance + 0) / max(current_liabilities, 1)  # Simplified: cash only as current assets
            bullets.append(f"⚠️ **WORKING CAPITAL CRISIS**: Current liabilities (${current_liabilities:,.0f}) exceed current assets by ${abs(working_capital):,.0f}. Current ratio of {current_ratio:.2f}:1 indicates significant past-due obligations or structural cash flow problems. **FULL LIABILITY BREAKDOWN ANALYSIS REQUIRED BEFORE ANY CAPITAL DECISION**")
        
        # Bullet 1: The decision
        if decision == 'CONTRIBUTE':
            if contribution_breakdown:
                # Show transparent breakdown of contribution calculation
                deficit = contribution_breakdown.get('projected_deficit', 0)
                months_forward = contribution_breakdown.get('months_forward', 0)
                forward_deficit = contribution_breakdown.get('forward_projected_deficit', 0)
                wc_restore = contribution_breakdown.get('working_capital_restoration', 0)
                reserve_buffer = contribution_breakdown.get('operating_reserve_buffer', 0)
                forward_reason = contribution_breakdown.get('forward_reason', '')
                
                # Build detailed breakdown
                breakdown_parts = []
                if months_forward > 0:
                    breakdown_parts.append(f"{months_forward}-Month Projected Deficits: ${forward_deficit:,.0f}")
                elif deficit > 0:
                    breakdown_parts.append(f"1-Month Deficit: ${deficit:,.0f}")
                
                if wc_restore > 0:
                    breakdown_parts.append(f"Working Capital Restoration: ${wc_restore:,.0f}")
                
                if reserve_buffer > 0:
                    breakdown_parts.append(f"Operating Reserve Buffer (3mo): ${reserve_buffer:,.0f}")
                
                breakdown_text = " + ".join(breakdown_parts) + f" = **${amount:,.0f}**"
                
                if working_capital < -50000:
                    if months_forward > 0:
                        bullets.append(f"**FORWARD-LOOKING CONTRIBUTION REQUIRED: ${amount:,.0f}** ({breakdown_text}). Rationale: {forward_reason}. This covers immediate crisis plus forward exposure until property stabilizes.")
                    else:
                        bullets.append(f"**PRELIMINARY ESTIMATE: ${amount:,.0f} contribution MAY BE NEEDED** ({breakdown_text}) - However, actual requirement depends on liability breakdown and root cause analysis")
                else:
                    bullets.append(f"**RECOMMENDATION: CONTRIBUTE ${amount:,.0f}** to cover shortfall and maintain reserves. Breakdown: {breakdown_text}")
            else:
                # Fallback if no breakdown available
                if working_capital < -50000:
                    bullets.append(f"**PRELIMINARY ESTIMATE: ${amount:,.0f} contribution MAY BE NEEDED** - However, this is based on incomplete analysis. Actual requirement depends on liability breakdown and root cause of working capital deficit")
                else:
                    bullets.append(f"**RECOMMENDATION: CONTRIBUTE ${amount:,.0f}** to cover projected cash shortfall and maintain adequate reserves")
        elif decision == 'DISTRIBUTE':
            bullets.append(f"**RECOMMENDATION: DISTRIBUTE ${amount:,.0f}** to partners based on strong performance and excess cash position")
        else:
            bullets.append(f"**RECOMMENDATION: NO ACTION REQUIRED** - Property cash position is stable and reserves are adequate")
        
        # Bullet 2: Projected cash flow
        if projected_fcf < 0:
            season = seasonal_factor.get('season', 'this period')
            if season == 'Summer Session':
                season_text = 'expected seasonal pattern'
            elif season == 'Unknown':
                season_text = 'requiring attention'
            else:
                season_text = f'unusual for {season}'
            bullets.append(f"Projected Free Cash Flow shows deficit of ${abs(projected_fcf):,.0f} for upcoming month, which is {season_text}")
        else:
            bullets.append(f"Projected Free Cash Flow shows surplus of ${projected_fcf:,.0f}, reflecting strong operational performance")
        
        # Bullet 3: Liquidity position
        reserve_status = "strong" if months_of_reserves > 10 else "adequate" if months_of_reserves > 6 else "tight"
        bullets.append(f"Cash reserves of ${cash_balance:,.0f} provide {months_of_reserves:.1f} months of coverage - {reserve_status} liquidity position")
        
        # Bullet 4: Operating performance (NOI)
        # Variance % = (actual - budget) / budget * 100
        # Positive variance = actual > budget = GOOD
        # Negative variance = actual < budget = BAD
        if abs(noi_ytd_variance_pct) < 5:
            bullets.append(f"Net Operating Income tracking within 5% of budget YTD ({noi_ytd_variance_pct:+.1f}%), indicating reliable budget assumptions")
        elif noi_ytd_variance_pct > 5:
            bullets.append(f"Net Operating Income exceeding budget by {noi_ytd_variance_pct:.1f}% YTD, demonstrating strong property performance")
        else:  # noi_ytd_variance_pct < -5
            bullets.append(f"Net Operating Income underperforming budget by {abs(noi_ytd_variance_pct):.1f}% YTD, with recent month at {noi_month_variance_pct:+.1f}% - monitor trend closely")
        
        # Bullet 5: Expense management
        # For expenses: negative variance = under budget = GOOD (spending less)
        # Positive variance = over budget = BAD (spending more)
        if expenses_ytd_variance_pct < -5:
            bullets.append(f"Operating expenses running {abs(expenses_ytd_variance_pct):.1f}% under budget YTD, contributing to favorable cash position")
        elif expenses_ytd_variance_pct > 5:
            bullets.append(f"Operating expenses {expenses_ytd_variance_pct:.1f}% over budget YTD - expense control measures recommended")
        else:
            bullets.append(f"Operating expenses tracking close to budget ({expenses_ytd_variance_pct:+.1f}% YTD)")
        
        # Bullet 6: Market/seasonal context
        season_desc = seasonal_factor.get('season', 'Current period')
        expected_occ = seasonal_factor.get('expected_occupancy', 'Normal')
        
        # Clean up "Unable to determine" and "Unknown" values
        if expected_occ in ['Unable to determine', 'Unknown']:
            expected_occ = 'typical'
        if season_desc == 'Unknown':
            season_desc = 'Current period'
            
        if enrollment_trend == 'growing':
            bullets.append(f"Market fundamentals are favorable: {season_desc} with {expected_occ} occupancy expected, supported by growing university enrollment")
        elif enrollment_trend == 'declining':
            bullets.append(f"Market headwinds present: {season_desc} period with enrollment declining - conservative cash management warranted")
        else:
            bullets.append(f"Seasonal context: {season_desc} with {expected_occ} occupancy expected under normal market conditions")
        
        # Bullet 7: Risk/opportunity note (conditional)
        if decision == 'CONTRIBUTE':
            bullets.append("Risk mitigation: Capital contribution ensures property can meet all obligations without stress on operations")
        elif decision == 'DISTRIBUTE':
            bullets.append("Distribution opportunity: Excess cash can be returned to partners while maintaining prudent reserve levels")
        elif months_of_reserves < 6:
            bullets.append("Monitor closely: While no immediate action needed, reserves are below optimal level - avoid distributions until reserves improve")
        elif projected_fcf < 0 and seasonal_factor.get('season') != 'Summer Session':
            bullets.append("Investigation recommended: Deficit during peak season may indicate budget assumption errors or one-time expenses requiring review")
        
        return bullets[:7]  # Return maximum 7 bullets
    
    def _generate_detailed_rationale(self, cash_forecast_data: Dict, income_statement_data: Dict,
                                    balance_sheet_data: Dict, economic_analysis: Dict,
                                    decision: str, amount: float, months_of_reserves: float,
                                    occupancy_adjustment_note: str = None) -> Dict:
        """Generate detailed multi-page analysis"""
        
        return {
            'cash_forecast_analysis': self._format_cash_forecast_details(cash_forecast_data),
            'income_statement_analysis': self._format_income_statement_details(income_statement_data),
            'balance_sheet_analysis': self._format_balance_sheet_details(balance_sheet_data, months_of_reserves),
            'economic_context': self._format_economic_context(economic_analysis),
            'risk_assessment': self._generate_risk_assessment(
                cash_forecast_data, income_statement_data, balance_sheet_data, economic_analysis
            ),
            'decision_rationale': self._format_decision_rationale(
                decision, amount, cash_forecast_data, income_statement_data, 
                balance_sheet_data, economic_analysis
            )
        }
    
    def _format_cash_forecast_details(self, data: Dict) -> str:
        """Format cash forecast section"""
        
        base_analysis = f"""
CASH FORECAST ANALYSIS
{'='*80}

Property: {data.get('property_name', 'Unknown')}
Current Month: {data.get('current_month', 'Unknown')} (Actual)
Projected Month: {data.get('projected_month', 'Unknown')} (Budget)

Current Month Free Cash Flow: ${data.get('current_fcf', 0):,.2f}
Projected Month Free Cash Flow: ${data.get('projected_fcf', 0):,.2f}
Variance: ${data.get('projected_fcf', 0) - data.get('current_fcf', 0):,.2f}

Occupancy:
  Current Actual: {data.get('current_occupancy', 0):.1f}%
  Projected Budget: {data.get('projected_occupancy', 0):.1f}%

Actual Distributions/Contributions in {data.get('current_month', 'Current Month')}: ${data.get('current_distributions', 0):,.2f}
"""
        
        # Add 6-month projection if available
        projected_months = data.get('projected_months', [])
        if projected_months:
            total_fcf = sum(m['fcf'] for m in projected_months)
            avg_fcf = total_fcf / len(projected_months)
            lowest_month = min(projected_months, key=lambda x: x['fcf'])
            highest_month = max(projected_months, key=lambda x: x['fcf'])
            negative_months = [m for m in projected_months if m['fcf'] < 0]
            
            projection_section = f"""
{'='*80}
6-MONTH CASH FLOW PROJECTION
{'='*80}

Analyzing next {len(projected_months)} months of projections:
"""
            for i, month in enumerate(projected_months, 1):
                status_icon = "✓" if month['fcf'] > 0 else "✗"
                projection_section += f"  {i}. {month['month']:<15} FCF: ${month['fcf']:>12,.2f}  Occ: {month['occupancy']:>5.1f}%  {status_icon}\n"
            
            projection_section += f"""
Summary Statistics:
  Total Projected FCF (6 months): ${total_fcf:,.2f}
  Average Monthly FCF:            ${avg_fcf:,.2f}
  Highest Month:                  {highest_month['month']} (${highest_month['fcf']:,.2f})
  Lowest Month:                   {lowest_month['month']} (${lowest_month['fcf']:,.2f})
  Positive Months:                {len([m for m in projected_months if m['fcf'] > 0])} of {len(projected_months)}
  Negative Months:                {len(negative_months)}
"""
            if negative_months:
                projection_section += f"  ⚠️  Warning: {len(negative_months)} month(s) show negative cash flow\n"
            
            base_analysis += projection_section
        
        base_analysis += f"""
INTERPRETATION:
{self._interpret_cash_forecast(data)}
"""
        return base_analysis
    
    def _format_income_statement_details(self, data: Dict) -> str:
        """Format income statement section"""
        # Extract reporting period (with fallback to hardcoded values)
        reporting_month = data.get('reporting_month', 'September 2025')
        ytd_period = data.get('ytd_period', 'Jan-Sep')
        year = reporting_month.split()[-1] if reporting_month != 'Unknown' else '2025'
        
        return f"""
INCOME STATEMENT ANALYSIS
{'='*80}

{reporting_month} Performance (Month):
  Total Operating Income:  ${data.get('income_month_actual', 0):,.2f} vs ${data.get('income_month_budget', 0):,.2f} budget ({data.get('income_month_variance_pct', 0):+.2f}%)
  Total Operating Expenses: ${data.get('expenses_month_actual', 0):,.2f} vs ${data.get('expenses_month_budget', 0):,.2f} budget ({data.get('expenses_month_variance_pct', 0):+.2f}%)
  Net Operating Income:     ${data.get('noi_month_actual', 0):,.2f} vs ${data.get('noi_month_budget', 0):,.2f} budget ({data.get('noi_month_variance_pct', 0):+.2f}%)

Year-to-Date {year} Performance ({ytd_period}):
  Total Operating Income:  ${data.get('income_ytd_actual', 0):,.2f} vs ${data.get('income_ytd_budget', 0):,.2f} budget ({data.get('income_ytd_variance_pct', 0):+.2f}%)
  Total Operating Expenses: ${data.get('expenses_ytd_actual', 0):,.2f} vs ${data.get('expenses_ytd_budget', 0):,.2f} budget ({data.get('expenses_ytd_variance_pct', 0):+.2f}%)
  Net Operating Income:     ${data.get('noi_ytd_actual', 0):,.2f} vs ${data.get('noi_ytd_budget', 0):,.2f} budget ({data.get('noi_ytd_variance_pct', 0):+.2f}%)

INTERPRETATION:
{self._interpret_income_statement(data)}
"""
    
    def _format_balance_sheet_details(self, data: Dict, months_of_reserves: float) -> str:
        """Format balance sheet section"""
        # Extract reporting month from data (with fallback)
        reporting_month = data.get('reporting_month', 'September 2025')
        
        # Calculate prior month for comparison
        month_year = reporting_month.split()
        if len(month_year) == 2:
            current_month_name = month_year[0]
            year = month_year[1]
            
            # Get prior month name
            months = ['January', 'February', 'March', 'April', 'May', 'June',
                     'July', 'August', 'September', 'October', 'November', 'December']
            try:
                current_idx = months.index(current_month_name)
                prior_month_name = months[current_idx - 1] if current_idx > 0 else 'December'
                prior_year = year if current_idx > 0 else str(int(year) - 1)
                prior_month = f"{prior_month_name} {prior_year}"
            except ValueError:
                prior_month = "Prior Month"
        else:
            current_month_name = reporting_month
            prior_month = "Prior Month"
        
        return f"""
BALANCE SHEET ANALYSIS
{'='*80}

Liquidity Position ({reporting_month}):
  Cash and Cash Equivalents: ${data.get('cash_balance', 0):,.2f}
  Accounts Receivable:       ${data.get('accounts_receivable', 0):,.2f}
  Total Current Assets:      ${data.get('cash_balance', 0) + data.get('accounts_receivable', 0):,.2f}
  
  Current Liabilities:       ${data.get('current_liabilities', 0):,.2f}
  Working Capital:           ${data.get('cash_balance', 0) - data.get('current_liabilities', 0):,.2f}
  Current Ratio:             {(data.get('cash_balance', 0) + data.get('accounts_receivable', 0)) / max(data.get('current_liabilities', 1), 1):.2f}:1

Debt Position:
  Total Notes Payable:       ${data.get('total_debt', 0):,.2f}
  Monthly Principal Payment: ${data.get('monthly_principal', 0):,.2f}
  Accrued Interest:          ${data.get('accrued_interest', 0):,.2f}
  Est. Monthly Debt Service: ${data.get('monthly_debt_service', 0):,.2f}

Reserve Analysis:
  Months of Reserves:        {months_of_reserves:.1f} months
  Assessment:                {"STRONG (>10 months)" if months_of_reserves > 10 else "ADEQUATE (6-10 months)" if months_of_reserves > 6 else "TIGHT (<6 months)"}

Month-over-Month Cash Change:
  {prior_month} Cash:          ${data.get('cash_prior_month', 0):,.2f}
  {reporting_month} Cash:       ${data.get('cash_balance', 0):,.2f}
  Change:                    ${data.get('cash_balance', 0) - data.get('cash_prior_month', 0):,.2f} ({((data.get('cash_balance', 0) - data.get('cash_prior_month', 0)) / max(data.get('cash_prior_month', 1), 1) * 100):+.1f}%)

INTERPRETATION:
{self._interpret_balance_sheet(data, months_of_reserves)}
"""
    
    def _format_economic_context(self, data: Dict) -> str:
        """Format economic analysis section"""
        analysis_text = data.get('full_analysis', 'Economic analysis not available')
        
        return f"""
ECONOMIC & MARKET CONTEXT
{'='*80}

{analysis_text}
"""
    
    def _generate_risk_assessment(self, cash_data: Dict, income_data: Dict, 
                                  balance_data: Dict, econ_data: Dict) -> str:
        """Generate risk assessment section"""
        risks = []
        
        # Cash flow risks
        if cash_data.get('projected_fcf', 0) < 0:
            risks.append("• Projected cash flow deficit may require liquidity support if trend continues")
        
        # Performance risks
        if income_data.get('noi_month_variance_pct', 0) < -10:
            risks.append("• Recent monthly NOI significantly below budget - investigate root causes")
        
        # Expense variance: positive = over budget (BAD), negative = under budget (GOOD)
        if income_data.get('expenses_ytd_variance_pct', 0) > 10:
            risks.append("• Operating expenses significantly over budget - expense control measures needed")
        
        # Liquidity risks
        months_reserves = balance_data.get('months_of_reserves', 999)
        if months_reserves < 6:
            risks.append("• Reserve levels below recommended 6-month minimum - limits financial flexibility")
        
        # Market risks
        if econ_data.get('enrollment_trend') == 'declining':
            risks.append("• University enrollment declining - may pressure occupancy and rental rates")
        
        if econ_data.get('new_supply', False):
            risks.append("• New competing properties entering market - may require pricing/concession strategies")
        
        if not risks:
            risks.append("• No material risks identified - property showing stable performance")
        
        return f"""
RISK ASSESSMENT
{'='*80}

Key Risks Identified:

{chr(10).join(risks)}

Risk Mitigation Strategies:
• Maintain minimum 6 months operating reserves in cash
• Monitor monthly performance trends for early warning signs
• Review budget assumptions quarterly and adjust projections
• Maintain competitive market position through property improvements and resident services
• Ensure adequate insurance coverage and contingency planning
"""
    
    def _format_decision_rationale(self, decision: str, amount: float, 
                                  cash_data: Dict, income_data: Dict,
                                  balance_data: Dict, econ_data: Dict) -> str:
        """Format the final decision rationale"""
        
        if decision == 'CONTRIBUTE':
            return f"""
DECISION RATIONALE: CAPITAL CONTRIBUTION REQUIRED
{'='*80}

Recommended Contribution Amount: ${amount:,.2f}

This recommendation is based on the following factors:

1. PROJECTED CASH SHORTFALL
   - The property is projected to have negative free cash flow in the upcoming month
   - Without additional capital, the property may need to draw on reserves
   - The contribution amount includes a buffer to ensure smooth operations

2. RESERVE LEVELS
   - Current reserves may be insufficient to comfortably absorb the projected deficit
   - Maintaining adequate liquidity is essential for operational stability
   - Capital contribution prevents depletion of cash reserves below prudent levels

3. MARKET CONDITIONS
   - {self._get_market_condition_text(econ_data)}

4. ALTERNATIVE CONSIDERATIONS
   - Could defer non-essential expenditures to preserve cash
   - Could draw on existing reserves if shortfall is truly temporary
   - Could arrange short-term credit facility instead of equity contribution

RECOMMENDED ACTION:
Wire ${amount:,.2f} to property operating account within 10 business days to ensure
adequate cash is available for upcoming month obligations.
"""
        
        elif decision == 'DISTRIBUTE':
            return f"""
DECISION RATIONALE: CASH DISTRIBUTION RECOMMENDED
{'='*80}

Recommended Distribution Amount: ${amount:,.2f}

This recommendation is based on the following factors:

1. STRONG CASH POSITION
   - Property has generated surplus cash flow beyond operational needs
   - Current reserves exceed recommended minimum by comfortable margin
   - Distribution will not impair financial flexibility or operational capability

2. OPERATING PERFORMANCE
   - Net Operating Income {income_data.get('noi_ytd_variance_pct', 0):+.1f}% vs budget demonstrates strong performance
   - Expense management effective with costs tracking to budget
   - Revenue performance supports sustainable cash generation

3. RESERVE ADEQUACY POST-DISTRIBUTION
   - After distribution, reserves will remain at {self._calculate_reserves_after_distribution(balance_data, amount):.1f} months
   - This {'exceeds' if self._calculate_reserves_after_distribution(balance_data, amount) >= 6 else 'maintains'} the 6-month minimum reserve requirement
   - Property retains adequate cushion for unexpected expenses or market changes

4. MARKET CONDITIONS
   - {self._get_market_condition_text(econ_data)}

RECOMMENDED ACTION:
Process distribution of ${amount:,.2f} to partners according to ownership percentages.
Maintain minimum ${balance_data.get('cash_balance', 0) - amount:,.2f} in operating account post-distribution.
"""
        
        else:  # DO_NOTHING
            return f"""
DECISION RATIONALE: NO ACTION REQUIRED
{'='*80}

No capital contribution or distribution is recommended at this time.

This recommendation is based on the following factors:

1. STABLE CASH POSITION
   - {'Projected deficit is minor and well within reserve capacity' if cash_data.get('projected_fcf', 0) < 0 else 'Projected cash flow is positive but not sufficient to warrant distribution'}
   - Current reserves of ${balance_data.get('cash_balance', 0):,.2f} provide {balance_data.get('months_of_reserves', 0):.1f} months of coverage
   - No immediate liquidity concerns

2. OPERATIONAL PERFORMANCE
   - Property operating within expected parameters
   - {'Any variances from budget are not material to cash position' if abs(income_data.get('noi_ytd_variance_pct', 0)) < 10 else 'Performance variances warrant monitoring but not immediate action'}

3. PRUDENT CASH MANAGEMENT
   - Maintaining current reserve levels provides financial flexibility
   - Cushion available for unexpected expenses or market changes
   - Position allows property to handle normal business fluctuations

4. MARKET CONDITIONS
   - {self._get_market_condition_text(econ_data)}

RECOMMENDED ACTION:
Continue normal operations. Monitor monthly performance and reassess cash position next month.
{'Consider distribution if surplus pattern continues for 2-3 months.' if cash_data.get('projected_fcf', 0) > 50000 else ''}
{'Review budget assumptions if deficit pattern emerges.' if cash_data.get('projected_fcf', 0) < 0 else ''}
"""
    
    def _get_market_condition_text(self, econ_data: Dict) -> str:
        """Get market condition summary text"""
        if econ_data.get('enrollment_trend') == 'growing':
            return "University enrollment growing and market fundamentals are favorable"
        elif econ_data.get('enrollment_trend') == 'declining':
            return "University enrollment declining - conservative cash management prudent"
        else:
            return "Market conditions stable with normal seasonal patterns expected"
    
    def _interpret_cash_forecast(self, data: Dict) -> str:
        """Interpret cash forecast data"""
        projected_fcf = data.get('projected_fcf', 0)
        current_fcf = data.get('current_fcf', 0)
        
        if projected_fcf < 0:
            return f"The projected month shows a cash deficit of ${abs(projected_fcf):,.2f}. This represents a significant variance from the current month's positive cash flow of ${current_fcf:,.2f}. The deficit may be due to seasonal factors, one-time expenses, debt service, or distributions planned for the month."
        else:
            return f"The projected month shows positive free cash flow of ${projected_fcf:,.2f}, consistent with the current month's performance of ${current_fcf:,.2f}. This indicates stable cash generation capability."
    
    def _interpret_income_statement(self, data: Dict) -> str:
        """Interpret income statement data
        
        Variance % = (actual - budget) / budget * 100
        Positive = actual > budget (GOOD for revenue/NOI, BAD for expenses)
        Negative = actual < budget (BAD for revenue/NOI, GOOD for expenses)
        """
        noi_ytd_var = data.get('noi_ytd_variance_pct', 0)
        noi_month_var = data.get('noi_month_variance_pct', 0)
        
        if abs(noi_ytd_var) < 5 and abs(noi_month_var) < 5:
            return "Operating performance is tracking close to budget both YTD and for the recent month, indicating reliable budget assumptions and stable operations."
        elif noi_ytd_var > 5:
            return f"Property is outperforming budget with NOI {noi_ytd_var:+.1f}% above plan YTD. Recent month showed {noi_month_var:+.1f}% variance, {'continuing strong performance' if noi_month_var > 0 else 'with some recent softness to monitor'}."
        elif noi_ytd_var < -5:
            return f"Property is underperforming budget with NOI at {noi_ytd_var:.1f}% of plan YTD. Recent month at {noi_month_var:+.1f}% indicates {'improvement trend' if noi_month_var > noi_ytd_var else 'continued weakness'}. Review revenue and expense drivers."
        else:
            # Between -5 and +5 but monthly variance is significant
            return f"Operating performance tracking close to budget YTD ({noi_ytd_var:+.1f}%), though recent month shows {noi_month_var:+.1f}% variance requiring attention."
    
    def _interpret_balance_sheet(self, data: Dict, months_of_reserves: float) -> str:
        """Interpret balance sheet data"""
        if months_of_reserves > 10:
            return f"Liquidity position is very strong with {months_of_reserves:.1f} months of reserves. The property has ample cushion to absorb unexpected expenses or temporary cash flow disruptions. Current ratio of {(data.get('cash_balance', 0) + data.get('accounts_receivable', 0)) / max(data.get('current_liabilities', 1), 1):.2f}:1 exceeds recommended minimum of 1.5:1."
        elif months_of_reserves > 6:
            return f"Liquidity position is adequate with {months_of_reserves:.1f} months of reserves. The property can handle normal business fluctuations and minor unexpected expenses. Maintain current reserve levels."
        else:
            return f"Liquidity position is tight with only {months_of_reserves:.1f} months of reserves. Property has limited cushion for unexpected expenses. Avoid distributions and build reserves through retained cash flow."


if __name__ == "__main__":
    # Test the recommendation engine with sample data
    print("Testing Recommendation Engine...\n")
    
    engine = RecommendationEngine()
    
    # Sample data from Rittenhouse Station analysis
    cash_forecast = {
        'property_name': 'Rittenhouse Station',
        'current_month': 'September 2025',
        'projected_month': 'October 2025',
        'current_fcf': 633531.05,
        'projected_fcf': -18202.58,
        'current_occupancy': 94.5,
        'projected_occupancy': 93.0,
        'current_distributions': 0
    }
    
    income_statement = {
        'noi_month_actual': 245061.10,
        'noi_month_budget': 268135.01,
        'noi_month_variance_pct': -8.61,
        'noi_ytd_actual': 2160069.99,
        'noi_ytd_budget': 2092353.37,
        'noi_ytd_variance_pct': 3.24,
        'income_month_actual': 425818.20,
        'income_month_budget': 449702.12,
        'income_month_variance_pct': -5.31,
        'income_ytd_actual': 3646924.30,
        'income_ytd_budget': 3668413.75,
        'income_ytd_variance_pct': -0.59,
        'expenses_month_actual': 180757.10,
        'expenses_month_budget': 181567.11,
        'expenses_month_variance_pct': 0.45,
        'expenses_ytd_actual': 1486854.31,
        'expenses_ytd_budget': 1576060.38,
        'expenses_ytd_variance_pct': 5.66
    }
    
    balance_sheet = {
        'cash_balance': 1465132.44,
        'cash_prior_month': 1604829.88,
        'accounts_receivable': 18243.51,
        'current_liabilities': 521864.86,
        'total_debt': 23014395.23,
        'monthly_principal': 57072.78,
        'accrued_interest': 115698.30,
        'monthly_debt_service': 62635.89,
        'months_of_reserves': 17.2
    }
    
    economic_analysis = {
        'seasonal_factor': {
            'season': 'Fall Semester',
            'expected_occupancy': 'High (90-95%)',
            'cash_flow_pattern': 'Strong - peak leasing season'
        },
        'enrollment_trend': 'growing',
        'new_supply': True,
        'full_analysis': 'University of Cincinnati enrollment growing at 1.5% annually. Strong market fundamentals with 95% average occupancy. New supply of 500-700 beds coming online.'
    }
    
    result = engine.analyze_and_recommend(
        cash_forecast_data=cash_forecast,
        income_statement_data=income_statement,
        balance_sheet_data=balance_sheet,
        economic_analysis=economic_analysis
    )
    
    # Display results
    print("="*100)
    print(f"CASH FORECAST RECOMMENDATION - {result['property_name']}")
    print(f"{result['analysis_month']} → {result['projected_month']}")
    print("="*100)
    print()
    
    print(f"DECISION: {result['decision']}")
    if result['amount']:
        print(f"AMOUNT: ${result['amount']:,.2f}")
    print(f"CONFIDENCE: {result['confidence']}")
    print()
    
    print("EXECUTIVE SUMMARY")
    print("-"*100)
    for bullet in result['executive_summary']:
        print(f"  {bullet}")
    print()
    
    print("\nDETAILED RATIONALE")
    print("="*100)
    print(result['detailed_rationale']['decision_rationale'])
