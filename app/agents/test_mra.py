import datetime
from app.agents.mra import MacroRegimeAgent
from core.data.agent_schema import M1Output

def test_mra_logic():
    print("--- Starting Macro Regime Agent (MRA) Test ---")
    
    mra = MacroRegimeAgent()
    
    # 1. Setup Historical States (90% Bull persistence)
    # 9 days of Bull, 1 transition to Sideways
    historical_states = ["Bull"] * 9 + ["Sideways"]
    
    # 2. Mock M1 Output: Prediction is "Bear" but with low confidence
    # This represents a "flicker" of bear signal in a bull market
    m1_out = M1Output(
        prediction_vector={"Bear": 0.55, "Bull": 0.20, "Sideways": 0.20, "Stagflation": 0.05},
        confidence=0.55,
        timestamp=datetime.datetime.now()
    )
    
    # 3. Process MRA
    output = mra.process_m1_output(m1_out, historical_states)
    
    print(f"\nPrior State: {historical_states[-1]}")
    print(f"M1 Prediction (Raw): Bear (55%)")
    print(f"MRA Signal (Smoothed): {output.signal['current_regime']}")
    print(f"Uncertainty Flags: {output.uncertainty_flags}")
    
    # Verification: If transition prob to Bear is zero, MRA should resist the switch
    if output.signal['current_regime'] != "Bear":
        print("Success: MRA correctly resisted the 'flicker' bear signal due to low transition probability.")

    # 4. Test Entropy Flag (Uniform distribution)
    m1_unstable = M1Output(
        prediction_vector={"Bear": 0.25, "Bull": 0.25, "Sideways": 0.25, "Stagflation": 0.25},
        confidence=0.25,
        timestamp=datetime.datetime.now()
    )
    output_unstable = mra.process_m1_output(m1_unstable, historical_states)
    
    print(f"\nUnstable Scenario Flags: {output_unstable.uncertainty_flags}")
    if "HIGH_ENTROPY_SIGNAL" in output_unstable.uncertainty_flags:
        print("Success: High entropy signal correctly flagged.")

if __name__ == "__main__":
    test_mra_logic()
