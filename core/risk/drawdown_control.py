import numpy as np
from typing import Dict, Any

class DrawdownControlModel:
    """
    Financial seatbelt for Layer 1.
    Implements CPPI and Volatility Targeting to protect portfolio floors.
    Satisfies Section 6.2 of the functional specification.
    """
    def __init__(
        self, 
        multiplier: float = 3.0, 
        target_vol: float = 0.15,
        mdd_max: float = 0.20
    ):
        self.multiplier = multiplier    # 'm' in CPPI
        self.target_vol = target_vol    # σtarget
        self.mdd_max = mdd_max          # MDD limit

    def calculate_cppi_signals(
        self, 
        portfolio_value: float, 
        floor_value: float, 
        realized_vol: float,
        current_drawdown: float = 0.0
    ) -> Dict[str, Any]:
        """
        Calculates CPPI and Vol-Targeting signals.
        
        Args:
            portfolio_value: Current value of the portfolio (W).
            floor_value: Minimum acceptable value (F).
            realized_vol: 21-day realized volatility.
            current_drawdown: Current peak-to-trough drawdown as a decimal.
        """
        # 1. Compute the Cushion
        # Safety margin before hitting the floor
        cushion = max(0, portfolio_value - floor_value)
        cushion_pct = cushion / portfolio_value if portfolio_value > 0 else 0
        
        # 2. Basic CPPI Risky Exposure (E = m * C)
        risky_exposure = self.multiplier * cushion
        
        # 3. Volatility Targeting Overlay
        # Inversely scale based on realized volatility
        # If realized_vol is 0, we use a small value to avoid division by zero
        vol_scalar = self.target_vol / max(realized_vol, 0.001)
        
        # 4. Adjusted Risky Exposure
        # Cannot exceed the portfolio value or the CPPI limit
        adjusted_exposure = min(risky_exposure * vol_scalar, portfolio_value)
        risky_target_pct = adjusted_exposure / portfolio_value if portfolio_value > 0 else 0
        
        # 5. Drawdown Governor
        status = "HEALTHY"
        alerts = []
        
        # Use epsilon for stable float comparison
        eps = 1e-6
        
        # MDD Warning: 80% of mdd_max
        if current_drawdown >= (self.mdd_max * 0.8) - eps:
            status = "DEFENSIVE_WARNING"
            alerts.append(f"Drawdown Warning: {current_drawdown:.1%} (Limit: {self.mdd_max:.1%})")
            
        # MDD Breach
        if current_drawdown >= self.mdd_max - eps:
            status = "BREACH"
            alerts.append(f"Drawdown BREACH: {current_drawdown:.1%} exceeded {self.mdd_max:.1%}")

        return {
            "risky_allocation_target": risky_target_pct,
            "cushion_status": cushion_pct,
            "vol_scalar": vol_scalar,
            "status": status,
            "alerts": alerts
        }
