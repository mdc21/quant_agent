from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str

class UserProfile(BaseModel):
    user_key: str
    name: str
    email: str
    role: str
    risk_profile: str
    onboarding_complete: bool

class GoalConfig(BaseModel):
    id: str
    name: str
    tier: str
    icon: str
    target: float
    horizon: int
    future_value: float
    target_value: float
    funded_pct: float
    description: str

class GoalsUpdateRequest(BaseModel):
    user_key: str
    goals: List[GoalConfig]
    risk_profile: str
    monthly_expenses: float
    inflation_rate: float = 0.06

class QuickAdviceRequest(BaseModel):
    user_key: str
    investment_type: str  # "Lump-sum" or "SIP"
    amount: float
    horizon: str
    purpose: str
    risk_profile: str

class Holding(BaseModel):
    symbol: str
    quantity: float
    avg_price: float
    current_price: Optional[float] = None
    market_value: Optional[float] = None
    pnl_pct: Optional[float] = None

class PortfolioUploadRequest(BaseModel):
    user_key: str
    holdings: List[Holding]

class RebalanceAction(BaseModel):
    asset: str
    action: str  # "EXIT", "TRIM", "HOLD", "TOP-UP", "NEW BUY"
    amount: float
    tax_harvest: str = "—"

class PortfolioReviewResponse(BaseModel):
    equity_sleeve: List[Dict[str, Any]]
    passive_sleeve: List[Dict[str, Any]]
    rebalance_plan: List[Any] # Flexible for new tax fields
    metrics: Dict[str, Any]
    narrative: str
    total_est_tax: float = 0.0

class ChatRequest(BaseModel):
    user_key: str
    question: str
    context: Optional[Dict[str, Any]] = None
    history: Optional[List[Dict[str, str]]] = None
