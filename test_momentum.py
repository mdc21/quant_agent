import sys
import logging
from core.data.momentum_calculator import MomentumCalculator

logging.basicConfig(level=logging.INFO)

def main():
    print("Testing MomentumCalculator with HistoricalProvider...")
    # Test with a few symbols, some that exist in DB (e.g. RELIANCE) and some that might not
    symbols = ["RELIANCE", "TCS", "INFY", "FAKE_TICKER"]
    
    mc = MomentumCalculator(lookback_days=252, skip_days=21)
    scores = mc.compute_momentum_scores(symbols)
    
    print("\n--- Final Scores ---")
    for sym, score in scores.items():
        print(f"{sym}: {score:.2f}")

if __name__ == "__main__":
    main()
