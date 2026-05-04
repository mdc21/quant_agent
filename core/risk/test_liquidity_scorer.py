from core.risk.liquidity_scorer import LiquidityScorer

def test_liquidity_scorer():
    print("--- Starting Liquidity Scorer (M5) Test ---")
    
    scorer = LiquidityScorer(max_dtl=20, max_adv_pct=0.05)
    
    # 1. Stress Test: Large Position in Small-Cap
    # Position: 10 Crore (100,000,000 INR)
    # ADV: 1 Crore (10,000,000 INR)
    position_value = 100_000_000
    adv_small = 10_000_000
    
    print("\n[Scenario: 10 Crore Position in 1 Crore ADV Stock]")
    metrics = scorer.calculate_metrics("SMALLCAP_XYZ", position_value, adv_small)
    
    print(f"DTL: {metrics['dtl']:.1f} days")
    print(f"Liquidity Score: {metrics['liquidity_score']:.1f}")
    print(f"Status: {metrics['status']}")
    for alert in metrics['alerts']:
        print(f"ALERT: {alert}")
        
    if metrics['status'] == "BREACH" and metrics['liquidity_score'] == 0:
        print("Success: Scorer correctly identified extreme illiquidity.")

    # 2. Healthy Scenario: Large Position in Blue Chip
    # Position: 10 Crore
    # ADV: 500 Crore (5,000,000,000 INR)
    adv_blue = 5_000_000_000
    print("\n[Scenario: 10 Crore Position in 500 Crore ADV Stock]")
    metrics_blue = scorer.calculate_metrics("BLUECHIP_ABC", position_value, adv_blue)
    
    print(f"DTL: {metrics_blue['dtl']:.2f} days")
    print(f"Liquidity Score: {metrics_blue['liquidity_score']:.1f}")
    print(f"Status: {metrics_blue['status']}")
    
    if metrics_blue['status'] == "HEALTHY" and metrics_blue['liquidity_score'] > 90:
        print("Success: Blue chip stock correctly scored high for liquidity.")

    # 3. Portfolio Buffer Check
    total_val = 1_000_000_000 # 100 Crore
    cash = 20_000_000       # 2 Crore (2% - Should Fail)
    
    is_safe = scorer.validate_portfolio_buffer(total_val, cash)
    print(f"\nPortfolio Buffer Check (2% Cash): {'SAFE' if is_safe else 'INSUFFICIENT'}")
    if not is_safe:
        print("Success: Scorer correctly flagged insufficient cash buffer.")

if __name__ == "__main__":
    test_liquidity_scorer()
