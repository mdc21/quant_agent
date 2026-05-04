import numpy as np
from typing import Dict, Any

class LiquidityScorer:
    """
    Exit-strategy sensor (Task M5).
    Ensures portfolio liquidity and enforces position caps.
    Satisfies Section 4.1.1 of the functional specification.
    """
    def __init__(self, max_dtl: int = 20, max_adv_pct: float = 0.05):
        self.max_dtl = max_dtl             # 20-Day Golden Rule
        self.max_adv_pct = max_adv_pct     # 5% ADV Position Cap

    def calculate_metrics(
        self, 
        symbol: str, 
        position_value: float, 
        adv_30d: float, 
        participation_rate: float = 0.10
    ) -> Dict[str, Any]:
        """
        Calculates DTL and Liquidity Score.
        
        Args:
            symbol: Stock identifier.
            position_value: Value of the position in INR.
            adv_30d: 30-day Average Daily Volume in INR.
            participation_rate: % of ADV we are willing to trade daily (default 10%).
        """
        if adv_30d <= 0:
            return {"symbol": symbol, "dtl": 999, "liquidity_score": 0, "status": "ILLIQUID"}

        # 1. Calculate Days-to-Liquidate (DTL)
        # DTL = Total Value / (Daily Participation Volume)
        daily_exit_limit = adv_30d * participation_rate
        dtl = position_value / daily_exit_limit
        
        # 2. Calculate Liquidity Score (Normalized 0-100)
        # Lower DTL = Higher Score. A DTL of 20 results in a score of 0.
        liquidity_score = max(0, 100 - (dtl * (100 / self.max_dtl))) 
        
        # 3. Guardrail Checks
        status = "HEALTHY"
        alerts = []
        
        if dtl > self.max_dtl:
            status = "BREACH"
            alerts.append(f"DTL Breach: {dtl:.1f} days (Limit: {self.max_dtl})")
            
        if position_value > (adv_30d * self.max_adv_pct):
            # This is a warning if the position is > 5% of ADV
            if status != "BREACH": status = "WARNING"
            alerts.append(f"Position Cap Alert: {position_value/adv_30d:.1%} of ADV (Limit: {self.max_adv_pct:.1%})")

        return {
            "symbol": symbol,
            "dtl": dtl,
            "liquidity_score": liquidity_score,
            "adv_30d": adv_30d,
            "status": status,
            "alerts": alerts
        }

    def validate_portfolio_buffer(self, total_portfolio_value: float, liquid_cash: float) -> bool:
        """
        Ensures at least 5% of the portfolio remains in liquid funds.
        """
        buffer_pct = liquid_cash / total_portfolio_value
        return buffer_pct >= 0.05
