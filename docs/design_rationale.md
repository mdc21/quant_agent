# 🛡️ YourBestPath Fiduciary Engine: Design Rationale

## 1. Objective
To build an institutional-grade quantitative engine that enforces strict capital-weighted mandates across market cap categories and sectors, while optimizing for risk-adjusted returns and transaction costs.

## 2. Key Architectural Decisions

### A. Capital-Weight vs. Stock-Count Enforcement
- **Decision**: All institutional constraints (Multi-Cap 60:25:15 and Sector Caps) are enforced at the **Capital Level (Rupee-value)** rather than simple stock counts.
- **Rationale**: Investors care about where their money is, not how many tickers they own. Count-based constraints allow for significant "capital drift" if one stock is weighted significantly higher than another.

### B. Dual-Layer Selection Pipeline
- **Decision**: The engine uses a "Target-Count Sieve" before the "Capital-Weight Optimizer."
- **Rationale**: To prevent "Small Cap Starvation" (where Large Caps win based on nominal quality scores), the engine explicitly harvests the top $N$ stocks from each category (Large, Mid, Small) to ensure a diverse and compliant candidate pool reaches the solver.

### C. Risk-Profiled Sector Diversification
- **Decision**: Sector hard ceilings are dynamic based on the user's risk mandate:
  - **Aggressive**: 25% (Allows concentration in growth clusters).
  - **Balanced**: 20%.
  - **Conservative**: 15% (Strict spreading for capital protection).
- **Rationale**: Growth is often sectoral (e.g., Tech/Energy bulls). Aggressive profiles require the flexibility to capture these trends without breaking institutional guardrails.

## 3. Mathematical Challenges & Solutions

### I. The Infeasibility Paradox
- **Challenge**: Simultaneously satisfying UCITS 5/10/40, Sector Caps, and Multi-Cap Targets is mathematically fragile.
- **Solution**: Implemented **Range-Based Constraints** (±2% buffer) and a **Cascading Fallback** mechanism in the CVXPY solver. This ensures the engine always converges on a safe, compliant portfolio even in highly restricted universes.

### II. Optimizer Concentration
- **Challenge**: Mean-Variance Optimization (MVO) naturally dilutes weights across many symbols.
- **Solution**: The pipeline restricts the optimization pool to the exact number of desired positions (`max_stocks`), forcing the solver to allocate capital precisely within the mandated set of high-conviction candidates.

## 4. Compliance & Auditability
- All decisions are cryptographically sealed in the **Layer 4 Audit Ledger**.
- The engine prioritizes **Compliance over Alpha**; any trade that would violate a sector or individual cap is automatically rejected by the `GENPOA` architect.

---
*Signed, YourBestPath Fiduciary Engine Architect*
*Dated: May 4, 2026*
