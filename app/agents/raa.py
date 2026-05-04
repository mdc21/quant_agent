import numpy as np
import pandas as pd
from typing import List, Dict, Any
from core.data.agent_schema import RiskReport

class RiskAnalysisAgent:
    """
    Risk Analysis Agent (RAA).
    The 'Safety Inspector' that enforces hard limits and vetoes dangerous allocations.
    Satisfies Task A7 of the Agent Mesh.
    """
    def __init__(self, single_stock_cap: float = 0.08, sector_cap: float = 0.25):
        self.single_stock_cap = single_stock_cap
        self.sector_cap = sector_cap

    def calculate_var_99(self, weights: np.array, cov_matrix: pd.DataFrame) -> float:
        """
        Calculates parametric 99% Value-at-Risk (VaR).
        """
        # Z-score for 99% confidence is 2.33
        port_vol = np.sqrt(weights.T @ cov_matrix.values @ weights)
        var_99 = 2.33 * port_vol
        return float(var_99)

    def calculate_mctr(self, weights: np.array, cov_matrix: pd.DataFrame) -> Dict[str, float]:
        """
        Calculates Marginal Contribution to Risk (MCTR) for each asset.
        """
        port_vol = np.sqrt(weights.T @ cov_matrix.values @ weights)
        if port_vol == 0:
            return {symbol: 0.0 for symbol in cov_matrix.columns}
            
        # Marginal Risk = (Covariance * Weights) / Port_Vol
        marginal_risk = (cov_matrix.values @ weights) / port_vol
        
        mctr = {
            symbol: float(marginal_risk[i] * weights[i]) 
            for i, symbol in enumerate(cov_matrix.columns)
        }
        return mctr

    def inspect_portfolio(
        self, 
        target_weights: np.array, 
        cov_matrix: pd.DataFrame, 
        sector_map: Dict[str, str],
        max_var: float = 0.15
    ) -> RiskReport:
        """
        Enforces concentration limits, VaR limits, and sector caps.
        """
        breaches = []
        symbols = list(cov_matrix.columns)
        
        # 1. Single Stock Concentration (Section 10)
        for i, weight in enumerate(target_weights):
            if weight > self.single_stock_cap:
                breaches.append(f"Concentration Breach: {symbols[i]} at {weight:.1%}")

        # 2. Sector Concentration
        sector_sums = {}
        for i, weight in enumerate(target_weights):
            sector = sector_map.get(symbols[i], "Unknown")
            sector_sums[sector] = sector_sums.get(sector, 0.0) + weight
            
        for sector, total in sector_sums.items():
            if total > self.sector_cap:
                breaches.append(f"Sector Breach: {sector} at {total:.1%}")

        # 3. Tail Risk (VaR)
        var_99 = self.calculate_var_99(target_weights, cov_matrix)
        if var_99 > max_var:
            breaches.append(f"VaR Breach: 99% VaR is {var_99:.1%} (Max {max_var:.1%})")

        # 4. Final Veto Decision
        is_compliant = len(breaches) == 0
        mctr = self.calculate_mctr(target_weights, cov_matrix)
        
        return RiskReport(
            is_compliant=is_compliant,
            breaches=breaches,
            var_99=var_99,
            mctr=mctr
        )
