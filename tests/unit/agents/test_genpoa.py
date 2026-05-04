import numpy as np
import pandas as pd
from app.agents.genpoa import PortfolioArchitect
from core.data.agent_schema import GoalSleeve

def test_genpoa_logic():
    print("--- Starting Portfolio Construction Agent (GENPOA) Test ---")
    
    architect = PortfolioArchitect(risk_aversion=2.5)
    symbols = ["RELIND", "TCS", "HDFC", "CASH"]
    n = len(symbols)
    
    # 1. Setup Mock Inputs
    expected_returns = pd.Series([0.15, 0.12, 0.10, 0.05], index=symbols)
    
    # Positive definite covariance matrix
    cov_data = np.array([
        [0.04, 0.02, 0.01, 0.00],
        [0.02, 0.04, 0.02, 0.00],
        [0.01, 0.02, 0.04, 0.00],
        [0.00, 0.00, 0.00, 0.01]
    ])
    cov_matrix = pd.DataFrame(cov_data, index=symbols, columns=symbols)
    
    current_weights = np.array([0.25, 0.25, 0.25, 0.25])
    tcm_costs = np.array([0.01, 0.01, 0.01, 0.00]) # 1% cost to move in equity
    
    # 2. Churn Limit Test
    # First, find the optimal weights for the base case to use as 'current_weights'
    print("\n[Scenario: Baseline Optimization]")
    w_base = architect.optimize_mvo_with_costs(
        expected_returns, cov_matrix, current_weights, np.zeros(n) # No cost for base
    )
    print(f"Baseline Optimal Weights: {w_base}")
    
    # Scenario: Expected returns are only slightly better than cost
    # We increase return for TCS by only 0.2% (less than 1% cost)
    print("\n[Scenario: Low Benefit vs High Cost]")
    small_benefit_rets = expected_returns.copy()
    small_benefit_rets["TCS"] += 0.002 # 0.2% improvement
    
    target_low_benefit = architect.optimize_mvo_with_costs(
        small_benefit_rets, cov_matrix, w_base, tcm_costs
    )
    
    # Check if weights moved significantly from w_base
    diff = np.abs(target_low_benefit - w_base).sum()
    print(f"Total Weight Change (Churn) from Base: {diff:.6f}")
    if diff < 1e-4:
        print("Success: Churn penalty prevented unnecessary trading for marginal gains.")

    # 3. Glide-Path Validation
    print("\n[Scenario: Glide-Path Shifting]")
    # 20-year Retirement Goal
    sleeve_long = GoalSleeve(label="Retirement", tier=2, target_value=1e8, horizon_years=20, min_prob_success=0.85, constraints=[])
    w_long = architect.architect_portfolio(sleeve_long, expected_returns, cov_matrix, current_weights, tcm_costs)
    
    # 2-year Education Goal
    sleeve_short = GoalSleeve(label="Education", tier=1, target_value=1e6, horizon_years=2, min_prob_success=0.99, constraints=[])
    w_short = architect.architect_portfolio(sleeve_short, expected_returns, cov_matrix, current_weights, tcm_costs)
    
    print(f"Long-term Equity Exposure: {w_long.sum():.1%}")
    print(f"Short-term Equity Exposure: {w_short.sum():.1%}")
    
    if w_short.sum() < w_long.sum() * 0.5:
        print("Success: Glide-path correctly reduced risk for short-term goal.")

    # 4. HRP Fallback Trigger
    print("\n[Scenario: HRP Fallback]")
    # Singular matrix (columns 0 and 1 are identical)
    singular_cov = cov_matrix.copy()
    singular_cov.iloc[:, 1] = singular_cov.iloc[:, 0]
    
    w_hrp = architect.optimize_mvo_with_costs(expected_returns, singular_cov, current_weights, tcm_costs)
    print(f"HRP Weights Generated: {w_hrp}")
    if w_hrp is not None:
        print("Success: System successfully fell back to HRP on singular matrix.")

if __name__ == "__main__":
    test_genpoa_logic()
