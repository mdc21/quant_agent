import sys
import os
from pathlib import Path
from unittest.mock import MagicMock

# Add project root to path
root_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(root_dir))

from app.agents.allocator import PathAllocator
from core.data.store import DataStore
from core.data.agent_schema import StockCandidate

def verify_icici_allocation():
    print("--- 🛡️ ICICIBANK Allocation Verification (May 2026) ---")
    store = DataStore()
    lib = store.lib
    
    # 1. Fetch the hardened ICICI data
    symbol = "ICICIBANK"
    symbol_key = f"FUNDAMENTALS_{symbol}"
    
    if not lib.has_symbol(symbol_key):
        print(f"Error: {symbol} not found in ArcticDB.")
        return
        
    fundamentals = lib.read(symbol_key).data.iloc[-1].to_dict()
    print(f"Hardened Metrics: GNPA: {fundamentals.get('gnpa')}, NIM: {fundamentals.get('nim')}, CASA: {fundamentals.get('casa_ratio')}")
    
    # 2. Mock EQRA Candidates
    # We'll provide ICICI and HDFC as top picks
    mock_candidates = [
        StockCandidate(
            symbol="ICICIBANK",
            conviction_score=0.95,
            rationale="Elite banking anchor with NIM expansion.",
            lineage_id="VERIFIED_FY26",
            factors={
                "q_score": 9.0,
                "roa": fundamentals.get("roa", 0.023),
                "fiduciary_grade": True,
                **fundamentals
            }
        ),
        StockCandidate(
            symbol="HDFCBANK",
            conviction_score=0.85,
            rationale="Stable post-merger pillar.",
            lineage_id="VERIFIED_FY26",
            factors={
                "q_score": 8.5,
                "roa": 0.0188,
                "fiduciary_grade": True
            }
        ),
        StockCandidate(
            symbol="KOTAKBANK",
            conviction_score=0.92,
            rationale="Superior underwriting discipline.",
            lineage_id="VERIFIED_FY26",
            factors={
                "q_score": 9.2,
                "roa": 0.0214,
                "fiduciary_grade": True
            }
        )
    ]
    
    # 3. Initialize PathAllocator for 4L Portfolio
    allocator = PathAllocator(
        total_capital=400000,
        risk_profile="Aggressive"
    )
    
    # Mock EQRA and Metadata fetching
    allocator.eqra = MagicMock()
    allocator.eqra.screen_stocks.return_value = mock_candidates
    
    allocator._fetch_metadata_bulk = MagicMock()
    allocator._fetch_metadata_bulk.return_value = {
        "ICICIBANK": ("Financial Services", "Large Cap"),
        "HDFCBANK": ("Financial Services", "Large Cap"),
        "KOTAKBANK": ("Financial Services", "Large Cap")
    }
    
    # Mock Covariance to avoid price fetching
    import pandas as pd
    import numpy as np
    allocator._build_covariance = MagicMock()
    allocator._build_covariance.return_value = pd.DataFrame(
        np.eye(3) * 0.04, 
        index=["ICICIBANK", "HDFCBANK", "KOTAKBANK"],
        columns=["ICICIBANK", "HDFCBANK", "KOTAKBANK"]
    )

    # 4. Run Selection
    print("\nSimulating PathAllocator: build_equity_sleeve...")
    sleeve, universe = allocator.build_equity_sleeve()
    
    # 5. Check ICICI results
    icici_alloc = next((item for item in sleeve if item["symbol"] == "ICICIBANK"), None)
    
    if icici_alloc:
        print(f"\n✅ ICICIBANK Allocation Result:")
        print(f"Allocation Amount: ₹{icici_alloc['target_capital']:,.0f}")
        print(f"Weight in Alpha Sleeve: {icici_alloc['target_weight']*100:.1f}%")
        print(f"Total Portfolio Weight: {(icici_alloc['target_capital']/allocator.total_capital)*100:.1f}%")
        print(f"Rationale: {icici_alloc.get('rationale', 'N/A')}")
    else:
        print("\n❌ ICICIBANK was not selected.")

if __name__ == "__main__":
    verify_icici_allocation()
