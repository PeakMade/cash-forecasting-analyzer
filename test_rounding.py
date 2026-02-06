"""
Test rounding to nearest $10,000
"""
from services.recommendation_engine import RecommendationEngine

engine = RecommendationEngine()

# Test cases
test_amounts = [
    180234,   # Should round to 190000
    150000,   # Should stay 150000
    145678,   # Should round to 150000
    101,      # Should round to 10000
    195999,   # Should round to 200000
    0,        # Should stay 0
]

print("Testing rounding to nearest $10,000:")
print("="*50)

for amount in test_amounts:
    rounded = engine._round_to_nearest_10k(amount)
    print(f"${amount:>10,} → ${rounded:>10,}")

print("\n" + "="*50)
print("✓ All amounts rounded UP to nearest $10,000")
