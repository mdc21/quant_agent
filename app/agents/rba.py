import math
from typing import List, Dict, Any, Optional
from core.data.agent_schema import TradeInstruction

class RebalancingAgent:
    """
    Rebalancing Agent (RBA).
    The 'Execution Commander' that translates weights into executable trades.
    Satisfies Task A9 of the Agent Mesh.
    """
    def __init__(self, cash_buffer_pct: float = 0.015, min_trade_value: float = 500):
        self.cash_buffer_pct = cash_buffer_pct # 1.5% Buffer
        self.min_trade_value = min_trade_value # Dust Filter

    def generate_trade_list(
        self, 
        target_weights: Dict[str, float], 
        total_portfolio_value: float, 
        current_prices: Dict[str, float],
        current_holdings: Dict[str, int]
    ) -> List[TradeInstruction]:
        """
        Translates weights into integer share trades with cash buffer and dust filtering.
        """
        trades = []
        reserved_cash = total_portfolio_value * self.cash_buffer_pct
        investable_capital = total_portfolio_value - reserved_cash
        
        # 1. Calculate ideal trades
        for symbol, weight in target_weights.items():
            price = current_prices.get(symbol)
            if not price or price <= 0:
                continue
                
            # Ideal integer quantity (Always round down for safety)
            target_qty = math.floor((investable_capital * weight) / price)
            curr_qty = current_holdings.get(symbol, 0)
            delta_qty = target_qty - curr_qty
            
            if delta_qty == 0:
                continue
                
            trade_value = abs(delta_qty * price)
            
            # 2. Dust Filter
            if trade_value < self.min_trade_value:
                continue
                
            trades.append(TradeInstruction(
                symbol=symbol,
                action="BUY" if delta_qty > 0 else "SELL",
                quantity=abs(delta_qty),
                order_type="LIMIT",
                estimated_price=price,
                total_value=trade_value,
                rationale=f"Rebalance: Move from {curr_qty} to {target_qty} shares (Target Weight: {weight:.1%})"
            ))
            
        # 3. Sequencing: SELL first to release capital
        # In Python, 'SELL' > 'BUY' alphabetically, so we can sort descending
        return sorted(trades, key=lambda x: x.action, reverse=True)
