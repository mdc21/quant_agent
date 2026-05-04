from app.agents.pora import PortfolioReviewAgent
from core.data.agent_schema import CurrentPosition, StockCandidate

def test_pora_logic():
    print("--- Starting Portfolio Review Agent (PORA) Test ---")
    
    pora = PortfolioReviewAgent(stop_loss_limit=0.15, min_f_score=5)
    
    # 1. Mock Current Holdings
    current_holdings = [
        CurrentPosition(symbol="RELIANCE", purchase_price=2500, current_price=2700, 
                        current_f_score=9, entry_conviction=0.95, weight=0.10),
        CurrentPosition(symbol="LOSING_STK", purchase_price=1000, current_price=800, # 20% Loss
                        current_f_score=7, entry_conviction=0.80, weight=0.05),
        CurrentPosition(symbol="STALE_STK", purchase_price=500, current_price=520, 
                        current_f_score=4, entry_conviction=0.85, weight=0.05) # F-Score 4
    ]
    
    # 2. Mock New Buy List (EQRA Output)
    buy_list = [
        StockCandidate(symbol="RELIANCE", conviction_score=0.96, rationale="...", 
                       factors={}, lineage_id="L1"),
        StockCandidate(symbol="NEW_STAR", conviction_score=0.92, rationale="...", 
                       factors={}, lineage_id="L2")
    ]
    
    # 3. Run Audit
    signals = pora.audit_portfolio(current_holdings, buy_list)
    
    print(f"\nAudit Signals Generated: {len(signals)}")
    for s in signals:
        print(f"Symbol: {s.symbol}")
        print(f"  Action: {s.action}")
        print(f"  Rationale: {s.rationale}")
        
    # Verification
    res_map = {s.symbol: s.action for s in signals}
    
    if res_map.get("LOSING_STK") == "EXIT":
        print("\nSuccess: Hard stop-loss correctly triggered EXIT.")
        
    if res_map.get("STALE_STK") == "EXIT":
        print("Success: Style drift (F-Score < 5) correctly triggered EXIT.")
        
    if res_map.get("RELIANCE") == "HOLD":
        print("Success: Thesis intact holding correctly maintained.")

if __name__ == "__main__":
    test_pora_logic()
