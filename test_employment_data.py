"""
Test Employment & Economic Data from Enhanced Web Search
Shows what employment metrics we're getting with the improved prompt
"""
import os
from dotenv import load_dotenv
from services.economic_analysis import EconomicAnalyzer

# Load environment variables
load_dotenv()

def test_employment_data():
    """Test the enhanced employment data collection"""
    
    print("=" * 80)
    print("Testing Enhanced Employment & Economic Data Collection")
    print("=" * 80)
    
    # Initialize analyzer
    analyzer = EconomicAnalyzer()
    
    # Test property details
    property_name = "Campus Creek Cottages"
    university = "University of Cincinnati"
    city = "Cincinnati"
    state = "OH"
    zip_code = "45221"
    current_month = "March 2026"
    
    print(f"\nProperty: {property_name}")
    print(f"University: {university}")
    print(f"Location: {city}, {state}")
    print(f"Model: {analyzer.model}")
    print(f"IPEDS Enabled: {analyzer.ipeds.enabled}")
    
    print("\n" + "=" * 80)
    print("Calling Economic Analysis with Enhanced Employment Prompt")
    print("=" * 80)
    print("\nLooking for:")
    print("  ✓ Current unemployment rate")
    print("  ✓ Job growth trends")
    print("  ✓ Major employers")
    print("  ✓ Student employment opportunities")
    print("  ✓ Cost of living trends")
    print("  ✓ Economic outlook")
    print("\n" + "=" * 80)
    
    # Run analysis
    result = analyzer.analyze_property_context(
        property_name=property_name,
        university=university,
        city=city,
        state=state,
        zip_code=zip_code,
        current_month=current_month
    )
    
    # Display results
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)
    
    if result['success']:
        print(f"\n✓ Analysis completed successfully")
        print(f"  Tokens used: {result['tokens_used']:,}")
        
        analysis = result['analysis']
        
        # Extract employment section
        print("\n" + "=" * 80)
        print("EMPLOYMENT & ECONOMIC DATA SECTION")
        print("=" * 80)
        
        # Find the employment section
        if "LOCAL EMPLOYMENT" in analysis or "ECONOMIC CONDITIONS" in analysis:
            # Extract employment section
            start_markers = ["3. LOCAL EMPLOYMENT", "3. EMPLOYMENT", "LOCAL EMPLOYMENT"]
            end_markers = ["4. STUDENT HOUSING", "4. HOUSING MARKET"]
            
            employment_section = ""
            for start in start_markers:
                if start in analysis:
                    start_idx = analysis.find(start)
                    for end in end_markers:
                        if end in analysis[start_idx:]:
                            end_idx = start_idx + analysis[start_idx:].find(end)
                            employment_section = analysis[start_idx:end_idx]
                            break
                    if employment_section:
                        break
            
            if employment_section:
                print(employment_section)
            else:
                print("Employment section not found in expected format")
                print("\nShowing first 1500 characters of full analysis:")
                print(analysis[:1500])
        else:
            print("Employment section not clearly marked")
            print("\nShowing full analysis:")
            print(analysis)
        
        print("\n" + "=" * 80)
        print("✓ Test completed successfully!")
        print("=" * 80)
        
        # Check for key metrics
        print("\nData Quality Check:")
        metrics_found = []
        
        if "unemployment" in analysis.lower():
            metrics_found.append("✓ Unemployment rate")
        if "job growth" in analysis.lower() or "employment growth" in analysis.lower():
            metrics_found.append("✓ Job growth")
        if "major employer" in analysis.lower() or "top employer" in analysis.lower():
            metrics_found.append("✓ Major employers")
        if "student employment" in analysis.lower() or "part-time" in analysis.lower():
            metrics_found.append("✓ Student employment")
        if "cost of living" in analysis.lower():
            metrics_found.append("✓ Cost of living")
        
        if metrics_found:
            print("\nMetrics found in analysis:")
            for metric in metrics_found:
                print(f"  {metric}")
        else:
            print("\n⚠️  Warning: Expected employment metrics not clearly identified")
        
    else:
        print(f"\n✗ Analysis failed: {result.get('error', 'Unknown error')}")
    
    return result

if __name__ == "__main__":
    test_employment_data()
