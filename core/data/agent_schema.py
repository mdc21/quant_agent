from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import datetime

class GoalSleeve(BaseModel):
    """
    Structured goal definition for Layer 2 Agent Mesh.
    Satisfies Section 4.2.1 of the functional specification.
    """
    label: str               # e.g., "Retirement"
    tier: int                # 1 (Survival), 2 (Safety), 3 (Growth)
    target_value: float      # Future value required (Inflation adjusted)
    horizon_years: int       # Time to goal
    min_prob_success: float  # e.g., 0.99 for Tier 1
    constraints: List[str]   # e.g., ["sector_exclude:Tobacco"]
    current_assets: float = 0.0
    monthly_savings: float = 0.0

class GoalMesh(BaseModel):
    """
    Container for the three-tier hierarchy of goals.
    """
    sleeves: List[GoalSleeve]
    user_risk_tolerance: str # "Conservative", "Moderate", "Aggressive"

class AgentOutput(BaseModel):
    """
    Standardized output for all mesh agents (Task C1).
    """
    agent_id: str
    signal: dict
    confidence: float
    rationale: str
    uncertainty_flags: List[str]

class M1Output(BaseModel):
    """
    Wrapper for the raw output from the Regime Classifier (M1).
    """
    prediction_vector: Dict[str, float] # e.g. {"Bear": 0.1, "Bull": 0.7, ...}
    confidence: float
    timestamp: datetime.datetime

class StockCandidate(BaseModel):
    """
    Structured stock recommendation from EQRA (Task A3).
    """
    symbol: str
    conviction_score: float
    rationale: str
    factors: Dict[str, Any] # e.g., {"f_score": 8, "momentum": 0.92}
    lineage_id: str

class PassiveVehicle(BaseModel):
    """
    Structured passive fund recommendation from PFRA (Task A4).
    """
    ticker: str
    category: str       # e.g., "Large Cap", "International"
    tracking_error: float
    expense_ratio: float
    liquidity_score: float
    conviction_score: float
    rationale: str

class CurrentPosition(BaseModel):
    """
    Represents an existing portfolio holding for PORA review.
    """
    symbol: str
    purchase_price: float
    current_price: float
    current_f_score: int
    entry_conviction: float
    weight: float

class PositionSignal(BaseModel):
    """
    Audit signal for an existing holding (Task A5).
    """
    symbol: str
    action: str # "HOLD", "TRIM", "EXIT"
    rationale: str
    drift_score: float # 0.0 to 1.0 (Higher means more drift)

class RiskReport(BaseModel):
    """
    Final compliance report from RAA (Task A7).
    """
    is_compliant: bool
    breaches: List[str]
    var_99: float
    mctr: Dict[str, float] # Marginal Contribution to Risk per symbol

class TaxLot(BaseModel):
    """
    Represents a specific batch of shares for tax accounting (Task A8).
    """
    symbol: str
    buy_date: datetime.datetime
    buy_price: float
    quantity: int
    current_price: float

class TaxSaleInstruction(BaseModel):
    """
    Optimized sale plan for a specific position.
    """
    symbol: str
    total_quantity: int
    lots_to_sell: List[Dict[str, Any]] # List of {"lot_index": int, "quantity": int, "tax_type": str}
    estimated_tax: float

class TradeInstruction(BaseModel):
    """
    Broker-ready order instruction (Task A9).
    """
    symbol: str
    action: str # "BUY", "SELL"
    quantity: int
    order_type: str # "LIMIT", "MARKET"
    estimated_price: float
    total_value: float
    rationale: str
