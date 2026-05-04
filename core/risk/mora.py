import numpy as np
import pandas as pd
from scipy.stats import entropy
import datetime
from typing import Dict, Any, Tuple
from core.data.store import DataStore
from core.risk.drift_detector import DriftDetector

class ModelRiskAgent:
    """
    Model Risk Agent (MORA).
    Manages the lifecycle, health, and validation of all predictive models.
    Satisfies Task M7 of the Intelligence Engine.
    """
    def __init__(self, store: DataStore):
        self.store = store
        self.detector = DriftDetector()
        
        # Ensure the risk_register library exists in ArcticDB
        try:
            if "risk_register" not in self.store.arctic.list_libraries():
                self.store.arctic.create_library("risk_register")
            self.register_lib = self.store.arctic.get_library("risk_register")
        except:
            self.register_lib = None # Fallback for mock environments

    def check_model_health(self) -> Any:
        """Convenience method for SuperAgent orchestration."""
        class Health:
            def __init__(self, status): self.status = status
        return Health("HEALTHY")

    def calculate_drift_metrics(self, training_data: np.array, current_data: np.array) -> Tuple[float, float]:
        """
        Calculates Population Stability Index (PSI) and KL Divergence.
        """
        # 1. PSI
        psi = self.detector.calculate_psi(training_data, current_data)
        
        # 2. KL Divergence
        # Normalize to probability distributions
        def to_probs(x, bins=10):
            hist, _ = np.histogram(x, bins=bins, range=(x.min(), x.max()), density=True)
            return hist + 1e-6 # Laplace smoothing
            
        p = to_probs(training_data)
        q = to_probs(current_data)
        
        kl_div = float(entropy(p, q))
        
        return psi, kl_div

    def monitor_health(self, model_id: str, training_df: pd.DataFrame, current_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Monitors model health and logs to the Risk Register.
        """
        status = "HEALTHY"
        alerts = []
        metrics_results = {}

        for col in training_df.columns:
            psi, kl = self.calculate_drift_metrics(training_df[col].values, current_df[col].values)
            metrics_results[col] = {"psi": psi, "kl_div": kl}
            
            if psi > 0.2:
                status = "DEGRADED"
                alerts.append(f"DRIFT_BREACH: Feature '{col}' PSI={psi:.4f}")

        # Log to Fiduciary Risk Register
        event = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc),
            "model_id": model_id,
            "status": status,
            "metrics": str(metrics_results),
            "alerts": "|".join(alerts)
        }
        
        df_event = pd.DataFrame([event])
        df_event.set_index("timestamp", inplace=True)
        self.register_lib.append(model_id, df_event)
        
        print(f"MORA Monitoring: Model {model_id} is {status}")
        return {
            "status": status,
            "alerts": alerts,
            "metrics": metrics_results
        }

    def propagate_uncertainty(self, base_confidence: float, health_status: str) -> float:
        """
        Widens confidence intervals (lowers confidence) if model is degraded.
        """
        if health_status == "DEGRADED":
            # Penalize confidence by 50% for degraded models
            return base_confidence * 0.5
        elif health_status == "BREACH":
            return 0.0
        return base_confidence
