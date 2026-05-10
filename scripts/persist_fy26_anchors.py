import sys
import os
import pandas as pd
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.data.store import DataStore

def persist_anchors():
    store = DataStore()
    lib = store.lib
    
    # FY26 Year-End Verified Metrics (March 2026)
    anchors = {
        "KOTAKBANK": {
            "gnpa": 0.012,
            "nim": 0.0467,
            "casa_ratio": 0.433,
            "roa": 0.0214,
            "capital_culture_score": 9.5,
            "underwriting_sentiment": "ML-driven conservative growth; no loan sales.",
            "date": "2026-03-31"
        },
        "ICICIBANK": {
            "gnpa": 0.0158,
            "nim": 0.0431,
            "casa_ratio": 0.394,
            "roa": 0.023,
            "capital_culture_score": 9.0,
            "underwriting_sentiment": "Ecosystem lead growth; high risk-adjusted returns.",
            "date": "2026-03-31"
        },
        "HDFCBANK": {
            "gnpa": 0.0124,
            "nim": 0.0344,
            "casa_ratio": 0.382,
            "roa": 0.0188,
            "capital_culture_score": 8.5,
            "underwriting_sentiment": "Post-merger stabilization; focus on granular deposits.",
            "date": "2026-03-31"
        }
    }
    
    for sym, metrics in anchors.items():
        symbol_key = f"FUNDAMENTALS_{sym}"
        print(f"Updating {sym} with verified FY26 Year-End metrics...")
        
        # Read existing or create new
        if lib.has_symbol(symbol_key):
            df = lib.read(symbol_key).data
            # Update latest row or add new
            for k, v in metrics.items():
                df[k] = v
        else:
            df = pd.DataFrame([metrics])
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            
        lib.write(symbol_key, df)
        print(f"SUCCESS: {sym} hardened in ArcticDB.")

if __name__ == "__main__":
    persist_anchors()
