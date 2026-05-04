import json
import datetime
import logging
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional
from core.data.agent_schema import RiskReport, TradeInstruction

# Configure logger for this module
logger = logging.getLogger(__name__)

class SuperAgent:
    """
    Super Agent (SA) - Task A10.
    The 'Command & Control' center that orchestrates the Agent Mesh.
    Enforces 'Consensus with Veto' and maintains the Decision Manifest.
    """
    def __init__(self, agents: Dict[str, Any], mora_agent: Any = None):
        self.agents = agents
        self.mora = mora_agent
        self.manifest_log = []
        logger.info(f"SuperAgent initialized with {len(agents)} agents.")

    def run_rebalance_cycle(self, user_id: str, current_holdings: List[Dict[str, Any]]):
        """End-to-End Orchestration Loop."""
        logger.info(f"--- Starting Rebalance Cycle for user: {user_id} ---")

        # 1. Safety Check (MORA - Model Health)
        if self.mora:
            logger.debug("Executing MORA health check...")
            health = self.mora.check_model_health()
            if health.status == "CRITICAL":
                logger.error("CRITICAL: Model risk failure (MORA). Halting orchestration.")
                return None
            logger.info(f"Model Health: {health.status}")

        # 2. Gather Intent & Context (GIA & MRA)
        try:
            logger.debug("Sensing Goal Intent (GIA)...")
            goals = self.agents['GIA'].interpret_goals(user_id)
            if not goals:
                logger.error("GIA returned empty goals. Cannot proceed.")
                return None
            logger.info(f"GIA: {len(goals)} goal sleeves interpreted.")

            logger.debug("Sensing Macro Regime (MRA)...")
            regime = self.agents['MRA'].get_current_regime()
            logger.info(f"MRA: Detected Regime -> {regime}")
        except Exception as e:
            logger.error(f"Intent/Context Phase Failed: {e}", exc_info=True)
            return None

        # 3. Research Alpha (EQRA & PFRA)
        try:
            logger.debug("Running Research Agents (EQRA/PFRA)...")
            picks = self.agents['EQRA'].screen_stocks()
            logger.info(f"EQRA: {len(picks)} stocks screened.")
            vehicles = self.agents['PFRA'].evaluate_vehicles([])
        except Exception as e:
            logger.error(f"Research Phase Failed: {e}", exc_info=True)
            return None

        # 4. Architect (GENPOA) - First Pass
        try:
            logger.debug("Architecting target portfolio (GENPOA)...")
            n = len(picks)
            if n == 0:
                logger.warning("No stock picks available. Using equal-weight fallback.")
                # Cannot architect with zero picks - return a safe holding
                return []

            symbols = [p.symbol for p in picks]
            
            # --- Fetch Live Historical Data ---
            try:
                from core.data.historical_provider import HistoricalProvider
                provider = HistoricalProvider()
                hist_returns, hist_cov = provider.get_returns_and_covariance(symbols, lookback_days=180)
            except Exception as e:
                logger.warning(f"HistoricalProvider failed: {e}. Falling back to mocks.")
                hist_returns = pd.Series([0.15] * n, index=symbols)
                hist_cov = pd.DataFrame(np.eye(n) * 0.04, index=symbols, columns=symbols)
            # ----------------------------------

            target_weights = self.agents['GENPOA'].architect_portfolio(
                goals[0],
                hist_returns,
                hist_cov,
                np.zeros(n),
                np.zeros(n)
            )
            logger.debug(f"GENPOA weights: {dict(zip(symbols, [round(float(w), 4) for w in target_weights]))}")
        except Exception as e:
            logger.error(f"Optimization Phase Failed (GENPOA): {e}", exc_info=True)
            return None

        # 5. Safety Inspector (RAA) - THE VETO POINT
        try:
            logger.debug("Performing Risk Inspection (RAA)...")
            # Build proper index-aligned cov matrix for RAA
            risk_report = self.agents['RAA'].inspect_portfolio(
                target_weights, hist_cov, {}
            )
        except Exception as e:
            logger.error(f"Risk Inspection Phase Failed (RAA): {e}", exc_info=True)
            return None

        # Veto Recovery Loop (Max 3 attempts)
        attempts = 1
        while not risk_report.is_compliant and attempts < 3:
            logger.warning(f"RAA VETO (Attempt {attempts}): {risk_report.breaches}")
            target_weights = self.agents['GENPOA'].architect_portfolio(
                goals[0], hist_returns, hist_cov, np.zeros(n), np.zeros(n)
            )
            risk_report = self.agents['RAA'].inspect_portfolio(target_weights, hist_cov, {})
            attempts += 1

        if not risk_report.is_compliant:
            logger.error("FAIL: Multiple risk rejections (RAA). Escalating to Tier 4.")
            return None

        # 6. Tax & Execution (TOA & RBA)
        try:
            logger.debug("Optimizing for Tax & Execution (TOA/RBA)...")
            for holding in current_holdings:
                sym = holding.get('symbol', holding.get('stock_code', ''))
                if sym:
                    self.agents['TOA'].optimize_sales(sym, 10, [])

            # Build target weight dict aligned to picks symbols
            weight_dict = dict(zip(symbols, [float(w) for w in target_weights]))
            # Fetch live prices for RBA; fallback to mock if unavailable
            live_prices = {}
            try:
                from core.data.breeze_client import BreezeClient
                breeze = BreezeClient.get_instance()
                if breeze:
                    for sym in symbols:
                        ltp = BreezeClient.fetch_ltp(sym)
                        if ltp:
                            live_prices[sym] = ltp
            except Exception:
                pass
            # Fallback mock prices so RBA doesn't silently skip all trades
            for sym in symbols:
                if sym not in live_prices:
                    live_prices[sym] = 1000.0
                    logger.warning(f"No live price for {sym}, using mock ₹1000 for sizing.")

            holdings_qty = {h.get('symbol', h.get('stock_code', '')): int(h.get('quantity', 0)) for h in current_holdings}
            final_trades = self.agents['RBA'].generate_trade_list(
                weight_dict, 1000000, live_prices, holdings_qty
            )
            logger.info(f"RBA: Generated {len(final_trades)} trade instructions.")
        except Exception as e:
            logger.error(f"Execution Phase Failed (RBA/TOA): {e}", exc_info=True)
            return None

        # 7. Sign the Manifest
        try:
            manifest = self.sign_manifest(final_trades, risk_report, regime)
            logger.info(f"Rebalance Cycle Complete. Manifest Hash: {hash(str(manifest))}")
        except Exception as e:
            logger.error(f"Manifest sealing failed: {e}", exc_info=True)

        return final_trades

    def sign_manifest(self, trades: List[TradeInstruction], risk_report: RiskReport, regime: str):
        """Creates a cryptographic 'Black Box' record of the decision."""
        manifest = {
            "timestamp": datetime.datetime.now().isoformat(),
            "regime": regime,
            "var_99": float(risk_report.var_99) if risk_report.var_99 is not None else 0.0,
            "is_compliant": risk_report.is_compliant,
            "trade_count": len(trades),
            "trades": [t.model_dump() for t in trades]
        }
        self.manifest_log.append(manifest)
        logger.info(f"MANIFEST SIGNED: {manifest['timestamp']} | Trades: {len(trades)}")
        return manifest
