import unittest
from unittest.mock import MagicMock
import numpy as np
import pandas as pd
from app.agents.super_agent import SuperAgent
from core.data.agent_schema import RiskReport, TradeInstruction, GoalSleeve

class TestSuperAgent(unittest.TestCase):
    def setUp(self):
        # Mocking all agents
        self.mocks = {
            'GIA': MagicMock(),
            'MRA': MagicMock(),
            'EQRA': MagicMock(),
            'PFRA': MagicMock(),
            'PORA': MagicMock(),
            'GENPOA': MagicMock(),
            'RAA': MagicMock(),
            'TOA': MagicMock(),
            'RBA': MagicMock()
        }
        self.sa = SuperAgent(self.mocks)

    def test_orchestration_cycle(self):
        print("\n--- Testing Super Agent Orchestration Cycle ---")
        
        # 1. Setup Mock Returns
        self.mocks['GIA'].interpret_goals.return_value = [
            GoalSleeve(label="Test", tier=1, target_value=1e6, horizon_years=10, min_prob_success=0.99, constraints=[])
        ]
        self.mocks['MRA'].get_current_regime.return_value = "BULL"
        from core.data.agent_schema import StockCandidate
        self.mocks['EQRA'].screen_stocks.return_value = [
            StockCandidate(symbol="RELIND", conviction_score=0.8, rationale="Quality", factors={}, lineage_id="L1"),
            StockCandidate(symbol="TCS", conviction_score=0.7, rationale="Stability", factors={}, lineage_id="L1")
        ]
        
        # GENPOA returns target weights
        self.mocks['GENPOA'].architect_portfolio.return_value = np.array([0.5, 0.5])
        
        # RAA returns compliant report
        self.mocks['RAA'].inspect_portfolio.return_value = RiskReport(
            is_compliant=True, breaches=[], var_99=0.08, mctr={}
        )
        
        # RBA returns trades
        self.mocks['RBA'].generate_trade_list.return_value = [
            TradeInstruction(symbol="RELIND", action="BUY", quantity=10, order_type="LIMIT", 
                             estimated_price=2500, total_value=25000, rationale="...")
        ]
        
        # 2. Run Cycle
        trades = self.sa.run_rebalance_cycle("user_123", [{"symbol": "RELIND"}])
        
        # 3. Assertions
        self.assertEqual(len(trades), 1)
        self.assertEqual(len(self.sa.manifest_log), 1)
        self.assertEqual(self.sa.manifest_log[0]['regime'], "BULL")
        print("Success: Super Agent successfully orchestrated the full chain.")

    def test_veto_recovery(self):
        print("\n--- Testing Super Agent Veto Recovery ---")
        
        # Setup first call to RAA to FAIL, second to PASS
        fail_report = RiskReport(is_compliant=False, breaches=["Concentration"], var_99=0.20, mctr={})
        pass_report = RiskReport(is_compliant=True, breaches=[], var_99=0.10, mctr={})
        
        self.mocks['RAA'].inspect_portfolio.side_effect = [fail_report, pass_report]
        
        # Other mocks
        from core.data.agent_schema import StockCandidate
        self.mocks['EQRA'].screen_stocks.return_value = [
            StockCandidate(symbol="RELIND", conviction_score=0.8, rationale="Quality", factors={}, lineage_id="L1")
        ]
        self.mocks['GIA'].interpret_goals.return_value = [MagicMock()]
        self.mocks['MRA'].get_current_regime.return_value = "SIDEWAYS"
        self.mocks['GENPOA'].architect_portfolio.return_value = np.array([0.4, 0.4])
        self.mocks['RBA'].generate_trade_list.return_value = []
        
        # Run Cycle
        self.sa.run_rebalance_cycle("user_123", [])
        
        # Should have called RAA twice
        self.assertEqual(self.mocks['RAA'].inspect_portfolio.call_count, 2)
        print("Success: Super Agent correctly handled Veto and recovered.")

if __name__ == "__main__":
    unittest.main()
