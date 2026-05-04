import pandas as pd
import numpy as np
from typing import List, Optional
from core.data.store import DataStore

class FeatureEngineer:
    """
    Generates quantitative features for the Intelligence Engine (Layer 1).
    Focuses on Volatility, Momentum, and Dispersion.
    """
    def __init__(self, store: DataStore):
        self.store = store

    def get_regime_features(self, symbol: str) -> pd.DataFrame:
        """
        Calculates features required for the Task M1 Regime Classifier.
        Adapted for 1-minute high-frequency data.
        """
        df = self.store.read_symbol(symbol)
        if df.empty:
            return pd.DataFrame()

        # Work with 1-minute data directly to ensure we have enough points
        df_feat = df['close'].to_frame()

        # 1. Volatility (Short-term and Long-term 1-min vol)
        # Using 20-min and 60-min windows for demonstration
        df_feat['vol_21d'] = df_feat['close'].pct_change().rolling(window=20).std() 
        df_feat['vol_63d'] = df_feat['close'].pct_change().rolling(window=60).std() 

        # 2. Momentum (60-min vs 20-min)
        df_feat['mom_12_1m'] = (df_feat['close'].shift(20) / df_feat['close'].shift(60)) - 1

        # 3. Returns (1-min log returns)
        df_feat['returns'] = np.log(df_feat['close'] / df_feat['close'].shift(1))

        # Drop NaN rows from rolling windows
        return df_feat.dropna()

    def get_factor_loadings(self, symbol: str) -> pd.Series:
        """
        Computes the sensitivity of a stock to the 5 primary risk factors.
        Market, Momentum, Quality, Value, Low-Volatility.
        """
        # In a real system, these would be pulled from fundamental and price data
        # Here we provide a simplified version based on available data
        
        loadings = {
            "Market": 1.0, # Beta to market (default 1.0)
            "Momentum": np.random.normal(0.5, 0.2), # Placeholder logic
            "Quality": 1.0 if np.random.rand() > 0.5 else 0.0, # e.g. F-Score > 7
            "Value": np.random.normal(0.0, 0.5), # e.g. P/E relative
            "Low-Volatility": np.random.normal(0.2, 0.1)
        }
        return pd.Series(loadings)

    def get_adv(self, symbol: str, window: int = 30) -> float:
        """
        Calculates the Average Daily Volume (ADV) over a specified window.
        Used for market impact estimation.
        """
        df = self.store.read_symbol(symbol)
        if df.empty or 'volume' not in df.columns:
            return 0.0
            
        # Resample to daily and take the mean of volume
        adv = df['volume'].resample('D').sum().rolling(window=window).mean().iloc[-1]
        return float(adv)

    def get_dispersion(self, symbols: List[str]) -> pd.Series:
        """
        Calculates cross-sectional volatility (Dispersion) for a universe.
        """
        # Fetch data for all symbols
        universe_data = {}
        for s in symbols:
            df = self.store.read_symbol(s)
            if not df.empty:
                universe_data[s] = df['close'].resample('D').last().pct_change()
        
        df_univ = pd.DataFrame(universe_data)
        return df_univ.std(axis=1) # Cross-sectional std
