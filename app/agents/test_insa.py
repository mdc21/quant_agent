import pandas as pd
from app.agents.insa import InsightNarrativeEngine

def test_insa_logic():
    print("--- Starting Insight & Narrative Engine (INSA) Test ---")
    
    insa = InsightNarrativeEngine(api_key=None) # Using fallback
    
    # 1. Test Attribution
    print("\n[Scenario: Performance Attribution]")
    port_rets = pd.Series([0.02, 0.01, -0.01])
    bench_rets = pd.Series([0.01, 0.01, 0.01])
    
    attr = insa.calculate_attribution(port_rets, bench_rets)
    print(f"Excess Return: {attr['excess_return']:.2%}")
    print(f"Top Contributor: {attr['top_stock']}")
    
    # 2. Test Narrative Generation
    print("\n[Scenario: Narrative Generation]")
    manifest = {
        "regime": "BULL",
        "trade_count": 5,
        "var_99": 0.08
    }
    
    narrative = insa.generate_narrative(manifest, attr)
    print(f"Generated Narrative:\n{narrative}")
    
    if "BULL" in narrative and "5" in narrative:
        print("Success: Narrative correctly cited manifest data.")

    # 3. Test Goal Tracking (Critical Alert)
    print("\n[Scenario: Goal Progress & Alerting]")
    goals = [
        {"label": "Emergency Fund", "tier": 1, "success_prob": 0.92, "target_value": 1200000, "current_value": 1100000},
        {"label": "Retirement", "tier": 2, "success_prob": 0.85, "target_value": 50000000, "current_value": 30000000}
    ]
    
    report = insa.track_goal_progress(goals)
    for r in report:
        print(f"Goal: {r['label']} | Status: {r['status']} | Prob: {r['success_prob']:.1%}")
        
    if report[0]['status'] == "IMMEDIATE ACTION REQUIRED":
        print("Success: Tier 1 breach correctly triggered critical alert.")

if __name__ == "__main__":
    test_insa_logic()
