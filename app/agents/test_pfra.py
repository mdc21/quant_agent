import pandas as pd
import numpy as np
from app.agents.pfra import PassiveResearchAgent

def test_pfra_logic():
    print("--- Starting Passive Research Agent (PFRA) Test ---")
    
    pfra = PassiveResearchAgent(min_adv=5_000_000) # 50 Lakhs
    
    # 1. Setup Mock Returns (252 days)
    np.random.seed(42)
    benchmark_rets = pd.Series(np.random.normal(0.0005, 0.01, 252))
    
    # Fund A: Low TE (0.1%), Low TER (0.1%), High Liq
    fund_a_rets = benchmark_rets + np.random.normal(0, 0.0001, 252)
    
    # Fund B: High TE (0.5%), High TER (0.5%), High Liq
    fund_b_rets = benchmark_rets + np.random.normal(0, 0.0005, 252)
    
    # Fund C: Illiquid (disqualify)
    fund_c_rets = benchmark_rets.copy()
    
    vehicle_data = [
        {
            "ticker": "NIFTY_BEES", "category": "Large Cap", "ter": 0.001, "liq_score": 0.9, 
            "adv": 50_000_000, "returns": fund_a_rets, "benchmark_returns": benchmark_rets
        },
        {
            "ticker": "EXPENSIVE_ETF", "category": "Large Cap", "ter": 0.005, "liq_score": 0.8, 
            "adv": 20_000_000, "returns": fund_b_rets, "benchmark_returns": benchmark_rets
        },
        {
            "ticker": "ILLIQUID_ETF", "category": "Large Cap", "ter": 0.001, "liq_score": 0.5, 
            "adv": 1_000_000, "returns": fund_c_rets, "benchmark_returns": benchmark_rets
        }
    ]
    
    # 2. Run Evaluation
    results = pfra.evaluate_vehicles(vehicle_data)
    
    print(f"\nFunds evaluated: {len(results)}")
    for r in results:
        print(f"Ticker: {r.ticker}")
        print(f"  Conviction: {r.conviction_score:.2f}")
        print(f"  {r.rationale}")
        
    # Verification
    tickers = [r.ticker for r in results]
    if "NIFTY_BEES" in tickers and "ILLIQUID_ETF" not in tickers:
        print("\nSuccess: PFRA correctly filtered illiquid funds.")
        
    if results[0].ticker == "NIFTY_BEES":
        print("Success: Low-cost, low-TE fund ranked highest.")

if __name__ == "__main__":
    test_pfra_logic()
