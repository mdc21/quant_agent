from app.agents.rba import RebalancingAgent

def test_rba_logic():
    print("--- Starting Rebalancing Agent (RBA) Test ---")
    
    rba = RebalancingAgent(cash_buffer_pct=0.015, min_trade_value=500)
    
    # 1. Setup Mock Data
    total_val = 1_00_000 # 1 Lakh
    target_weights = {
        "RELIANCE": 0.30,
        "TCS": 0.20,
        "INFY": 0.20,
        "HDFC": 0.29, # Sum = 0.99 (leaving 1% residual)
        "DUST": 0.001  # Should be ignored by dust filter
    }
    
    prices = {
        "RELIANCE": 2500,
        "TCS": 3500,
        "INFY": 1500,
        "HDFC": 1600,
        "DUST": 100
    }
    
    current_holdings = {
        "RELIANCE": 10, # Needs to BUY
        "TCS": 15,     # Needs to SELL
        "INFY": 0,      # Needs to BUY
        "HDFC": 18,     # Needs to BUY
        "DUST": 0       # Target 1 share = 100 value (< 500 dust)
    }
    
    # 2. Run Rebalance
    trades = rba.generate_trade_list(target_weights, total_val, prices, current_holdings)
    
    print(f"\nTrades Generated: {len(trades)}")
    for t in trades:
        print(f"{t.action} {t.quantity} {t.symbol} @ {t.estimated_price} (Value: {t.total_value:.0f})")
        
    # Verification
    # 1. Sequencing (SELL first)
    if trades[0].action == "SELL":
        print("\nSuccess: SELL orders sequenced first.")
        
    # 2. Dust Filter
    if "DUST" not in [t.symbol for t in trades]:
        print("Success: Dust trade (< 500) correctly filtered.")
        
    # 3. Cash Buffer
    total_buy_value = sum(t.total_value for t in trades if t.action == "BUY")
    max_investable = total_val * (1 - 0.015)
    print(f"Total Buy Value: {total_buy_value:.0f} (Max Investable: {max_investable:.0f})")
    
    if total_buy_value <= max_investable:
        print("Success: Cash buffer maintained. No over-allocation.")
        
    # 4. Integer Rounding
    if all(isinstance(t.quantity, int) for t in trades):
        print("Success: All trade quantities are integers.")

if __name__ == "__main__":
    test_rba_logic()
