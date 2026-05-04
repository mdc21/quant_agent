import pandas as pd
import numpy as np
from core.models.forecaster import ReturnForecaster

def test_forecaster_logic():
    print("--- Starting Return Forecaster (Black-Litterman) Test ---")
    
    # 1. Setup Mock Data (3 assets)
    assets = ['RELIANCE', 'TCS', 'HDFCBANK']
    prices = pd.Series([2500, 3400, 1600], index=assets)
    
    # Mock Covariance (Ledoit-Wolf like)
    cov = pd.DataFrame([
        [0.0004, 0.0001, 0.0001],
        [0.0001, 0.0003, 0.0001],
        [0.0001, 0.0001, 0.0005]
    ], index=assets, columns=assets)
    
    forecaster = ReturnForecaster(delta=2.5)
    
    # 2. Test Confidence Sensitivity
    # View: RELIANCE will return 20%
    # Test A: Low Confidence (0.1)
    view_low = {'RELIANCE': (0.20, 0.1)}
    returns_low = forecaster.compute_posterior_returns(cov, prices, view_low)
    
    # Test B: High Confidence (0.9)
    view_high = {'RELIANCE': (0.20, 0.9)}
    returns_high = forecaster.compute_posterior_returns(cov, prices, view_high)
    
    print(f"\nRELIANCE Expected Return (Low Conf 0.1): {returns_low['RELIANCE']:.2%}")
    print(f"RELIANCE Expected Return (High Conf 0.9): {returns_high['RELIANCE']:.2%}")
    
    if returns_high['RELIANCE'] > returns_low['RELIANCE']:
        print("Success: Higher confidence correctly pulls posterior closer to the view.")
    
    # 3. Test Regime Scaling
    # Bull Regime (Multiplier 1.2)
    bull_returns = forecaster.compute_posterior_returns(cov, prices, view_high, regime_multiplier=1.2)
    # Bear Regime (Multiplier 0.7)
    bear_returns = forecaster.compute_posterior_returns(cov, prices, view_high, regime_multiplier=0.7)
    
    print(f"\nOverall Return (Bull Regime): {bull_returns.mean():.2%}")
    print(f"Overall Return (Bear Regime): {bear_returns.mean():.2%}")
    
    if bear_returns.mean() < bull_returns.mean():
        print("Success: Regime multiplier correctly recalibrates the final returns.")

if __name__ == "__main__":
    test_forecaster_logic()
