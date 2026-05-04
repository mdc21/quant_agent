import pandas as pd
import numpy as np
from pypfopt import black_litterman
from typing import Dict, Tuple, Optional

class ReturnForecaster:
    """
    Synthesizes Market Equilibrium with Active Agent Views.
    Implements Task M3: The Return Forecaster using Black-Litterman.
    """
    def __init__(self, delta: float = 2.5):
        self.delta = delta # Risk aversion coefficient

    def compute_posterior_returns(
        self, 
        cov_matrix: pd.DataFrame, 
        market_prices: pd.Series, 
        agent_views: Dict[str, Tuple[float, float]],
        regime_multiplier: float = 1.0
    ) -> pd.Series:
        """
        Calculates Black-Litterman posterior returns.
        
        Args:
            cov_matrix: Ledoit-Wolf shrunk covariance matrix (N x N)
            market_prices: Series of latest prices for assets (N)
            agent_views: Dict mapping symbol to (expected_return, confidence)
            regime_multiplier: Factor from M1 to scale final returns
            
        Returns:
            posterior_returns: Series of forward-looking returns (N)
        """
        # 1. Calculate Market Prior (Equilibrium Returns)
        # BACKING OUT what the market expects based on current weights
        market_prior = black_litterman.market_implied_prior_returns(
            market_prices, 
            self.delta, 
            cov_matrix
        )
        
        # 2. Extract Views and Confidences
        view_dict = {s: r for s, (r, c) in agent_views.items()}
        
        # 3. Handle Confidence (Omega) using Idzorek's method
        view_confidences = [c for s, (r, c) in agent_views.items()]
        
        bl = black_litterman.BlackLittermanModel(
            cov_matrix, 
            pi=market_prior, 
            absolute_views=view_dict,
            omega="idzorek",
            view_confidences=view_confidences
        )
        
        # 4. Calculate Posterior
        posterior_returns = bl.bl_returns()
        
        # 5. Regime-Conditional Recalibration
        # Apply 'Shrinkage to Cash' or 'Aggressive Scaling'
        final_returns = posterior_returns * regime_multiplier
        
        return final_returns
