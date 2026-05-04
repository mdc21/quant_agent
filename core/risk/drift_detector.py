import numpy as np
import pandas as pd
from typing import Dict

class DriftDetector:
    """
    Monitors model risk via Population Stability Index (PSI).
    Satisfies Layer 1 and Layer 4 Model Risk requirements.
    """
    @staticmethod
    def calculate_psi(expected: np.array, actual: np.array, buckets: int = 10) -> float:
        """
        Calculates the Population Stability Index (PSI) between two distributions.
        - PSI < 0.1: No significant shift.
        - 0.1 <= PSI < 0.2: Moderate shift (monitor).
        - PSI >= 0.2: Significant shift (Degraded status).
        """
        def scale_by_range(x, min_val, max_val):
            return (x - min_val) / (max_val - min_val + 1e-6)

        min_val = min(expected.min(), actual.min())
        max_val = max(expected.max(), actual.max())

        expected_scaled = scale_by_range(expected, min_val, max_val)
        actual_scaled = scale_by_range(actual, min_val, max_val)

        # Create buckets
        expected_percents = np.histogram(expected_scaled, bins=buckets, range=(0, 1))[0] / len(expected)
        actual_percents = np.histogram(actual_scaled, bins=buckets, range=(0, 1))[0] / len(actual)

        # Avoid division by zero
        expected_percents = np.where(expected_percents == 0, 1e-6, expected_percents)
        actual_percents = np.where(actual_percents == 0, 1e-6, actual_percents)

        psi = np.sum((expected_percents - actual_percents) * np.log(expected_percents / actual_percents))
        return float(psi)

    def check_feature_drift(self, train_df: pd.DataFrame, current_df: pd.DataFrame) -> Dict[str, float]:
        """
        Checks for drift across all features.
        """
        results = {}
        for col in train_df.columns:
            psi = self.calculate_psi(train_df[col].values, current_df[col].values)
            results[col] = psi
            
            if psi >= 0.2:
                print(f"ALERT: Significant Drift detected in feature '{col}' (PSI: {psi:.4f})")
        
        return results
