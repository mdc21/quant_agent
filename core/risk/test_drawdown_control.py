from core.risk.drawdown_control import DrawdownControlModel

def test_drawdown_control():
    print("--- Starting Drawdown Control (M6) Test ---")
    
    # Target 15% Vol, 20% MDD Max, Multiplier 3
    model = DrawdownControlModel(multiplier=3.0, target_vol=0.15, mdd_max=0.20)
    
    # 1. Healthy Scenario
    # Value: 100 Crore, Floor: 80 Crore, Vol: 15% (Target)
    portfolio_value = 1_000_000_000
    floor_value = 800_000_000
    vol_normal = 0.15
    
    print("\n[Scenario: Healthy Market]")
    res_normal = model.calculate_cppi_signals(portfolio_value, floor_value, vol_normal)
    print(f"Risky Allocation Target: {res_normal['risky_allocation_target']:.1%}")
    print(f"Cushion Status: {res_normal['cushion_status']:.1%}")
    
    if res_normal['risky_allocation_target'] >= 0.6:
        print("Success: Healthy cushion allows for significant risky allocation.")

    # 2. Crash Survival Test
    # Portfolio drops to 85 Crore (Close to Floor)
    portfolio_crash = 850_000_000
    print("\n[Scenario: Market Crash - Approaching Floor]")
    res_crash = model.calculate_cppi_signals(portfolio_crash, floor_value, vol_normal)
    print(f"Risky Allocation Target: {res_crash['risky_allocation_target']:.1%}")
    
    if res_crash['risky_allocation_target'] < 0.2:
        print("Success: CPPI correctly compressed risky exposure to protect the floor.")

    # 3. Volatility Targeting Response
    # Cushion is healthy (100 Crore), but volatility spikes to 45%
    vol_spike = 0.45
    print("\n[Scenario: Volatility Spike - 45% Realized Vol]")
    res_vol = model.calculate_cppi_signals(portfolio_value, floor_value, vol_spike)
    print(f"Vol Scalar: {res_vol['vol_scalar']:.2f}")
    print(f"Risky Allocation Target: {res_vol['risky_allocation_target']:.1%}")
    
    if res_vol['risky_allocation_target'] < res_normal['risky_allocation_target'] * 0.5:
        print("Success: Volatility targeting correctly scaled down exposure.")

    # 4. Drawdown Governor Trigger
    print("\n[Scenario: Drawdown Governor Alert]")
    # Current drawdown 16% (80% of 20% limit)
    res_gov = model.calculate_cppi_signals(portfolio_value, floor_value, vol_normal, current_drawdown=0.16)
    print(f"Status: {res_gov['status']}")
    for alert in res_gov['alerts']:
        print(f"ALERT: {alert}")
        
    if res_gov['status'] == "DEFENSIVE_WARNING":
        print("Success: Governor correctly triggered at 80% MDD threshold.")

if __name__ == "__main__":
    test_drawdown_control()
