import pandas as pd
from arcticdb import Arctic
from typing import List, Optional, Dict, Any
import datetime
from .schema import PITMarketData

from core.data.db import get_arctic

class DataStore:
    """
    ArcticDB-based Time-Series Store with PIT (Point-In-Time) support.
    """
    def __init__(self, uri: str = "lmdb://./data/arctic"):
        self.arctic = get_arctic(uri)
        
        if "market_data" not in self.arctic.list_libraries():
            self.arctic.create_library("market_data")
        if "audit_log" not in self.arctic.list_libraries():
            self.arctic.create_library("audit_log")
        if "user_goals" not in self.arctic.list_libraries():
            self.arctic.create_library("user_goals")
        if "user_portfolios" not in self.arctic.list_libraries():
            self.arctic.create_library("user_portfolios")
            
        self.lib = self.arctic.get_library("market_data")
        self.audit_lib = self.arctic.get_library("audit_log")
        self.goals_lib = self.arctic.get_library("user_goals")
        self.portfolio_lib = self.arctic.get_library("user_portfolios")

    def log_quality_event(self, event_type: str, details: Dict[str, Any], lineage_id: str):
        """
        Records a data quality event in the immutable audit log.
        """
        event = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc),
            "event_type": event_type,
            "details": str(details),
            "lineage_id": lineage_id,
            "status": "QUARANTINED" if "OUTLIER" in event_type else "APPLIED"
        }
        df = pd.DataFrame([event])
        df.set_index("timestamp", inplace=True)
        
        # Append to the audit log library
        self.audit_lib.append(lineage_id, df)
        print(f"Audit Logged: {event_type} for {lineage_id}")

    def write_records(self, symbol: str, records: List[PITMarketData], metadata: Optional[Dict[str, Any]] = None):
        """
        Writes PIT-tagged records to the store.
        """
        if not records:
            return

        # Convert records to DataFrame for ArcticDB
        data = []
        for r in records:
            row = {
                "as_of_date": r.as_of_date,
                "recorded_at": r.recorded_at,
                "lineage_id": r.lineage_id,
                "source": r.source,
                "quality_score": r.quality_score,
                **r.data
            }
            data.append(row)
        
        df = pd.DataFrame(data)
        df.set_index("as_of_date", inplace=True)
        
        # Write/Update the symbol in ArcticDB
        self.lib.write(
            symbol, 
            df, 
            metadata=metadata or {'pit_validated': True}
        )

    def read_symbol(self, symbol: str, as_of: Optional[datetime.datetime] = None) -> pd.DataFrame:
        """
        Reads data for a symbol. If as_of is provided, it performs a PIT lookup.
        """
        if symbol not in self.list_symbols():
            print(f"Warning: Symbol {symbol} not found in library.")
            return pd.DataFrame()

        if as_of:
            return self.lib.read(symbol, as_of=as_of).data
        else:
            return self.lib.read(symbol).data

    def list_symbols(self) -> List[str]:
        return self.lib.list_symbols()

    def save_goals(self, user_id: str, goals: List[Dict[str, Any]], risk_tolerance: str = "Moderate", inflation_rate: float = 0.06, **kwargs):
        """
        Saves user goals, risk tolerance, and inflation rate to the user_goals library.
        """
        df = pd.DataFrame(goals)
        # Store metadata like risk_tolerance and inflation_rate in the version metadata
        self.goals_lib.write(
            user_id, 
            df, 
            metadata={
                "risk_tolerance": risk_tolerance, 
                "inflation_rate": inflation_rate,
                "updated_at": str(datetime.datetime.now())
            }
        )
        print(f"Goals saved for user: {user_id} with inflation_rate: {inflation_rate}")

    def get_goals(self, user_id: str) -> Dict[str, Any]:
        """
        Retrieves user goals and risk tolerance.
        """
        if user_id not in self.goals_lib.list_symbols():
            return {}
        
        version = self.goals_lib.read(user_id)
        return {
            "goals": version.data.to_dict('records'),
            "risk_tolerance": version.metadata.get("risk_tolerance", "Moderate"),
            "inflation_rate": version.metadata.get("inflation_rate", 0.06)
        }

    def save_portfolio(self, user_id: str, holdings: List[Dict[str, Any]], metadata: Optional[Dict[str, Any]] = None):
        """
        Saves user portfolio holdings.
        """
        df = pd.DataFrame(holdings)
        self.portfolio_lib.write(
            user_id, 
            df, 
            metadata={
                **(metadata or {}),
                "updated_at": str(datetime.datetime.now())
            }
        )
        print(f"Portfolio saved for user: {user_id}")

    def get_portfolio(self, user_id: str) -> Dict[str, Any]:
        """
        Retrieves user portfolio holdings.
        """
        if user_id not in self.portfolio_lib.list_symbols():
            return {}
        
        version = self.portfolio_lib.read(user_id)
        return {
            "holdings": version.data.to_dict('records'),
            "metadata": version.metadata
        }
