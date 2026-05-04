import numpy as np
import pandas as pd
from app.agents.raa import RiskAnalysisAgent

def test_raa_logic():
    print("--- Starting Risk Analysis Agent (RAA) Test ---")
    
    raa = RiskAnalysisAgent(single_stock_cap=0.08, sector_cap=0.25)
    symbols = ["RELIANCE", "TCS", "INFY", "HDFC", "CASH"]
    sector_map = {
        "RELIANCE": "Energy",
        "TCS": "IT",
        "INFY": "IT",
        "HDFC": "Financials",
        "CASH": "Cash"
    }
    
    # Setup Covariance (Moderate Vol)
    n = len(symbols)
    cov_data = np.eye(n) * 0.04 # 20% vol each
    cov_data[4, 4] = 0.0 # CASH has ZERO vol
    cov_matrix = pd.DataFrame(cov_data, index=symbols, columns=symbols)
    
    # 1. Test Concentration Breach (15% in RELIANCE)
    print("\n[Scenario: Single Stock Concentration Breach]")
    weights_concentrated = np.array([0.15, 0.20, 0.20, 0.25, 0.20])
    report_conc = raa.inspect_portfolio(weights_concentrated, cov_matrix, sector_map)
    
    print(f"Is Compliant: {report_conc.is_compliant}")
    for breach in report_conc.breaches:
        print(f"BREACH: {breach}")
        
    if "RELIANCE" in report_conc.breaches[0] and not report_conc.is_compliant:
        print("Success: Single stock breach correctly flagged.")

    # 2. Test Sector Breach (IT Sector: TCS + INFY = 40%)
    print("\n[Scenario: Sector Concentration Breach]")
    # RELIANCE 5%, IT 40%, HDFC 25%, CASH 30%
    weights_sector = np.array([0.05, 0.20, 0.20, 0.25, 0.30])
    report_sector = raa.inspect_portfolio(weights_sector, cov_matrix, sector_map)
    
    for breach in report_sector.breaches:
        print(f"BREACH: {breach}")
        
    if any("Sector Breach: IT" in b for b in report_sector.breaches):
        print("Success: Sector breach (IT > 25%) correctly flagged.")

    # 3. Test VaR Sensitivity (Equity vs Cash)
    print("\n[Scenario: VaR Sensitivity]")
    weights_equity = np.array([0.25, 0.25, 0.25, 0.25, 0.00])
    weights_cash = np.array([0.05, 0.05, 0.05, 0.05, 0.80])
    
    var_equity = raa.calculate_var_99(weights_equity, cov_matrix)
    var_cash = raa.calculate_var_99(weights_cash, cov_matrix)
    
    print(f"100% Equity VaR (99%): {var_equity:.1%}")
    print(f"80% Cash VaR (99%): {var_cash:.1%}")
    
    if var_cash < var_equity * 0.5:
        print("Success: VaR correctly reflected risk reduction from cash.")

    # 4. Test MCTR
    print("\n[Scenario: Marginal Contribution to Risk]")
    report_mctr = raa.inspect_portfolio(weights_equity, cov_matrix, sector_map)
    print("MCTR per Asset:")
    for symbol, risk in report_mctr.mctr.items():
        print(f"  {symbol}: {risk:.4f}")

if __name__ == "__main__":
    test_raa_logic()
