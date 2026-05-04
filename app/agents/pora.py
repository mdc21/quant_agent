import pandas as pd
from typing import List, Dict, Any, Optional
from core.data.agent_schema import PositionSignal, CurrentPosition, StockCandidate

class PortfolioReviewAgent:
    """
    Portfolio Review Agent (PORA).
    The 'Sunk Cost Killer' that continuously justifies every position.
    Satisfies Task A5 of the Agent Mesh.
    """
    def __init__(self, stop_loss_limit: float = 0.15, min_f_score: int = 5):
        self.stop_loss_limit = stop_loss_limit
        self.min_f_score = min_f_score

    def audit_portfolio(
        self, 
        current_holdings: List[CurrentPosition], 
        buy_list: List[StockCandidate],
        esg_data: Dict[str, str] = {}
    ) -> List[PositionSignal]:
        """
        Runs the three pillars of review: Style Drift, Momentum Decay, and Compliance.
        """
        signals = []
        buy_list_symbols = [c.symbol for c in buy_list]
        
        for pos in current_holdings:
            # Pillar 1: Hard Stop-Loss (15% drop)
            returns = (pos.current_price / pos.purchase_price) - 1
            if returns <= -self.stop_loss_limit:
                signals.append(PositionSignal(
                    symbol=pos.symbol,
                    action="EXIT",
                    rationale=f"Hard Stop-Loss Triggered: {returns:.1%} loss",
                    drift_score=1.0
                ))
                continue

            # Pillar 2: Style/Fundamental Drift
            if pos.current_f_score < self.min_f_score:
                signals.append(PositionSignal(
                    symbol=pos.symbol,
                    action="EXIT",
                    rationale=f"Style Drift: F-Score {pos.current_f_score} < {self.min_f_score}",
                    drift_score=0.9
                ))
                continue

            # Pillar 3: ESG & Compliance Watchdog
            if esg_data.get(pos.symbol) == "RESTRICTED":
                signals.append(PositionSignal(
                    symbol=pos.symbol,
                    action="EXIT",
                    rationale="Compliance Breach: Asset moved to Restricted List",
                    drift_score=1.0
                ))
                continue

            # Pillar 4: The Replacement Test (Momentum Decay)
            # If the stock is no longer in the top 50 candidates, suggest a TRIM
            if pos.symbol not in buy_list_symbols[:50]:
                # Check how much the conviction has dropped
                current_candidate = next((c for c in buy_list if c.symbol == pos.symbol), None)
                curr_conviction = current_candidate.conviction_score if current_candidate else 0.0
                conviction_gap = pos.entry_conviction - curr_conviction
                
                signals.append(PositionSignal(
                    symbol=pos.symbol,
                    action="TRIM",
                    rationale=f"Momentum Decay: Conviction dropped by {conviction_gap:.2f}. Better candidates available.",
                    drift_score=min(1.0, max(0.0, conviction_gap * 2))
                ))
            else:
                # Thesis remains intact
                signals.append(PositionSignal(
                    symbol=pos.symbol,
                    action="HOLD",
                    rationale="Thesis Intact: High quality and momentum maintained.",
                    drift_score=0.0
                ))
                
        return signals
