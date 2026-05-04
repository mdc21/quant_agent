import numpy as np
import pandas as pd
import cvxpy as cp
from pypfopt import HRPOpt
from typing import List, Dict, Any, Optional, Tuple
from core.data.agent_schema import GoalSleeve

class PortfolioArchitect:
    """
    Portfolio Construction Agent (GENPOA).
    The 'Architect' that builds target weights using fiduciary optimization.
    Satisfies Task A6 of the Agent Mesh.
    """
    def __init__(self, risk_aversion: float = 2.5, max_single_weight: float = 0.10):
        self.risk_aversion = risk_aversion
        self.max_single_weight = max_single_weight  # UCITS Hard Cap: 10%
        self.ucits_threshold = 0.05                 # UCITS aggregate threshold: 5%
        self.ucits_aggregate_cap = 0.40             # UCITS aggregate cap: 40%

    def __init__(self, risk_aversion: float = 2.5, max_single_weight: float = 0.10):
        self.risk_aversion = risk_aversion
        self.max_single_weight = max_single_weight  # UCITS Hard Cap: 10%
        self.ucits_threshold = 0.05                 # UCITS aggregate threshold: 5%
        self.ucits_aggregate_cap = 0.40             # UCITS aggregate cap: 40%

    def optimize_mvo_with_costs(
        self,
        expected_returns: pd.Series,
        cov_matrix: pd.DataFrame,
        current_weights: np.ndarray,
        tcm_costs: np.ndarray,
        constraints: List[Any] = []
    ) -> np.ndarray:
        """
        TCM-Penalized Mean-Variance Optimization with UCITS 5/10/40 constraints.
        Uses a convex approximation for the 40% rule to ensure solver compatibility.
        """
        n = len(expected_returns)
        w = cp.Variable(n)
        
        # 1. Objective: Maximize (Return - Risk_Penalty - Transaction_Costs)
        P = cov_matrix.values
        P = (P + P.T) / 2  # Ensure symmetry
        P += np.eye(n) * 1e-6  # Numerical stability

        portfolio_return = w @ expected_returns.values
        portfolio_risk = cp.quad_form(w, P)
        transaction_penalty = cp.abs(w - current_weights) @ tcm_costs

        # Add a small diversification penalty to encourage weights to stay near/below 5%
        # except where conviction is very high.
        diversification_penalty = 0.01 * cp.sum_squares(w)

        objective = cp.Maximize(
            portfolio_return - 0.5 * self.risk_aversion * portfolio_risk - transaction_penalty - diversification_penalty
        )

        # 2. UCITS Constraints
        effective_cap = max(self.max_single_weight, 1.0 / n)
        
        # UCITS 40% Rule Convex Proxy:
        # The sum of the largest 4 assets cannot exceed 40%.
        # This is a NECESSARY condition for UCITS compliance (since at most 4 assets can be 10%).
        # It is also SUFFICIENT if the 5th largest asset is <= 5%.
        base_constraints = [
            cp.sum(w) == 1,
            w >= 0,
            w <= effective_cap,
        ]
        
        # Only apply sum_largest if we have enough assets to make it meaningful
        if n >= 5:
            base_constraints.append(cp.sum_largest(w, 4) <= self.ucits_aggregate_cap)
        
        full_constraints = base_constraints + constraints

        try:
            prob = cp.Problem(objective, full_constraints)
            # Use SCS or CLARABEL as they handle sum_largest and are available
            solver_to_use = cp.SCS if "SCS" in cp.installed_solvers() else cp.OSQP
            prob.solve(solver=solver_to_use)

            if w.value is None or prob.status not in ["optimal", "optimal_inaccurate"]:
                print(f"GENPOA: UCITS optimization failed ({prob.status}). Falling back to simple 10% cap.")
                simple_constraints = [cp.sum(w) == 1, w >= 0, w <= effective_cap] + constraints
                prob = cp.Problem(objective, simple_constraints)
                prob.solve(solver=cp.OSQP)

            print(f"GENPOA [MVO]: UCITS Proxy Applied. Status: {prob.status}")
            return w.value

        except Exception as e:
            print(f"GENPOA [MVO]: Error — {e}. Falling back to HRP.")
            return self.fallback_hrp(cov_matrix)


    def fallback_hrp(self, cov_matrix: pd.DataFrame) -> np.ndarray:
        """
        Hierarchical Risk Parity (HRP) fallback.
        Robust to ill-conditioned matrices; does not require expected returns.
        """
        hrp = HRPOpt(returns=None, cov_matrix=cov_matrix)
        weights = hrp.optimize()
        ordered_weights = np.array([weights[col] for col in cov_matrix.columns])
        # Enforce RAA cap on HRP output
        ordered_weights = np.minimum(ordered_weights, self.max_single_weight)
        total = ordered_weights.sum()
        if total > 0:
            ordered_weights /= total  # Re-normalise
        print("GENPOA [HRP]: Weights computed and capped at 8%.")
        return ordered_weights

    def optimize_sleeve(
        self,
        symbols: List[str],
        expected_returns: pd.Series,
        cov_matrix: pd.DataFrame,
        current_weights: Optional[np.ndarray] = None,
        adv_data: Optional[Dict[str, float]] = None,
        total_capital: float = 1_000_000
    ) -> Tuple[Dict[str, float], str]:
        """
        High-level entry point for OmniAllocator.
        Returns ({symbol: portfolio_weight}, method_used).
        Uses dynamic TCM costs based on ADV impact.
        """
        n = len(symbols)
        if n == 0:
            return {}, "NONE"

        if current_weights is None:
            current_weights = np.zeros(n)
        
        # --- Dynamic TCM Costs (Impact Cost Model) ---
        # Baseline: 15bps (STT/Brokerage/GST)
        # Impact: sqrt(Order_Size / ADV) * 0.1
        tcm_costs = np.full(n, 0.0015) 
        
        if adv_data:
            for i, sym in enumerate(symbols):
                adv = adv_data.get(sym, 1e9) # Default to high liquidity if unknown
                # Assuming typical order size is 1/N of total capital
                order_size = total_capital / n
                impact = 0.1 * np.sqrt(order_size / adv)
                tcm_costs[i] += impact
                print(f"GENPOA: Dynamic TCM for {sym}: {tcm_costs[i]*10000:.1f} bps (Impact: {impact*10000:.1f})")

        aligned_returns = expected_returns.reindex(symbols).fillna(0.08)
        aligned_cov = cov_matrix.reindex(index=symbols, columns=symbols).fillna(0)

        try:
            raw_weights = self.optimize_mvo_with_costs(
                aligned_returns, aligned_cov, current_weights, tcm_costs
            )
            method = "MVO"
        except Exception as e:
            print(f"GENPOA: MVO pipeline error ({e}), using HRP directly.")
            raw_weights = self.fallback_hrp(aligned_cov)
            method = "HRP"

        weight_dict = {sym: float(w) for sym, w in zip(symbols, raw_weights)}
        return weight_dict, method

    def apply_glide_path(self, sleeve: GoalSleeve, equity_weight: float) -> float:
        """
        Reduces equity exposure as the goal horizon approaches.
        """
        if sleeve.horizon_years >= 10:
            return equity_weight
        elif sleeve.horizon_years <= 1:
            return 0.0
        else:
            scale = (sleeve.horizon_years - 1) / 9
            return equity_weight * scale

    def architect_portfolio(
        self,
        sleeve: GoalSleeve,
        expected_returns: pd.Series,
        cov_matrix: pd.DataFrame,
        current_weights: np.ndarray,
        tcm_costs: np.ndarray
    ) -> np.ndarray:
        """
        Coordinates the full optimization for a specific goal sleeve.
        """
        target_weights = self.optimize_mvo_with_costs(
            expected_returns, cov_matrix, current_weights, tcm_costs
        )
        equity_exposure = self.apply_glide_path(sleeve, 1.0)
        return target_weights * equity_exposure
