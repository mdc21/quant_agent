import datetime
import time
import pandas as pd
from core.data.schema import MarketDataRecord
from core.data.store import DataStore
from core.data.ingestion import Ingestor, DataQualityGate

def test_pit_functionality():
    print("Starting Layer 0 PIT Verification...")
    
    # Initialize components
    store = DataStore(uri="lmdb://./data/arctic_test")
    ingestor = Ingestor(source_id="test_source")
    
    symbol = "RELIANCE"
    event_time = datetime.datetime(2024, 1, 1, 10, 0)
    
    # 1. First Ingestion (Version 1)
    record1 = MarketDataRecord(
        symbol=symbol,
        as_of_date=event_time,
        recorded_at=datetime.datetime.utcnow(),
        data_payload={"close": 2500.0, "volume": 100000},
        source_id="source_v1"
    )
    store.write_records([record1])
    print(f"Stored Version 1 at {record1.recorded_at}")
    
    time.sleep(1) # Ensure recorded_at is different
    pit_checkpoint = datetime.datetime.utcnow()
    time.sleep(1)
    
    # 2. Correction Ingestion (Version 2 - same event time, different system time)
    record2 = MarketDataRecord(
        symbol=symbol,
        as_of_date=event_time,
        recorded_at=datetime.datetime.utcnow(),
        data_payload={"close": 2505.0, "volume": 100000}, # Corrected price
        source_id="source_v1_correction"
    )
    store.write_records([record2])
    print(f"Stored Version 2 at {record2.recorded_at}")
    
    # 3. Verification
    print("\n--- Verifying PIT Lookups ---")
    
    # Read Latest
    latest = store.read_symbol(symbol)
    print(f"Latest Close Price: {latest['close'].iloc[-1]} (Expected 2505.0)")
    
    # Read at PIT Checkpoint (Should see Version 1)
    historical = store.read_symbol(symbol, as_of=pit_checkpoint)
    print(f"Historical (PIT) Close Price: {historical['close'].iloc[-1]} (Expected 2500.0)")
    
    assert latest['close'].iloc[-1] == 2505.0
    assert historical['close'].iloc[-1] == 2500.0
    print("\nSUCCESS: PIT Logic Validated.")

if __name__ == "__main__":
    test_pit_functionality()
