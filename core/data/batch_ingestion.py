import sys
import argparse
import time
from typing import List
import pandas as pd

from core.data.universe_fetcher import UniverseFetcher
from core.data.fiduciary_validator import FiduciaryValidator
from core.data.store import DataStore
from core.utils.logger import get_data_logger

logger = get_data_logger("BatchIngestion")

def run_batch_ingestion(index_name: str, delay_between_requests: int = 5):
    """
    Downloads index constituents, fetches XBRL + API fundamentals, validates them,
    and stores the final result in ArcticDB.
    """
    logger.info(f"=== Starting Batch Ingestion for {index_name} ===")
    
    fetcher = UniverseFetcher()
    symbols = fetcher.get_universe(index_name)
    
    if not symbols:
        logger.error(f"Batch Ingestion Aborted: No symbols found for {index_name}.")
        return

    validator = FiduciaryValidator()
    store = DataStore()
    lib = store.lib

    success_count = 0
    fail_count = 0

    for i, sym in enumerate(symbols):
        logger.info(f"[{i+1}/{len(symbols)}] Processing {sym}...")
        
        # 1. Dual-Feed Validation (YFinance vs Screener.in)
        is_grade, fundamentals = validator.validate_fundamentals(sym)
        
        if fundamentals:
            fundamentals['fiduciary_grade'] = is_grade
            
            # 3. Store securely in ArcticDB
            df = pd.DataFrame([fundamentals])
            if 'date' in df.columns and not df['date'].isnull().all():
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
                
            lib.write(f"FUNDAMENTALS_{sym}", df)
            success_count += 1
            logger.info(f"-> Successfully ingested fundamentals for {sym} (Fiduciary Grade: {is_grade})")
        else:
            fail_count += 1
            logger.warning(f"-> Failed to ingest fundamentals for {sym}")
            
        # Respect NSE rate limits
        if i < len(symbols) - 1:
            time.sleep(delay_between_requests)
            
    logger.info(f"=== Batch Ingestion Complete ===")
    logger.info(f"Index: {index_name}")
    logger.info(f"Success: {success_count} | Failed: {fail_count}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch Ingestion for Fundamental Data")
    parser.add_argument("--index", type=str, default="TEST BATCH", help="Index name (e.g., 'NIFTY 50')")
    parser.add_argument("--delay", type=int, default=5, help="Seconds to wait between requests")
    
    args = parser.parse_args()
    run_batch_ingestion(args.index, args.delay)
