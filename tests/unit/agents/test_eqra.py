from app.agents.eqra import EquityResearchAgent

def test_eqra_logic():
    print("--- Starting Equity Research Agent (EQRA) Test ---")
    
    eqra = EquityResearchAgent(min_f_score=7, min_roce=0.15)
    
    # 1. Mock Universe Fundamentals
    universe_fundamentals = {
        "RELIANCE": {
            "net_income": 1000, "total_assets": 8000, "roa": 0.12, "roa_prev": 0.10, "operating_cash_flow": 1200,
            "debt_equity": 0.4, "debt_equity_prev": 0.5, "current_ratio": 1.5, "current_ratio_prev": 1.4,
            "shares_out": 100, "shares_out_prev": 100,
            "gross_margin": 0.25, "gross_margin_prev": 0.24, "asset_turnover": 0.8, "asset_turnover_prev": 0.7,
            "roce": 0.18, "lineage_id": "SESS_20260426_FUND"
        },
        "JUNK_CORP": {
            "net_income": -50, "total_assets": 5000, "roa": -0.05, "roa_prev": 0.02, "operating_cash_flow": -100,
            "debt_equity": 2.5, "debt_equity_prev": 2.0, "current_ratio": 0.8, "current_ratio_prev": 0.9,
            "shares_out": 120, "shares_out_prev": 100,
            "gross_margin": 0.10, "gross_margin_prev": 0.15, "asset_turnover": 0.4, "asset_turnover_prev": 0.5,
            "roce": 0.02, "lineage_id": "SESS_20260426_FUND"
        },
        "HDFC_BANK": {
            "net_income": 800, "total_assets": 4000, "roa": 0.15, "roa_prev": 0.14, "operating_cash_flow": 900,
            "debt_equity": 0.1, "debt_equity_prev": 0.1, "current_ratio": 1.2, "current_ratio_prev": 1.1,
            "shares_out": 500, "shares_out_prev": 500,
            "gross_margin": 0.40, "gross_margin_prev": 0.38, "asset_turnover": 0.6, "asset_turnover_prev": 0.6,
            "roce": 0.22, "lineage_id": "SESS_20260426_FUND"
        }
    }
    
    # 2. Mock Momentum Ranks (0.0 to 1.0)
    price_momentum = {
        "RELIANCE": 0.95, # High momentum
        "JUNK_CORP": 0.10, # Low momentum
        "HDFC_BANK": 0.40  # Low momentum
    }
    
    # 3. Run Screening
    candidates = eqra.screen_universe(universe_fundamentals, price_momentum)
    
    print(f"\nCandidates identified: {len(candidates)}")
    for c in candidates:
        print(f"Symbol: {c.symbol}")
        print(f"  Conviction Score: {c.conviction_score:.2f}")
        print(f"  Rationale: {c.rationale}")
        print(f"  Lineage: {c.lineage_id}")
        
    # Verification
    symbols = [c.symbol for c in candidates]
    if "RELIANCE" in symbols and "JUNK_CORP" not in symbols:
        print("\nSuccess: EQRA correctly filtered quality and momentum candidates.")
    
    if candidates[0].symbol == "RELIANCE":
        print("Success: RELIANCE ranked #1 due to strong quality + momentum blend.")

if __name__ == "__main__":
    test_eqra_logic()
