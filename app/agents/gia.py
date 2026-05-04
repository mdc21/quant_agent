import numpy as np
from typing import List, Dict, Any
from core.data.agent_schema import GoalSleeve, GoalMesh

class GoalInterpretationAgent:
    """
    Goal Interpretation Agent (GIA).
    Translates user desires into a mathematical objective function.

    Each goal sleeve has its own return/volatility assumption that
    reflects its mandated asset class — not a flat equity assumption.

    Sleeve parameters (annualised):
      Tier 1 — Survival  : Liquid Fund / FD     → 6.5% return, 0.5% vol
      Tier 2 — Safety    : Balanced / Debt ETF   → 9.0% return, 8.0% vol
      Tier 3 — Growth    : Direct Equity / ETF   → 13.0% return, 18.0% vol
    """

    # ── Per-tier Monte Carlo assumptions ─────────────────────────────────────
    _TIER_PARAMS = {
        1: {"label": "Survival",  "return": 0.065, "vol": 0.005},   # Liquid / FD
        2: {"label": "Safety",    "return": 0.09,  "vol": 0.08},    # Balanced / Debt
        3: {"label": "Growth",    "return": 0.13,  "vol": 0.18},    # Equity / Alpha
    }

    # ── Minimum probability of success per tier ───────────────────────────────
    _TIER_THRESHOLDS = {
        1: 0.99,   # Survival — non-negotiable floor
        2: 0.95,   # Safety   — retirement corpus needs near-certainty
        3: 0.70,   # Growth   — alpha-seeking; accepts higher risk
    }

    def __init__(self, inflation_rate: float = 0.06):
        self.inflation_rate = inflation_rate

    def interpret_goals(self, user_id: str) -> List[Any]:
        """Fetches user goals from the DataStore and converts them to GoalSleeves."""
        from core.data.store import DataStore
        store = DataStore()
        user_data = store.get_goals(user_id)

        if not user_data:
            print(f"GIA: No goals found for user {user_id}. Returning empty mesh.")
            return []
            
        # Update inflation rate from stored metadata
        self.inflation_rate = user_data.get("inflation_rate", self.inflation_rate)

        mesh = self.interpret_user_goals(user_data)
        return mesh.sleeves

    def interpret_user_goals(self, raw_input: Dict[str, Any]) -> GoalMesh:
        """Main entry point to build the Goal Mesh."""
        sleeves = []
        for g in raw_input.get("goals", []):
            # Inflation adjustment: FV = PV × (1+i)^n
            fv_target = g["target_pv"] * ((1 + self.inflation_rate) ** g["horizon"])

            sleeve = GoalSleeve(
                label=g["label"],
                tier=g["tier"],
                target_value=fv_target,
                horizon_years=g["horizon"],
                min_prob_success=self._TIER_THRESHOLDS.get(g["tier"], 0.70),
                constraints=g.get("constraints", []),
                current_assets=g.get("current_assets", 0.0),
                monthly_savings=g.get("monthly_savings", 0.0)
            )
            sleeves.append(sleeve)

        return GoalMesh(
            sleeves=sleeves,
            user_risk_tolerance=raw_input.get("risk_tolerance", "Moderate")
        )

    def get_tier_threshold(self, tier: int) -> float:
        """Returns the mandatory success probability for each tier."""
        return self._TIER_THRESHOLDS.get(tier, 0.70)

    def run_feasibility_check(self, sleeve: GoalSleeve, num_paths: int = 1000) -> Dict[str, Any]:
        """
        Monte Carlo feasibility check with sleeve-specific return/vol assumptions.

        Survival  → liquid fund params  → should show ~99% with FD-like certainty
        Safety    → balanced/debt params → retirement corpus modelling
        Growth    → equity params        → alpha-seeking with meaningful downside risk
        """
        params = self._TIER_PARAMS.get(sleeve.tier, self._TIER_PARAMS[3])
        mu  = params["return"]
        sig = params["vol"]

        # Log-normal monthly returns: r_t ~ μ - ½σ² + σ·ε
        dt = 1 / 12
        monthly_shocks = (
            (mu - 0.5 * sig**2) * dt
            + sig * np.sqrt(dt) * np.random.normal(0, 1, (num_paths, sleeve.horizon_years * 12))
        )

        paths = np.zeros((num_paths, sleeve.horizon_years * 12 + 1))
        paths[:, 0] = sleeve.current_assets

        for t in range(1, sleeve.horizon_years * 12 + 1):
            paths[:, t] = paths[:, t-1] * np.exp(monthly_shocks[:, t-1]) + sleeve.monthly_savings

        final_values = paths[:, -1]
        p_success    = float(np.mean(final_values >= sleeve.target_value))
        is_feasible  = p_success >= sleeve.min_prob_success

        return {
            "label":          sleeve.label,
            "p_success":      p_success,
            "is_feasible":    is_feasible,
            "median_outcome": float(np.median(final_values)),
            "target_value":   sleeve.target_value,
            "asset_mandate":  params["label"],  # surfaced in UI for transparency
        }

