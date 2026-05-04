import numpy as np
import pandas as pd
from hmmlearn.hmm import GaussianHMM
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import mlflow
import mlflow.sklearn

class MarketRegimeClassifier:
    """
    Champion/Challenger Ensemble (HMM + RandomForest) for Market Regime Detection.
    Using RandomForest as a robust alternative to XGBoost for cross-platform compatibility.
    """
    def __init__(self, n_regimes: int = 4):
        self.n_regimes = n_regimes
        self.hmm_model = GaussianHMM(
            n_components=n_regimes, 
            covariance_type="diag", # More stable than "full" for small data
            n_iter=1000,
            random_state=42,
            min_covar=1e-3 # Prevents non-positive-definite errors
        )
        self.clf_model = None
        self.regime_names = {0: "Bear", 1: "Sideways", 2: "Bull", 3: "Stagflation"}

    def train_hmm(self, features: pd.DataFrame):
        X = features[['vol_21d', 'returns']].values
        self.hmm_model.fit(X)
        states = self.hmm_model.predict(X)
        return states

    def train_ensemble(self, features: pd.DataFrame):
        with mlflow.start_run(run_name="Regime_Ensemble_Train"):
            # 1. Discover States with HMM
            states = self.train_hmm(features)
            features['state'] = states
            
            # 2. Prepare Supervised Learning
            X = features[['vol_21d', 'vol_63d', 'mom_12_1m']].values
            y = states
            
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # 3. Train RandomForest Challenger (No libomp required)
            self.clf_model = RandomForestClassifier(
                n_estimators=100,
                max_depth=5,
                random_state=42
            )
            self.clf_model.fit(X_train, y_train)
            
            # 4. Log to MLflow
            mlflow.log_param("n_regimes", self.n_regimes)
            mlflow.log_metric("accuracy", self.clf_model.score(X_test, y_test))
            mlflow.sklearn.log_model(self.clf_model, "regime_rf_model")
            
            print(f"Model trained (RandomForest). Test Accuracy: {self.clf_model.score(X_test, y_test):.2f}")

    def predict_regime_probs(self, current_features: np.array) -> np.array:
        if self.clf_model is None:
            raise ValueError("Model not trained yet.")
        
        return self.clf_model.predict_proba(current_features.reshape(1, -1))

    def get_regime_multiplier(self, probs: np.array) -> float:
        """
        Calculates a 'Shrinkage to Cash' multiplier based on the regime probability vector.
        - Bear/Stagflation: Multiplier < 1.0 (Defensive)
        - Bull: Multiplier > 1.0 (Aggressive)
        """
        # Map indices to impact factors
        # 0: Bear (0.7), 1: Sideways (1.0), 2: Bull (1.2), 3: Stagflation (0.8)
        impact_map = {0: 0.7, 1: 1.0, 2: 1.2, 3: 0.8}
        
        multiplier = 0.0
        for i, prob in enumerate(probs[0]):
            multiplier += prob * impact_map.get(i, 1.0)
            
        return multiplier
