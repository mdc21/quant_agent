import numpy as np
from typing import List, Dict, Any
from core.data.agent_schema import GoalSleeve, GoalMesh

class GoalInterpretationAgent:
    """
    Goal Interpretation Agent (GIA).
    Translates user desires into a mathematical objective function.
    Satisfies Task A1 of the Agent Mesh.
    """
    def __init__(self, inflation_rate: float = 0.06):
        self.inflation_rate = inflation_rate

    def interpret_goals(self, user_id: str) -> List[Any]:
        """
        Fetches user goals from the DataStore and converts them to GoalSleeves.
        """
        from core.data.store import DataStore
        store = DataStore()
        user_data = store.get_goals(user_id)
        
        if not user_data:
            print(f"GIA: No goals found for user {user_id}. Returning empty mesh.")
            # Fallback to a single placeholder goal if completely empty to avoid crash
            return []
            
        mesh = self.interpret_user_goals(user_data)
        return mesh.sleeves


    def interpret_user_goals(self, raw_input: Dict[str, Any]) -> GoalMesh:
        """
        Main entry point to build the Goal Mesh.
        """
        sleeves = []
        for g in raw_input.get("goals", []):
            # 1. Inflation Adjustment (FV = PV * (1+i)^n)
            fv_target = g["target_pv"] * ((1 + self.inflation_rate) ** g["horizon"])
            
            sleeve = GoalSleeve(
                label=g["label"],
                tier=g["tier"],
                target_value=fv_target,
                horizon_years=g["horizon"],
                min_prob_success=self.get_tier_threshold(g["tier"]),
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
        """
        Returns the mandatory success probability for each tier.
        """
        mapping = {1: 0.99, 2: 0.85, 3: 0.60}
        return mapping.get(tier, 0.60)

    def run_feasibility_check(self, sleeve: GoalSleeve, num_paths: int = 1000) -> Dict[str, Any]:
        """
        Performs a Monte Carlo simulation to check if a goal is achievable.
        """
        # Assumptions for the baseline check
        # Moderate portfolio return ~10%, vol ~15%
        expected_return = 0.10
        volatility = 0.15
        
        # Simulate paths
        dt = 1/12
        monthly_ret = (expected_return - 0.5 * volatility**2) * dt + \
                      volatility * np.sqrt(dt) * np.random.normal(0, 1, (num_paths, sleeve.horizon_years * 12))
        
        # Compound returns and add savings
        paths = np.zeros((num_paths, sleeve.horizon_years * 12 + 1))
        paths[:, 0] = sleeve.current_assets
        
        for t in range(1, sleeve.horizon_years * 12 + 1):
            paths[:, t] = paths[:, t-1] * np.exp(monthly_ret[:, t-1]) + sleeve.monthly_savings
            
        final_values = paths[:, -1]
        p_success = np.mean(final_values >= sleeve.target_value)
        
        is_feasible = p_success >= sleeve.min_prob_success
        
        return {
            "label": sleeve.label,
            "p_success": p_success,
            "is_feasible": is_feasible,
            "median_outcome": np.median(final_values)
        }
