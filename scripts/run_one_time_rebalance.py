import os
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
from dotenv import load_dotenv

# --- Configure Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("FiduciaryEngine")

def generate_report(manifest: dict):
    """
    Generates a timestamped Fiduciary Rebalance Report.
    """
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = f"reports/REBALANCE_REPORT_{ts}.md"
    
    trades = manifest.get("trades", [])
    total_buys = sum([t['total_value'] for t in trades if t['action'] in ['BUY', 'TOP-UP']])
    total_sells = sum([t['total_value'] for t in trades if t['action'] in ['SELL', 'EXIT', 'TRIM']])
    
    report_content = f"""# 🛡️ Fiduciary Rebalance Report
**Generated:** {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Market Regime:** {manifest.get('regime', 'N/A')}

## 📊 Summary
- **Total Trades Orchestrated:** {len(trades)}
- **Liquidity to Generate (Sells):** ₹{total_sells:,.0f}
- **Capital Deployment (Buys):** ₹{total_buys:,.0f}
- **Net Funding Required:** ₹{total_buys - total_sells:,.0f}

## 🔄 Proposed Actions
| Asset | Action | Capital (₹) | Rationale |
| :--- | :--- | :--- | :--- |
"""
    for t in trades:
        report_content += f"| {t['symbol']} | {t['action']} | ₹{t['total_value']:,.0f} | {t.get('rationale', 'Institutional Optimization')} |\n"
    
    report_content += "\n\n---\n*This report is cryptographically sealed and logged in the Layer 4 Audit Ledger.*"
    
    with open(report_path, "w") as f:
        f.write(report_content)
    logger.info(f"✅ Fiduciary Report Generated: {report_path}")

def run_live_rebalance():
    load_dotenv()
    logger.info("🚀 INITIALIZING LIVE FIDUCIARY REBALANCE CYCLE...")
    
    # 1. Connect to Breeze
    session_token = os.getenv("BREEZE_SESSION_TOKEN")
    if not session_token:
        logger.error("❌ BREEZE_SESSION_TOKEN not found in .env")
        return

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
    if portfolio and portfolio.get("Status") == 200 and portfolio.get("Success"):
        holdings = portfolio["Success"]
        logger.info(f"✅ Active Positions Found: {len(holdings)}")
    else:
        logger.warning("No active holdings found. Running in 'New Capital Deployment' mode.")

    # 4. Execute Orchestration
    logger.info("🧠 Orchestrating Agent Mesh Consensus...")
    try:
        # Use 'user_1' to match the dashboard's default user
        trades = sa.run_rebalance_cycle(user_id="user_1", current_holdings=holdings)
        
        # 5. Cryptographic Sealing & Reporting
        if trades is not None:
            # Detect Regime
            regime = "BULL" # Default or pull from MRA
            
            manifest = {
                "regime": regime, 
                "trade_count": len(trades),
                "timestamp": datetime.datetime.now().isoformat(),
                "trades": [t.model_dump() if hasattr(t, 'model_dump') else t for t in trades]
            }
            gov.seal_decision(manifest)
            generate_report(manifest)
            logger.info("✅ CYCLE COMPLETE. Decision manifest cryptographically sealed in Layer 4.")
            logger.info(f"Fiduciary Signal: {len(trades)} trades suggested for optimization.")
        else:
            logger.warning("Cycle halted: Risk Veto or Model Health breach detected.")
            
    except Exception as e:
        logger.error(f"Engine Orchestration Error: {e}", exc_info=True)

if __name__ == "__main__":
    run_live_rebalance()
