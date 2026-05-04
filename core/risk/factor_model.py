import numpy as np
import pandas as pd
from sklearn.covariance import LedoitWolf
from typing import Tuple, Dict, Any

class FactorRiskModel:
    """
    Ex-Ante Factor Risk Model (Layer A).
    Implements Ledoit-Wolf shrinkage and factor risk decomposition.
    Satisfies Section 6.1 of the functional specification.
    """
    def __init__(self, shrinkage_target: str = "ledoit-wolf"):
        self.shrinkage_target = shrinkage_target
        self.lw = LedoitWolf()

    def compute_risk_decomposition(
        self, 
        returns_df: pd.DataFrame, 
        factor_loadings: pd.DataFrame
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Decomposes total risk into Systematic (Factor) and Idiosyncratic risk.
        
        Args:
            returns_df: DataFrame of asset returns (T x N)
            factor_loadings: DataFrame of betas/loadings (N x K)
            
        Returns:
            systematic_cov: N x N systematic covariance matrix
            idiosyncratic_risk: N-length series of stock-specific risk (variance)
        """
        # 1. Ledoit-Wolf Covariance Shrinkage (Total Risk)
        # lw.fit returns the shrunk covariance matrix
        total_cov_matrix = self.lw.fit(returns_df).covariance_
        total_cov = pd.DataFrame(total_cov_matrix, index=returns_df.columns, columns=returns_df.columns)
        
        # 2. Factor Covariance (K x K)
        # We assume the 'returns_df' columns for the factors are provided or implied
        # In a real model, factors are often pre-defined (e.g. Nifty 500 returns)
        # Here we use the covariance of the factors themselves
        factor_cov = returns_df[factor_loadings.columns].cov()
        
        # 3. Systematic Risk (N x N)
        # Systematic = Loading * Factor_Cov * Loading.T
        systematic_cov = factor_loadings.dot(factor_cov).dot(factor_loadings.T)
        
        # 4. Idiosyncratic Risk (N x 1)
        # We only care about assets present in factor_loadings.index
        assets = factor_loadings.index
        total_cov_assets = total_cov.loc[assets, assets]
        
        total_variance = np.diag(total_cov_assets)
        systematic_variance = np.diag(systematic_cov)
        
        # Ensure non-negative idiosyncratic risk (noise reduction)
        idiosyncratic_risk = np.maximum(total_variance - systematic_variance, 0)
        idiosyncratic_series = pd.Series(idiosyncratic_risk, index=assets)
        
        return systematic_cov, idiosyncratic_series

    def calculate_portfolio_risk(
        self, 
        weights: pd.Series, 
        systematic_cov: pd.DataFrame, 
        idiosyncratic_risk: pd.Series
    ) -> Dict[str, float]:
        """
        Calculates the total ex-ante portfolio volatility and its components.
        """
        # Portfolio Systematic Variance
        sys_var = weights.dot(systematic_cov).dot(weights)
        
        # Portfolio Idiosyncratic Variance (Sum of weighted variances)
        idio_var = np.sum((weights**2) * idiosyncratic_risk)
        
        total_var = sys_var + idio_var
        
        return {
            "total_vol": np.sqrt(total_var) * np.sqrt(252), # Annualized
            "systematic_vol": np.sqrt(sys_var) * np.sqrt(252),
            "idiosyncratic_vol": np.sqrt(idio_var) * np.sqrt(252),
            "systematic_contribution": sys_var / total_var
        }
