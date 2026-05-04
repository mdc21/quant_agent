import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict, field_serializer

class PITMarketData(BaseModel):
    """
    Fiduciary-grade Point-in-Time (PIT) Market Data Model.
    Enforces dual-timestamp logic and source lineage.
    """
    symbol: str = Field(..., description="Security identifier (e.g., 'RELIANCE')")
    exchange: str = Field(default="NSE", description="Exchange identifier")
    data: Dict[str, Any] = Field(..., description="Raw OHLCV or fundamental data payload")
    as_of_date: datetime.datetime = Field(..., description="The actual date/time of the market event")
    recorded_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc),
        description="System time when this data was stored (The 'PIT' tag)"
    )
    lineage_id: str = Field(..., description="Daily Session Metadata link")
    source: str = Field(default="icici_breeze_v1", description="Data lineage source")
    quality_score: float = Field(default=1.0, description="DQ validation score")

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @field_serializer('as_of_date', 'recorded_at')
    def serialize_dt(self, dt: datetime.datetime, _info):
        return dt.isoformat()
