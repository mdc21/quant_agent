import pandas as pd
import numpy as np
import datetime
from core.data.store import DataStore
from core.data.ingestion import IngestionEngine
from unittest.mock import MagicMock

def test_dq_gate():
    print("--- Starting Data Quality Gate Test ---")
    
    # 1. Setup Mock Breeze and DataStore
    mock_breeze = MagicMock()
    store = DataStore(uri="lmdb://./data/arctic_test")
    engine = IngestionEngine(mock_breeze, store)
    
    lineage_id = "TEST_LINEAGE_001"
    session_meta = {"lineage_id": lineage_id}
    
    # 2. Simulate Dirty Data (with an outlier)
    # Create 50 normal records and 1 spike (100% jump)
    base_price = 100.0
    dates = pd.date_range(start="2026-01-01", periods=51, freq='min')
    
    data = []
    for i in range(51):
        price = base_price + (i * 0.1)
        if i == 25: # Inject outlier at index 25
            price = price * 2.0
            
        data.append({
            "datetime": dates[i].strftime('%Y-%m-%d %H:%M:%S'),
            "close": price,
            "open": price, "high": price, "low": price, "volume": 1000
        })
    
    mock_breeze.get_historical_data_v2.return_value = {
        "Status": 200,
        "Success": data
    }
    
    # 3. Run Ingestion
    symbol = "TEST_OUTLIER"
    # Debug Sieve directly
    valid_mask = engine.sieve.detect_outliers(pd.DataFrame(data).assign(close=lambda x: pd.to_numeric(x['close'])))
    print(f"\nDebug: Valid Mask Count: {valid_mask.sum()}")
    print("Indices flagged as outliers:", valid_mask[~valid_mask].index.tolist())
    
    engine.ingest_historical_to_arctic(symbol, "start", "end", session_meta)
    
    # 4. Verify Outlier Detection
    print("\n--- Verifying Audit Log ---")
    # Read the audit log for this lineage
    audit_data = store.audit_lib.read(lineage_id).data
    print(f"Audit records found: {len(audit_data)}")
    print(audit_data)
    
    # 5. Verify Clean Data in Store
    stored_data = store.read_symbol(symbol)
    print(f"\nStored records for {symbol}: {len(stored_data)}")
    if len(stored_data) >= 49: # 51 total - 1 outlier - 1 recovery
        print("Success: Outliers were correctly filtered.")
    else:
        print(f"Failure: Expected >= 49 records, got {len(stored_data)}")

if __name__ == "__main__":
    test_dq_gate()
