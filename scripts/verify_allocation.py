import os
import sys
import pandas as pd
import numpy as np

# Ensure project root is in path
project_root = os.path.abspath(os.path.join(os.getcwd()))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.agents.allocator import OmniAllocator

def verify():
    print("=== Final Fiduciary Audit: Overlapping Constraints ===")
    print("Rules: 20% Sector Cap + UCITS 5/10/40 Asset Cap")
    
    allocator = OmniAllocator(
        max_stocks=15,
        max_funds=10,
        risk_profile="Aggressive",
        total_capital=1000000,
        equity_split_percent=100 # Test with 100% equity to see stock concentration
    )
    
    # Generate Equity Sleeve
    print("Running OmniAllocator.build_equity_sleeve()...")
    equity_sleeve = allocator.build_equity_sleeve()
    
    if not equity_sleeve:
        print("No equities found. Check market data.")
        return

    df = pd.DataFrame(equity_sleeve)
    weights = df['target_weight']
    
    print("\n--- Asset-Level Audit (UCITS 5/10/40) ---")
    print(f"Max Single Weight: {weights.max():.2%}")
    
    large_holdings = weights[weights > 0.05]
    large_holdings_sum = large_holdings.sum()
    
    print(f"Number of holdings > 5%: {len(large_holdings)}")
    print(f"Sum of holdings > 5%: {large_holdings_sum:.2%} (Limit: 40%)")
    
    ucits_breach = False
    if weights.max() > 0.1001: # 10%
        print("❌ UCITS BREACH: Single asset exceeds 10%")
        ucits_breach = True
    if large_holdings_sum > 0.4001: # 40%
        print(f"❌ UCITS BREACH: Sum of >5% holdings is {large_holdings_sum:.2%}")
        ucits_breach = True
    
    if not ucits_breach:
        print("✅ UCITS 5/10/40 VERIFIED: Pass")

    print("\n--- Sector-Level Audit (20% Healthy Ceiling) ---")
    sector_dist = df.groupby('sector')['target_weight'].sum()
    print("Sector Distribution:")
    print(sector_dist)
    
    max_sector = sector_dist.max()
    print(f"Max Sector Concentration: {max_sector:.2%}")
    
    if max_sector > 0.2001: # 20%
        print(f"❌ SECTOR BREACH: {sector_dist.idxmax()} concentration is {max_sector:.2%}")
    else:
        print("✅ SECTOR 20% CEILING VERIFIED: Pass")

    # Display allocation
    print("\n--- Optimized Portfolio (UCITS + Sector Constrained) ---")
    print(df[['symbol', 'sector', 'target_weight']].sort_values('target_weight', ascending=False))

if __name__ == "__main__":
    verify()
