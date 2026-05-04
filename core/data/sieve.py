import pandas as pd
import numpy as np

class DataSieve:
    """
    Identifies price and fundamental anomalies before they are committed to the golden store.
    Satisfies institutional data quality requirements.
    """
    def __init__(self, threshold_std: float = 4.0, max_pct_jump: float = 0.15):
        self.threshold_std = threshold_std  # Standard deviations for Z-score
        self.max_pct_jump = max_pct_jump    # Hard cap (e.g., 15% jump in 1 min)

    def detect_outliers(self, df: pd.DataFrame) -> pd.Series:
        """
        Flags anomalies in the price series. 
        Returns a boolean mask where True = Valid, False = Outlier.
        """
        if df.empty or 'close' not in df.columns:
            return pd.Series(dtype=bool)

        # 1. Percentage Change Check (compared to previous row)
        pct_change = df['close'].pct_change().abs()
        pct_mask = (pct_change < self.max_pct_jump) | pct_change.isna()

        # 2. Statistical Z-Score Check (rolling window)
        rolling_mean = df['close'].rolling(window=20).mean()
        rolling_std = df['close'].rolling(window=20).std()
        
        rolling_std = rolling_std.replace(0, np.nan)
        z_score = (df['close'] - rolling_mean) / rolling_std
        z_mask = (z_score.abs() < self.threshold_std) | z_score.isna()

        # 3. Combine Masks
        valid_mask = pct_mask & z_mask
        
        return valid_mask
