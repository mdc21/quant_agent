import sys
import os
import pandas as pd
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.data.store import DataStore
from core.data.fiduciary_validator import FiduciaryValidator

def rehydrate_symbols(symbols):
    store = DataStore()
    lib = store.lib
    validator = FiduciaryValidator()
    
    for sym in symbols:
        symbol_key = f"FUNDAMENTALS_{sym}"
        print(f"\n--- Rehydrating {sym} ---")
        
        # 1. Clear existing data to force refresh
        if lib.has_symbol(symbol_key):
            print(f"Removing existing record for {symbol_key}...")
            lib.delete(symbol_key)
        
        # 2. Trigger fresh validation (this will fetch the new specialized ratios)
        print(f"Triggering deep fiduciary hydration for {sym}...")
        is_grade, fundamentals = validator.validate_fundamentals(sym)
        
        if fundamentals:
            # 3. Persist new data back to ArcticDB
            df_to_save = pd.DataFrame([fundamentals])
            if 'date' in df_to_save.columns and not df_to_save['date'].isnull().all():
                df_to_save['date'] = pd.to_datetime(df_to_save['date'])
                df_to_save.set_index('date', inplace=True)
            
            lib.write(symbol_key, df_to_save)
            print(f"SUCCESS: {sym} hydrated with new metrics.")
            print(f"Metrics: GNPA: {fundamentals.get('gnpa')}, CASA: {fundamentals.get('casa_ratio')}, NIM: {fundamentals.get('nim')}")
        else:
            print(f"ERROR: Failed to hydrate {sym}.")

if __name__ == "__main__":
    target_symbols = sys.argv[1:]
    if not target_symbols:
        print("Usage: python3 scripts/rehydrate_financials.py SYMBOL1 SYMBOL2 ...")
        # Default to a few elite banks if no args provided
        target_symbols = ["HDFCBANK", "ICICIBANK", "KOTAKBANK", "AXISBANK", "SBIN"]
    
    rehydrate_symbols(target_symbols)
