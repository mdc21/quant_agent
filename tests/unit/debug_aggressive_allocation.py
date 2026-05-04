import os
import sys

# Ensure project root is in path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.agents.allocator import PathAllocator

def check_aggressive_counts():
    print("🔍 Auditing Aggressive Profile Allocation Logic")
    allocator = PathAllocator(risk_profile="Aggressive", max_stocks=15)
    
    # We will simulate build_equity_sleeve but print the counts
    # We need to mock EQRA to return a mix of caps
    from unittest.mock import MagicMock
    from core.data.agent_schema import StockCandidate
    
    # Create 50 candidates: 40 Large, 5 Mid, 5 Small
    candidates = []
    for i in range(1, 41):
        candidates.append(StockCandidate(symbol=f"L{i}", conviction_score=0.9, rationale="", factors={"q_score": 4, "roa": 0.05}, lineage_id="L1"))
    for i in range(1, 6):
        candidates.append(StockCandidate(symbol=f"M{i}", conviction_score=0.8, rationale="", factors={"q_score": 4, "roa": 0.05}, lineage_id="L1"))
    for i in range(1, 6):
        candidates.append(StockCandidate(symbol=f"S{i}", conviction_score=0.7, rationale="", factors={"q_score": 4, "roa": 0.05}, lineage_id="L1"))
        
    allocator.eqra.screen_stocks = MagicMock(return_value=candidates)
    
    # Mock _fetch_metadata to return specific caps and DIFFERENT sectors
    def mock_meta(symbol):
        if symbol.startswith("L"): return "Sector1", "Large Cap"
        if symbol.startswith("M"): return "Sector2", "Mid Cap"
        if symbol.startswith("S"): return "Sector3", "Small Cap"
        return "Unknown", "Mid Cap"
    
    allocator._fetch_metadata = mock_meta
    
    sleeve = allocator.build_equity_sleeve()
    
    from collections import Counter
    counts = Counter([s['cap'] for s in sleeve])
    print(f"Results for Max Stocks = 15:")
    print(f"  Large: {counts['Large Cap']} (Target: 10)")
    print(f"  Mid:   {counts['Mid Cap']} (Target: 3)")
    print(f"  Small: {counts['Small Cap']} (Target: 2)")
    
    if counts['Small Cap'] < 2:
        print("❌ SMALL CAP UNDER-ALLOCATED")
    else:
        print("✅ ALLOCATION TARGETS MET")

if __name__ == "__main__":
    check_aggressive_counts()
