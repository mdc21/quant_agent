import sys
from core.data.universe_fetcher import UniverseFetcher
from core.data.store import DataStore
import warnings

# Suppress pandas warnings for cleaner output
warnings.filterwarnings("ignore")

print("--- 1. Testing NSE Archives UniverseFetcher ---")
fetcher = UniverseFetcher()
try:
    symbols = fetcher.get_universe("NIFTY 50")
    if symbols:
        print(f"SUCCESS: Fetched {len(symbols)} symbols from NSE Archives for NIFTY 50.")
        print(f"First 5 symbols: {symbols[:5]}")
    else:
        print("FAILED: No symbols fetched.")
except Exception as e:
    print(f"ERROR fetching universe: {e}")

print("\n--- 2. Testing ArcticDB Storage ---")
store = DataStore()
try:
    lib = store.lib
    # Check if the fundamental data we just ingested exists
    if lib.has_symbol("FUNDAMENTALS_RELIANCE"):
        print("SUCCESS: 'FUNDAMENTALS_RELIANCE' found in ArcticDB!")
        df = lib.read("FUNDAMENTALS_RELIANCE").data
        print("\nData Snapshot:")
        print(df.to_string())
    else:
        print("FAILED: 'FUNDAMENTALS_RELIANCE' NOT found in ArcticDB.")
        print(f"Available symbols in library: {store.list_symbols()[:10]}")
except Exception as e:
    print(f"ERROR reading ArcticDB: {e}")
