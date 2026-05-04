import numpy as np

class TransactionCostModel:
    """
    Predictive Transaction Cost Model (TCM).
    Implements Almgren-Chriss Market Impact and Indian Regulatory Costs.
    Satisfies Task M4 of the Intelligence Engine.
    """
    def __init__(
        self, 
        stt_rate: float = 0.001,      # 0.1% for delivery
        brokerage_rate: float = 0.0005, # 0.05% typical
        impact_coefficient: float = 0.1 # Scaling factor for market impact
    ):
        self.stt_rate = stt_rate
        self.brokerage_rate = brokerage_rate
        self.impact_coefficient = impact_coefficient

    def estimate_total_cost(
        self, 
        trade_value: float, 
        adv: float, 
        volatility: float,
        bid_ask_spread: float = 0.001 # Default 10 bps
    ) -> float:
        """
        Estimates the total cost of a trade (Fixed + Variable).
        
        Args:
            trade_value: Total value of the trade in INR.
            adv: Average Daily Volume of the stock in INR.
            volatility: Realized volatility of the stock.
            bid_ask_spread: Bid-Ask spread as a percentage of price.
            
        Returns:
            total_cost_inr: The estimated cost in INR.
        """
        if adv <= 0:
            return trade_value * 0.05 # Conservative fallback (5% for zero liquidity)

        # 1. Fixed Costs (STT + Brokerage)
        fixed_cost = trade_value * (self.stt_rate + self.brokerage_rate)
        
        # 2. Spread Cost (Half-spread)
        spread_cost = trade_value * (bid_ask_spread / 2.0)
        
        # 3. Market Impact (Almgren-Chriss Square Root Model)
        # Cost is proportional to volatility and the square root of trade size relative to ADV
        participation_rate = trade_value / adv
        impact_cost = self.impact_coefficient * trade_value * volatility * np.sqrt(participation_rate)
        
        total_cost = fixed_cost + spread_cost + impact_cost
        return total_cost

    def check_rebalance_threshold(
        self, 
        benefit_inr: float, 
        tcm_cost_inr: float, 
        threshold: float = 1.5
    ) -> bool:
        """
        Determines if a rebalance is economically justified.
        """
        if tcm_cost_inr <= 0:
            return True
            
        ratio = benefit_inr / tcm_cost_inr
        return ratio > threshold
