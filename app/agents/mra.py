import numpy as np
import pandas as pd
from typing import List, Dict, Any
from core.data.agent_schema import AgentOutput, M1Output

class MacroRegimeAgent:
    """
    Macro Regime Agent (MRA).
    The 'Economic Historian' that contextualizes AI predictions.
    Satisfies Task A2 of the Agent Mesh.
    """
    def __init__(self, states: List[str] = ["Bear", "Sideways", "Bull", "Stagflation"]):
        self.states = states
        self.state_to_idx = {state: i for i, state in enumerate(states)}
        self.transition_matrix = None

    def get_current_regime(self) -> str:
        """
        Convenience method for SuperAgent orchestration.
        In production, this queries Layer 1 models.
        """
        # Mocking current regime fetch
        return "Bull"

    def compute_transition_matrix(self, historical_states: List[str]):
        """
        Calculates the 90-day rolling transition matrix P(State_t | State_t-1).
        """
        n = len(self.states)
        matrix = np.zeros((n, n))
        
        # Count transitions
        for i in range(len(historical_states) - 1):
            curr_state = historical_states[i]
            next_state = historical_states[i+1]
            if curr_state in self.state_to_idx and next_state in self.state_to_idx:
                matrix[self.state_to_idx[curr_state]][self.state_to_idx[next_state]] += 1
        
        # Normalize to probabilities
        for i in range(n):
            row_sum = matrix[i].sum()
            if row_sum > 0:
                matrix[i] = matrix[i] / row_sum
            else:
                # Fallback: high persistence (self-transition)
                matrix[i][i] = 1.0
                
        self.transition_matrix = matrix
        return matrix

    def process_m1_output(self, m1_output: M1Output, historical_states: List[str]) -> AgentOutput:
        """
        Bayesian update and instability detection.
        """
        # 1. Update Transition Matrix
        self.compute_transition_matrix(historical_states)
        
        # 2. Bayesian Update
        prior_state = historical_states[-1]
        prior_idx = self.state_to_idx.get(prior_state, 1) # Default Sideways
        
        raw_probs = m1_output.prediction_vector
        raw_vec = np.array([raw_probs.get(s, 0.0) for s in self.states])
        
        # Combine ML prediction with Persistence probability from matrix
        persistence_vec = self.transition_matrix[prior_idx]
        
        # Bayesian Update: Posterior is proportional to Prior * Likelihood
        # Here we treat ML prediction as Likelihood and Transition Probs as Prior
        posterior_vec = raw_vec * persistence_vec
        if posterior_vec.sum() > 0:
            posterior_vec = posterior_vec / posterior_vec.sum()
        else:
            posterior_vec = raw_vec # Fallback
            
        posterior_probs = {s: float(posterior_vec[i]) for i, s in enumerate(self.states)}
        
        # 3. Detect Instability
        uncertainty_flags = []
        if m1_output.confidence < 0.60:
            uncertainty_flags.append("HIGH_TRANSITION_RISK")
            
        # Entropy Check (Uniform distribution = High Entropy)
        entropy = -np.sum(posterior_vec * np.log(posterior_vec + 1e-9))
        if entropy > 1.2: # Threshold for high uncertainty in 4-state system
            uncertainty_flags.append("HIGH_ENTROPY_SIGNAL")

        current_regime = self.states[np.argmax(posterior_vec)]
        
        return AgentOutput(
            agent_id="MRA",
            signal={"current_regime": current_regime, "probs": posterior_probs},
            confidence=float(np.max(posterior_vec)),
            rationale=f"Market context updated from {prior_state}. Stability probability applied.",
            uncertainty_flags=uncertainty_flags
        )
