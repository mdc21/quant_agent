import pandas as pd
import numpy as np
from core.risk.factor_model import FactorRiskModel
from core.risk.risk_report import RiskReporter

def test_factor_risk_logic():
    print("--- Starting Factor Risk Model Test ---")
    
    # 1. Simulate Portfolio Returns (5 stocks, 252 days)
    np.random.seed(42)
    assets = ['STK_1', 'STK_2', 'STK_3', 'STK_4', 'STK_5']
    factors = ['Market', 'Momentum', 'Quality', 'Value', 'Low-Volatility']
    
    returns_data = np.random.normal(0.0005, 0.01, (252, 5))
    # Add some high correlation to test shrinkage
    returns_data[:, 0] = returns_data[:, 1] * 0.9 + np.random.normal(0, 0.001, 252)
    
    returns_df = pd.DataFrame(returns_data, columns=assets)
    
    # Simulate Factor Returns (for risk decomposition)
    factor_returns = pd.DataFrame(np.random.normal(0.0005, 0.012, (252, 5)), columns=factors)
    full_returns = pd.concat([returns_df, factor_returns], axis=1)
    
    # 2. Simulate Factor Loadings (Betas)
    loadings_data = np.random.normal(1.0, 0.2, (5, 5))
    loadings_df = pd.DataFrame(loadings_data, index=assets, columns=factors)
    
    # 3. Compute Risk Decomposition
    model = FactorRiskModel()
    sys_cov, idio_risk = model.compute_risk_decomposition(full_returns, loadings_df)
    
    # 4. Verify Reconciliation (Total Vol = Sys + Idio)
    weights = pd.Series([0.2, 0.2, 0.2, 0.2, 0.2], index=assets)
    risk_metrics = model.calculate_portfolio_risk(weights, sys_cov, idio_risk)
    
    print(f"\nPortfolio Total Vol (Ex-Ante): {risk_metrics['total_vol']:.2f}%")
    print(f"Systematic Contribution: {risk_metrics['systematic_contribution']:.1%}")
    
    # 5. Generate Exposure Report
    reporter = RiskReporter(limit_threshold=0.30)
    portfolio_exposure = weights.dot(loadings_df)
    benchmark_exposure = pd.Series([1.0, 0.5, 0.5, 0.5, 0.5], index=factors)
    
    reporter.generate_factor_exposure_report(portfolio_exposure, benchmark_exposure)

if __name__ == "__main__":
    test_factor_risk_logic()
