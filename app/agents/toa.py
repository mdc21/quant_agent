import datetime
from typing import List, Dict, Any, Tuple
from core.data.agent_schema import TaxLot, TaxSaleInstruction

class TaxOptimizationAgent:
    """
    Tax Optimisation Agent (TOA).
    Maximizes post-tax alpha through lot accounting and harvesting.
    Satisfies Task A8 of the Agent Mesh.
    """
    def __init__(self, stcg_rate: float = 0.20, ltcg_rate: float = 0.125, ltcg_exemption: float = 125000):
        self.stcg_rate = stcg_rate           # 20% STCG (July 2024 Budget)
        self.ltcg_rate = ltcg_rate           # 12.5% LTCG (July 2024 Budget)
        self.ltcg_exemption = ltcg_exemption # ₹1.25 Lakh Exemption

    def categorize_lot(self, lot: TaxLot) -> str:
        """
        Determines if a lot is STCG or LTCG (Indian rules: 365 days).
        """
        today = datetime.datetime.now()
        is_long_term = (today - lot.buy_date).days > 365
        return "LTCG" if is_long_term else "STCG"

    def calculate_lot_tax(self, lot: TaxLot, quantity: int) -> float:
        """
        Calculates estimated tax for a specific quantity of a lot.
        """
        gain_per_share = lot.current_price - lot.buy_price
        if gain_per_share <= 0:
            return 0.0 # Loss (no tax, harvesting opportunity)
            
        total_gain = gain_per_share * quantity
        tax_type = self.categorize_lot(lot)
        rate = self.ltcg_rate if tax_type == "LTCG" else self.stcg_rate
        
        return total_gain * rate

    def optimize_sales(self, symbol: str, quantity_to_sell: int, lots: List[TaxLot]) -> TaxSaleInstruction:
        """
        Implements priority logic: Loss-making lots -> LTCG -> STCG.
        """
        # 1. Sort lots by tax efficiency
        # Priority 1: Losses (Most loss first)
        # Priority 2: LTCG (Long-term gains)
        # Priority 3: STCG (Short-term gains)
        
        def sale_priority(l):
            gain = l.current_price - l.buy_price
            tax_type = self.categorize_lot(l)
            if gain <= 0: return (0, gain) # High priority (0), largest loss first
            if tax_type == "LTCG": return (1, gain) # Medium priority
            return (2, gain) # Low priority
            
        sorted_lots = sorted(enumerate(lots), key=lambda x: sale_priority(x[1]))
        
        lots_to_sell = []
        remaining = quantity_to_sell
        total_tax = 0.0
        
        for idx, lot in sorted_lots:
            if remaining <= 0: break
            
            sold = min(lot.quantity, remaining)
            tax = self.calculate_lot_tax(lot, sold)
            
            lots_to_sell.append({
                "lot_index": idx,
                "quantity": sold,
                "tax_type": self.categorize_lot(lot),
                "gain": (lot.current_price - lot.buy_price) * sold
            })
            
            total_tax += tax
            remaining -= sold
            
        return TaxSaleInstruction(
            symbol=symbol,
            total_quantity=quantity_to_sell,
            lots_to_sell=lots_to_sell,
            estimated_tax=total_tax
        )

    def find_harvesting_opportunities(self, all_lots: List[TaxLot], current_realized_ltcg: float = 0.0) -> List[Dict[str, Any]]:
        """
        Identifies LTCG Harvesting and Tax-Loss Harvesting opportunities.
        """
        opps = []
        ltcg_available = self.ltcg_exemption - current_realized_ltcg
        
        for lot in all_lots:
            gain = (lot.current_price - lot.buy_price) * lot.quantity
            
            # 1. Tax-Loss Harvesting (Any loss)
            if gain < 0:
                opps.append({
                    "symbol": lot.symbol,
                    "type": "TAX_LOSS_HARVEST",
                    "value": abs(gain),
                    "rationale": f"Harvesting loss of {abs(gain):.0f} to offset future gains."
                })
                
            # 2. LTCG Harvesting (Within ₹1.25L exemption)
            elif self.categorize_lot(lot) == "LTCG" and ltcg_available > 0:
                harvest_gain = min(gain, ltcg_available)
                if harvest_gain > 5000: # Only suggest if worth the friction
                    opps.append({
                        "symbol": lot.symbol,
                        "type": "LTCG_HARVEST",
                        "value": harvest_gain,
                        "rationale": f"Utilizing tax-free LTCG exemption (Remaining: {ltcg_available:.0f})."
                    })
                    ltcg_available -= harvest_gain
                    
        return opps
