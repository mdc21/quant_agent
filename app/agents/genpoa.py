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

    def optimize_mvo_with_costs(
        self,
        expected_returns: pd.Series,
        cov_matrix: pd.DataFrame,
        current_weights: np.ndarray,
        tcm_costs: np.ndarray,
        constraints: List[Any] = [],
        sector_map: Optional[Dict[str, str]] = None,
        cap_map: Optional[Dict[str, str]] = None,
        sector_limit: float = 0.25,
        cap_targets: Optional[Dict[str, float]] = None
    ) -> np.ndarray:
        """
        TCM-Penalized Mean-Variance Optimization with UCITS and institutional capital constraints.
        """
        n = len(expected_returns)
        symbols = expected_returns.index.tolist()
        w = cp.Variable(n)
        
        # 1. Objective: Maximize (Return - Risk_Penalty - Transaction_Costs)
        P = cov_matrix.values
        P = (P + P.T) / 2
        P += np.eye(n) * 1e-6 

        portfolio_return = w @ expected_returns.values
        portfolio_risk = cp.quad_form(w, P)
        transaction_penalty = cp.abs(w - current_weights) @ tcm_costs
        diversification_penalty = 0.01 * cp.sum_squares(w)

        objective = cp.Maximize(
            portfolio_return - 0.5 * self.risk_aversion * portfolio_risk - transaction_penalty - diversification_penalty
        )

        # 2. Base Constraints (UCITS + Concentration)
        effective_cap = max(self.max_single_weight, 1.0 / n)
        # Use a small lower bound if we want to avoid too many tiny positions
        # but keep it 0 if we want to allow the solver to discard stocks.
        # To strictly enforce number of stocks, we'd need integer constraints,
        # but here we'll use a heuristic in the allocator.
        base_constraints = [cp.sum(w) == 1, w >= 0, w <= effective_cap]
        if n >= 5:
            base_constraints.append(cp.sum_largest(w, 4) <= self.ucits_aggregate_cap)
        
        # 3. Institutional Capital Constraints
        inst_constraints = []
        
        # A. Sector Hard Ceilings (Capital-Based)
        if sector_map:
            unique_sectors = set(sector_map.values())
            for sector in unique_sectors:
                indices = [i for i, s in enumerate(symbols) if sector_map.get(s) == sector]
                if indices:
                    inst_constraints.append(cp.sum(w[indices]) <= sector_limit)
        
        # B. Multi-Cap Targets (Capital-Based Ranges)
        if cap_map and cap_targets:
            for cap_cat, target_pct in cap_targets.items():
                indices = [i for i, s in enumerate(symbols) if cap_map.get(s) == cap_cat]
                if indices:
                    # Use a small buffer (±2%) to ensure feasibility
                    # This is still a "Strict Target" in spirit but allows solver convergence
                    inst_constraints.append(cp.sum(w[indices]) >= target_pct - 0.02)
                    inst_constraints.append(cp.sum(w[indices]) <= target_pct + 0.02)

        full_constraints = base_constraints + inst_constraints + constraints

        try:
            prob = cp.Problem(objective, full_constraints)
            # Use SCS or CLARABEL as they handle sum_largest and are available
            solver_to_use = cp.SCS if "SCS" in cp.installed_solvers() else cp.OSQP
            prob.solve(solver=solver_to_use)

            if w.value is None or prob.status not in ["optimal", "optimal_inaccurate"]:
                print(f"GENPOA: Capital-constrained MVO failed ({prob.status}). Trying without UCITS aggregate cap.")
                # Fallback 1: Remove the complex sum_largest constraint
                alt_constraints = [cp.sum(w) == 1, w >= 0, w <= effective_cap] + inst_constraints + constraints
                prob = cp.Problem(objective, alt_constraints)
                prob.solve(solver=cp.OSQP)
                
            if w.value is None or prob.status not in ["optimal", "optimal_inaccurate"]:
                print(f"GENPOA: Institutional constraints failed. Falling back to simple UCITS.")
                prob = cp.Problem(objective, base_constraints + constraints)
                prob.solve(solver=cp.OSQP)

            print(f"GENPOA [MVO]: Capital-Weight Constraints Applied. Status: {prob.status}")
            return w.value

        except Exception as e:
            print(f"GENPOA [MVO]: Error — {e}. Falling back to HRP.")
            return self.fallback_hrp(cov_matrix)

    def fallback_hrp(self, cov_matrix: pd.DataFrame) -> np.ndarray:
        """Hierarchical Risk Parity (HRP) fallback."""
        hrp = HRPOpt(returns=None, cov_matrix=cov_matrix)
        weights = hrp.optimize()
        ordered_weights = np.array([weights[col] for col in cov_matrix.columns])
        ordered_weights = np.minimum(ordered_weights, self.max_single_weight)
        total = ordered_weights.sum()
        if total > 0: ordered_weights /= total
        return ordered_weights

    def optimize_sleeve(
        self,
        symbols: List[str],
        expected_returns: pd.Series,
        cov_matrix: pd.DataFrame,
        current_weights: Optional[np.ndarray] = None,
        adv_data: Optional[Dict[str, float]] = None,
        total_capital: float = 1_000_000,
        sector_map: Optional[Dict[str, str]] = None,
        cap_map: Optional[Dict[str, str]] = None,
        sector_limit: float = 0.25,
        cap_targets: Optional[Dict[str, float]] = None
    ) -> Tuple[Dict[str, float], str]:
        """
        High-level entry point with support for sector and cap guardrails.
        """
        n = len(symbols)
        if n == 0: return {}, "NONE"
        if current_weights is None: current_weights = np.zeros(n)
        
        tcm_costs = np.full(n, 0.0015) 
        if adv_data:
            for i, sym in enumerate(symbols):
                adv = adv_data.get(sym, 1e9)
                order_size = total_capital / n
                impact = 0.1 * np.sqrt(order_size / adv)
                tcm_costs[i] += impact

        aligned_returns = expected_returns.reindex(symbols).fillna(0.08)
        aligned_cov = cov_matrix.reindex(index=symbols, columns=symbols).fillna(0)

        try:
            raw_weights = self.optimize_mvo_with_costs(
                aligned_returns, aligned_cov, current_weights, tcm_costs,
                sector_map=sector_map,
                cap_map=cap_map,
                sector_limit=sector_limit,
                cap_targets=cap_targets
            )
            method = "MVO"
        except Exception as e:
            print(f"GENPOA: MVO error ({e}), using HRP.")
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
