import os
from dotenv import load_dotenv
import pandas as pd
import numpy as np
from core.data.store import DataStore
from core.features.engineer import FeatureEngineer
from core.models.regime_classifier import MarketRegimeClassifier
from core.risk.drift_detector import DriftDetector

# Load environment variables
load_dotenv()

def run_regime_training():
    print("--- Starting Market Regime Classifier Training ---")
    
    # 1. Initialize Components
    store = DataStore(uri="lmdb://./data/arctic")
    engineer = FeatureEngineer(store)
    classifier = MarketRegimeClassifier(n_regimes=4)
    detector = DriftDetector()
    
    # 2. Fetch Data & Engineer Features
    # Using Nifty 50 or a liquid proxy for market regime
    symbol = "RELIND" # Using RELIANCE as a proxy for now, but usually NIFTY_50
    features = engineer.get_regime_features(symbol)
    
    if features.empty:
        print(f"Error: No features generated for {symbol}. Ensure Layer 0 has enough historical data.")
        return

    # 3. Training/Test Split for Drift Baseline
    train_data = features.iloc[:-200] # All but last 200 mins
    current_data = features.iloc[-200:] # Last 200 mins
    
    # 4. Check for Drift Before Training
    print("Checking for feature drift...")
    drift_results = detector.check_feature_drift(train_data[['vol_21d', 'vol_63d']], current_data[['vol_21d', 'vol_63d']])
    
    # 5. Execute Ensemble Training
    classifier.train_ensemble(features)
    
    # 6. Sample Prediction
    latest_features = features[['vol_21d', 'vol_63d', 'mom_12_1m']].iloc[-1].values
    probs = classifier.predict_regime_probs(latest_features)
    
    print("\n--- Model Output: Regime Probability Vector ---")
    for i, prob in enumerate(probs[0]):
        regime_name = classifier.regime_names.get(i, f"State_{i}")
        print(f"{regime_name}: {prob:.2%}")

if __name__ == "__main__":
    run_regime_training()
