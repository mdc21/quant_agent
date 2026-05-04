import os
from dotenv import load_dotenv
from breeze_connect import BreezeConnect
from core.data.store import DataStore
from core.data.ingestion import IngestionEngine
import datetime

# Load credentials
load_dotenv()

def run_historical_ingestion():
    api_key = os.getenv("ICICIDIRECT_API_KEY")
    secret_key = os.getenv("ICICIDIRECT_SECRET_KEY")
    session_token = "55426099" # From previous verification
    
    # Initialize Breeze
    breeze = BreezeConnect(api_key=api_key)
    breeze.generate_session(api_secret=secret_key, session_token=session_token)
    
    # Session Metadata for Lineage [cite: 59]
    session_meta = {
        "lineage_id": f"SESS_{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d_%H%M%S')}",
        "source_api": "icici_breeze_v1"
    }
    
    # Initialize Layer 0 Store and Engine
    store = DataStore(uri="lmdb://./data/arctic")
    engine = IngestionEngine(breeze, store)
    
    # Define time range (using last 5 days to ensure we hit a trading day)
    symbol = "RELIND" 
    to_date = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.000Z")
    from_date = (datetime.datetime.now() - datetime.timedelta(days=5)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    
    # Execute Ingestion
    engine.ingest_historical_to_arctic(
        symbol=symbol,
        from_date=from_date,
        to_date=to_date,
        session_meta=session_meta
    )
    
    # Verify by reading back
    print("\n--- Verifying ArcticDB Storage ---")
    if symbol in store.list_symbols():
        data = store.read_symbol(symbol)
        print(f"Retrieved {len(data)} records from ArcticDB for {symbol}.")
        print(data.tail())
    else:
        print(f"Verification Failed: Symbol {symbol} not found in ArcticDB. Check if ingestion was successful.")

if __name__ == "__main__":
    run_historical_ingestion()
