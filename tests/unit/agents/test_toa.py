import datetime
from app.agents.toa import TaxOptimizationAgent
from core.data.agent_schema import TaxLot

def test_toa_logic():
    print("--- Starting Tax Optimisation Agent (TOA) Test ---")
    
    toa = TaxOptimizationAgent()
    today = datetime.datetime.now()
    
    # 1. Setup Mock Lots
    lots = [
        # Lot 0: STCG (Recent), Gain
        TaxLot(symbol="RELIND", buy_date=today - datetime.timedelta(days=100), 
               buy_price=2000, quantity=50, current_price=2500),
        # Lot 1: LTCG (Old), Gain
        TaxLot(symbol="RELIND", buy_date=today - datetime.timedelta(days=400), 
               buy_price=1800, quantity=100, current_price=2500),
        # Lot 2: STCG (Recent), Loss
        TaxLot(symbol="RELIND", buy_date=today - datetime.timedelta(days=50), 
               buy_price=2800, quantity=30, current_price=2500)
    ]
    
    # 2. Test Priority Logic (Sell 100 shares)
    print("\n[Scenario: Priority Lot Selection]")
    # Expect: Sell Lot 2 (Loss) first, then Lot 1 (LTCG)
    instruction = toa.optimize_sales("RELIND", 100, lots)
    
    print(f"Total Shares Sold: {instruction.total_quantity}")
    print(f"Estimated Tax: {instruction.estimated_tax:.2f} INR")
    for s in instruction.lots_to_sell:
        print(f"  Lot {s['lot_index']} ({s['tax_type']}): {s['quantity']} shares, Gain/Loss: {s['gain']:.0f}")
        
    # Verification
    if instruction.lots_to_sell[0]['lot_index'] == 2:
        print("Success: Loss-making lot correctly prioritized.")
    if instruction.lots_to_sell[1]['tax_type'] == "LTCG":
        print("Success: LTCG lot prioritized over STCG for gains.")

    # 3. Test Harvesting Opportunities
    print("\n[Scenario: Harvesting Search]")
    # Portfolio LTCG: Lot 1 has (2500-1800)*100 = 70,000 gain
    # Portfolio Loss: Lot 2 has (2500-2800)*30 = -9,000 loss
    opps = toa.find_harvesting_opportunities(lots)
    
    for opp in opps:
        print(f"Type: {opp['type']}, Value: {opp['value']:.0f}")
        print(f"  Rationale: {opp['rationale']}")
        
    types = [o['type'] for o in opps]
    if "TAX_LOSS_HARVEST" in types and "LTCG_HARVEST" in types:
        print("\nSuccess: Both LTCG and Tax-Loss opportunities identified.")

if __name__ == "__main__":
    test_toa_logic()
