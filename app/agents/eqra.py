import pandas as pd
import numpy as np
from typing import List, Dict, Any
from core.data.agent_schema import StockCandidate

class EquityResearchAgent:
    """
    Equity Research Agent (EQRA).
    The 'Stock Picker' using QARP (Quality at a Reasonable Price).
    Satisfies Task A3 of the Agent Mesh.
    """
    def __init__(self, min_f_score: int = 7, min_roce: float = 0.15):
        self.min_f_score = min_f_score
        self.min_roce = min_roce

    def calculate_qarp_score(self, fundamentals: Dict[str, Any]) -> int:
        """
        Calculates a 4-point Quality At a Reasonable Price (QARP) Score 
        using verified ArcticDB Fiduciary metrics.
        """
        score = 0
        net_income = fundamentals.get('net_income', 0)
        cfo = fundamentals.get('operating_cash_flow', 0)
        assets = fundamentals.get('total_assets', 0)
        liabilities = fundamentals.get('total_liabilities', float('inf'))
        
        # 1. Profitability
        if net_income > 0: score += 1
        
        # 2. Cash Generation
        if cfo > 0: score += 1
        
        # 3. Earnings Quality (Cash > Profit)
        if cfo > net_income: score += 1
        
        # 4. Solvency
        if liabilities < assets: score += 1
            
        return score

    def screen_stocks(self, index_name: str = "NIFTY 50") -> List[StockCandidate]:
        """
        Queries ArcticDB for pre-ingested fundamentals of the target universe.
        """
        from core.data.universe_fetcher import UniverseFetcher
        from core.data.store import DataStore
        
        print(f"EQRA: Initiating screen for universe: {index_name}")
        fetcher = UniverseFetcher()
        store = DataStore()
        lib = store.lib
        
        if index_name == "ALL":
            symbols = [sym.replace("FUNDAMENTALS_", "") for sym in store.list_symbols() if sym.startswith("FUNDAMENTALS_")]
        else:
            symbols = fetcher.get_universe(index_name)
            
        if not symbols:
            print(f"EQRA: No symbols found for {index_name}")
            return []
            
        live_universe = {}
        
        for sym in symbols:
            symbol_key = f"FUNDAMENTALS_{sym}"
            try:
                if lib.has_symbol(symbol_key):
                    df = lib.read(symbol_key).data
                    if not df.empty:
                        fundamentals = df.iloc[0].to_dict()
                        live_universe[sym] = fundamentals
                else:
                    print(f"EQRA: Missing pre-ingested data for {sym}. Run batch ingestion first.")
            except Exception as e:
                print(f"EQRA: Error reading {sym} from vault: {e}")

        if not live_universe:
            return []

        # --- P2: Real 12-1 month momentum (replaces flat 0.75 constant) ---
        from core.data.momentum_calculator import MomentumCalculator
        universe_symbols = list(live_universe.keys())
        print(f"EQRA: Computing 12-1 month momentum scores for {len(universe_symbols)} symbols...")
        try:
            calc = MomentumCalculator()
            momentum = calc.compute_momentum_scores(universe_symbols)
        except Exception as e:
            print(f"EQRA: Momentum computation failed ({e}). Falling back to neutral 0.5.")
            momentum = {sym: 0.5 for sym in universe_symbols}
        
        return self.screen_universe(live_universe, momentum)

    def screen_universe(self, universe_fundamentals: Dict[str, Dict[str, Any]], price_momentum: Dict[str, float]) -> List[StockCandidate]:
        """
        Runs the multi-stage sieve to identify candidates using Fiduciary metrics.
        """
        candidates = []
        
        for symbol, fundamentals in universe_fundamentals.items():
            # Calculate ROA
            assets = fundamentals.get('total_assets', 0)
            net_income = fundamentals.get('net_income', 0)
            roa = (net_income / assets) if assets > 0 else 0
            
            # Stage 1: Quality Gate (QARP Score)
            q_score = self.calculate_qarp_score(fundamentals)
            
            # Stage 2: Fundamental Screen
            # --- Core gates (always enforced) ---
            passes_quality = (
                q_score >= 2 and        # At least 2/4 on QARP
                roa >= 0.015            # Min 1.5% ROA (allows banks & capital-heavy Ind-AS)
            )

            # --- P3: ROCE > 15% gate (enforced only when data exists in vault) ---
            roce = fundamentals.get('roce', None)
            if roce is not None and roce > 0:
                # Data exists — apply the spec filter
                passes_roce = roce >= self.min_roce   # default 0.15 = 15%
            else:
                # Field not yet in vault (old record) — skip filter, don't penalise
                passes_roce = True

            # --- P3: FCF positive in ≥ 3 of last 4 years gate ---
            fcf_positive = fundamentals.get('fcf_positive_years', None)
            fcf_checked = fundamentals.get('fcf_years_checked', 0)
            if fcf_positive is not None and fcf_checked >= 3:
                # Data exists — apply the spec filter (3 of last 4 years)
                passes_fcf = fcf_positive >= 3
            else:
                # Field not yet in vault — skip filter
                passes_fcf = True

            passes_fundamental = passes_quality and passes_roce and passes_fcf
            
            if passes_fundamental:
                # Stage 3: Momentum Overlay
                momentum_rank = price_momentum.get(symbol, 0.0)
                
                # Final Conviction Score: 60% Quality + 40% Momentum
                quality_normalized = q_score / 4.0
                conviction = (0.6 * quality_normalized) + (0.4 * momentum_rank)
                
                # Get Fiduciary Grade
                fiduciary_grade = fundamentals.get('fiduciary_grade', False)

                # Build rationale with all available signals
                rationale_parts = [
                    f"QARP: {q_score}/4",
                    f"ROA: {roa:.1%}",
                    f"Momentum: {momentum_rank:.0%}ile",
                    f"Fiduciary: {fiduciary_grade}",
                ]
                if roce is not None:
                    rationale_parts.append(f"ROCE: {roce:.1%}")
                if fcf_positive is not None:
                    rationale_parts.append(f"FCF+yrs: {fcf_positive}/{fcf_checked}")
                
                candidates.append(StockCandidate(
                    symbol=symbol,
                    conviction_score=conviction,
                    rationale=" | ".join(rationale_parts),
                    factors={
                        "q_score": q_score,
                        "momentum": momentum_rank,
                        "roa": roa,
                        "roce": roce if roce is not None else 0.0,
                        "fcf_positive_years": fcf_positive if fcf_positive is not None else 0,
                        "fiduciary_grade": fiduciary_grade,
                    },
                    lineage_id=fundamentals.get('lineage_id', 'UNKNOWN')
                ))
                
        # Sort by conviction
        return sorted(candidates, key=lambda x: x.conviction_score, reverse=True)
