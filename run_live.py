import time
import datetime
import os
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

def run_always_on_loop(session_token: str):
    print("=========================================================")
    print("   QA-1 QUANT ENGINE: LIVE AUTONOMOUS LOOP ACTIVE        ")
    print("=========================================================\n")
    
    # 1. Initialize Breeze Session
    try:
        BreezeClient.get_instance(session_token)
        print(f"Breeze API connected via session: {session_token[:4]}...")
    except Exception as e:
        print(f"FAILED TO INITIALIZE BREEZE: {e}")
        return

    # 2. Initialize Agent Mesh
    from core.data.store import DataStore
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
    
    mora = ModelRiskAgent(store)
    sa = SuperAgent(agents_mesh, mora_agent=mora)
    
    print("Agents Initialized. Starting fiduciary monitoring...")
    
    while True:
        try:
            print(f"\n[Cycle Started: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]")
            
            # Fetch actual portfolio holdings from Breeze
            breeze = BreezeClient.get_instance()
            portfolio = breeze.get_portfolio_holdings()
            
            holdings = []
            if portfolio.get("Status") == 200 and portfolio.get("Success"):
                holdings = portfolio["Success"]
                print(f"Fetched {len(holdings)} live positions from ICICI account.")
            else:
                print("No live holdings found or error fetching. Using empty portfolio.")
            
            # Run the Master Orchestrator
            trades = sa.run_rebalance_cycle(user_id="PROD_USER_001", current_holdings=holdings)
            
            if trades:
                print(f"Orchestration complete. {len(trades)} trade instructions generated and sealed.")
            else:
                print("No rebalance signals detected for current regime.")
                
            print("Monitoring... Next cycle in 24 hours.")
            time.sleep(86400) 
            
        except KeyboardInterrupt:
            print("\nShutting down gracefully...")
            break
        except Exception as e:
            print(f"ERROR: {e}. Retrying in 1 hour.")
            time.sleep(3600)

if __name__ == "__main__":
    # Use the token provided by the user
    ACTIVE_TOKEN = "55426264" 
    run_always_on_loop(ACTIVE_TOKEN)
