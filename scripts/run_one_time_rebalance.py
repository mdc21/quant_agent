import logging
import datetime
import pandas as pd
import numpy as np
from app.agents.super_agent import SuperAgent
from app.agents.gia import GoalInterpretationAgent
from app.agents.mra import MacroRegimeAgent
from app.agents.eqra import EquityResearchAgent
from app.agents.pfra import PassiveResearchAgent
from app.agents.pora import PortfolioReviewAgent
from app.agents.genpoa import PortfolioArchitect
from app.agents.raa import RiskAnalysisAgent
from app.agents.toa import TaxOptimizationAgent
from app.agents.rba import RebalancingAgent
from core.risk.mora import ModelRiskAgent
from core.data.breeze_client import BreezeClient
from app.agents.governance import GovernanceAgent
from core.data.store import DataStore

# --- Configure Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("FiduciaryEngine")

def run_live_rebalance():
    logger.info("🚀 INITIALIZING LIVE FIDUCIARY REBALANCE CYCLE...")
    
    # 1. Connect to Breeze
    session_token = "55426264" 
    try:
        BreezeClient.get_instance(session_token)
        logger.info("✅ Breeze API Connected & Authenticated.")
    except Exception as e:
        logger.error(f"❌ Connection Failed: {e}")
        return

    # 2. Initialize Agents & Mesh
    store = DataStore()
    agents_mesh = {
        'GIA': GoalInterpretationAgent(),
        'MRA': MacroRegimeAgent(),
        'EQRA': EquityResearchAgent(),
        'PFRA': PassiveResearchAgent(),
        'PORA': PortfolioReviewAgent(),
        'GENPOA': PortfolioArchitect(),
        'RAA': RiskAnalysisAgent(),
        'TOA': TaxOptimizationAgent(),
        'RBA': RebalancingAgent()
    }
    sa = SuperAgent(agents_mesh, mora_agent=ModelRiskAgent(store))
    gov = GovernanceAgent()

    # 3. Fetch Live Portfolio
    logger.info("🔍 Querying live holdings from ICICI...")
    breeze = BreezeClient.get_instance()
    portfolio = breeze.get_portfolio_holdings()
    
    holdings = []
    if portfolio.get("Status") == 200 and portfolio.get("Success"):
        holdings = portfolio["Success"]
        logger.info(f"✅ Active Positions Found: {len(holdings)}")
    else:
        logger.warning("No active holdings found. Running in 'New Capital Deployment' mode.")

    # 4. Execute Orchestration
    logger.info("🧠 Orchestrating Agent Mesh Consensus...")
    try:
        trades = sa.run_rebalance_cycle(user_id="PROD_USER_001", current_holdings=holdings)
        
        # 5. Cryptographic Sealing
        if trades is not None:
            manifest = {
                "regime": "BULL", 
                "trade_count": len(trades),
                "timestamp": datetime.datetime.now().isoformat(),
                "trades": [t.dict() for t in trades]
            }
            gov.seal_decision(manifest)
            logger.info("✅ CYCLE COMPLETE. Decision manifest cryptographically sealed in Layer 4.")
            logger.info(f"Fiduciary Signal: {len(trades)} trades suggested for optimization.")
        else:
            logger.warning("Cycle halted: Risk Veto or Model Health breach detected.")
            
    except Exception as e:
        logger.error(f"Engine Orchestration Error: {e}", exc_info=True)

if __name__ == "__main__":
    run_live_rebalance()
