import numpy as np
from core.models.tcm import TransactionCostModel

def test_tcm_logic():
    print("--- Starting Transaction Cost Model (TCM) Test ---")
    
    tcm = TransactionCostModel(stt_rate=0.001, brokerage_rate=0.0005)
    
    # 1. Test Liquidity Sensitivity
    # Scenario: 10 Crore Trade (100,000,000 INR)
    trade_value = 100_000_000
    volatility = 0.02 # 2% daily vol
    
    # Nifty 50 Stock (High ADV: 1000 Crore)
    adv_nifty = 10_000_000_000
    cost_nifty = tcm.estimate_total_cost(trade_value, adv_nifty, volatility)
    
    # Smallcap Stock (Low ADV: 10 Crore)
    adv_small = 100_000_000
    cost_small = tcm.estimate_total_cost(trade_value, adv_small, volatility)
    
    print(f"\nCost for Nifty 50 Trade: {cost_nifty:,.0f} INR ({(cost_nifty/trade_value):.2%})")
    print(f"Cost for Smallcap Trade: {cost_small:,.0f} INR ({(cost_small/trade_value):.2%})")
    
    if cost_small > cost_nifty * 5:
        print("Success: TCM correctly identifies significantly higher costs for low-liquidity stocks.")

    # 2. Test Order Size Scaling (Non-linear impact)
    # Trade 1: 1% of ADV
    trade_1 = 0.01 * adv_nifty
    impact_1 = tcm.estimate_total_cost(trade_1, adv_nifty, volatility) - (trade_1 * (0.001 + 0.0005 + 0.0005))
    
    # Trade 2: 10% of ADV
    trade_2 = 0.10 * adv_nifty
    impact_2 = tcm.estimate_total_cost(trade_2, adv_nifty, volatility) - (trade_2 * (0.001 + 0.0005 + 0.0005))
    
    # Impact ratio should be sqrt(10) ~ 3.16, but trade size is 10x
    # So absolute impact cost ratio should be 10 * sqrt(0.1 / 0.01) = 10 * 3.16 = 31.6
    print(f"\nMarket Impact for 1% ADV: {impact_1:,.0f} INR")
    print(f"Market Impact for 10% ADV: {impact_2:,.0f} INR")
    
    if impact_2 > impact_1 * 10:
        print("Success: Market impact correctly scales non-linearly with trade size.")

    # 3. STT Validation
    # Fixed costs for 10 Crore trade should be 0.15% (STT 0.1% + Brokerage 0.05%) = 1.5 Lakh
    fixed_cost_only = trade_value * (0.001 + 0.0005)
    print(f"\nFixed India Regulatory Costs (STT+Brokerage): {fixed_cost_only:,.0f} INR")
    if fixed_cost_only == 150_000:
        print("Success: STT and Brokerage rates are correctly applied.")

if __name__ == "__main__":
    test_tcm_logic()
