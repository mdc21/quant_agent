import datetime
import pandas as pd
from typing import List, Dict, Any, Optional
from .schema import PITMarketData
from .store import DataStore

from .sieve import DataSieve

class IngestionEngine:
    """
    Fiduciary PIT Ingestion Engine for Layer 0.
    """
    def __init__(self, breeze_client, store: DataStore):
        self.breeze = breeze_client
        self.store = store
        self.sieve = DataSieve()

    def ingest_historical_to_arctic(self, symbol: str, from_date: str, to_date: str, session_meta: Dict[str, Any]):
        """
        Pulls historical data from Breeze API and stores it in ArcticDB with PIT tagging.
        """
        print(f"Fetching historical data for {symbol} from {from_date} to {to_date}...")
        
        # 1. Fetch raw data from Breeze API
        raw_data = self.breeze.get_historical_data_v2(
            interval="1day",
            from_date=from_date,
            to_date=to_date,
            stock_code=symbol,
            exchange_code="NSE",
            product_type="cash"
        )

        if raw_data.get('Status') != 200:
            print(f"Error fetching data from Breeze: {raw_data.get('Error')}")
            return

        # 2. Transform into DataFrame for Sieve
        df_raw = pd.DataFrame(raw_data.get('Success', []))
        if df_raw.empty:
            print(f"No records found for {symbol} in the specified range.")
            return

        # Ensure numeric columns
        df_raw['close'] = pd.to_numeric(df_raw['close'])
        
        # 3. Data Sieve (Outlier Detection)
        valid_mask = self.sieve.detect_outliers(df_raw)
        
        clean_df = df_raw[valid_mask]
        quarantined_df = df_raw[~valid_mask]
        
        if not quarantined_df.empty:
            self.store.log_quality_event(
                "OUTLIER_DETECTED", 
                {"symbol": symbol, "count": len(quarantined_df), "indices": quarantined_df.index.tolist()},
                session_meta['lineage_id']
            )

        # 4. Transform clean data into PIT Records
        pit_records = []
        for _, entry in clean_df.iterrows():
            record = PITMarketData(
                symbol=symbol,
                exchange="NSE",
                data=entry.to_dict(),
                as_of_date=pd.to_datetime(entry['datetime']),
                recorded_at=datetime.datetime.now(datetime.timezone.utc),
                lineage_id=session_meta['lineage_id'],
                source="icici_breeze_v1"
            )
            pit_records.append(record)

        # 5. Write to ArcticDB (Layer 0 Storage)
        if pit_records:
            self.store.write_records(
                symbol, 
                pit_records, 
                metadata={'source': 'icici_direct', 'pit_validated': True}
            )
            print(f"Successfully stored {len(pit_records)} PIT-tagged records for {symbol}.")
