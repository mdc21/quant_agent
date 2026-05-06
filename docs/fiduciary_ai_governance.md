# YourBestPath Fiduciary AI: Functional & Design Governance

This document outlines the functional architecture and design decisions governing the **YourBestPath Fiduciary AI** (Insight & Narrative Engine - INSA). It serves as the definitive reference for how the system provides transparent, defensible financial advice.

## 1. Functional Architecture: The 4-Layer Cascade

To ensure 100% availability and fiduciary compliance, INSA utilizes a hierarchical fallback mechanism:

1.  **Tier 1: High-Reasoning (GPT-4o)** – Used for complex cross-portfolio analysis and goal-feasibility narratives.
2.  **Tier 2: High-Speed (Groq/Llama 3.1)** – Parallel fallback for standard chat queries to ensure sub-second response times.
3.  **Tier 3: Reliability (Gemini 1.5 Flash)** – Broad-reach fallback with high token limits for deep document/manifest parsing.
4.  **Tier 4: Deterministic Guardrail (Local Engine)** – A rule-based fallback that generates responses using local math and logic if all external APIs are offline. This prevents "hallucination by silence."

## 2. Design Decision: Comparative Context Manifest

A core design principle is that the AI never "guesses." Every prompt is injected with an **Immutable Decision Manifest**.

### Functional Data Structure:
```json
{
  "amount": 38274882.0,
  "risk_profile": "Aggressive",
  "investor_portfolio": [
    {"Symbol": "INDUSTOWER", "market_value": 2277355, "avg_buy_price": 210}
  ],
  "proposed_portfolio": {
    "equity_sleeve": [{"symbol": "HINDUNILVR", "target_weight": 0.08}],
    "passive_sleeve": [{"ticker": "CPSEETF", "target_weight": 0.0667}]
  }
}
```

**Decision Rationale**: By providing both [EXISTING] and [PROPOSED] portfolios, the AI can perform **Migration Attribution**—explaining exactly why an investor should sell a specific legacy holding to fund a high-ROCE fiduciary alternative.

## 3. System Prompt Strategy

The system prompt is structured to enforce a **Fiduciary Persona**:

*   **Transparency First**: Every answer must reference the selection criteria (ROCE > 1.5%, FCF Quality).
*   **Guardrail Awareness**: The AI is aware of UCITS 5/10/40 and 20% Sector Ceiling limits.
*   **Non-Apologetic Professionalism**: The AI acts as a peer to institutional advisors, not a submissive chatbot.

---

## 4. Real-World Interaction Examples (Audit Log)

The following examples are captured from `app/data/llm_calls.log`.

### Example A: Explaining Selection Criteria (ROCE)
**User**: *"Explain the ROCE filter used in this portfolio"*  
**AI Response (Groq)**:  
> "As the YourBestPath Fiduciary AI, I'd be happy to explain the Return on Capital Employed (ROCE) filter... We set a minimum threshold of 1.5%. For instance, NATIONALUM has an ROCE of 3.8% (Healthy), while HINDCOPPER has 0.0%, suggesting it is not generating profit effectively and may be re-examined."

### Example B: Comparative Rebalancing Logic
**User**: *"Why is my investor portfolio volatility less than the proposed portfolio?"*  
**AI Response (Groq)**:  
> "After reviewing the composition, the current portfolio contains a significant allocation to passive funds (Liquid Bees, Gold Bees, Gilt Bees at 6.7% each). These funds exhibit lower volatility than the proposed 80% equity-skewed aggressive plan. Our rebalancing strategy prioritizes high-ROCE alpha, which inherently increases volatility compared to your cash-heavy legacy holdings."

### Example C: Handling Market Write-offs
**User**: *"There are stocks in my portfolio not found (probably no longer traded). What is the action?"*  
**AI Response (Groq)**:  
> "In accordance with our fiduciary duty, I recommend liquidating these non-traded holdings where possible or writing them off to ₹0 to ensure your capital allocation reflects live market reality. We will re-deploy any recovered value into UCITS-compliant funds that meet our 1.5% ROCE threshold."

---

## 5. Auditability & Governance
Every LLM call is logged in `app/data/llm_calls.log` with:
*   `timestamp`: ISO format for chronological audit.
*   `provider`: Which tier of the cascade responded.
*   *input*: The full system prompt + manifest.
*   `output`: The raw text provided to the investor.

This log ensures that the system's "advice" can be back-tested and verified against fiduciary standards at any time.
