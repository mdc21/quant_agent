import datetime
import time
import pandas as pd
from core.data.schema import PITMarketData
from core.data.store import DataStore

def test_pit_functionality():
    print("Starting Layer 0 PIT Verification...")
    
    # Initialize components
    store = DataStore()
    
    symbol = "RELIANCE"
    event_time = datetime.datetime(2024, 1, 1, 10, 0)
    
    # 1. First Ingestion (Version 1)
    record1 = PITMarketData(
        symbol=symbol,
        exchange="NSE",
        data={"close": 2500.0, "volume": 100000},
        as_of_date=event_time,
        recorded_at=datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=10),
        lineage_id="L1",
        source="test"
    )
    store.write_records(symbol, [record1])
    print(f"Stored Version 1 at {record1.recorded_at}")
    
    time.sleep(1) # Ensure recorded_at is different
    pit_checkpoint = datetime.datetime.utcnow()
    time.sleep(1)
    
    # 2. Correction Ingestion (Version 2 - same event time, different system time)
    record2 = PITMarketData(
        symbol=symbol,
        exchange="NSE",
        data={"close": 2505.0, "volume": 100000}, # Corrected price
        as_of_date=event_time,
        recorded_at=datetime.datetime.now(datetime.timezone.utc),
        lineage_id="L1",
        source="test_correction"
    )
    store.write_records(symbol, [record2])
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
