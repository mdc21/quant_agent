import os
import sys
import pandas as pd
from typing import Dict, Any

# Ensure project root is in path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.agents.allocator import PathAllocator

def verify_aggressive_capital_distribution():
    print("\n🛡️  Fiduciary Audit: Aggressive Profile Capital Distribution")
    print("==============================================================")
    
    # 1. Initialize Allocator for Aggressive Profile
    # Total Capital: 10 Lakh, Max Stocks: 15
    total_capital = 1_000_000
    risk_profile = "Aggressive"
    
    allocator = PathAllocator(
        risk_profile=risk_profile,
        total_capital=total_capital,
        max_stocks=15,
        equity_split_percent=60 # 60% of Equity goes to Direct Stocks
    )
    
    print(f"Risk Profile: {risk_profile}")
    print(f"Target Multi-Cap Ratio (Capital): 60:25:15")
    print(f"Target Equity Allocation (Macro): {allocator.equity_allocation*100:.0f}%")
    print(f"Target Alpha (Direct Stock) Capital: ₹{allocator.alpha_capital:,.2f}")
    print("--------------------------------------------------------------")
    
    # 2. Mock Metadata & EQRA to ensure we have candidates to pick from
    from unittest.mock import MagicMock
    from core.data.agent_schema import StockCandidate
    
    # Create 40 mock candidates (20 Large, 10 Mid, 10 Small)
    mock_candidates = []
    for i in range(1, 41):
        # Give slightly higher conviction to some to test prioritization
        conv = 0.7 + (i % 4) * 0.1
        mock_candidates.append(StockCandidate(
            symbol=f"SYM_{i}", conviction_score=conv, rationale="", 
            factors={"q_score": 4, "roa": 0.05}, lineage_id="L1"
        ))
    allocator.eqra.screen_stocks = MagicMock(return_value=mock_candidates)
    
    # Map symbols to specific caps and sectors
    # 1-20: Large, 21-30: Mid, 31-40: Small
    def mock_meta(symbol):
        idx = int(symbol.split("_")[1])
        if idx <= 20: cap = "Large Cap"
        elif idx <= 30: cap = "Mid Cap"
        else: cap = "Small Cap"
        
        # Distribute into 10 sectors to allow more room
        sectors = ["Financials", "Technology", "FMCG", "Energy", "Materials", "Industrials", "Auto", "Pharma", "Consumer", "Infra"]
        sector = sectors[idx % 10]
        return sector, cap
        
    allocator._fetch_metadata = mock_meta
    
    # Mock price history
    import pandas as pd
    import numpy as np
    mock_returns = pd.DataFrame(np.random.randn(10, 40), columns=[f"SYM_{i}" for i in range(1, 41)])
    allocator._fetch_price_history = MagicMock(return_value=mock_returns)

    print("🧠 Orchestrating Capital-Weighted Optimization (Refined Mock)...")
    sleeve = allocator.build_equity_sleeve()
    
    if not sleeve:
        print("❌ Audit Failed: No stocks selected.")
        return

    # 3. Aggregate Capital by Market Cap Category
    cap_distribution = {}
    total_deployed = 0
    
    for stock in sleeve:
        cap = stock['cap']
        capital = stock['target_capital']
        cap_distribution[cap] = cap_distribution.get(cap, 0) + capital
        total_deployed += capital

    # 4. Print Findings
    print("\n📊 Final Capital Distribution (Direct Equity Sleeve):")
    for cap, capital in sorted(cap_distribution.items()):
        percentage = (capital / total_deployed) * 100
        print(f"  {cap:10}: ₹{capital:12,.2f} ({percentage:5.1f}%)")
    
    print(f"\nTotal Deployed Capital: ₹{total_deployed:,.2f}")
    
    # 5. Sector Check
    sector_distribution = {}
    for stock in sleeve:
        sector = stock['sector']
        capital = stock['target_capital']
        sector_distribution[sector] = sector_distribution.get(sector, 0) + capital
        
    print("\n🏢 Sector Exposure (Cap Ceiling Check):")
    for sector, capital in sorted(sector_distribution.items(), key=lambda x: x[1], reverse=True):
        percentage = (capital / total_deployed) * 100
        status = "✅ PASS" if percentage <= 26.5 else "❌ FAIL" # 25% + buffer
        print(f"  {sector:25}: {percentage:5.1f}% [{status}]")

    print("\n==============================================================")
    print("AUDIT COMPLETE.")

if __name__ == "__main__":
    try:
        verify_aggressive_capital_distribution()
    except Exception as e:
        print(f"❌ Critical Audit Error: {e}")
        import traceback
        traceback.print_exc()
