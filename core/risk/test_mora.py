import pandas as pd
import numpy as np
from core.risk.mora import ModelRiskAgent
from core.data.store import DataStore

def test_mora_logic():
    print("--- Starting Model Risk Agent (MORA) Test ---")
    
    store = DataStore()
    mora = ModelRiskAgent(store)
    
    # 1. Setup Mock Training and Current Data
    # Feature: Volatility
    np.random.seed(42)
    training_data = pd.DataFrame({
        "vol_21d": np.random.normal(0.01, 0.002, 1000)
    })
    
    # Healthy Current Data
    current_data_healthy = pd.DataFrame({
        "vol_21d": np.random.normal(0.01, 0.002, 200)
    })
    
    # Degraded Data (Radically different volatility)
    current_data_drifted = pd.DataFrame({
        "vol_21d": np.random.normal(0.05, 0.01, 200) # 5x higher mean
    })
    
    # 2. Test Healthy Monitoring
    print("\n[Scenario: Healthy Market Data]")
    health_healthy = mora.monitor_health("RegimeClassifier_v1", training_data, current_data_healthy)
    print(f"Status: {health_healthy['status']}")
    
    # 3. Test Drift Detection (PSI Breach)
    print("\n[Scenario: Radical Market Drift]")
    health_drifted = mora.monitor_health("RegimeClassifier_v1", training_data, current_data_drifted)
    print(f"Status: {health_drifted['status']}")
    for alert in health_drifted['alerts']:
        print(f"ALERT: {alert}")
        
    if health_drifted['status'] == "DEGRADED":
        print("Success: MORA correctly detected the drift breach.")

    # 4. Test Uncertainty Propagation
    original_conf = 0.8
    penalized_conf = mora.propagate_uncertainty(original_conf, health_drifted['status'])
    print(f"\nOriginal Confidence: {original_conf:.1%}")
    print(f"Propagated Confidence (MORA Adjusted): {penalized_conf:.1%}")
    
    if penalized_conf < original_conf:
        print("Success: Uncertainty correctly propagated to downstream agents.")

if __name__ == "__main__":
    test_mora_logic()
